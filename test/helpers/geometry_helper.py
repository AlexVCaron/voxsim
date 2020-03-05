from simulator.factory import GeometryFactory
import numpy as np


class GeometryHelper:

    @staticmethod
    def get_dummy_empty_geometry_handler():
        resolution = [10, 10, 10]
        spacing = [2, 2, 2]

        geometry_handler = GeometryFactory.get_geometry_handler(resolution, spacing)

        return geometry_handler

    @staticmethod
    def get_dummy_geometry_handler(n_clusters=1, n_bundle_per_cluster=(1,), n_spheres=0):
        assert len(n_bundle_per_cluster) == n_clusters

        resolution = [10, 10, 10]
        spacing = [2, 2, 2]

        geometry_handler = GeometryFactory.get_geometry_handler(resolution, spacing)

        for i in range(n_clusters):
            bundles = [
                GeometryFactory.create_bundle(2, 1, 5, [[1, 0, 0], [0.5, 0, 0], [0, 0, 0]])
                for _ in range(n_bundle_per_cluster[i])
            ]
            meta = GeometryFactory.create_cluster_meta(3, 1000, 1, [0.5, 0, 0], [[0, 1], [0, 1], [0, 1]])

            geometry_handler.add_cluster(GeometryFactory.create_cluster(meta, bundles, [0.5, 0, 0]))

        for _ in range(n_spheres):
            geometry_handler.add_sphere(
                GeometryFactory.create_sphere(2, [np.random.uniform(0, resolution[i]) for i in range(len(resolution))])
            )

        return geometry_handler
