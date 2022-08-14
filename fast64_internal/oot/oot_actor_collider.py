from typing import Dict
import bpy, mathutils, os
from bpy.utils import register_class, unregister_class
from ..utility import PluginError, prop_split, parentObject, raisePluginError, copyPropertyGroup
from bpy.app.handlers import persistent
import logging
from ..f3d.f3d_material import createF3DMat, update_preset_manual
from .oot_constants import ootEnumColliderShape, ootEnumColliderType, ootEnumColliderElement, ootEnumHitboxSound

logging.basicConfig(format="%(asctime)s: %(message)s", datefmt="%m/%d/%Y %I:%M:%S %p")
logger = logging.getLogger(__name__)


def updateCollider(self, context: bpy.types.Context) -> None:
    updateColliderOnObj(context.object)


def updateColliderOnObj(obj: bpy.types.Object, updateJointSiblings: bool = True) -> None:
    if obj.ootGeometryType == "Actor Collider":
        colliderProp = obj.ootActorCollider
        if colliderProp.colliderShape == "COLSHAPE_JNTSPH":
            if obj.parent == None:
                return
            queryProp = obj.parent.ootActorCollider
        else:
            queryProp = colliderProp

        if colliderProp.colliderShape == "COLSHAPE_TRIS":
            material = getColliderMat("oot_collider_cyan", (0, 0.5, 1, 0.3))
        elif queryProp.hitbox.enable and (queryProp.hurtbox.enable or queryProp.physics.enable):
            material = getColliderMat("oot_collider_magenta", (1, 0, 1, 0.5))
        elif queryProp.hitbox.enable:
            material = getColliderMat("oot_collider_red", (1, 0, 0, 0.5))
        elif queryProp.hurtbox.enable or queryProp.physics.enable:
            material = getColliderMat("oot_collider_blue", (0, 0, 1, 0.5))
        else:
            material = getColliderMat("oot_collider_white", (1, 1, 1, 0.5))
        applyColliderGeoNodes(obj, material, colliderProp.colliderShape)

        if updateJointSiblings and colliderProp.colliderShape == "COLSHAPE_JNTSPH" and obj.parent is not None:
            for child in obj.parent.children:
                updateColliderOnObj(child, False)


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
    enable: bpy.props.BoolProperty(name="Hitbox (AT)", update=updateCollider, default=False)
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
    enable: bpy.props.BoolProperty(name="Hurtbox (AC)", update=updateCollider, default=True)
    attacksBounceOff: bpy.props.BoolProperty(name="Attacks Bounce Off")
    hurtByPlayer: bpy.props.BoolProperty(name="Player", default=True)
    hurtByEnemy: bpy.props.BoolProperty(name="Enemy", default=False)
    hurtByOther: bpy.props.BoolProperty(name="Other", default=False)
    noDamage: bpy.props.BoolProperty(name="Doesn't Take Damage", default=False)

    def draw(self, layout: bpy.types.UILayout):
        layout = layout.box().column()
        layout.prop(self, "enable")
        if self.enable:
            layout.prop(self, "attacksBounceOff")
            layout.prop(self, "noDamage")
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
    enable: bpy.props.BoolProperty(name="Physics (OC)", update=updateCollider, default=True)
    noPush: bpy.props.BoolProperty(name="Don't Push Others")
    collidesWith: bpy.props.PointerProperty(type=OOTColliderLayers)
    isCollider: bpy.props.PointerProperty(type=OOTColliderLayers)
    skipHurtboxCheck: bpy.props.BoolProperty(name="Skip Hurtbox Check After First Collision")
    isType1: bpy.props.BoolProperty(name="Is Type 1", default=False)
    unk1: bpy.props.BoolProperty(name="Unknown 1", default=False)
    unk2: bpy.props.BoolProperty(name="Unknown 2", default=False)

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
            row = layout.row(align=True)
            row.prop(self, "unk1")
            row.prop(self, "unk2")


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
    colliderShape: bpy.props.EnumProperty(
        items=ootEnumColliderShape, name="Shape", default="COLSHAPE_CYLINDER", update=updateCollider
    )
    colliderType: bpy.props.EnumProperty(items=ootEnumColliderType, name="Hit Reaction")
    hitbox: bpy.props.PointerProperty(type=OOTColliderHitboxProperty, name="Hitbox (AT)")
    hurtbox: bpy.props.PointerProperty(type=OOTColliderHurtboxProperty, name="Hurtbox (AC)")
    physics: bpy.props.PointerProperty(type=OOTColliderPhysicsProperty, name="Physics (OC)")

    def draw(self, obj: bpy.types.Object, layout: bpy.types.UILayout):
        if obj.ootActorCollider.colliderShape == "COLSHAPE_JNTSPH":
            armatureObj = obj.parent
            if obj.parent is not None and isinstance(obj.parent.data, bpy.types.Armature) and obj.parent_bone != "":
                layout.label(text="Armature Specific", icon="INFO")
                prop_split(layout, armatureObj.ootActorCollider, "colliderType", "Collider Type")
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

    def draw(self, obj: bpy.types.Object | None, layout: bpy.types.UILayout):
        if obj is not None and obj.ootActorCollider.colliderShape == "COLSHAPE_JNTSPH":
            armatureObj = obj.parent
            if obj.parent is not None and isinstance(obj.parent.data, bpy.types.Armature) and obj.parent_bone != "":
                layout = layout.column()
                layout.label(text="Joint Specific", icon="INFO")
            else:
                return

        if obj is not None and obj.ootActorCollider.colliderShape == "COLSHAPE_TRIS":
            layout = layout.column()
            layout.label(text="Touch/bump defined in materials.", icon="INFO")
            layout.label(text="Materials will not be visualized.")
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
        obj = context.object
        if obj.ootGeometryType == "Actor Collider":
            box = self.layout.box().column()
            name = shapeNameToSimpleName(obj.ootActorCollider.colliderShape)
            box.box().label(text=f"OOT Actor {name} Collider Inspector")
            obj.ootActorCollider.draw(obj, box)
            obj.ootActorColliderItem.draw(obj, box)


