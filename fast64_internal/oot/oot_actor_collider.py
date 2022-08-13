import bpy
from bpy.utils import register_class, unregister_class
from ..utility import prop_split


ootEnumGeometryType = [
    ("Regular", "Regular", "Regular"),
    ("Actor Collider", "Actor Collider", "Actor Collider"),
]

ootEnumColliderShape = [
    ("COLSHAPE_JNTSPH", "Joint Sphere", "Joint Sphere"),
    ("COLSHAPE_CYLINDER", "Cylinder", "Cylinder"),
    ("COLSHAPE_TRIS", "Triangles", "Triangles"),
]

ootEnumColliderType = [
    ("COLTYPE_HIT0", "Blue Blood, White Hitmark", "Blue Blood, White Hitmark"),
    ("COLTYPE_HIT1", "No Blood, Dust Hitmark", "No Blood, Dust Hitmark"),
    ("COLTYPE_HIT2", "Green Blood, Dust Hitmark", "Green Blood, Dust Hitmark"),
    ("COLTYPE_HIT3", "No Blood, White Hitmark", "No Blood, White Hitmark"),
    ("COLTYPE_HIT4", "Water Burst, No hitmark", "Water Burst, No hitmark"),
    ("COLTYPE_HIT5", "No blood, Red Hitmark", "No blood, Red Hitmark"),
    ("COLTYPE_HIT6", "Green Blood, White Hitmark", "Green Blood, White Hitmark"),
    ("COLTYPE_HIT7", "Red Blood, White Hitmark", "Red Blood, White Hitmark"),
    ("COLTYPE_HIT8", "Blue Blood, Red Hitmark", "Blue Blood, Red Hitmark"),
    ("COLTYPE_META", "Meta", "Meta"),
    ("COLTYPE_NONE", "None", "None"),
    ("COLTYPE_WOOD", "Wood", "Wood"),
    ("COLTYPE_HARD", "Hard", "Hard"),
    ("COLTYPE_TREE", "Tree", "Tree"),
]

ootEnumColliderElement = [
    ("ELEMTYPE_UNK0", "Element 0", "Element 0"),
    ("ELEMTYPE_UNK1", "Element 1", "Element 1"),
    ("ELEMTYPE_UNK2", "Element 2", "Element 2"),
    ("ELEMTYPE_UNK3", "Element 3", "Element 3"),
    ("ELEMTYPE_UNK4", "Element 4", "Element 4"),
    ("ELEMTYPE_UNK5", "Element 5", "Element 5"),
    ("ELEMTYPE_UNK6", "Element 6", "Element 6"),
    ("ELEMTYPE_UNK7", "Element 7", "Element 7"),
]

ootEnumHitboxSound = [
    ("TOUCH_SFX_NORMAL", "Hurtbox", "Hurtbox"),
    ("TOUCH_SFX_HARD", "Hard", "Hard"),
    ("TOUCH_SFX_WOOD", "Wood", "Wood"),
    ("TOUCH_SFX_NONE", "None", "None"),
]

