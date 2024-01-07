import math, bpy, gpu
from gpu_extras.batch import batch_for_shader
from .material import CustomRenderEngineMaterialSettings
from .settings import Fast64RenderEngineSettings, Fast64RenderEnginePanel
from .light_settings import Fast64RenderEngineLightPanel
from .light_renderering import DirectionalLightRendering, LocalLightRendering
from .mesh_rendering import MeshDraw, MaterialShader
from .default_shaders import (
    VERTEX_2D,
    PIXEL_2D,
    PIXEL_RGBL,
    PIXEL_FXAA,
    PIXEL_DEFERRED_WORLDPOS,
    PIXEL_SHADINGMODEL,
    PIXEL_SCENE_LIGHTING,
)


# https://docs.blender.org/api/current/bpy.types.RenderEngine.html
class Fast64RenderEngine(bpy.types.RenderEngine):
    # These three members are used by blender to set up the
    # RenderEngine; define its internal name, visible name and capabilities.
    bl_idname = "FAST64"
    bl_label = "Fast64"
    bl_use_preview = True

    # Hides Cycles node trees in the node editor.
    bl_use_shading_nodes_custom = False

    # Init is called whenever a new render engine instance is created. Multiple
    # instances may exist at the same time, for example for a viewport and final
    # render.
    def __init__(self):
        self.scene_data = None
        self.draw_data = None
        self.draw_calls = {}
        self.lights = []
        self.mesh_objects = []
        self.material_shaders = dict()

    # When the render engine instance is destroy, this is called. Clean up any
    # render engine data here, for example stopping running render threads.
    def __del__(self):
        pass

    def get_settings(self, context):
        return context.scene.f3d_render_engine_settings

    # This is the method called by Blender for both final renders (F12) and
    # small preview for materials, world and lights.
    def render(self, depsgraph):
        scene = depsgraph.scene
        scale = scene.render.resolution_percentage / 100.0
        self.size_x = int(scene.render.resolution_x * scale)
        self.size_y = int(scene.render.resolution_y * scale)

        # Fill the render result with a flat color. The framebuffer is
        # defined as a list of pixels, each pixel itself being a list of
        # R,G,B,A values.
        if self.is_preview:
            color = [0.1, 0.2, 0.1, 1.0]
        else:
            color = [0.2, 0.1, 0.1, 1.0]

        pixel_count = self.size_x * self.size_y
        rect = [color] * pixel_count

        # Here we write the pixel values to the RenderResult
        result = self.begin_result(0, 0, self.size_x, self.size_y)
        layer = result.layers[0].passes["Combined"]
        layer.rect = rect
        self.end_result(result)

    def create_mesh_draw(self, meshObj: bpy.types.Object):
        material_shaders: dict[int, MaterialShader] = {}
        for i in range(len(meshObj.material_slots)):
            material = meshObj.material_slots[i].material
            if material is not None:
                material_shaders[i] = MaterialShader(material)

        return MeshDraw(meshObj.data, material_shaders)

    def add_material_user(self, mesh, material):
        if not material.name in self.materials_users:
            self.materials_users[material.name] = set()
        self.materials_users[material.name].add(mesh)

    def update_material_user(self, mesh, old_material, new_material):
        self.materials_users[old_material.name].remove(mesh)
        self.add_material_user(mesh, new_material)

    def get_material_users(self, material):
        return self.materials_users[material.name]

    # For viewport renders, this method gets called once at the start and
    # whenever the scene or 3D viewport changes. This method is where data
    # should be read from Blender in the same thread. Typically a render
    # thread will be started to do the work while keeping Blender responsive.
    def view_update(self, context, depsgraph):
        region = context.region
        view3d = context.space_data
        scene = depsgraph.scene

        # Get viewport dimensions
        dimensions = region.width, region.height

        if not self.scene_data:
            # First time initialization
            print("Initializing renderer", flush=True)
            self.scene_data = [0]
            first_time = True

            self.default_material_shader = MaterialShader(None)
            self.materials_users = dict()

            # find all materials in the scene and compile shaders
            # for id in depsgraph.ids:
            #     if isinstance(id, bpy.types.Material):
            #         self.material_shaders[id.name] = MaterialShader(id)

            # Loop over all datablocks used in the scene.
            for datablock in depsgraph.ids:
                if isinstance(datablock, bpy.types.Object) and datablock.type == "MESH":
                    # print(datablock.type, " ", datablock.name, flush=True)
                    self.draw_calls[datablock.name] = self.create_mesh_draw(datablock)
                    if datablock.active_material:
                        self.add_material_user(datablock, datablock.active_material)

        else:
            first_time = False

            # for upd in depsgraph.updates:
            #     print(upd.id.name)
            # print("", flush=True)
            # Test which datablocks changed
            for update in depsgraph.updates:
                # print("Datablock updated: ", update.id.name, flush=True)
                datablock = update.id
                if (
                    isinstance(datablock, bpy.types.Object)
                    and datablock.type == "MESH"
                    and (update.is_updated_geometry or update.is_updated_shading)
                ):
                    # print("mesh updated: ", datablock.name, flush=True)
                    # del self.draw_calls[datablock.name]

                    self.draw_calls[datablock.name] = self.create_mesh_draw(datablock)

            # Test if any material was added, removed or changed.
            if depsgraph.id_type_updated("MATERIAL"):
                # print("Materials updated", flush=True)
                for update in depsgraph.updates:
                    if isinstance(update.id, bpy.types.Material):
                        # print(f"material updated: {update.id.name}", flush=True)
                        self.material_shaders[update.id.name].update()
                pass

        # Loop over all object instances in the scene.
        if first_time or depsgraph.id_type_updated("OBJECT"):
            pass
            self.mesh_objects = []
            for instance in depsgraph.object_instances:
                object = instance.object
                if object.type == "MESH":
                    self.mesh_objects.append(object)
            self.lights = []
            # for light in self.lights:
            #     self.lights.remove(light)
            for instance in depsgraph.object_instances:
                object = instance.object
                if object.type == "LIGHT":
                    match object.data.type:
                        case "SUN":
                            # print("light: ", object.name)
                            # light_direction = mathutils.Vector((0, 0, 1))
                            # light_direction.rotate(object.matrix_world.decompose()[1])
                            # light = light_direction.to_4d()
                            # light.w = object.data.energy
                            # self.lights.append(light)
                            self.lights.append(DirectionalLightRendering(object))
                        case "POINT" | "SPOT":
                            self.lights.append(LocalLightRendering(object))

    # For viewport renders, this method is called whenever Blender redraws
    # the 3D viewport. The renderer is expected to quickly draw the render
    # with OpenGL, and not perform other expensive work.
    # Blender will draw overlays for selection and editing on top of the
    # rendered image automatically.
    def view_draw(self, context, depsgraph):
        region = context.region
        scene = depsgraph.scene

        # Get viewport dimensions
        dimensions = region.width, region.height

        settings = self.get_settings(context)

        fb = gpu.state.active_framebuffer_get()  # it's framebuffer_active_get in the api docs wtf?
        x, y, w, h = gpu.state.viewport_get()

        offscr_scale = settings.backbuffer_scale
        fb_size = (math.floor(w * offscr_scale), math.floor(h * offscr_scale))
        final_color_format = "RGBA16"
        gbuffer_format = "RGBA16"
        normal_format = "RGBA32F"
        # if offscr_scale > 1:
        #     offscr_scale = math.floor(offscr_scale)
        basecolor = gpu.types.GPUTexture(fb_size, format=gbuffer_format)
        shadowcolor = gpu.types.GPUTexture(fb_size, format=gbuffer_format)
        normal = gpu.types.GPUTexture(fb_size, format=normal_format)
        t_shadingmodel = gpu.types.GPUTexture(fb_size, format="R8UI")
        z = gpu.types.GPUTexture(fb_size, format="DEPTH_COMPONENT24")
        gbuffer = gpu.types.GPUFrameBuffer(depth_slot=z, color_slots=(basecolor, shadowcolor, normal, t_shadingmodel))

        with gbuffer.bind():
            gpu.state.active_framebuffer_get().clear(color=(0, 0, 0, 0), depth=1.0)
            t_shadingmodel.clear(format="UBYTE", value=tuple([0]))

            # Bind (fragment) shader that converts from scene linear to display space,
            # self.bind_display_space_shader(scene)

            gpu.state.depth_test_set("LESS")
            gpu.state.depth_mask_set(True)
            gpu.state.face_culling_set("BACK")

            for object in self.mesh_objects:
                draw = self.draw_calls[object.name]
                mvp = context.region_data.window_matrix @ context.region_data.view_matrix
                draw.draw(object.matrix_world, mvp, settings, basecolor)
            # for key, draw in self.draw_calls.items():
            #     print(draw.object.name, " ", draw.object.hide_viewport, flush=True)
            #     draw.draw(draw.object.matrix_world, context.region_data, self.lights, settings)

            # self.unbind_display_space_shader()

        tscenelit = gpu.types.GPUTexture(fb_size, format=final_color_format)
        lighting = gpu.types.GPUFrameBuffer(color_slots=(tscenelit))

        with lighting.bind():
            lighting.clear(color=(0, 0, 0, 0))
            gpu.state.depth_test_set("ALWAYS")

            ps_prefix = "\n#define BACKGROUND_COLOR " + ("1" if settings.world_color_clear else "0") + "\n"
            ps_prefix += CustomRenderEngineMaterialSettings.get_shadingmodels_define()
            shader = gpu.types.GPUShader(VERTEX_2D, ps_prefix + PIXEL_SCENE_LIGHTING)
            shader.bind()
            shader.uniform_float("scene_color", settings.world_color)
            shader.uniform_sampler("tbasecolor", basecolor)
            shader.uniform_sampler("tshadingmodel", t_shadingmodel)
            batch_for_shader(shader, "TRI_FAN", {"pos": ((0, 0), (1, 0), (1, 1), (0, 1))}).draw(shader)

            gpu.state.blend_set("ADDITIVE")
            for light in self.lights:
                light.draw(
                    context.region_data,
                    z,
                    basecolor,
                    shadowcolor,
                    normal,
                    t_shadingmodel,
                )

            gpu.state.blend_set("NONE")

        trgbl = gpu.types.GPUTexture(fb_size, format=final_color_format)
        rgbl = gpu.types.GPUFrameBuffer(color_slots=(trgbl))

        with rgbl.bind():
            shader = gpu.types.GPUShader(VERTEX_2D, PIXEL_RGBL)
            shader.bind()
            shader.uniform_sampler("image", tscenelit)
            batch_for_shader(shader, "TRI_FAN", {"pos": ((0, 0), (1, 0), (1, 1), (0, 1))}).draw(shader)

        present_pixel_shader = PIXEL_2D

        pixel_shader_prefix = """
            vec4 finalize_color(vec4 incolor) { return incolor; }
        """
        match settings.out_buffer:
            case "SCENELIT":
                if settings.use_fxaa:
                    out_texture = trgbl
                    pixel_shader_prefix = """
                        #define FXAA_GLSL_130 1
                        #define FXAA_PC 1
                        //#define FXAA_QUALITY__PRESET 29
                    """
                    if settings.use_fxaa:
                        pixel_shader_prefix += """
                            #define USE_FXAA 1
                        """
                    present_pixel_shader = PIXEL_FXAA.replace("FXAA_HEADER", open("shaders/FXAA311.glsl").read())
                else:
                    out_texture = tscenelit
            case "BASECOLOR":
                out_texture = basecolor
            case "SHADOWCOLOR":
                out_texture = shadowcolor
            case "NORMAL":
                out_texture = normal
                pixel_shader_prefix = """
                    vec4 finalize_color(vec4 incolor) { return incolor * 0.5 + 0.5; }
                """
            case "DEPTH":
                out_texture = z
                pixel_shader_prefix = """
                    vec4 finalize_color(vec4 incolor)
                    {
                        float z = pow(incolor.x, 256);
                        return vec4(z, z, z, 1);
                    }
                """
            case "POSITION":
                present_pixel_shader = PIXEL_DEFERRED_WORLDPOS
                out_texture = tscenelit
                pixel_shader_prefix = ""
            case "SHADINGMODEL":
                present_pixel_shader = PIXEL_SHADINGMODEL
                pixel_shader_prefix = CustomRenderEngineMaterialSettings.get_shadingmodels_define()
                out_texture = t_shadingmodel

        with fb.bind():
            if settings.world_color_clear:
                fb.clear(color=settings.world_color)
            fb.clear(depth=1.0)

            gpu.state.depth_test_set("ALWAYS")
            gpu.state.depth_mask_set(True)

            coords = ((0, 0), (1, 0), (1, 1), (0, 1))
            shader = gpu.types.GPUShader(VERTEX_2D, pixel_shader_prefix + present_pixel_shader)
            vbo = gpu.types.GPUVertBuf(shader.format_calc(), 4)
            vbo.attr_fill("pos", coords)
            batch = gpu.types.GPUBatch(type="TRI_FAN", buf=vbo)
            shader.bind()
            shader.uniform_sampler("image", out_texture)
            shader.uniform_sampler("depth", z)
            if settings.out_buffer == "POSITION":
                region_data = context.region_data
                # shader.uniform_float("mat_view", region_data.view_matrix)
                # shader.uniform_float("mat_projection", region_data.window_matrix)
                shader.uniform_float(
                    "mat_view_projection",
                    region_data.window_matrix @ region_data.view_matrix,
                )
            # shader.uniform_int("view_size", (w, h))
            # shader.uniform_int("buffer_size", (rgb.width, rgb.height))
            try:
                shader.uniform_float("invScreenSize", (1.0 / w, 1.0 / h))
            except ValueError:
                pass
            batch.draw(shader)


