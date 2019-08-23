from factory.geometry_factory.features.ORM.Objects.bundle import Bundle
from factory.geometry_factory.features.ORM.Objects.world import World


class ConfigBuilder:
    @staticmethod
    def create_bundle_object(extension, names, scalings, center):
        bundle = Bundle()
        bundle.set_extension_from_path(extension).set_fibers_names(names).set_scalings(scalings).set_center(center)
        return bundle

    @staticmethod
    def create_world(dimension, resolution):
        world = World()
        world.set_dimension(dimension).set_resolutions(resolution)

        return world
