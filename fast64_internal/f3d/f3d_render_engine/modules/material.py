import bpy
import nodeitems_utils


class CustomRenderEngineMaterialSettings(bpy.types.PropertyGroup):
    EShadingModels = [
        ("UNLIT", "Unlit", "", 0),
        ("LAMBERT", "Lambert", "", 1),
        ("TOON", "Toon", "", 2),
    ]

    tex_base_color: bpy.props.StringProperty(name="Base Color Texture")
    tex_shadow_tint: bpy.props.StringProperty(name="Shadow Tint Texture")
    col_shadow_tint: bpy.props.FloatVectorProperty(
        name="Shadow Color Tint",
        size=3,
        default=(1, 1, 1),
        subtype="COLOR",
        min=0,
        max=1,
    )
    shading_model: bpy.props.EnumProperty(items=EShadingModels, name="Shading Model", default=1)
    f_sm_param: bpy.props.FloatProperty(name="Shading Model Parameter", soft_min=0, soft_max=1)

    @classmethod
    def get_shadingmodel_value(cls, id):
        for _, sm in enumerate(cls.EShadingModels):
            if sm[0] == id:
                return sm[3]

    @classmethod
    def get_shadingmodels_define(cls):
        out_str = ""
        for _, shadingmodel in enumerate(cls.EShadingModels):
            out_str += f"\n#define SHADINGMODEL_{shadingmodel[0]} {shadingmodel[3]}\n"
        return out_str


class CUSTOM_MATERIAL_PT_surface(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "material"
    bl_label = "Surface"

    COMPAT_ENGINES = ["FAST64"]

    @classmethod
    def poll(cls, context):
        mat = context.material
        return mat and context.engine in cls.COMPAT_ENGINES and not mat.grease_pencil

    def draw(self, context):
        layout = self.layout
        mat = context.material

        layout.use_property_split = True

        layout.prop(mat, "diffuse_color", text="Base Color Tint")
        layout.prop(mat, "metallic")
        layout.prop(mat, "specular_intensity")
        layout.prop(mat, "roughness")

        if mat.custom_settings:
            layout.separator()
            layout.prop_search(mat.custom_settings, "tex_base_color", bpy.data, "images")
            layout.prop_search(mat.custom_settings, "tex_shadow_tint", bpy.data, "images")
            layout.prop(mat.custom_settings, "col_shadow_tint")
            layout.prop(mat.custom_settings, "shading_model")
            layout.prop(mat.custom_settings, "f_sm_param")


def register():
    bpy.utils.register_class(CustomRenderEngineMaterialSettings)
    bpy.utils.register_class(CUSTOM_MATERIAL_PT_surface)
    bpy.types.Material.custom_settings = bpy.props.PointerProperty(type=CustomRenderEngineMaterialSettings)


def unregister():
    bpy.utils.unregister_class(CustomRenderEngineMaterialSettings)
    bpy.utils.unregister_class(CUSTOM_MATERIAL_PT_surface)
    del bpy.types.Material.custom_settings
