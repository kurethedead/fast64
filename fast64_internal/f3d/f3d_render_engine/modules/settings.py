import bpy
from .operators import OBJECT_OT_Fast64TestCTypes

# Do not use 0, which is reserved for "None" renderer.
# These should be integer values corresponding to the RendererType enum in fast64_core.
rendererTypes = [
    ("1", "OpenGL", "Default high level OpenGL renderer"),
    ("2", "OpenGLButAgain", "Default high level OpenGL renderer, but again for testing purposes"),
]


def update_renderer(self, context: bpy.types.Context):
    # init_renderer(int(context.scene.f3d_render_engine_settings.rendererType))
    pass


class Fast64RenderEngineSettings(bpy.types.PropertyGroup):
    rendererType: bpy.props.EnumProperty(name="Renderer", items=rendererTypes, update=update_renderer)
    backbuffer_scale: bpy.props.FloatProperty(name="Backbuffer Scale", default=1.0, min=0.1, max=10)
    use_fxaa: bpy.props.BoolProperty(name="FXAA", default=True)

    out_buffer: bpy.props.EnumProperty(
        items=[
            ("SCENELIT", "Deferred Lighting", ""),
            ("BASECOLOR", "Base Color", ""),
            ("SHADOWCOLOR", "Shadow Color", ""),
            ("NORMAL", "World Normal", ""),
            ("POSITION", "World Position", ""),
            ("DEPTH", "Depth", ""),
            ("SHADINGMODEL", "Shading Model", ""),
        ],
        name="Out Buffer",
        options=set(),
    )

    enable_outline: bpy.props.BoolProperty(name="Render Outlines", default=False, options=set())
    outline_width: bpy.props.FloatProperty(name="Outline Width", default=1, min=0, soft_max=10, options=set())
    outline_color: bpy.props.FloatVectorProperty(
        name="Outline Color",
        size=4,
        default=(0, 0, 0, 1),
        subtype="COLOR",
        min=0,
        max=1,
        options=set(),
    )
    outline_depth_exponent: bpy.props.FloatProperty(
        name="Outline Depth Scale Exponent", default=0.75, min=0, max=1, options=set()
    )
    shading_sharpness: bpy.props.FloatProperty(
        name="Shading Sharpness",
        default=1,
        subtype="FACTOR",
        min=0,
        max=1,
        options=set(),
    )
    fresnel_fac: bpy.props.FloatProperty(name="Fresnel Factor", default=0.5, min=0, max=1)
    use_vertexcolor_alpha: bpy.props.BoolProperty(
        name="Use Vertex Color Alpha",
        default=False,
        options=set(),
        description="Used as offset scaling",
    )
    use_vertexcolor_rgb: bpy.props.BoolProperty(
        name="Use Vertex Color RGB",
        default=False,
        options=set(),
        description="Used as normal map for outline",
    )

    # TODO: Materials
    basecolor_texture: bpy.props.StringProperty(name="Base Color")
    shadowtint_texture: bpy.props.StringProperty(name="Shadow Tint")

    world_color: bpy.props.FloatVectorProperty(
        name="World Color",
        size=4,
        default=(0.1, 0.1, 0.1, 1),
        subtype="COLOR",
        min=0,
        max=1,
        options=set(),
    )
    world_color_clear: bpy.props.BoolProperty(name="World Color Background", default=False, options=set())


class Fast64RenderEnginePanel(bpy.types.Panel):
    bl_idname = "RENDER_PT_CustomRenderEngine"
    bl_label = "Custom Render Engine Settings"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "render"
    # COMPAT_ENGINES = {'FAST64'}

    @classmethod
    def poll(cls, context):
        return context.engine == "FAST64"

    def draw(self, context):
        layout = self.layout
        layout.use_property_decorate = True
        layout.use_property_split = True
        settings = context.scene.f3d_render_engine_settings

        layout.operator(OBJECT_OT_Fast64TestCTypes.bl_idname)
        layout.prop(settings, "rendererType")
        layout.prop(settings, "backbuffer_scale")
        layout.prop(settings, "use_fxaa")
        layout.prop(settings, "out_buffer")
        layout.prop(settings, "enable_outline")
        layout.prop(settings, "outline_width")
        layout.prop(settings, "outline_color")
        layout.prop(settings, "outline_depth_exponent")
        layout.prop(settings, "use_vertexcolor_alpha")
        layout.prop(settings, "use_vertexcolor_rgb")
        layout.prop_search(settings, "basecolor_texture", bpy.data, "images")
        layout.prop_search(settings, "shadowtint_texture", bpy.data, "images")
        layout.prop(settings, "world_color")
        layout.prop(settings, "world_color_clear")
        layout.prop(settings, "shading_sharpness")
        layout.prop(settings, "fresnel_fac")
