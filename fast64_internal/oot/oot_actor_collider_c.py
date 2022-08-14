import bpy, mathutils, os, re
from ..utility import PluginError, hexOrDecInt
from .oot_model_classes import ootGetActorData, ootGetIncludedAssetData, ootGetActorDataPaths, ootGetLinkData
from .oot_constants import ootEnumColliderShape, ootEnumColliderType, ootEnumColliderElement, ootEnumHitboxSound
from .oot_actor_collider import (
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
    addColliderThenParent,
)

# has 1 capture group
def flagRegex(commaTerminating: bool = True) -> str:
    return r"\s*([0-9a-zA-Z\_\s\|]*)\s*" + ("," if commaTerminating else ",?")


# has {count} capture groups
def flagListRegex(count: int) -> str:
    regex = ""
    if count < 1:
        return ""
    for i in range(count - 1):
        regex += flagRegex()
    regex += flagRegex(False)
    return regex


# has 3 capture groups
def touchBumpRegex() -> str:
    return r"\{\s*" + flagListRegex(3) + r"\s*\}\s*,"


# has 7 capture groups
def colliderInitRegex() -> str:
    return r"\{\s*" + flagListRegex(5) + "(" + flagRegex() + ")?" + r"\s*\}\s*,"


# has 10 capture groups
def colliderInfoInitRegex() -> str:
    return r"\{\s*" + flagRegex() + touchBumpRegex() + touchBumpRegex() + flagListRegex(3) + r"\s*\}\s*,"


# assumes enums are in numerical order.
def getEnumValue(value: str, enumTuples: list[tuple[str, str, str]]) -> str:
    enumList = [i[0] for i in enumTuples]

    if value in enumList:
        return value
    else:
        try:
            parsedValue = hexOrDecInt(value)
            if parsedValue < len(enumList):
                return parsedValue
            else:
                raise PluginError(f"Out of bounds index: {value}")
        except ValueError:
            raise PluginError(f"Invalid value: {value}")


def parseATFlags(flagData: str, atProp: OOTColliderHitboxProperty):
    flags = [flag.strip() for flag in flagData.split("|")]
    atProp.enable = "AT_ON" in flags
    atProp.alignPlayer = "AT_TYPE_PLAYER" in flags or "AT_TYPE_ALL" in flags
    atProp.alignEnemy = "AT_TYPE_ENEMY" in flags or "AT_TYPE_ALL" in flags
    atProp.alignOther = "AT_TYPE_OTHER" in flags or "AT_TYPE_ALL" in flags
    atProp.alignSelf = "AT_TYPE_SELF" in flags


def parseACFlags(flagData: str, acProp: OOTColliderHurtboxProperty):
    flags = [flag.strip() for flag in flagData.split("|")]
    acProp.enable = "AC_ON" in flags
    acProp.attacksBounceOff = "AC_HARD" in flags
    acProp.hurtByPlayer = "AC_TYPE_PLAYER" in flags or "AC_TYPE_ALL" in flags
    acProp.hurtByEnemy = "AC_TYPE_ENEMY" in flags or "AC_TYPE_ALL" in flags
    acProp.hurtByOther = "AC_TYPE_OTHER" in flags or "AC_TYPE_ALL" in flags
    acProp.noDamage = "AC_NO_DAMAGE" in flags


def parseOCFlags(oc1Data: str, oc2Data: str | None, ocProp: OOTColliderPhysicsProperty):
    flags1 = [flag.strip() for flag in oc1Data.split("|")]
    ocProp.enable = "OC_ON" in flags1
    ocProp.noPush = "OC_NO_PUSH" in flags1
    ocProp.collidesWith.player = "OC1_TYPE_PLAYER" in flags1 or "OC1_TYPE_ALL" in flags1
    ocProp.collidesWith.type1 = "OC1_TYPE_1" in flags1 or "OC1_TYPE_ALL" in flags1
    ocProp.collidesWith.type2 = "OC1_TYPE_2" in flags1 or "OC1_TYPE_ALL" in flags1

    if oc2Data is not None:
        flags2 = [flag.strip() for flag in oc2Data.split("|")]
        ocProp.isCollider.player = "OC2_TYPE_PLAYER" in flags2 or "OC1_TYPE_ALL" in flags2
        ocProp.isCollider.type1 = "OC2_TYPE_1" in flags2 or "OC1_TYPE_ALL" in flags2
        ocProp.isCollider.type2 = "OC2_TYPE_2" in flags2 or "OC1_TYPE_ALL" in flags2
        ocProp.skipHurtboxCheck = "OC2_FIRST_ONLY" in flags2
        ocProp.unk1 = "OC2_UNK1" in flags2
        ocProp.unk2 = "OC2_UNK2" in flags2


def parseColliderInit(match: re.Match, colliderProp: OOTActorColliderProperty):
    colliderProp.colliderType = getEnumValue(match.group(1).strip(), ootEnumColliderType)
    parseATFlags(match.group(2), colliderProp.hitbox)
    parseACFlags(match.group(3), colliderProp.hurtbox)
    parseOCFlags(match.group(4), match.group(5), colliderProp.physics)


