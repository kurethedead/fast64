from dataclasses import dataclass
from os import path
from ...utility import ootGetSceneOrRoomHeader, PluginError
from .oot_getters import getXMLRoot, getEnumList
from .oot_data import OoT_BaseElement

# Note: "object" in this context refers to an OoT Object file (like ``gameplay_keep``)


@dataclass
class OoT_ObjectElement(OoT_BaseElement):
    index: int


class OoT_ObjectData:
    """Everything related to OoT objects"""

    def __init__(self):
        # general object list
        self.objectList: list[OoT_ObjectElement] = []

        # list of tuples used by Blender's enum properties
        self.ootEnumObjectKey: list[tuple] = []
        self.ootEnumObjectIDLegacy: list[tuple] = []  # for old blends

        # Path to the ``ObjectList.xml`` file
        objectXML = path.dirname(path.abspath(__file__)) + "/xml/ObjectList.xml"
        objectRoot = getXMLRoot(objectXML)

        for obj in objectRoot.iterfind("Object"):
            objName = f"{obj.attrib['Name']} - {obj.attrib['ID'].removeprefix('OBJECT_')}"
            self.objectList.append(
                OoT_ObjectElement(obj.attrib["ID"], obj.attrib["Key"], objName, int(obj.attrib["Index"]))
            )

        self.objectsByID = {obj.id: obj for obj in self.objectList}
        self.objectsByKey = {obj.key: obj for obj in self.objectList}
        self.ootEnumObjectKey = getEnumList(self.objectList, "Custom Object")[0]

        # create the legacy object list
        lastIndex = self.objectsByKey["obj_timeblock"].index
        self.ootEnumObjectIDLegacy = [None] * lastIndex
        self.ootEnumObjectIDLegacy.insert(0, ("Custom", "Custom Object", "Custom"))
        for obj in self.objectList:
            if obj.index < lastIndex + 1:
                self.ootEnumObjectIDLegacy[obj.index] = (obj.id, obj.name, obj.id)

        # validate the legacy list, if there's any None element then something's wrong
        if None in self.ootEnumObjectIDLegacy:
            raise PluginError("ERROR: Legacy Object List doesn't match!")

    def upgradeObjectList(self, objList):
        for obj in objList:
            if obj.objectID == "Custom":
                obj.objectKey = obj.objectID
            else:
                obj.objectKey = self.objectsByID[obj.objectID].key

    def upgradeRoomHeaders(self, roomObj):
        altHeaders = roomObj.ootAlternateRoomHeaders
        for sceneLayer in [
            roomObj.ootRoomHeader,
            altHeaders.childNightHeader,
            altHeaders.adultDayHeader,
            altHeaders.adultNightHeader,
        ]:
            if sceneLayer is not None:
                self.upgradeObjectList(sceneLayer.objectList)
        for i in range(len(altHeaders.cutsceneHeaders)):
            self.upgradeObjectList(altHeaders.cutsceneHeaders[i].objectList)

    def addMissingObjectToProp(self, roomObj, headerIndex, objectKey):
        """Add the missing object to the room empty object OoT object list"""
        if roomObj is not None:
            roomProp = ootGetSceneOrRoomHeader(roomObj, headerIndex, True)
            if roomProp is not None:
                collection = roomProp.objectList
                collection.add()
                collection.move(len(collection) - 1, (headerIndex + 1))
                collection[-1].objectKey = objectKey

    def addMissingObjectsToList(self, roomObj, room, actorData, headerIndex):
        """Adds missing objects to the object list"""
        if len(room.actorList) > 0:
            for roomActor in room.actorList:
                actor = actorData.actorsByID.get(roomActor.actorID)
                if actor is not None and actor.key != "player" and len(actor.tiedObjects) > 0:
                    for objKey in actor.tiedObjects:
                        if objKey not in ["obj_gameplay_keep", "obj_gameplay_field_keep", "obj_gameplay_dangeon_keep"]:
                            objID = self.objectsByKey[objKey].id
                            if not (objID in room.objectIDList):
                                room.objectIDList.append(objID)
                                self.addMissingObjectToProp(roomObj, headerIndex, objKey)

    def addRoomHeadersObjects(self, roomObj, room, actorData):
        """Adds missing objects for alternate room headers"""
        sceneLayers = [room, room.childNightHeader, room.adultDayHeader, room.adultNightHeader]
        for i, layer in enumerate(sceneLayers):
            if layer is not None:
                self.addMissingObjectsToList(roomObj, layer, actorData, i)
        for i in range(len(room.cutsceneHeaders)):
            self.addMissingObjectsToList(roomObj, room.cutsceneHeaders[i], actorData, i + 4)
