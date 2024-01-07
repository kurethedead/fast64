import bpy


# expose light properties
class Fast64RenderEngineLightPanel(bpy.types.Panel):
    # bl_idname = "RENDER_PT_CustomRenderEngineLight"
    bl_label = "Light"
    bl_context = "data"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"

    @classmethod
    def poll(cls, context):
        return context.engine == "FAST64"

    def draw(self, context):
        # layout = self.layout
        light = context.light
        if isinstance(light, bpy.types.Light):
            col = self.layout.column()
            col.prop(light, "color")
            col.prop(light, "energy")

            match light.type:
                case "SUN":
                    col.prop(light, "angle")
                case "POINT":
                    col.prop(light, "shadow_soft_size")
                case "SPOT":
                    col.prop(light, "shadow_soft_size")
                    col.prop(light, "spot_size")
                    col.prop(light, "spot_blend")