def parseDamageFlags(flags: int, flagProp: OOTDamageFlagsProperty):
    flagProp.dekuNut = flags & (1 << 0)
    flagProp.dekuStick = flags & (1 << 1)
    flagProp.slingshot = flags & (1 << 2)
    flagProp.explosive = flags & (1 << 3)
    flagProp.boomerang = flags & (1 << 4)
    flagProp.arrowNormal = flags & (1 << 5)
    flagProp.hammerSwing = flags & (1 << 6)
    flagProp.hookshot = flags & (1 << 7)
    flagProp.slashKokiriSword = flags & (1 << 8)
    flagProp.slashMasterSword = flags & (1 << 9)
    flagProp.slashGiantSword = flags & (1 << 10)
    flagProp.arrowFire = flags & (1 << 11)
    flagProp.arrowIce = flags & (1 << 12)
    flagProp.arrowLight = flags & (1 << 13)
    flagProp.arrowUnk1 = flags & (1 << 14)
    flagProp.arrowUnk2 = flags & (1 << 15)
    flagProp.arrowUnk3 = flags & (1 << 16)
    flagProp.magicFire = flags & (1 << 17)
    flagProp.magicIce = flags & (1 << 18)
    flagProp.magicLight = flags & (1 << 19)
    flagProp.shield = flags & (1 << 20)
    flagProp.mirrorRay = flags & (1 << 21)
    flagProp.spinKokiriSword = flags & (1 << 22)
    flagProp.spinGiantSword = flags & (1 << 23)
    flagProp.spinMasterSword = flags & (1 << 24)
    flagProp.jumpKokiriSword = flags & (1 << 25)
    flagProp.jumpGiantSword = flags & (1 << 26)
    flagProp.jumpMasterSword = flags & (1 << 27)
    flagProp.unknown1 = flags & (1 << 28)
    flagProp.unblockable = flags & (1 << 29)
    flagProp.hammerJump = flags & (1 << 30)
    flagProp.unknown2 = flags & (1 << 31)


def parseTouch(match: re.Match, touch: OOTColliderHitboxItemProperty):
    dmgFlags = int(match.group(9).strip(), 16)
    parseDamageFlags(dmgFlags, touch.damageFlags)
    touch.effect = hexOrDecInt(match.group(10))
    touch.damage = hexOrDecInt(match.group(11))

    flags = [flag.strip() for flag in match.group(15).split("|")]
    touch.enable = "TOUCH_ON" in flags

    for flag in flags:
        if flag in [i[0] for i in ootEnumHitboxSound]:
            touch.soundEffect = flag

    touch.drawHitmarksForEveryCollision = "TOUCH_AT_HITMARK" in flags


def parseBump(match: re.Match, bump: OOTColliderHurtboxItemProperty):
    dmgFlags = int(match.group(9).strip(), 12)
    parseDamageFlags(dmgFlags, bump.damageFlags)
    bump.effect = hexOrDecInt(match.group(13))
    bump.defense = hexOrDecInt(match.group(14))

    flags = [flag.strip() for flag in match.group(16).split("|")]
    bump.enable = "BUMP_ON" in flags
    bump.hookable = "BUMP_HOOKABLE" in flags
    bump.giveInfoToHit = "BUMP_NO_AT_INFO" in flags
    bump.takesDamage = "BUMP_NO_DAMAGE" not in flags
    bump.hasSound = "BUMP_NO_SWORD_SFX" not in flags
    bump.hasHitmark = "BUMP_NO_HITMARK" not in flags


def parseObjectElement(match: re.Match, objectElem: OOTColliderPhysicsItemProperty):
    flags = [flag.strip() for flag in match.group(17).split("|")]
    objectElem.enable = "OCELEM_ON" in flags
    objectElem.toggleUnk3 = "OCELEM_UNK3" in flags


def parseColliderInfoInit(match: re.Match, colliderItemProp: OOTActorColliderItemProperty):
    colliderItemProp.element = getEnumValue(match.group(8).strip(), ootEnumColliderElement)
    parseTouch(match, colliderItemProp.touch)
    parseBump(match, colliderItemProp.bump)
    parseObjectElement(match, colliderItemProp.objectElem)


def parseColliderData(basePath: str, overlayName: str, isLink: bool, parentObj: bpy.types.Object):
    if not isLink:
        actorData = ootGetActorData(basePath, overlayName)
        currentPaths = ootGetActorDataPaths(basePath, overlayName)
    else:
        actorData = ootGetLinkData(basePath)
        currentPaths = [os.path.join(basePath, f"src/code/z_player_lib.c")]
    actorData = ootGetIncludedAssetData(basePath, currentPaths, actorData) + actorData

    parseCylinderColliders(actorData, parentObj)


def parseCylinderColliders(data: str, parentObj: bpy.types.Object):
    for cylinderMatch in re.finditer(
        r"ColliderCylinderInit(Type1)?\s*([0-9a-zA-Z\_]*)\s*=\s*\{(.*?)\}\s*;",
        data,
        flags=re.DOTALL,
    ):
        isType1 = cylinderMatch.group(1) is not None
        name = cylinderMatch.group(2)
        colliderData = cylinderMatch.group(3)

        # regex match exact struct structure
        regex = (
            colliderInitRegex()  # 7 groups
            + colliderInfoInitRegex()  # 10 groups
            + r"\{\s*"
            + flagListRegex(3)
            + r"\{\s*"
            + flagListRegex(3)
            + r"\}\s*\}"
        )

        print(colliderData)
        print(regex)

        dataMatch = re.search(
            regex,
            colliderData,
            flags=re.DOTALL,
        )
        if dataMatch is None:
            raise PluginError(f"Collider {name} has unexpected struct format.")

        obj = addColliderThenParent("COLSHAPE_CYLINDER", parentObj, None)
        parseColliderInit(dataMatch, obj.ootActorCollider)
        parseColliderInfoInit(dataMatch, obj.ootActorColliderItem)
