from math import pi

from factory.geometry_factory.geometry_factory import GeometryFactory
from factory.simulation_factory.simulation_factory import SimulationFactory
from runner.simulation_runner import SimulationRunner
from utils.Rotation import rotate_fiber, Rotation, Plane

from utils.qspace_sampler.sampling import multishell

resolution = [10, 10, 10]
spacing = [2, 2, 2]
sampling = 30

anchors = [
    [0.15, 0, 0.5],
    [0.25, 0.4, 0.5],
    [0.5, 0.45, 0.5],
    [0.75, 0.4, 0.5],
    [0.85, 0, 0.5]
]

fiber_radius = 1.5

fibers_limits = [[0, 1], [0, 1], [0, 1]]


def create_geometry_francois(output_folder, output_naming):
    geometry_handler = GeometryFactory.get_geometry_handler(resolution, spacing)

    fiber1 = GeometryFactory.create_fiber(4, 1, sampling, anchors)

    rot_180Z = Rotation(Plane.XY).generate(pi)

    _, fiber2 = rotate_fiber(fiber1, [], rot_180Z, [0.5, 0.5, 0.5], [])

    # _, fiber1 = translate_fiber(fiber1, [], [0, 0.05, 0])
    # _, fiber2 = translate_fiber(fiber2, [], [0, 0.15, 0])

    # fibers_center = mean(array(fiber1.get_anchors() + fiber2.get_anchors()), axis=0).tolist()
    fibers_center = [0.5, 0.5, 0.5]

    bundle = GeometryFactory.create_bundle(
        GeometryFactory.create_bundle_meta(3, 1000, 1, fibers_center, fibers_limits),
        [fiber1, fiber2]
    )

    geometry_handler.add_bundle(bundle)

    return geometry_handler.generate_json_configuration_files(
        output_naming,
        output_folder
    ), geometry_handler


def create_simulation_b1000_francois(geometry_handler, output_folder, output_naming):
    fiber_compartment = SimulationFactory.generate_fiber_tensor_compartment(
        1.7E-3, 0.4E-3, 0.4E-3, 100, 70, SimulationFactory.CompartmentType.INTRA_AXONAL
    )

    csf_compartment = SimulationFactory.generate_extra_ball_compartment(
        3E-3, 4000, 2000, SimulationFactory.CompartmentType.EXTRA_AXONAL_1
    )

    base_b1000_simulation_handler = SimulationFactory.get_simulation_handler(
        geometry_handler, [fiber_compartment, csf_compartment]
    )

    base_b1000_simulation_handler.set_acquisition_profile(
        SimulationFactory.generate_acquisition_profile(
            100, 1000, 10
        )
    )

    b1000_weights = multishell.compute_weights(1, [64], [[0]], [1])
    b1000_dirs = multishell.optimize(1, [64], b1000_weights, max_iter=1000)

    base_b1000_simulation_handler.set_gradient_profile(
        SimulationFactory.generate_gradient_profile(
            [0] + [1000 for i in range(64)],
            [[0, 0, 0]] + b1000_dirs,
            SimulationFactory.AcquisitionType.STEJSKAL_TANNER
        )
    )

    return base_b1000_simulation_handler.generate_xml_configuration_file(
        output_naming,
        output_folder
    )


if __name__ == "__main__":
    geometry_infos, geometry_handler = create_geometry_francois(
        "/media/vala2004/b1f812ac-9843-4a1f-877a-f1f3bd303399/data/geometry_francois",
        "geometry"
    )

    simulation_infos = create_simulation_b1000_francois(
        geometry_handler,
        "/media/vala2004/b1f812ac-9843-4a1f-877a-f1f3bd303399/data/geometry_francois",
        "simulation"
    )

    SimulationRunner("runner", geometry_infos, simulation_infos).run(
        "/media/vala2004/b1f812ac-9843-4a1f-877a-f1f3bd303399/data/geometry_francois/output"
    )

