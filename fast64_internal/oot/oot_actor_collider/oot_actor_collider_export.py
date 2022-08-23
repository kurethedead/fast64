from typing import Callable
import bpy, mathutils, os, re, math
from ...utility import CData, PluginError, hexOrDecInt, toAlnum
from ..oot_model_classes import ootGetActorData, ootGetIncludedAssetData, ootGetActorDataPaths, ootGetLinkData
from ..oot_constants import ootEnumColliderShape, ootEnumColliderType, ootEnumColliderElement, ootEnumHitboxSound
from .oot_actor_collider_properties import (
    OOTActorColliderItemProperty,
    OOTActorColliderProperty,
    OOTColliderHitboxItemProperty,
    OOTColliderHitboxProperty,
    OOTColliderHurtboxItemProperty,
    OOTColliderHurtboxProperty,
    OOTColliderPhysicsItemProperty,
    OOTColliderPhysicsProperty,
    OOTColliderLayers,
    OOTDamageFlagsProperty,
    OOTActorColliderImportExportSettings,
)
from ..oot_utility import getOrderedBoneList, getOOTScale


def getColliderData(parentObj: bpy.types.Object) -> CData:

    # TODO: Handle hidden?
    colliderObjs = [obj for obj in parentObj.children if obj.ootGeometryType == "Actor Collider"]

    data = CData()
    data.source += getColliderDataSingle(colliderObjs, "COLSHAPE_CYLINDER", "ColliderCylinderInit")
    data.source += getColliderDataJointSphere(colliderObjs)
    data.source += getColliderDataMesh(colliderObjs)
    data.source += getColliderDataSingle(colliderObjs, "COLSHAPE_QUAD", "ColliderQuadInit")

    return data


def getShapeData(obj: bpy.types.Object, bone: bpy.types.Bone | None = None) -> str:
    shape = obj.ootActorCollider.colliderShape
    translate, rotate, scale = obj.matrix_local.decompose()
    yUpToZUp = mathutils.Quaternion((1, 0, 0), math.radians(90.0))

    if shape == "COLSHAPE_JNTSPH":
        if obj.parent is None:
            raise PluginError(f"Joint sphere collider {obj.name} must be parented to a mesh or armature.")

        isUniform = abs(scale[0] - scale[1]) < 0.001 and abs(scale[1] - scale[2]) < 0.001
        if not isUniform:
            raise PluginError(f"Sphere collider {obj.name} must have uniform scale (radius).")

        if isinstance(obj.parent.data, bpy.types.Armature) and bone is not None:
            boneList = getOrderedBoneList(obj.parent)
            limb = boneList.index(bone) + 1
        else:
            limb = obj.ootActorColliderItem.limbOverride

        # When object is parented to bone, its matrix_local is relative to the tail(?) of that bone.
        # No need to apply yUpToZUp here?
        translateData = ", ".join(
            [
                str(round(value))
                for value in getOOTScale(obj.parent.ootActorScale)
                * (
                    (translate - (mathutils.Vector(bone.head) - mathutils.Vector(bone.tail)))
                    if bone is not None
                    else translate
                )
            ]
        )
        scale = bpy.context.scene.ootBlenderScale * scale
        radius = round(abs(scale[0]))

        return f"{{ {limb}, {{ {{ {translateData} }} , {radius} }}, 100 }},\n"

    elif shape == "COLSHAPE_CYLINDER":
        # Convert to OOT space transforms
        translate = bpy.context.scene.ootBlenderScale * (yUpToZUp.inverted() @ translate)
        scale = bpy.context.scene.ootBlenderScale * (yUpToZUp.inverted() @ scale)

        isUniformXY = abs(scale[0] - scale[1]) < 0.001
        if not isUniformXY:
            raise PluginError(f"Cylinder collider {obj.name} must have uniform XY scale (radius).")
        radius = round(abs(scale[0]))
        height = round(abs(scale[1] * 2))

        yShift = round(translate[1])
        position = [round(translate[0]), 0, round(translate[2])]

        return f"{{ {radius}, {height}, {yShift}, {{ {position[0]}, {position[1]}, {position[2]} }} }},\n"

    elif shape == "COLSHAPE_TRIS":
        pass  # handled in its own function
    elif shape == "COLSHAPE_QUAD":
        # geometry data ignored
        return "{ { { 0.0f, 0.0f, 0.0f }, { 0.0f, 0.0f, 0.0f }, { 0.0f, 0.0f, 0.0f }, { 0.0f, 0.0f, 0.0f } } },\n"
    else:
        raise PluginError(f"Invalid shape: {shape} for {obj.name}")


