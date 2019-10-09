from numpy import array


def translate_bundle(fiber, translation, bbox=None):
    anchors = fiber.get_anchors()
    t_anchors = []
    t_bbox = []
    for anchor in anchors:
        t_anchors.append((array(anchor) + array(translation)).tolist())
    if bbox:
        for pt in bbox:
            t_bbox.append((array(pt) + array(translation)).tolist())

    return t_bbox, t_anchors
