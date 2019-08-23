from enum import Enum


class Plane(Enum):
    XY = (0, 1)
    ZX = (0, 2)
    YZ = (1, 2)