class OOT_ActorColliderMaterialPanel(bpy.types.Panel):
    bl_label = "OOT Actor Collider Material Inspector"
    bl_idname = "OBJECT_PT_OOT_Actor_Collider_Material_Inspector"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "material"
    bl_options = {"HIDE_HEADER"}

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return (
            context.scene.gameEditorMode == "OOT"
            and (context.object is not None and isinstance(context.object.data, bpy.types.Mesh))
            and context.object.ootGeometryType == "Actor Collider"
            and context.material is not None
        )

    def draw(self, context: bpy.types.Context):
        material = context.material
        box = self.layout.box().column()
        box.box().label(text=f"OOT Actor Mesh Collider Inspector")
        material.ootActorColliderItem.draw(None, box)


class OOT_AddActorCollider(bpy.types.Operator):
    bl_idname = "object.oot_add_actor_collider_operator"
    bl_label = "Add Actor Collider"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    shape: bpy.props.EnumProperty(items=ootEnumColliderShape)

    def execute(self, context):
        try:
            activeObj = bpy.context.view_layer.objects.active
            selectedObjs = bpy.context.selected_objects

            if activeObj is None:
                raise PluginError("No object selected.")

            if context.mode != "OBJECT":
                bpy.ops.object.mode_set(mode="OBJECT")
            bpy.ops.object.select_all(action="DESELECT")

            if self.shape == "COLSHAPE_JNTSPH":
                if isinstance(activeObj.data, bpy.types.Armature):
                    selectedBones = [bone for bone in activeObj.data.bones if bone.select]
                    if len(selectedBones) == 0:
                        raise PluginError("Cannot add joint spheres since no bones are selected on armature.")
                    for bone in selectedBones:
                        addColliderThenParent(self.shape, activeObj, bone)
                else:
                    raise PluginError("Cannot add joint spheres to non armature object.")
            else:
                addColliderThenParent(self.shape, activeObj, None)

        except Exception as e:
            raisePluginError(self, e)
            return {"CANCELLED"}

        return {"FINISHED"}


