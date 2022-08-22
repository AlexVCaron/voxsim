#!/usr/bin/env python3

import argparse
import math
import pathlib
import random
import tempfile

import numpy as np
import numpy.linalg

from simulator.factory import GeometryFactory, Plane, SimulationFactory
from simulator.runner.legacy import SimulationRunner
from simulator.utils.test_helpers import GeometryHelper

resolution = [1, 1, 1]
spacing = [1, 1, 1]

spheres_center = [[-2, 7, 10], [2, -1, 11]]
sphere_radius = 5

n_point_per_centroid = 5
bundle_radius = 4
bundle_symmetry = 1
bundle_n_fibers = 200
bundle_limits = [[0, 1], [0, 1], [0, 1]]
bundle_center = [0.5, 0.5, 0.5]
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
]


def get_geometry_parameters(output_folder: pathlib.Path, output_naming: str):
    geometry_handler = GeometryFactory.get_geometry_handler(resolution, spacing)

    bundle1 = GeometryFactory.create_bundle(
        bundle_radius, bundle_symmetry, n_point_per_centroid, base_anchors
    )
    _, bundle2 = GeometryFactory.rotate_bundle(
        bundle1, [0.5, 0.5, 0.5], math.pi / 6.0, Plane.YZ
    )

    cluster = GeometryFactory.create_cluster(
        GeometryFactory.create_cluster_meta(
            3, bundle_n_fibers, 1, bundle_center, bundle_limits
        ),
        [bundle1, bundle2],
        world_center,
    )

    geometry_handler.add_cluster(cluster)

    sphere_1 = GeometryFactory.create_sphere(sphere_radius, spheres_center[0])
    sphere_2 = GeometryFactory.create_sphere(sphere_radius, spheres_center[1])

    geometry_handler.add_sphere(sphere_1)
    geometry_handler.add_sphere(sphere_2)

    return geometry_handler.generate_json_configuration_files(
        output_naming, output_folder
    )


def get_simulation_parameters(output_folder: pathlib.Path, output_naming: str):
    fiber_compartment = SimulationFactory.generate_fiber_stick_compartment(
        0.007, 900, 80, SimulationFactory.CompartmentType.INTRA_AXONAL
    )

    restricted_fluid_compartment = (
        SimulationFactory.generate_extra_ball_compartment(
            2.0, 4000, 2000, SimulationFactory.CompartmentType.EXTRA_AXONAL_1
        )
    )

    csf_compartment = SimulationFactory.generate_extra_ball_compartment(
        3.0, 4000, 2000, SimulationFactory.CompartmentType.EXTRA_AXONAL_2
    )

    simulation_handler = SimulationFactory.get_simulation_handler(
        GeometryHelper.get_dummy_empty_geometry_handler(),
        [fiber_compartment, restricted_fluid_compartment, csf_compartment],
    )

    simulation_handler.set_acquisition_profile(
        SimulationFactory.generate_acquisition_profile(1, 1, 1, inhomogen_time=1, echo_train_length=1)
    )

    noise_artifact = SimulationFactory.generate_noise_model("gaussian", 30)
    motion_artifact = SimulationFactory.generate_motion_model(
        True, "random", [3.1415 / 6, 0, 0], [4, 0, 0]
    )

    simulation_handler.set_artifact_model(
        SimulationFactory.generate_artifact_model(
            noise_artifact, motion_artifact
        )
    )

    normalize = lambda a: (np.array(a) / np.linalg.norm(a)).tolist()

    simulation_handler.set_gradient_profile(
        SimulationFactory.generate_gradient_profile(
            [500 for i in range(9)]
            + [1000 for i in range(10)]
            + [2000 for i in range(10)],
            [
                normalize([random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(-1, 1)])
                for i in range(30)
            ],
            1,
            g_type=SimulationFactory.AcquisitionType.STEJSKAL_TANNER,
        )
    )

    return simulation_handler.generate_xml_configuration_file(
        output_naming, output_folder
    )


def run_simulation(output_folder: pathlib.Path):
    geometry_parameters = get_geometry_parameters(
        output_folder, "runner_test_geometry"
    )

    simulation_parameters = get_simulation_parameters(
        output_folder, "runner_test_simulation"
    )

    runner = SimulationRunner(
        "runner_test",
        geometry_parameters,
        simulation_parameters,
        output_nifti=False,
    )

    runner.run(output_folder, True)

    simulation_parameters = get_simulation_parameters(
        output_folder, "runner_test_simulation_standalone"
    )

    standalone_output = output_folder / "standalone_test"

    runner.run_simulation_standalone(
        standalone_output, output_folder, simulation_parameters, "standalone"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Simulation Runner Example Script")
    parser.add_argument(
        "--out", type=pathlib.Path, help="Output directory for the files"
    )

    args = parser.parse_args()
    if args.out:
        dest: pathlib.Path = args.out
        dest.mkdir(parents=True, exist_ok=True)
    else:
        dest = pathlib.Path(tempfile.mkdtemp(prefix="sim_runner"))

    print("Script execution results are in : {}".format(dest))
    run_simulation(dest)
