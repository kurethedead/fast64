import bpy, gpu, mathutils
from .material import CustomRenderEngineMaterialSettings
from .default_shaders import VERTEX_SHADER, PIXEL_SHADER, GEOMETRY_SHADER
from gpu_extras.batch import batch_for_shader
from gpu.types import GPUBatch, GPUShader
import numpy as np
from typing import List

RGB_TO_LUM_COEF = mathutils.Vector([0.2126729, 0.7151522, 0.0721750])


# TODO: This was copied from utility.py
def colorToLuminance(color: mathutils.Color | list[float] | mathutils.Vector):
    # https://github.com/blender/blender/blob/594f47ecd2d5367ca936cf6fc6ec8168c2b360d0/intern/cycles/render/shader.cpp#L387
    # These coefficients are used by Blender, so we use them as well for parity between Fast64 exports and Blender color conversions
    return RGB_TO_LUM_COEF.dot(color[:3])


# class MeshShader:
#     def __init__(self, vertex_path, pixel_path, geometry_path=None):
#         if len(vertex_path) == 0 or len(pixel_path) == 0:
#             raise ValueError
#         vertex = open(vertex_path).read()
#         pixel = open(pixel_path).read()
#         geometry = ""
#         if geometry_path:
#             geometry = open(geometry_path).read()

#         self.shader = gpu.types.GPUShader(vertex, pixel, geocode=geometry)

#     def texture(self, name: str, image: bpy.types.Image, col_fallback: typing.Tuple[float, float, float]):
#         if image:
#             tex = gpu.texture.from_image(image)
#         else:
#             tex = gpu.types.GPUTexture((1, 1))
#             tex.clear(format="FLOAT", value=(1, 1, 1, 1))
#         self.shader.uniform_sampler(name, tex)


# https://docs.blender.org/api/4.0/gpu.types.html#gpu.types.GPUShader
class MaterialShader:
    def __init__(self, material: bpy.types.Material):
        # vertex, fragment, geometry shaders
        self.shader = gpu.types.GPUShader(
            open("shaders/VertexShader.glsl").read(),
            open("shaders/BasePassPixelShader.glsl").read(),
            geocode=open("shaders/GeometryShader.glsl").read(),
        )
        # print("compiling material: " + ("default" if not material else material.name), flush=True)
        self.material: bpy.types.Material = material
        self.f3d_state_frag: gpu.types.GPUUniformBuf = None
        self.create_ubo(material)
        self.update()

    def create_ubo(self, material: bpy.types.Material):
        data = bytearray([i for i in range(16)])
        self.f3d_state_frag = gpu.types.GPUUniformBuf(data)

    def update(self):
        self.tbasecolor = gpu.types.GPUTexture((1, 1))
        self.tbasecolor.clear(format="FLOAT", value=(1, 1, 1, 1))

        self.tshadowtint = gpu.types.GPUTexture((1, 1))
        self.tshadowtint.clear(format="FLOAT", value=(0, 0, 0, 1))

        try:
            basecolor = bpy.data.images[self.material.custom_settings.tex_base_color]
            self.tbasecolor = gpu.texture.from_image(basecolor)
        except (AttributeError, KeyError):
            pass

        try:
            shadowtint = bpy.data.images[self.material.custom_settings.tex_shadow_tint]
            self.tshadowtint = gpu.texture.from_image(shadowtint)
        except (AttributeError, KeyError):
            pass

        if self.material:
            self.col_basecolor = tuple(self.material.diffuse_color[:3])
            # print(f"{self.material} {self.col_basecolor}", flush=True)
            self.shadingmodel = CustomRenderEngineMaterialSettings.get_shadingmodel_value(
                self.material.custom_settings.shading_model
            )
            # print(f"{self.material.name} {self.shadingmodel}", flush=True)
        else:
            self.col_basecolor = (1, 1, 1)
            self.shadingmodel = 1

    def bind(self):
        self.shader.bind()
        self.shader.uniform_block("f3d_state_frag", self.f3d_state_frag)
        self.shader.uniform_sampler("tbasecolor", self.tbasecolor)
        self.shader.uniform_sampler("tshadowtint", self.tshadowtint)
        self.shader.uniform_float("col_basecolor", self.col_basecolor)
        self.shader.uniform_int("shadingmodel", self.shadingmodel)
        return self.shader


class BatchData:
    def __init__(self, batch: GPUBatch, material_shader: MaterialShader, mesh_ubo: gpu.types.GPUUniformBuf):
        self.batch = batch
        self.material_shader = material_shader
        self.f3d_state_vert = mesh_ubo