class OOT_CopyColliderProperties(bpy.types.Operator):
    bl_idname = "object.oot_copy_collider_properties_operator"
    bl_label = "Copy Collider Properties"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    def execute(self, context):
        try:
            activeObj = bpy.context.view_layer.objects.active
            selectedObjs = [obj for obj in bpy.context.selected_objects if obj.ootGeometryType == "Actor Collider"]

            if activeObj is None:
                raise PluginError("No object selected.")

            if activeObj.ootGeometryType != "Actor Collider":
                raise PluginError("Active object is not an actor collider.")

            if context.mode != "OBJECT":
                bpy.ops.object.mode_set(mode="OBJECT")
            bpy.ops.object.select_all(action="DESELECT")

            if (
                activeObj.ootActorCollider.colliderShape == "COLSHAPE_JNTSPH"
                and activeObj.parent is not None
                and isinstance(activeObj.parent.data, bpy.types.Armature)
            ):
                parentCollider = activeObj.parent.ootActorCollider
            else:
                parentCollider = activeObj.ootActorCollider

            for obj in selectedObjs:
                if (
                    obj.ootActorCollider.colliderShape == "COLSHAPE_JNTSPH"
                    and obj.parent is not None
                    and isinstance(obj.parent.data, bpy.types.Armature)
                ):
                    copyPropertyGroup(parentCollider, obj.parent.ootActorCollider)
                else:
                    copyPropertyGroup(parentCollider, obj.ootActorCollider)
                copyPropertyGroup(activeObj.ootActorColliderItem, obj.ootActorColliderItem)

                updateColliderOnObj(obj)

        except Exception as e:
            raisePluginError(self, e)
            return {"CANCELLED"}

        return {"FINISHED"}


def addColliderThenParent(shapeName: str, obj: bpy.types.Object, bone: bpy.types.Bone | None) -> bpy.types.Object:
    colliderObj = addCollider(shapeName)
    if bone is not None:
        parentObject(obj, colliderObj, "BONE")
        colliderObj.parent_bone = bone.name
        colliderObj.matrix_world = obj.matrix_world @ obj.pose.bones[bone.name].matrix
    else:
        parentObject(obj, colliderObj)
        colliderObj.matrix_local = mathutils.Matrix.Identity(4)
    updateColliderOnObj(colliderObj)
    return colliderObj


def addCollider(shapeName: str) -> bpy.types.Object:
    link_oot_collider_library()
    if bpy.context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.select_all(action="DESELECT")

    # Mesh shape only matters for Triangle shape, otherwise will be controlled by geometry nodes.
    location = mathutils.Vector(bpy.context.scene.cursor.location)
    bpy.ops.mesh.primitive_plane_add(size=2, enter_editmode=False, align="WORLD", location=location[:])
    planeObj = bpy.context.view_layer.objects.active
    planeObj.name = "Collider"
    planeObj.ootGeometryType = "Actor Collider"

    if shapeName == "COLSHAPE_CYLINDER":
        planeObj.lock_location = (True, True, False)
        planeObj.lock_rotation = (True, True, True)
    elif shapeName == "COLSHAPE_TRIS":
        planeObj.lock_location = (True, True, True)
        planeObj.lock_rotation = (True, True, True)

    actorCollider = planeObj.ootActorCollider
    actorCollider.colliderShape = shapeName
    actorCollider.physics.enable = True
    return planeObj