# Defaults are from DMG_DEFAULT.
class OOTDamageFlagsProperty(bpy.types.PropertyGroup):
    expandTab: bpy.props.BoolProperty(default=False, name="Damage Flags")
    dekuNut: bpy.props.BoolProperty(default=True, name="Deku Nut")
    dekuStick: bpy.props.BoolProperty(default=True, name="Deku Stick")
    slingshot: bpy.props.BoolProperty(default=True, name="Slingshot")
    explosive: bpy.props.BoolProperty(default=True, name="Bomb")
    boomerang: bpy.props.BoolProperty(default=True, name="Boomerang")
    arrowNormal: bpy.props.BoolProperty(default=True, name="Normal")
    hammerSwing: bpy.props.BoolProperty(default=True, name="Hammer Swing")
    hookshot: bpy.props.BoolProperty(default=True, name="Hookshot")
    slashKokiriSword: bpy.props.BoolProperty(default=True, name="Kokiri")
    slashMasterSword: bpy.props.BoolProperty(default=True, name="Master")
    slashGiantSword: bpy.props.BoolProperty(default=True, name="Giant")
    arrowFire: bpy.props.BoolProperty(default=True, name="Fire")
    arrowIce: bpy.props.BoolProperty(default=True, name="Ice")
    arrowLight: bpy.props.BoolProperty(default=True, name="Light")
    arrowUnk1: bpy.props.BoolProperty(default=True, name="Unk1")
    arrowUnk2: bpy.props.BoolProperty(default=True, name="Unk2")
    arrowUnk3: bpy.props.BoolProperty(default=True, name="Unk3")
    magicFire: bpy.props.BoolProperty(default=True, name="Fire")
    magicIce: bpy.props.BoolProperty(default=True, name="Ice")
    magicLight: bpy.props.BoolProperty(default=True, name="Light")
    shield: bpy.props.BoolProperty(default=False, name="Shield")
    mirrorRay: bpy.props.BoolProperty(default=False, name="Mirror Ray")
    spinKokiriSword: bpy.props.BoolProperty(default=True, name="Kokiri")
    spinGiantSword: bpy.props.BoolProperty(default=True, name="Giant")
    spinMasterSword: bpy.props.BoolProperty(default=True, name="Master")
    jumpKokiriSword: bpy.props.BoolProperty(default=True, name="Kokiri")
    jumpGiantSword: bpy.props.BoolProperty(default=True, name="Giant")
    jumpMasterSword: bpy.props.BoolProperty(default=True, name="Master")
    unknown1: bpy.props.BoolProperty(default=True, name="Unknown 1")
    unblockable: bpy.props.BoolProperty(default=True, name="Unblockable")
    hammerJump: bpy.props.BoolProperty(default=True, name="Hammer Jump")
    unknown2: bpy.props.BoolProperty(default=True, name="Unknown 2")

    def draw(self, layout: bpy.types.UILayout):
        layout.prop(self, "expandTab", text="Damage Flags", icon="TRIA_DOWN" if self.expandTab else "TRIA_RIGHT")

        if self.expandTab:
            row = layout.row(align=True)
            row.prop(self, "dekuNut", toggle=1)
            row.prop(self, "dekuStick", toggle=1)
            row.prop(self, "slingshot", toggle=1)

            row = layout.row(align=True)
            row.prop(self, "explosive", toggle=1)
            row.prop(self, "boomerang", toggle=1)
            row.prop(self, "hookshot", toggle=1)

            row = layout.row(align=True)
            row.prop(self, "hammerSwing", toggle=1)
            row.prop(self, "hammerJump", toggle=1)

            row = layout.row(align=True)
            row.label(text="Slash")
            row.prop(self, "slashKokiriSword", toggle=1)
            row.prop(self, "slashMasterSword", toggle=1)
            row.prop(self, "slashGiantSword", toggle=1)

            row = layout.row(align=True)
            row.label(text="Spin")
            row.prop(self, "spinKokiriSword", toggle=1)
            row.prop(self, "spinMasterSword", toggle=1)
            row.prop(self, "spinGiantSword", toggle=1)

            row = layout.row(align=True)
            row.label(text="Jump")
            row.prop(self, "jumpKokiriSword", toggle=1)
            row.prop(self, "jumpMasterSword", toggle=1)
            row.prop(self, "jumpGiantSword", toggle=1)

            row = layout.row(align=True)
            row.label(text="Arrow")
            row.prop(self, "arrowNormal", toggle=1)
            row.prop(self, "arrowFire", toggle=1)
            row.prop(self, "arrowIce", toggle=1)
            row.prop(self, "arrowLight", toggle=1)

            row = layout.row(align=True)
            row.label(text="Arrow Unknown")
            row.prop(self, "arrowUnk1", toggle=1)
            row.prop(self, "arrowUnk2", toggle=1)
            row.prop(self, "arrowUnk3", toggle=1)

            row = layout.row(align=True)
            row.label(text="Magic")
            row.prop(self, "magicFire", toggle=1)
            row.prop(self, "magicIce", toggle=1)
            row.prop(self, "magicLight", toggle=1)

            row = layout.row(align=True)
            row.prop(self, "shield", toggle=1)
            row.prop(self, "mirrorRay", toggle=1)

            row = layout.row(align=True)
            row.prop(self, "unblockable", toggle=1)
            row.prop(self, "unknown1", toggle=1)
            row.prop(self, "unknown2", toggle=1)


