from math import pi

from factory.geometry_factory.geometry_factory import GeometryFactory
from utils.Rotation import rotate_fiber, Rotation, Plane

resolution = [10, 10, 10]
spacing = [2, 2, 2]
sampling = 30

spheres_center = [
    [-2, 7, 10],
    [2, -1, 11]
]
sphere_radius = 5

fibers_limits = [[0, 1], [0, 1], [0, 1]]
fibers_center = [0, 0, 0]

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

if __name__ == "__main__":

    geometry_handler = GeometryFactory.get_geometry_handler(resolution, spacing)

    fiber1 = GeometryFactory.create_fiber(4, 1, sampling, base_anchors)

    rot_30X = Rotation(Plane.YZ).generate(pi / 6.)

    _, fiber2 = rotate_fiber(fiber1, [], rot_30X, [0.5, 0.5, 0.5], [])

    bundle = GeometryFactory.create_bundle(
        GeometryFactory.create_bundle_meta(3, 1000, 1, fibers_center, fibers_limits),
        [fiber1, fiber2]
    )

    geometry_handler.add_bundle(bundle)

    geometry_handler.generate_json_configuration_files(
        "test_factory",
        "/media/vala2004/b1f812ac-9843-4a1f-877a-f1f3bd303399/data/simu_factory_test"
    )
