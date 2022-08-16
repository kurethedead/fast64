from typing import Callable
import bpy, mathutils, os, re, math
from ...utility import PluginError, hexOrDecInt, toAlnum
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


def writeColliderData(
    geometryName: str,
    basePath: str,
    overlayName: str,
    isLink: bool,
    parentObj: bpy.types.Object,
    colliderSettings: OOTActorColliderImportExportSettings,
):
    pass
