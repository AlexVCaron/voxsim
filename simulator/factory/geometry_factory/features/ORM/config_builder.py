from .Objects import Cluster, World


class ConfigBuilder:
    @staticmethod
    def create_cluster_object(extension, names, scalings, center):
        cluster = Cluster()
        cluster.set_extension_from_path(extension).set_bundles_names(
            names
        ).set_scalings(scalings).set_center(center)
        return cluster

    @staticmethod
    def create_world(dimension, resolution):
        world = World()
        world.set_dimension(dimension).set_resolutions(resolution)

        return world
