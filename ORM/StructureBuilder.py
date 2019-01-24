from scipy.ndimage import rotate

from ORM.Objects.structure.Bundle import Bundle
from ORM.Objects.structure.BundleMeta import BundleMeta
from ORM.Objects.structure.Fiber import Fiber
from ORM.utils.Plane import Plane


class StructureBuilder:

    @staticmethod
    def create_bundle_meta(dimensions, density, sampling, center, limits):
        bundle_meta = BundleMeta()
        bundle_meta.set_dimensions(dimensions)\
                   .set_center(center)\
                   .set_limits(limits)\
                   .set_density(density)\
                   .set_sampling(sampling)

        return bundle_meta

    @staticmethod
    def create_bundle(meta, fibers=list()):
        bundle = Bundle()
        bundle.set_bundle_meta(meta).set_fibers(fibers)

        return bundle

    @staticmethod
    def create_fiber(radius, symmetry, sampling, anchors=list()):
        fiber = Fiber()
        fiber.set_radius(radius).set_symmetry(symmetry).set_sampling(sampling).set_anchors(anchors)

        return fiber

    @staticmethod
    def rotate_fiber(fiber, angle, plane=Plane.XY):
        anchors = rotate(fiber.get_anchors(), angle, plane)
        fiber.set_anchors(anchors)

        return fiber