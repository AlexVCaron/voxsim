import numpy as np


def translate_bundle(fiber, translation, bbox=None):
    anchors = fiber.get_anchors()
    t_anchors = []
    t_bbox = []
    for anchor in anchors:
        t_anchors.append((np.array(anchor) + np.array(translation)).tolist())
    if bbox:
        for pt in bbox:
            t_bbox.append((np.array(pt) + np.array(translation)).tolist())

    return t_bbox, t_anchors