# RenderEngines also need to tell UI Panels that they are compatible with.
# We recommend to enable all panels marked as BLENDER_RENDER, and then
# exclude any panels that are replaced by custom panels registered by the
# render engine, or that are not supported.
def get_panels():
    exclude_panels = {
        "VIEWLAYER_PT_filter",
        "VIEWLAYER_PT_layer_passes",
    }

    include_panels = {
        "DATA_PT_EEVEE_light",
        "DATA_PT_EEVEE_light_distance",
        "DATA_PT_EEVEE_shadow",
        "EEVEE_MATERIAL_PT_context_material",
        # "EEVEE_MATERIAL_PT_surface",
    }

    panels = []
    for panel in bpy.types.Panel.__subclasses__():
        if hasattr(panel, "COMPAT_ENGINES") and "BLENDER_RENDER" in panel.COMPAT_ENGINES:
            if panel.__name__ not in exclude_panels:
                panels.append(panel)
        if panel.__name__ in include_panels:
            panels.append(panel)

    return panels


classes = [
    Fast64RenderEngine,
    Fast64RenderEngineSettings,
    Fast64RenderEnginePanel,
    # Fast64RenderEngineLightPanel
]


def register():
    # Register the RenderEngine
    for c in classes:
        bpy.utils.register_class(c)

    for panel in get_panels():
        panel.COMPAT_ENGINES.add("FAST64")

    bpy.types.Scene.f3d_render_engine_settings = bpy.props.PointerProperty(type=Fast64RenderEngineSettings)


def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)

    for panel in get_panels():
        if "FAST64" in panel.COMPAT_ENGINES:
            panel.COMPAT_ENGINES.remove("FAST64")
