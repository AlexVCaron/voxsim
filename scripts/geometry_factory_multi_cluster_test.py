from math import pi

from simulator.factory import GeometryFactory
from simulator.factory import Plane

resolution = [10, 10, 10]
spacing = [2, 2, 2]

spheres_center = [
    [-2, 7, 10],
    [2, -1, 11]
]
sphere_radius = 5

n_point_per_centroid = 5
bundle_radius = 4
bundle_symmetry = 1
bundle_n_fibers1, bundle_n_fibers2 = 1E4, 1E6
bundle_limits = [[0, 1], [0, 1], [0, 1]]
bundle_center = [0, 0, 0]
world_center = [5, 5, 5]

base_anchors = [
    [0.5, -0.3, 0.5],
    [0.5, -0.2, 0.5],
    [0.5, -0.1, 0.5],
    [0.5, 0, 0.5],
    [0.5, 0.1, 0.5],
    [0.5, 0.2, 0.5],
    [0.5, 0.3, 0.5],
    [0.5, 0.4, 0.5],
    [0.5, 0.5, 0.5],
    [0.5, 0.6, 0.5],
    [0.5, 0.7, 0.5],
    [0.5, 0.8, 0.5],
    [0.5, 0.9, 0.5],
    [0.5, 1.1, 0.5],
    [0.5, 1.2, 0.5],
    [0.5, 1.3, 0.5],
    [0.5, 1.4, 0.5]
]


def run_geometry_factory_test(output_folder, output_naming):
    geometry_handler = GeometryFactory.get_geometry_handler(resolution, spacing)

    bundle1 = GeometryFactory.create_bundle(bundle_radius, bundle_symmetry, n_point_per_centroid, base_anchors)
    _, bundle2 = GeometryFactory.rotate_bundle(bundle1, [0.5, 0.5, 0.5], pi / 6., Plane.YZ)

    cluster = GeometryFactory.create_cluster(
        GeometryFactory.create_cluster_meta(3, bundle_n_fibers1, 1, bundle_center, bundle_limits),
        [bundle1, bundle2],
        world_center
    )

    geometry_handler.add_cluster(cluster)

    cluster = GeometryFactory.create_cluster(
        GeometryFactory.create_cluster_meta(3, bundle_n_fibers2, 1, bundle_center, bundle_limits),
        [bundle1, bundle2],
        world_center
    )

    geometry_handler.add_cluster(cluster)

    sphere_1 = GeometryFactory.create_sphere(sphere_radius, spheres_center[0])
    sphere_2 = GeometryFactory.create_sphere(sphere_radius, spheres_center[1])

    geometry_handler.add_sphere(sphere_1)
    geometry_handler.add_sphere(sphere_2)

    return geometry_handler.generate_json_configuration_files(
        output_naming,
        output_folder
    )


if __name__ == "__main__":
    run_geometry_factory_test(
        "/media/vala2004/b1f812ac-9843-4a1f-877a-f1f3bd303399/data/simu_factory_test",
        "test_factory_multi_cluster"
    )
