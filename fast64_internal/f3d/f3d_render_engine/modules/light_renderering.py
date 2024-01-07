import gpu, mathutils, math
from .default_shaders import VERTEX_2D
from .material import CustomRenderEngineMaterialSettings
from gpu_extras.batch import batch_for_shader


# https://docs.blender.org/api/4.0/gpu.types.html#gpu.types.GPUShader
class LightRendering:
    def __init__(self, light_object):
        self.object = light_object
        # self.create_shader_info()
        self.create_shader()

    def get_defines(self):
        return CustomRenderEngineMaterialSettings.get_shadingmodels_define()

    # def create_shader_info(self):
    #     self.shaderinfo = gpu.types.GPUShaderCreateInfo()
    #     self.shaderinfo.vertex_source(VERTEX_2D)
    #     pixel_shader_source = open(get_path("shaders/DeferredLightPixelShader.glsl")).read()
    #     self.shaderinfo.fragment_source(pixel_shader_source)

    def create_shader(self):
        # self.shader = gpu.shader.create_from_info(self.shaderinfo)
        pixel_shader_source = open("shaders/DeferredLightPixelShader.glsl").read()
        self.shader = gpu.types.GPUShader(
            VERTEX_2D, pixel_shader_source, defines=self.get_defines()
        )
        self.batch = batch_for_shader(
            self.shader, "TRI_FAN", {"pos": ((0, 0), (1, 0), (1, 1), (0, 1))}
        )

    def set_uniforms(self, region_data):
        try:
            self.shader.uniform_float(
                "energy", self.object.data.energy * self.energy_factor
            )
            # self.shader.uniform_float("energy", self.object.data.energy)
        except ValueError:
            # optimized out by shader compiler
            pass
        try:
            self.shader.uniform_float(
                "mat_view_projection",
                region_data.window_matrix @ region_data.view_matrix,
            )
        except ValueError:
            # this is dumb
            pass
        try:
            self.shader.uniform_float("light_color", self.object.data.color)
        except ValueError:
            pass

    def draw(
        self, region_data, tdepth, tbasecolor, tshadowcolor, tworldnormal, tshadingmodel
    ):
        shader = self.shader
        shader.bind()
        shader.uniform_sampler("tdepth", tdepth)
        shader.uniform_sampler("tbasecolor", tbasecolor)
        shader.uniform_sampler("tshadowcolor", tshadowcolor)
        shader.uniform_sampler("tworldnormal", tworldnormal)
        shader.uniform_sampler("tshadingmodel", tshadingmodel)

        self.set_uniforms(region_data)

        self.batch.draw(shader)


class DirectionalLightRendering(LightRendering):
    def __init__(self, light_object):
        assert light_object.data.type == "SUN"
        super().__init__(light_object)
        self.energy_factor = 1
        light_direction = mathutils.Vector((0, 0, 1))
        light_direction.rotate(light_object.matrix_world.decompose()[1])
        self.direction = light_direction

    def get_defines(self):
        return (
            super().get_defines()
            + """
            #define DIRECTIONAL_LIGHT 1
        """
        )

    # def create_shader_info(self):
    #     super().create_shader_info()
    #     self.shaderinfo.define("DIRECTIONAL_LIGHT", "1")

    def set_uniforms(self, region_data):
        super().set_uniforms(region_data)
        shader = self.shader
        shader.uniform_float("light_direction", self.direction)


class LocalLightRendering(LightRendering):
    def __init__(self, light_object):
        assert light_object.data.type in ("POINT", "SPOT", "AREA")
        super().__init__(light_object)
        self.energy_factor = 0.09
        light = light_object.data

        # this cannot get instanced lights' location (eg. paticle systems, geometry nodes)
        # maybe try to fix that?
        self.location = light_object.matrix_world.to_translation()

        if light.use_custom_distance:
            self.attenuation = self.cutoff_distance
        else:
            self.attenuation = -1

    def get_defines(self):
        return (
            super().get_defines()
            + """
            #define LOCAL_LIGHT 1
        """
            + f"\n#define {self.object.data.type}_LIGHT 1\n"
        )

    def set_uniforms(self, region_data):
        super().set_uniforms(region_data)
        shader = self.shader
        shader.uniform_float("light_location", self.location)

        light = self.object.data
        if light.type == "SPOT":
            light_direction = mathutils.Vector((0, 0, 1))
            light_direction.rotate(self.object.matrix_world.decompose()[1])
            shader.uniform_float("light_spot_direction", light_direction)
            shader.uniform_float("light_spot_size", light.spot_size / math.pi)
            shader.uniform_float("light_spot_blend", light.spot_blend)
