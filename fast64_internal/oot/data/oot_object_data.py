from dataclasses import dataclass
from os import path
from .oot_getters import getXMLRoot, getEnumList
from .oot_data import OoT_BaseElement

# Note: "object" in this context refers to an OoT Object file (like ``gameplay_keep``)


@dataclass
class OoT_ObjectElement(OoT_BaseElement):
    pass


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

        for obj in getXMLRoot(objectXML).iterfind("Object"):
            objName = f"{obj.attrib['Name']} - {obj.attrib['ID'].replace('OBJECT_', '')}"
            self.objectList.append(OoT_ObjectElement(obj.attrib["ID"], obj.attrib["Key"], objName))

        self.objectsByID = {obj.id: obj for obj in self.objectList}
        self.objectsByKey = {obj.key: obj for obj in self.objectList}
        self.ootEnumObjectKey, self.ootEnumObjectIDLegacy = getEnumList(self.objectList, "Custom Object")

    def upgradeObjectList(self, objList):
        for obj in objList:
            obj.objectKey = self.objectsByID.get(obj.objectID).key

    def upgradeAltHeaders(self, roomObj):
        altHeaders = roomObj.ootAlternateRoomHeaders
        for header in ["childNightHeader", "adultDayHeader", "adultNightHeader"]:
            curHeader = getattr(altHeaders, header)
            if curHeader is not None:
                self.upgradeObjectList(curHeader.objectList)
        for i in range(len(altHeaders.cutsceneHeaders)):
            self.upgradeObjectList(altHeaders.cutsceneHeaders[i].objectList)

    def addMissingObjectToUI(self, roomObj, headerIndex, objectKey, csHeaderIndex):
        """Add the missing object to the room empty object OoT object list"""
        if roomObj is not None:
            if headerIndex == 0:
                roomProp = roomObj.ootRoomHeader
            elif headerIndex == 1:
                roomProp = roomObj.ootAlternateRoomHeaders.childNightHeader
            elif headerIndex == 2:
                roomProp = roomObj.ootAlternateRoomHeaders.adultDayHeader
            elif headerIndex == 3:
                roomProp = roomObj.ootAlternateRoomHeaders.adultNightHeader
            elif csHeaderIndex is not None:
                roomProp = roomObj.ootAlternateRoomHeaders.cutsceneHeaders[csHeaderIndex]
            if roomProp is not None:
                collection = roomProp.objectList
                collection.add()
                collection.move(len(collection) - 1, (headerIndex + 1))
                collection[-1].objectKey = objectKey

    def addMissingObjectsToList(self, roomObj, room, actorData, headerIndex, csHeaderIndex):
        """Adds missing objects to the object list"""
        if len(room.actorList) > 0:
            for roomActor in room.actorList:
                actor = actorData.actorsByID.get(roomActor.actorID)
                if not (actor.key == "player") and len(actor.tiedObjects) > 0:
                    for objKey in actor.tiedObjects:
                        if not objKey in ["obj_gameplay", "obj_gameplay_dangeon_keep"]:
                            objID = self.objectsByKey.get(objKey).id
                            if not (objID in room.objectIDList):
                                room.objectIDList.append(objID)
                                self.addMissingObjectToUI(roomObj, headerIndex, objKey, csHeaderIndex)

    def addAltHeadersObjects(self, roomObj, room, actorData):
        """Adds missing objects for alternate room headers"""
        altHeaders = ["childNightHeader", "adultDayHeader", "adultNightHeader"]
        for i, header in enumerate(altHeaders, 1):
            curHeader = getattr(room, header)
            if curHeader is not None:
                self.addMissingObjectsToList(roomObj, curHeader, actorData, i, None)
        for i in range(len(room.cutsceneHeaders)):
            self.addMissingObjectsToList(roomObj, room.cutsceneHeaders[i], actorData, 4, i)