# Apply geometry nodes for the correct collider shape
def applyColliderGeoNodes(obj: bpy.types.Object, material: bpy.types.Material, shapeName: str) -> None:
    nodesName = shapeNameToBlenderName(shapeName)

    if nodesName in bpy.data.node_groups:
        if "Collider Shape" not in obj.modifiers:
            modifier = obj.modifiers.new("Collider Shape", "NODES")
        else:
            modifier = obj.modifiers["Collider Shape"]
        modifier.node_group = bpy.data.node_groups[nodesName]
        modifier["Input_2"] = material
    else:
        raise PluginError(f"Could not find node group name: {nodesName}")


# Creates a semi-transparent solid color material (cached)
def getColliderMat(name: str, color: tuple[float, float, float, float]) -> bpy.types.Material:
    if name not in bpy.data.materials:
        newMat = createF3DMat(None, preset="oot_unlit_texture_transparent", index=0)
        newMat.name = name
        newMat.f3d_mat.combiner1.D = "1"
        newMat.f3d_mat.combiner1.D_alpha = "1"
        newMat.f3d_mat.prim_color = color
        update_preset_manual(newMat, bpy.context)
        return newMat
    else:
        return bpy.data.materials[name]


# unused? right now decided to go with regular hiding instead
def getColliderCollection(shapeName: str | None) -> bpy.types.Collection:
    if "OOT Colliders" not in bpy.data.collections:
        colliderCollection = bpy.data.collections.new("OOT Colliders")
        bpy.context.scene.collection.children.link(colliderCollection)
    else:
        colliderCollection = bpy.data.collections["OOT Colliders"]

    if shapeName is None:
        return colliderCollection

    name = shapeNameToBlenderName(shapeName)
    if name not in bpy.data.collections:
        shapeCollection = bpy.data.collections.new(name)
        colliderCollection.children.link(shapeCollection)
    else:
        shapeCollection = bpy.data.collections[name]

    return shapeCollection


def shapeNameToBlenderName(shapeName: str) -> str:
    return shapeNameLookup(
        shapeName,
        {
            "COLSHAPE_JNTSPH": "oot_collider_sphere",
            "COLSHAPE_CYLINDER": "oot_collider_cylinder",
            "COLSHAPE_TRIS": "oot_collider_triangles",
        },
    )


def shapeNameToSimpleName(shapeName: str) -> str:
    return shapeNameLookup(
        shapeName,
        {
            "COLSHAPE_JNTSPH": "Sphere",
            "COLSHAPE_CYLINDER": "Cylinder",
            "COLSHAPE_TRIS": "Mesh",
        },
    )


def shapeNameLookup(shapeName: str, nameDict: Dict[str, str]) -> str:
    if shapeName in nameDict:
        name = nameDict[shapeName]
        return name
    else:
        raise PluginError(f"Could not find shape name {shapeName} in name dictionary.")


def drawColliderVisibilityOperators(layout: bpy.types.UILayout):
    col = layout.column()
    col.label(text="Toggle Visibility (Excluding Selected)")
    row = col.row(align=True)
    visibilitySettings = bpy.context.scene.ootColliderVisibility
    row.prop(visibilitySettings, "jointSphere", text="Joint Sphere", toggle=1)
    row.prop(visibilitySettings, "cylinder", text="Cylinder", toggle=1)
    row.prop(visibilitySettings, "mesh", text="Mesh", toggle=1)


@persistent
def load_handler(dummy):
    logger.info("Checking for base F3D material library.")

    for lib in bpy.data.libraries:
        lib_path = bpy.path.abspath(lib.filepath)

        # detect if this is one your addon's libraries here
        if "oot_collider_library.blend" in lib_path:

            addon_dir = os.path.dirname(os.path.abspath(__file__))
            new_lib_path = os.path.join(addon_dir, "oot_collider_library.blend")

            if lib_path != new_lib_path:
                logger.info("Reloading the library: %s : %s => %s" % (lib.name, lib_path, new_lib_path))

                lib.filepath = new_lib_path
                lib.reload()
            bpy.context.scene["oot_collider_lib_dir"] = None  # force node reload!
            link_oot_collider_library()