def getColliderDataSingle(colliderObjs: list[bpy.types.Object], shape: str, structName: str) -> str:
    filteredObjs = [obj for obj in colliderObjs if obj.ootActorCollider.colliderShape == shape]
    colliderData = ""
    for obj in filteredObjs:
        collider = obj.ootActorCollider
        colliderItem = obj.ootActorColliderItem
        data = f"static {structName}{'Type1' if collider.physics.isType1 else ''} {collider.name} = {{\n"
        data += collider.to_c(1)
        data += colliderItem.to_c(1)
        data += "\t" + getShapeData(obj)
        data += "};\n\n"

        colliderData += data

    return colliderData


def getColliderDataJointSphere(colliderObjs: list[bpy.types.Object]) -> str:
    sphereObjs = [
        obj
        for obj in colliderObjs
        if obj.ootActorCollider.colliderShape == "COLSHAPE_JNTSPH" and obj.parent is not None
    ]
    if len(sphereObjs) == 0:
        return ""

    collider = sphereObjs[0].parent.ootActorCollider
    name = collider.name
    elementsName = collider.name + "Items"
    colliderData = ""

    colliderData += f"static ColliderJntSphElementInit {elementsName}[{len(sphereObjs)}] = {{\n"
    for obj in sphereObjs:
        if obj.parent is not None and isinstance(obj.parent.data, bpy.types.Armature) and obj.parent_bone != "":
            bone = obj.parent.data.bones[obj.parent_bone]
        else:
            bone = None

        data = "\t{\n"
        data += obj.ootActorColliderItem.to_c(2)
        data += "\t\t" + getShapeData(obj, bone)
        data += "\t},\n"

        colliderData += data
    colliderData += "};\n\n"

    # Required to make export use correct shape, otherwise unused so not an issue modifying here
    collider.shape = "COLSHAPE_JNTSPH"

    colliderData += f"static ColliderJntSphInit{'Type1' if collider.physics.isType1 else ''} {name} = {{\n"
    colliderData += collider.to_c(1)
    colliderData += f"\t{len(sphereObjs)},\n"
    colliderData += f"\t{elementsName},\n"
    colliderData += "};\n\n"

    return colliderData


def getColliderDataMesh(colliderObjs: list[bpy.types.Object]) -> str:
    meshObjs = [obj for obj in colliderObjs if obj.ootActorCollider.colliderShape == "COLSHAPE_TRIS"]
    colliderData = ""

    yUpToZUp = mathutils.Quaternion((1, 0, 0), math.radians(90.0))
    transformMatrix = (
        mathutils.Matrix.Diagonal(mathutils.Vector([bpy.context.scene.ootBlenderScale for i in range(3)] + [1]))
        @ yUpToZUp.to_matrix().to_4x4().inverted()
    )

    for obj in meshObjs:
        collider = obj.ootActorCollider
        name = collider.name
        elementsName = collider.name + "Items"
        mesh = obj.data

        if not (isinstance(mesh, bpy.types.Mesh) and len(mesh.materials) > 0):
            raise PluginError(f"Mesh collider object {obj.name} must have a mesh with at least one material.")

        obj.data.calc_loop_triangles()
        meshData = ""
        for face in obj.data.loop_triangles:
            material = obj.material_slots[face.material_index].material

            tris = [
                ", ".join(
                    [
                        format(value, "0.4f") + "f"
                        for value in (transformMatrix @ obj.matrix_local @ mesh.vertices[face.vertices[i]].co)
                    ]
                )
                for i in range(3)
            ]

            triData = f"{{ {{ {{ {tris[0]} }}, {{ {tris[1]} }}, {{ {tris[2]} }} }} }},\n"

            meshData += "\t{\n"
            meshData += material.ootActorColliderItem.to_c(2)
            meshData += "\t\t" + triData
            meshData += "\t},\n"

        colliderData += f"static ColliderTrisElementInit {elementsName}[{len(mesh.materials)}] = {{\n{meshData}}};\n\n"
        colliderData += f"static ColliderTrisInit{'Type1' if collider.physics.isType1 else ''} {name} = {{\n"
        colliderData += collider.to_c(1)
        colliderData += f"\t{len(obj.data.loop_triangles)},\n"
        colliderData += f"\t{elementsName},\n"
        colliderData += "};\n\n"

    return colliderData
