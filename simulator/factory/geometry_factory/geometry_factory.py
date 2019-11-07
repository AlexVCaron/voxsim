from .features import Cluster, ClusterMeta, Bundle, Sphere
from .utils import Plane
from .handlers import GeometryHandler
from .utils import rotate_bundle, Rotation, translate_bundle

from numpy import array


class GeometryFactory:

    @staticmethod
    def get_geometry_handler(resolution, spacing):
        return GeometryHandler(resolution, spacing)

    @staticmethod
    def create_cluster_meta(dimensions, fibers_per_bundle, sampling_distance, center, limits):
        cluster_meta = ClusterMeta()
        cluster_meta.set_dimensions(dimensions)\
                    .set_center(center)\
                    .set_limits(limits)\
                    .set_density(fibers_per_bundle)\
                    .set_sampling(sampling_distance)

        return cluster_meta

    @staticmethod
    def create_cluster(meta, bundles=list, world_center=None):
        cluster = Cluster()
        cluster.set_cluster_meta(meta)\
               .set_bundles(bundles)\
               .set_world_center(world_center if world_center else meta.get_center())

        return cluster

    @staticmethod
    def create_bundle(radius, symmetry, n_point_per_centroid, anchors=list):
        bundle = Bundle()
        bundle.set_radius(radius)\
              .set_symmetry(symmetry)\
              .set_n_point_per_centroid(n_point_per_centroid)\
              .set_anchors(anchors)

        return bundle

    @staticmethod
    def rotate_bundle(bundle, center, angle, plane=Plane.XY, bbox=None, bbox_center=None):
        bbox, anchors = rotate_bundle(bundle, Rotation(plane).generate(angle), center, bbox, bbox_center)
        return bbox, GeometryFactory.create_bundle(
            bundle.get_radius(),
            bundle.get_symmetry(),
            bundle.get_n_point_per_centroid(),
            anchors
        )

    @staticmethod
    def translate_bundle(bundle, translation, bbox=None):
        bbox, anchors = translate_bundle(bundle, translation, bbox)
        return bbox, GeometryFactory.create_bundle(
            bundle.get_radius(),
            bundle.get_symmetry(),
            bundle.get_n_point_per_centroid(),
            anchors
        )

    @staticmethod
    def create_sphere(radius, center, scaling=1):
        sphere = Sphere()
        sphere.set_radius(radius).set_center(center)
        if scaling > 0:
            sphere.set_scaling(scaling)

        return sphere

    @staticmethod
    def rotate_sphere(sphere, center, plane, angle):
        new_sphere = Sphere()
        rotation = Rotation(plane).generate(angle)
        new_center = (rotation @ (array(sphere.get_center()) - center)) + center

        new_sphere.set_radius(sphere.get_radius())\
                  .set_center(new_center.tolist())\
                  .set_scaling(sphere.get_scaling())

        return new_sphere

