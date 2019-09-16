from scipy.ndimage import rotate
from .features.bundle import Bundle
from .features.bundle_meta import BundleMeta
from .features.fiber import Fiber
from .features.sphere import Sphere
from factory.geometry_factory.handlers.geometry_handler import GeometryHandler
from .features.utils.plane import Plane


class GeometryFactory:

    @staticmethod
    def get_geometry_handler(resolution, spacing):
        return GeometryHandler(resolution, spacing)

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
    def create_bundle(meta, fibers=list):
        bundle = Bundle()
        bundle.set_bundle_meta(meta).set_fibers(fibers)

        return bundle

    @staticmethod
    def create_fiber(radius, symmetry, sampling, anchors=list):
        fiber = Fiber()
        fiber.set_radius(radius).set_symmetry(symmetry).set_sampling(sampling).set_anchors(anchors)

        return fiber

    @staticmethod
    def rotate_fiber(fiber, angle, plane=Plane.XY):
        anchors = rotate(fiber.get_anchors(), angle, plane)
        fiber.set_anchors(anchors)

        return fiber

    @staticmethod
    def create_sphere(radius, center, scaling=1):
        sphere = Sphere()
        sphere.set_radius(radius).set_center(center)
        if scaling > 0:
            sphere.set_scaling(scaling)

        return sphere