# AT
class OOTColliderHitboxProperty(bpy.types.PropertyGroup):
    enable: bpy.props.BoolProperty(name="Hitbox (AT)")
    attacksBounceOff: bpy.props.BoolProperty(name="Attacks Bounce Off")
    alignPlayer: bpy.props.BoolProperty(name="Player", default=False)
    alignEnemy: bpy.props.BoolProperty(name="Enemy", default=True)
    alignOther: bpy.props.BoolProperty(name="Other", default=False)
    alignSelf: bpy.props.BoolProperty(name="Self", default=False)

    def draw(self, layout: bpy.types.UILayout):
        layout = layout.box().column()
        layout.prop(self, "enable")
        if self.enable:
            layout.prop(self, "attacksBounceOff")
            alignToggles = layout.row(align=True)
            alignToggles.label(text="Aligned")
            alignToggles.prop(self, "alignPlayer", toggle=1)
            alignToggles.prop(self, "alignEnemy", toggle=1)
            alignToggles.prop(self, "alignOther", toggle=1)
            alignToggles.prop(self, "alignSelf", toggle=1)


# AC
class OOTColliderHurtboxProperty(bpy.types.PropertyGroup):
    enable: bpy.props.BoolProperty(name="Hurtbox (AC)")
    attacksBounceOff: bpy.props.BoolProperty(name="Attacks Bounce Off")
    hurtByPlayer: bpy.props.BoolProperty(name="Player", default=True)
    hurtByEnemy: bpy.props.BoolProperty(name="Enemy", default=False)
    hurtByOther: bpy.props.BoolProperty(name="Other", default=False)

    def draw(self, layout: bpy.types.UILayout):
        layout = layout.box().column()
        layout.prop(self, "enable")
        if self.enable:
            layout.prop(self, "attacksBounceOff")
            hurtToggles = layout.row(align=True)
            hurtToggles.label(text="Hurt By")
            hurtToggles.prop(self, "hurtByPlayer", toggle=1)
            hurtToggles.prop(self, "hurtByEnemy", toggle=1)
            hurtToggles.prop(self, "hurtByOther", toggle=1)


class OOTColliderLayers(bpy.types.PropertyGroup):
    player: bpy.props.BoolProperty(name="Player", default=False)
    type1: bpy.props.BoolProperty(name="Type 1", default=True)
    type2: bpy.props.BoolProperty(name="Type 2", default=False)

    def draw(self, layout: bpy.types.UILayout, name: str):
        collisionLayers = layout.row(align=True)
        collisionLayers.label(text=name)
        collisionLayers.prop(self, "player", toggle=1)
        collisionLayers.prop(self, "type1", toggle=1)
        collisionLayers.prop(self, "type2", toggle=1)


# OC
class OOTColliderPhysicsProperty(bpy.types.PropertyGroup):
    enable: bpy.props.BoolProperty(name="Physics (OC)")
    noPush: bpy.props.BoolProperty(name="Don't Push Others")
    collidesWith: bpy.props.PointerProperty(type=OOTColliderLayers)
    isCollider: bpy.props.PointerProperty(type=OOTColliderLayers)
    skipHurtboxCheck: bpy.props.BoolProperty(name="Skip Hurtbox Check After First Collision")
    isType1: bpy.props.BoolProperty(name="Is Type 1", default=False)

    def draw(self, layout: bpy.types.UILayout):
        layout = layout.box().column()
        layout.prop(self, "enable")
        if self.enable:
            layout.prop(self, "noPush")
            layout.prop(self, "skipHurtboxCheck")
            layout.prop(self, "isType1")
            self.collidesWith.draw(layout, "Hits Type")
            if not self.isType1:
                self.isCollider.draw(layout, "Is Type")


