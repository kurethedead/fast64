from dataclasses import dataclass, field
from typing import Optional
from ....utility import PluginError, CData, toAlnum, indent
from ....f3d.f3d_gbi import TextureExportSettings
from ...oot_level_classes import OOTRoomMesh, OOTBGImage
from ...room.properties import OOTRoomHeaderProperty


@dataclass
class RoomShapeDListsEntry:  # OOTDLGroup
    opa: str
    xlu: str

    def to_c(self):
        return f"{self.opa}, {self.xlu}"


@dataclass
class RoomShape:
    """This class is the base class for all room shapes."""

    name: str
    """Name of struct itself"""

    def to_c(self) -> CData:
        raise PluginError("to_c() not implemented.")

    def get_type(self) -> str:
        # returns value in oot_constants.ootEnumRoomShapeType
        raise PluginError("get_type() not implemented.")


@dataclass
class RoomShapeNormal(RoomShape):
    """This class defines the basic informations shared by other image classes"""

    entry_array_name: str
    """Name of RoomShapeDListsEntry list"""

    def to_c(self):
        """Returns the C data for the room shape"""

        info_data = CData()
        list_name = f"RoomShapeNormal {self.name}"

        # .h
        info_data.header = f"extern {list_name};\n"

        # .c
        num_entries = f"ARRAY_COUNT({self.entry_array_name})"
        info_data.source = (
            (list_name + " = {\n" + indent)
            + f",\n{indent}".join(
                [
                    f"{self.get_type()}",
                    num_entries,
                    f"{self.entry_array_name}",
                    f"{self.entry_array_name} + {num_entries}",
                ]
            )
            + "\n};\n\n"
        )

        return info_data

    def get_type(self):
        return "ROOM_SHAPE_TYPE_NORMAL"


@dataclass
class RoomShapeImageEntry:  # OOTBGImage
    image_name: str  # source
    width: str
    height: str
    format: str  # fmt
    size: str  # siz
    other_mode_flags: str  # tlutMode
    bg_cam_index: int = 0  # bgCamIndex: for which bg cam index is this entry for

    unk_00: int = field(init=False, default=130)  # for multi images only
    unk_0C: int = field(init=False, default=0)
    tlut: str = field(init=False, default="NULL")
    format: str = field(init=False, default="G_IM_FMT_RGBA")
    size: str = field(init=False, default="G_IM_SIZ_16b")
    tlut_count: int = field(init=False, default=0)  # tlutCount

    def to_c(self):
        return (
            indent
            + "{\n"
            + f",\n{indent * 2}".join(
                [
                    f"0x{self.unk_00:04X}, {self.bg_cam_index}",
                    f"{self.image_name}",
                    f"0x{self.unk_0C:08X}",
                    f"{self.tlut}",
                    f"{self.width}, {self.height}",
                    f"{self.format}, {self.size}",
                    f"{self.other_mode_flags}, 0x{self.tlut_count:04X},",
                ]
            )
            + indent
            + " },\n"
        )


@dataclass
class RoomShapeImageBase(RoomShape):
    """This class defines the basic informations shared by other image classes"""

    entry_array_name: str
    """Name of RoomShapeDListsEntry list"""

    def get_amount_type(self):
        raise PluginError("get_amount_type() not implemented.")

    def get_type(self):
        return "ROOM_SHAPE_TYPE_IMAGE"


@dataclass
class RoomShapeImageSingle(RoomShapeImageBase):
    image_entry: RoomShapeImageEntry

    def get_amount_type(self):
        return "ROOM_SHAPE_IMAGE_AMOUNT_SINGLE"

    def to_c(self):
        """Returns the single background image mode variable"""

        info_data = CData()
        list_name = f"RoomShapeImageSingle {self.name}"

        # .h
        info_data.header = f"extern {list_name};\n"

        # .c
        info_data.source = (list_name + " = {\n") + f",\n{indent}".join(
            [
                "{ " + f"{self.get_type()}, {self.get_amount_type()}, &{self.entry_array_name}" + " }",
                f"{self.image_entry.image_name}",
                f"0x{self.image_entry.unk_0C:08X}",
                f"{self.image_entry.tlut}",
                f"{self.image_entry.width}, {self.image_entry.height}",
                f"{self.image_entry.format}, {self.image_entry.size}",
                f"{self.image_entry.otherModeFlags}, 0x{self.image_entry.tlutCount:04X}",
            ]
        )

        return info_data


@dataclass
class RoomShapeImageMulti(RoomShapeImageBase):
    bg_entry_array_name: Optional[str]
    entries: list[RoomShapeImageEntry]

    def get_amount_type(self):
        return "ROOM_SHAPE_IMAGE_AMOUNT_MULTI"

    def to_c_entries(self) -> CData:
        info_data = CData()
        list_name = f"RoomShapeImageMultiBgEntry {self.name}[{len(self.entries)}]"

        # .h
        info_data.header = f"extern {list_name};\n"

        # .c
        info_data.source = list_name + " = {\n" + f"".join(elem.to_c() for elem in self.entries) + "};\n\n"

        return info_data

    def to_c(self) -> CData:
        """Returns the multiple background image mode variable"""

        info_data = CData()
        list_name = f"RoomShapeImageSingle {self.name}"  # TODO: Is this correct? Was copied over from old code

        # .h
        info_data.header = f"extern {list_name};\n"

        # .c
        info_data.source = (list_name + " = {\n") + f",\n{indent}".join(
            [
                "{ " + f"{self.get_type()}, {self.get_amount_type()}, &{self.entry_array_name}" + " }",
                f"ARRAY_COUNT({self.bg_entry_array_name})",
                f"{self.bg_entry_array_name}",
            ]
        )

        entry_data = self.to_c_entries()
        info_data.append(entry_data)

        return info_data


@dataclass
class RoomShapeCullableEntry:
    bounds_sphere_center: tuple[float, float, float]
    bounds_sphere_radius: float
    opa: str
    xlu: str

    def to_c(self):
        return f"{self.opa}, {self.xlu}"


@dataclass
class RoomShapeCullable(RoomShape):
    entry_array_name: str
    """Name of RoomShapeCullableEntry list"""

    entries: list[RoomShapeCullableEntry]

    def get_type(self):
        return "ROOM_SHAPE_TYPE_CULLABLE"

    def to_c_entries(self) -> CData:
        info_data = CData()
        list_name = f"RoomShapeCullableEntry {self.name}[{len(self.entries)}]"

        # .h
        info_data.header = f"extern {list_name};\n"

        # .c
        info_data.source = list_name + " = {\n" + f"".join(elem.to_c() for elem in self.entries) + "};\n\n"

        return info_data

    def to_c(self):
        """Returns the C data for the room shape"""

        info_data = CData()
        list_name = f"RoomShapeCullable {self.name}"

        # .h
        info_data.header = f"extern {list_name};\n"

        # .c
        num_entries = f"ARRAY_COUNTU({self.entry_array_name})"  # U? see ddan_room_0
        info_data.source = (
            (list_name + " = {\n" + indent)
            + f",\n{indent}".join(
                [
                    f"{self.get_type()}",
                    num_entries,
                    f"{self.entry_array_name}",
                    f"{self.entry_array_name} + {num_entries}",
                ]
            )
            + "\n};\n\n"
        )

        return info_data