def link_oot_collider_library():
    dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "oot_collider_library.blend")

    prevMode = bpy.context.mode
    if prevMode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")

    with bpy.data.libraries.load(dir) as (data_from, data_to):
        dirNode = os.path.join(dir, "NodeTree")

        # linking is SUPER slow, this only links if the scene hasnt been linked yet
        if bpy.context.scene.get("oot_collider_lib_dir") != dirNode or (
            "oot_collider_lib_ver" in bpy.context.scene
            and bpy.context.scene.ootColliderLibVer > bpy.context.scene["oot_collider_lib_ver"]
        ):
            for node_group in data_from.node_groups:
                if node_group is not None:
                    # append to prevent filepath issues
                    bpy.ops.wm.link(
                        filepath=os.path.join(dirNode, node_group), directory=dirNode, filename=node_group, link=False
                    )
            bpy.context.scene["oot_collider_lib_dir"] = dirNode
            bpy.context.scene["oot_collider_lib_ver"] = bpy.context.scene.ootColliderLibVer


bpy.app.handlers.load_post.append(load_handler)


def updateVisibilityJointSphere(self, context):
    updateVisibilityCollider("COLSHAPE_JNTSPH", self.jointSphere)


def updateVisibilityCylinder(self, context):
    updateVisibilityCollider("COLSHAPE_CYLINDER", self.cylinder)


def updateVisibilityMesh(self, context):
    updateVisibilityCollider("COLSHAPE_TRIS", self.mesh)


def updateVisibilityCollider(shapeName: str, visibility: bool) -> None:
    selectedObjs = bpy.context.selected_objects
    for obj in bpy.data.objects:
        if (
            isinstance(obj.data, bpy.types.Mesh)
            and obj.ootGeometryType == "Actor Collider"
            and obj.ootActorCollider.colliderShape == shapeName
            and obj not in selectedObjs
        ):
            obj.hide_set(not visibility)


class OOTColliderVisibilitySettings(bpy.types.PropertyGroup):
    jointSphere: bpy.props.BoolProperty(name="Joint Sphere", default=True, update=updateVisibilityJointSphere)
    cylinder: bpy.props.BoolProperty(name="Cylinder", default=True, update=updateVisibilityCylinder)
    mesh: bpy.props.BoolProperty(name="Mesh", default=True, update=updateVisibilityMesh)


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
    OOT_AddActorCollider,
    OOTColliderVisibilitySettings,
    OOT_CopyColliderProperties,
)

oot_actor_collider_panel_classes = (OOT_ActorColliderPanel, OOT_ActorColliderMaterialPanel)


def oot_actor_collider_panel_register():
    for cls in oot_actor_collider_panel_classes:
        register_class(cls)


def oot_actor_collider_panel_unregister():
    for cls in reversed(oot_actor_collider_panel_classes):
        unregister_class(cls)


def oot_actor_collider_register():
    for cls in oot_actor_collider_classes:
        register_class(cls)

    bpy.types.Object.ootActorCollider = bpy.props.PointerProperty(type=OOTActorColliderProperty)
    bpy.types.Object.ootActorColliderItem = bpy.props.PointerProperty(type=OOTActorColliderItemProperty)
    bpy.types.Material.ootActorColliderItem = bpy.props.PointerProperty(type=OOTActorColliderItemProperty)
    bpy.types.Scene.ootColliderLibVer = bpy.props.IntProperty(default=1)
    bpy.types.Scene.ootColliderVisibility = bpy.props.PointerProperty(type=OOTColliderVisibilitySettings)


def oot_actor_collider_unregister():
    for cls in reversed(oot_actor_collider_classes):
        unregister_class(cls)

    del bpy.types.Object.ootActorCollider
    del bpy.types.Object.ootActorColliderItem
    del bpy.types.Scene.ootColliderLibVer
    del bpy.types.Scene.ootColliderVisibility