# Touch
class OOTColliderHitboxItemProperty(bpy.types.PropertyGroup):
    # Flags
    enable: bpy.props.BoolProperty(name="Touch")
    soundEffect: bpy.props.EnumProperty(name="Sound Effect", items=ootEnumHitboxSound)
    drawHitmarksForEveryCollision: bpy.props.BoolProperty(name="Draw Hitmarks For Every Collision")

    # ColliderTouch
    damageFlags: bpy.props.PointerProperty(type=OOTDamageFlagsProperty, name="Damage Flags")
    effect: bpy.props.IntProperty(min=0, max=255, name="Effect")
    damage: bpy.props.IntProperty(min=0, max=255, name="Damage")

    def draw(self, layout: bpy.types.UILayout):
        layout = layout.box().column()
        layout.prop(self, "enable")
        if self.enable:
            prop_split(layout, self, "soundEffect", "Sound Effect")
            layout.prop(self, "drawHitmarksForEveryCollision")
            prop_split(layout, self, "effect", "Effect")
            prop_split(layout, self, "damage", "Damage")
            self.damageFlags.draw(layout)


# Bump
class OOTColliderHurtboxItemProperty(bpy.types.PropertyGroup):
    # Flags
    enable: bpy.props.BoolProperty(name="Bump")
    hookable: bpy.props.BoolProperty(name="Hookable")
    giveInfoToHit: bpy.props.BoolProperty(name="Give Info To Hit")
    takesDamage: bpy.props.BoolProperty(name="Damageable", default=True)
    hasSound: bpy.props.BoolProperty(name="Has SFX", default=True)
    hasHitmark: bpy.props.BoolProperty(name="Has Hitmark", default=True)

    # ColliderBumpInit
    damageFlags: bpy.props.PointerProperty(type=OOTDamageFlagsProperty, name="Damage Flags")
    effect: bpy.props.IntProperty(min=0, max=255, name="Effect")
    defense: bpy.props.IntProperty(min=0, max=255, name="Damage")

    def draw(self, layout: bpy.types.UILayout):
        layout = layout.box().column()
        layout.prop(self, "enable")
        if self.enable:
            layout.prop(self, "hookable")
            layout.prop(self, "giveInfoToHit")
            row = layout.row(align=True)
            row.prop(self, "takesDamage", toggle=1)
            row.prop(self, "hasSound", toggle=1)
            row.prop(self, "hasHitmark", toggle=1)
            prop_split(layout, self, "effect", "Effect")
            prop_split(layout, self, "defense", "Defense")
            self.damageFlags.draw(layout)


# OCElem
class OOTColliderPhysicsItemProperty(bpy.types.PropertyGroup):
    enable: bpy.props.BoolProperty(name="Object Element")
    toggleUnk3: bpy.props.BoolProperty(name="Unknown Toggle", default=False)

    def draw(self, layout: bpy.types.UILayout):
        layout = layout.box().column()
        layout.prop(self, "enable")
        if self.enable:
            layout.prop(self, "toggleUnk3")


# ColliderInit is for entire collection.
# ColliderInfoInit is for each item of a collection.

# Triangle/Cylinder will use their own object for ColliderInit.
# Joint Sphere will use armature object for ColliderInit.


class OOTActorColliderProperty(bpy.types.PropertyGroup):
    # ColliderInit
    colliderShape: bpy.props.EnumProperty(items=ootEnumColliderShape, name="Shape", default="COLSHAPE_CYLINDER")
    colliderType: bpy.props.EnumProperty(items=ootEnumColliderType, name="Hit Reaction")
    hitbox: bpy.props.PointerProperty(type=OOTColliderHitboxProperty, name="Hitbox (AT)")
    hurtbox: bpy.props.PointerProperty(type=OOTColliderHurtboxProperty, name="Hurtbox (AC)")
    physics: bpy.props.PointerProperty(type=OOTColliderPhysicsProperty, name="Physics (OC)")

    def draw(self, obj: bpy.types.Object, layout: bpy.types.UILayout):
        prop_split(layout, self, "colliderShape", "Collider Shape")
        if obj.ootActorCollider.colliderShape == "COLSHAPE_JNTSPH":
            armatureObj = obj.parent
            if obj.parent is not None and isinstance(obj.parent.data, bpy.types.Armature) and obj.parent_bone != "":
                layout.label(text="Armature Specific", icon="INFO")
                prop_split(layout, armatureObj, "colliderType", "Collider Type")
                armatureObj.ootActorCollider.hitbox.draw(layout)
                armatureObj.ootActorCollider.hurtbox.draw(layout)
                armatureObj.ootActorCollider.physics.draw(layout)
            else:
                layout.label(text="Joint sphere colliders must be parented to a bone in an armature.", icon="ERROR")
        else:
            prop_split(layout, self, "colliderType", "Collider Type")
            self.hitbox.draw(layout)
            self.hurtbox.draw(layout)
            self.physics.draw(layout)


