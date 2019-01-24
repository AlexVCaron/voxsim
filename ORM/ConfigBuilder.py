from ORM.Objects.config.Bundle import Bundle

from ORM.Objects.config.Sphere import Sphere
from ORM.Objects.config.World import World


class ConfigBuilder:
    @staticmethod
    def create_bundle_object(extension, names, scalings, center):
        bundle = Bundle()
        bundle.set_extension_from_path(extension).set_fibers_names(names).set_scalings(scalings).set_center(center)
        return bundle

    @staticmethod
    def create_sphere_object(radius, center, scaling=1, color=None):
        sphere = Sphere()
        sphere.set_radius(radius).set_center(center)
        if scaling > 0:
            sphere.set_scaling(scaling)
        if color:
            sphere.set_color(color)

        return sphere

    @staticmethod
    def create_world(dimension, resolution):
        world = World()
        world.set_dimension(dimension).set_resolutions(resolution)

        return world