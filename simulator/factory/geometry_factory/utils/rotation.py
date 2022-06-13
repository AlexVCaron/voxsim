from enum import Enum
from math import cos, sin

import numpy as np

from .plane import Plane


Rx = lambda theta: [
    [1, 0, 0],
    [0, cos(theta), -sin(theta)],
    [0, sin(theta), cos(theta)],
]

Ry = lambda theta: [
    [cos(theta), 0, sin(theta)],
    [0, 1, 0],
    [-sin(theta), 0, cos(theta)],
]

Rz = lambda theta: [
    [cos(theta), -sin(theta), 0],
    [sin(theta), cos(theta), 0],
    [0, 0, 1],
]


class Rotation:
    class _Rotations(Enum):
        @staticmethod
        def get_rotation(plane):
            return {Plane.XY: Rz, Plane.ZX: Ry, Plane.YZ: Rx}[plane]

    def __init__(self, plane):
        self._rotation = self._Rotations.get_rotation(plane)

    def generate(self, angle):
        return self._rotation(angle)


def rotate_bundle(fiber, rotation, center, bbox=None, bbox_center=None):
    anchors = np.array(fiber.get_anchors())
    r_anchors = []
    r_bbox = []
    for anchor in anchors:
        r_anchors.append(((rotation @ (anchor - center)) + center).tolist())

    if bbox and bbox_center:
        for pt in bbox:
            r_bbox.append((rotation @ (pt - bbox_center)) + bbox_center)

    return r_bbox, r_anchors