class OOTActorColliderItemProperty(bpy.types.PropertyGroup):
    # ColliderInfoInit
    element: bpy.props.EnumProperty(items=ootEnumColliderElement, name="Element Type")
    touch: bpy.props.PointerProperty(type=OOTColliderHitboxItemProperty, name="Touch")
    bump: bpy.props.PointerProperty(type=OOTColliderHurtboxItemProperty, name="Bump")
    objectElem: bpy.props.PointerProperty(type=OOTColliderPhysicsItemProperty, name="Object Element")

    def draw(self, obj: bpy.types.Object, layout: bpy.types.UILayout):
        if obj.ootActorCollider.colliderShape == "COLSHAPE_JNTSPH":
            armatureObj = obj.parent
            if obj.parent is not None and isinstance(obj.parent.data, bpy.types.Armature) and obj.parent_bone != "":
                layout = layout.column()
                layout.label(text="Joint Specific", icon="INFO")
                prop_split(layout, armatureObj, "element", "Element Type")
                armatureObj.ootActorColliderItem.touch.draw(layout)
                armatureObj.ootActorColliderItem.bump.draw(layout)
                armatureObj.ootActorColliderItem.objectElem.draw(layout)
        else:
            layout = layout.column()
            prop_split(layout, self, "element", "Element Type")
            self.touch.draw(layout)
            self.bump.draw(layout)
            self.objectElem.draw(layout)


class OOT_ActorColliderPanel(bpy.types.Panel):
    bl_label = "OOT Actor Collider Inspector"
    bl_idname = "OBJECT_PT_OOT_Actor_Collider_Inspector"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_options = {"HIDE_HEADER"}

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return context.scene.gameEditorMode == "OOT" and (
            context.object is not None and isinstance(context.object.data, bpy.types.Mesh)
        )

    def draw(self, context: bpy.types.Context):
        box = self.layout.box().column()
        box.box().label(text="OOT Actor Collider Inspector")
        obj = context.object

        # prop_split(box, obj, "ootDrawLayer", "Draw Layer")
        prop_split(box, obj, "ootGeometryType", "Geometry Type")
        if obj.ootGeometryType == "Actor Collider":
            obj.ootActorCollider.draw(obj, box)
            obj.ootActorColliderItem.draw(obj, box)

        # Doesn't work since all static meshes are pre-transformed
        # box.prop(obj.ootDynamicTransform, "billboard")

        # drawParentSceneRoom(box, obj)


oot_actor_collider_classes = (
    OOTColliderLayers,
    OOTDamageFlagsProperty,
    OOTColliderHitboxItemProperty,
    OOTColliderHurtboxItemProperty,
    OOTColliderPhysicsItemProperty,
    OOTColliderHitboxProperty,
    OOTColliderHurtboxProperty,
    OOTColliderPhysicsProperty,
    OOTActorColliderProperty,
    OOTActorColliderItemProperty,
)

oot_actor_collider_panel_classes = (OOT_ActorColliderPanel,)


def oot_actor_collider_panel_register():
    for cls in oot_actor_collider_panel_classes:
        register_class(cls)


def oot_actor_collider_panel_unregister():
    for cls in reversed(oot_actor_collider_panel_classes):
        unregister_class(cls)


def oot_actor_collider_register():
    for cls in oot_actor_collider_classes:
        register_class(cls)

    bpy.types.Object.ootGeometryType = bpy.props.EnumProperty(items=ootEnumGeometryType, name="Geometry Type")
    bpy.types.Object.ootActorCollider = bpy.props.PointerProperty(type=OOTActorColliderProperty)
    bpy.types.Object.ootActorColliderItem = bpy.props.PointerProperty(type=OOTActorColliderItemProperty)


def oot_actor_collider_unregister():
    for cls in reversed(oot_actor_collider_classes):
        unregister_class(cls)

    del bpy.types.Object.ootGeometryType
    del bpy.types.Object.ootActorCollider
    del bpy.types.Object.ootActorColliderItem