class MeshDraw:
    def __init__(self, mesh: bpy.types.Mesh, material_shaders: dict[int, MaterialShader]):
        self.batches: List[BatchData] = []
        self.default_shader: gpu.types.GPUShader = gpu.types.GPUShader(
            VERTEX_SHADER, PIXEL_SHADER, geocode=GEOMETRY_SHADER
        )
        self.f3d_state_vert: gpu.types.GPUUniformBuf = None

        # calculate loops
        mesh.calc_loop_triangles()
        try:
            mesh.calc_tangents()
        except:
            pass

        # split mesh data into separate arrays
        # gpu functions take in 2D arrays, but we have to pass reshaped versions to foreach_get since that function flattens data
        vertices = np.empty((len(mesh.loops), 3), dtype=np.float32)
        color = np.full((len(mesh.loops), 4), [0.5, 0.5, 1, 1], dtype=np.float32)
        normals = np.empty((len(mesh.loops), 3), dtype=np.float32)
        tangents = np.empty((len(mesh.loops), 3), dtype=np.float32)
        bitangent_signs = np.empty(len(mesh.loops), dtype=np.half)
        uvs = np.zeros((len(mesh.loops), 2), dtype=np.float32)

        coords = np.empty((len(mesh.vertices), 3), dtype=np.float32)
        mesh.vertices.foreach_get("co", np.reshape(coords, len(mesh.vertices) * 3))
        loop_vertices = np.empty(len(mesh.loops), dtype=np.int)
        mesh.loops.foreach_get("vertex_index", loop_vertices)
        vertices = coords[loop_vertices]

        mesh.loops.foreach_get("normal", np.reshape(normals, len(mesh.loops) * 3))
        mesh.loops.foreach_get("tangent", np.reshape(tangents, len(mesh.loops) * 3))
        mesh.loops.foreach_get("bitangent_sign", bitangent_signs)
        bitangent_signs = np.negative(bitangent_signs)

        uvLayer = mesh.uv_layers["UVMap"] if "UVMap" in mesh.uv_layers else None
        if uvLayer and len(uvLayer.data) > 0:
            uvLayer.data.foreach_get("uv", np.reshape(uvs, len(mesh.loops) * 2))

        colorLayer = mesh.vertex_colors["Col"] if "Col" in mesh.vertex_colors else None
        alphaLayer = mesh.vertex_colors["Alpha"] if "Alpha" in mesh.vertex_colors else None
        if colorLayer and len(colorLayer.data) > 0:
            colorLayer.data.foreach_get("color", np.reshape(color, len(mesh.loops) * 4))

        # TODO: Is this conversion too slow?
        if alphaLayer and len(alphaLayer.data) > 0:
            color = np.asarray(
                [
                    [
                        value[0],
                        value[1],
                        value[2],
                        colorToLuminance(alphaLayer.data[index].color),
                    ]
                    for index, value in enumerate(color)
                ]
            )

        # split mesh by materials
        facesByMat = {}
        for face in mesh.loop_triangles:
            if face.material_index not in facesByMat:
                facesByMat[face.material_index] = []
            facesByMat[face.material_index].append(face)

        self.batches = []
        for matIndex, faces in facesByMat.items():
            indices = np.array([face.loops for face in faces])

            if matIndex in material_shaders:
                material_shader = material_shaders[matIndex]
                shader = material_shader.shader
                mesh_ubo = self.create_mesh_ubo(material_shader.material)
            else:
                material_shader = None
                shader = self.default_shader
                mesh_ubo = None

            # currently all mesh data is sent for each material section, with indices determining what to draw
            # TODO: Is it faster to pre split all mesh data per section? We wouldn't be able to use foreach_get in that case.
            self.batches.append(
                BatchData(
                    batch_for_shader(
                        shader,
                        "TRIS",
                        {
                            "position": vertices,
                            "normal": normals,
                            "tangent": tangents,
                            "bitangent_sign": bitangent_signs,
                            "uv": uvs,
                            "color": color,
                        },
                        indices=indices,
                    ),
                    material_shader,
                    mesh_ubo,
                )
            )

    def create_mesh_ubo(self, material: bpy.types.Material) -> gpu.types.GPUUniformBuf:
        data = bytearray([i for i in range(16)])
        # TODO: pass most of f3d state in through here
        return gpu.types.GPUUniformBuf(data)

    def draw(self, transform, view_projection_matrix, settings, texture=None):
        for batchData in self.batches:
            if batchData.material_shader is None:
                shader = self.default_shader
                shader.bind()
            else:
                shader = batchData.material_shader.bind()

            if batchData.f3d_state_vert is not None:
                shader.uniform_block("f3d_state_vert", batchData.f3d_state_vert)
            shader.uniform_float("matrix_world", transform)
            shader.uniform_float("mat_view_projection", view_projection_matrix)

            shader.uniform_bool("render_outlines", [settings.enable_outline])
            shader.uniform_float("outline_width", settings.outline_width)
            shader.uniform_float("outline_color", settings.outline_color)
            shader.uniform_float("depth_scale_exponent", settings.outline_depth_exponent)
            shader.uniform_bool("use_vertexcolor_alpha", [settings.use_vertexcolor_alpha])
            shader.uniform_bool("use_vertexcolor_rgb", [settings.use_vertexcolor_rgb])

            # if settings.basecolor_texture:
            #     tbasecolor = gpu.texture.from_image(bpy.data.images[settings.basecolor_texture])
            # else:
            #     tbasecolor = gpu.types.GPUTexture((1, 1))
            #     tbasecolor.clear(format="FLOAT", value=(0.5, 0.5, 0.5, 1))
            # shader.uniform_sampler("tbasecolor", tbasecolor)

            # if settings.shadowtint_texture:
            #     tshadowtint = gpu.texture.from_image(bpy.data.images[settings.shadowtint_texture])
            # else:
            #     tshadowtint = gpu.types.GPUTexture((1, 1))
            #     tshadowtint.clear(format="FLOAT", value=(0, 0, 0, 1))
            # shader.uniform_sampler("tshadowtint", tshadowtint)

            # tbasecolor = gpu.types.GPUTexture((1, 1))
            # tbasecolor.clear(format="FLOAT", value=(1, 1, 1, 1))
            # tshadowtint = gpu.types.GPUTexture((1, 1))
            # tshadowtint.clear(format="FLOAT", value=(0, 0, 0, 1))
            # self.shader.bind()
            # self.shader.uniform_sampler("tbasecolor", tbasecolor)
            # self.shader.uniform_sampler("tshadowtint", tshadowtint)

            batchData.batch.draw(shader)

    def draw_forward(self, transform, region_data, lights, settings):
        def min(a, b):
            if a > b:
                return b
            else:
                return a

        self.shader.bind()
        try:
            self.shader.uniform_float("matrix_world", transform)
            # self.shader.uniform_float("perspective_matrix", perspective_matrix)
            self.shader.uniform_float("view_matrix", region_data.view_matrix)
            self.shader.uniform_float("projection_matrix", region_data.window_matrix)
            packed_lights = mathutils.Matrix.Diagonal(mathutils.Vector((0, 0, 0, 0)))
            for i in range(min(len(lights), 4)):
                packed_lights[i].xyz = lights[i].xyz  # direction
                packed_lights[i].w = lights[i].w  # strength
            self.shader.uniform_float("directional_lights", packed_lights.transposed())
            self.shader.uniform_bool("render_outlines", [settings.enable_outline])
            self.shader.uniform_float("shading_sharpness", settings.shading_sharpness)
            self.shader.uniform_float("fresnel_fac", settings.fresnel_fac)
            self.shader.uniform_float("world_color", settings.world_color)

            self.shader.uniform_float("outline_width", settings.outline_width)
            self.shader.uniform_float("depth_scale_exponent", settings.outline_depth_exponent)
            self.shader.uniform_bool("use_vertexcolor_alpha", [settings.use_vertexcolor_alpha])
            self.shader.uniform_bool("use_vertexcolor_rgb", [settings.use_vertexcolor_rgb])

            try:
                if settings.basecolor_texture:
                    tbasecolor = gpu.texture.from_image(bpy.data.images[settings.basecolor_texture])
                else:
                    tbasecolor = gpu.types.GPUTexture((1, 1))
                    tbasecolor.clear(format="FLOAT", value=(0.5, 0.5, 0.5, 1))
                self.shader.uniform_sampler("tbasecolor", tbasecolor)

                if settings.shadowtint_texture:
                    tshadowtint = gpu.texture.from_image(bpy.data.images[settings.basecolor_texture])
                else:
                    tshadowtint = gpu.types.GPUTexture((1, 1))
                    tshadowtint.clear(format="FLOAT", value=(0, 0, 0, 1))
                self.shader.uniform_sampler("tshadowtint", tshadowtint)

            except KeyError:
                pass
        except ValueError:
            pass
        self.batch.draw(self.shader)
