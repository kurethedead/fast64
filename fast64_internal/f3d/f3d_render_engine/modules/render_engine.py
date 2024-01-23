import math, bpy, gpu, threading
from gpu_extras.batch import batch_for_shader
from .material import CustomRenderEngineMaterialSettings
from .settings import Fast64RenderEngineSettings, Fast64RenderEnginePanel
from .light_settings import Fast64RenderEngineLightPanel
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
import numpy as np
from . import fast64_core

numBuffers = 2
scale = 0.25
componentSize = 4


# https://docs.blender.org/api/current/bpy.types.RenderEngine.html
class Fast64RenderEngine(bpy.types.RenderEngine):
    # These three members are used by blender to set up the
    # RenderEngine; define its internal name, visible name and capabilities.
    bl_idname = "FAST64"
    bl_label = "Fast64"
    bl_use_preview = True

    # Hides Cycles node trees in the node editor.
    bl_use_shading_nodes_custom = False

    def get_settings(self, context) -> Fast64RenderEngineSettings:
        return context.scene.f3d_render_engine_settings

    # Init is called whenever a new render engine instance is created. Multiple
    # instances may exist at the same time, for example for a viewport and final
    # render.
    def __init__(self):
        self.scene_data = None
        self.draw_data = None
        self.draw_calls = {}
        self.lights = []
        self.mesh_objects = []
        self.material_shaders: dict[str, MaterialShader] = dict()
        self.buffers = [gpu.types.Buffer("FLOAT", (1, 1, 4), np.array([[[1, 1, 1, 1]]]))] * numBuffers
        self.session = fast64_core.RenderSession(fast64_core.RenderConfig(fast64_core.RenderEngineType.OpenGL))
        self.session.Run(self.buffers)
        self.prevDimensions = (1, 1, 4)

    # When the render engine instance is destroy, this is called. Clean up any
    # render engine data here, for example stopping running render threads.
    def __del__(self):
        self.session.End()
        pass

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
        for i in range(len(meshObj.material_slots)):
            material = meshObj.material_slots[i].material
            if material is not None and material.name not in self.material_shaders:
                self.material_shaders[material.name] = MaterialShader(material)
                self.add_material_user(meshObj, material)

        return MeshDraw(meshObj, self.material_shaders)

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

        x, y, w, h = gpu.state.viewport_get()
        fb_size = (math.floor(w), math.floor(h))
        self.session.UpdateScene()

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

                            # TODO: Handle lights
                            # self.lights.append(DirectionalLightRendering(object))
                            pass
                        case "POINT" | "SPOT":
                            # self.lights.append(LocalLightRendering(object))
                            pass

    # For viewport renders, this method is called whenever Blender redraws
    # the 3D viewport. The renderer is expected to quickly draw the render
    # with OpenGL, and not perform other expensive work.
    # Blender will draw overlays for selection and editing on top of the
    # rendered image automatically.
    def view_draw(self, context, depsgraph):
        region = context.region
        scene = depsgraph.scene
        view3d = context.space_data

        # Get viewport dimensions
        dimensions = region.width, region.height
        settings = self.get_settings(context)

        fb = gpu.state.active_framebuffer_get()  # it's framebuffer_active_get in the api docs wtf?
        x, y, w, h = gpu.state.viewport_get()

        offscr_scale = settings.backbuffer_scale
        fb_size = (math.floor(w * offscr_scale * scale), math.floor(h * offscr_scale * scale), componentSize)
        # final_color_format = "RGBA8"
        final_color_format = "RGBA32F"

        nextBufferIndex = self.session.GetImage()
        nextBuffer = self.buffers[nextBufferIndex]
        oldBuffers = []  # used to keep references until rendering complete ??
        if tuple(nextBuffer.dimensions) != tuple(fb_size):
            print(f"Buffer replacement: {tuple(nextBuffer.dimensions)} != {tuple(fb_size)}")
            # This internally replaces buffer but in python we still have to manually do this
            # This is in order to keep reference to old buffer while in use
            oldBuffers = self.buffers
            newBuffers = [gpu.types.Buffer("FLOAT", fb_size, np.full(fb_size, 1)) for i in range(numBuffers)]
            self.session.ReplaceBuffers(newBuffers)
            self.buffers = newBuffers

        if nextBufferIndex == -1:
            return

        # GPUTexture dimensions exclude the third dimension (size of each pixel)
        colorTexture = gpu.types.GPUTexture(nextBuffer.dimensions[0:2], format=final_color_format, data=nextBuffer)

        with fb.bind():
            shader = gpu.types.GPUShader(VERTEX_2D, PIXEL_RGBL)
            shader.bind()
            shader.uniform_sampler("image", colorTexture)
            batch_for_shader(shader, "TRI_FAN", {"pos": ((0, 0), (1, 0), (1, 1), (0, 1))}).draw(shader)


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
