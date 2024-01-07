import os

from dataclasses import dataclass, field
from typing import Optional
from ...utility import writeFile


@dataclass
class RoomFile:
    """This class hosts the C data for every room files"""

    name: str
    roomMain: Optional[str] = None
    roomModel: Optional[str] = None
    roomModelInfo: Optional[str] = None
    singleFileExport: bool = False
    path: Optional[str] = None

    header: str = ""

    def write(self):
        if self.singleFileExport:
            roomMainPath = f"{self.name}.c"
            self.roomMain += self.roomModelInfo + self.roomModel
        else:
            roomMainPath = f"{self.name}_main.c"
            writeFile(os.path.join(self.path, f"{self.name}_model_info.c"), self.roomModelInfo)
            writeFile(os.path.join(self.path, f"{self.name}_model.c"), self.roomModel)

        writeFile(os.path.join(self.path, roomMainPath), self.roomMain)


@dataclass
class SceneFile:
    """This class hosts the C data for every scene files"""

    name: str
    sceneMain: Optional[str] = None
    sceneCollision: Optional[str] = None
    sceneCutscenes: list[str] = field(default_factory=list)
    sceneTextures: Optional[str] = None
    roomList: dict[int, RoomFile] = field(default_factory=dict)
    singleFileExport: bool = False
    path: Optional[str] = None
    header: str = ""

    hasCutscenes: bool = False
    hasSceneTextures: bool = False

    def __post_init__(self):
        self.hasCutscenes = len(self.sceneCutscenes) > 0
        self.hasSceneTextures = len(self.sceneTextures) > 0

    def getSourceWithSceneInclude(self, sceneInclude: str, source: str):
        ret = ""
        if not sceneInclude in source:
            ret = sceneInclude
        return ret + source

    def setIncludeData(self):
        """Adds includes at the beginning of each file to write"""

        sceneInclude = f'#include "{self.name}.h"\n\n\n'

        for roomData in self.roomList.values():
            roomData.roomMain = self.getSourceWithSceneInclude(sceneInclude, roomData.roomMain)

            if not self.singleFileExport:
                roomData.roomModelInfo = self.getSourceWithSceneInclude(sceneInclude, roomData.roomModelInfo)
                roomData.roomModel = self.getSourceWithSceneInclude(sceneInclude, roomData.roomModel)

        self.sceneMain = self.getSourceWithSceneInclude(sceneInclude, self.sceneMain)
        self.sceneTextures = self.getSourceWithSceneInclude(sceneInclude, self.sceneTextures)

        if not self.singleFileExport:
            self.sceneCollision = self.getSourceWithSceneInclude(sceneInclude, self.sceneCollision)
            if self.hasCutscenes:
                for cs in self.sceneCutscenes:
                    cs = self.getSourceWithSceneInclude(sceneInclude, cs)

    def write(self):
        self.setIncludeData()

        for room in self.roomList.values():
            self.header += room.header
            room.write()

        if self.singleFileExport:
            sceneMainPath = f"{self.name}.c"
            if self.hasCutscenes:
                self.sceneMain += "".join(cs for cs in self.sceneCutscenes)
            self.sceneMain += self.sceneCollision
        else:
            sceneMainPath = f"{self.name}_main.c"
            writeFile(os.path.join(self.path, f"{self.name}_col.c"), self.sceneCollision)
            if self.hasCutscenes:
                for i, cs in enumerate(self.sceneCutscenes):
                    writeFile(os.path.join(self.path, f"{self.name}_cs_{i}.c"), cs)

        if self.hasSceneTextures:
            writeFile(os.path.join(self.path, f"{self.name}_tex.c"), self.sceneTextures)

        writeFile(os.path.join(self.path, sceneMainPath), self.sceneMain)

        self.header += "\n#endif\n"
        writeFile(os.path.join(self.path, f"{self.name}.h"), self.header)
