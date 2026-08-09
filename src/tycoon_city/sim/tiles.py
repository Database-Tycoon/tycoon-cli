from enum import Enum, auto


class ZoneStyle(Enum):
    INDUSTRIAL = auto()
    COMMERCIAL = auto()
    RESIDENTIAL = auto()


class TileKind(Enum):
    GRASS = auto()
    ROAD = auto()
    POWER_LINE = auto()
    PLANT = auto()
    LOT = auto()
    WATER = auto()
