#!/usr/bin/env python3

import argparse
import pathlib
from math import pi, sqrt
from tempfile import mkdtemp

from numpy import mean

from simulator.factory import GeometryFactory, Plane, SimulationFactory
from simulator.runner.legacy import SimulationRunner

resolution = [40, 40, 40]
spacing = [1, 1, 1]
point_per_centroid = 30

x_anchors = [0.15, 0.25, 0.5, 0.75, 0.85]

anchors = [[x, sqrt(0.475 ** 2.0 - (x - 0.5) ** 2.0), 0.5] for x in x_anchors]
n_fibers_per_bundle = 1000

bundle_radius = 8
cluster_limits = [[0, 1], [0, 1], [0, 1]]
cluster_center = [0.5, 0.5, 0.5]


def create_geometry(output_folder: pathlib.Path, output_naming: str, fibers_per_bundle):
    geometry_handler = GeometryFactory.get_geometry_handler(resolution, spacing)

    bundle1 = GeometryFactory.create_bundle(
        bundle_radius, 1, point_per_centroid, anchors
    )
    _, bundle2 = GeometryFactory.rotate_bundle(
        bundle1, [0.5, 0.5, 0.5], pi, Plane.XY
    )

    cluster = GeometryFactory.create_cluster(
        GeometryFactory.create_cluster_meta(
            3, fibers_per_bundle, 1, cluster_center, cluster_limits
        ),
        [bundle1, bundle2],
    )

    geometry_handler.add_cluster(cluster)

    return (
        geometry_handler.generate_json_configuration_files(
            output_naming, output_folder
        ),
        geometry_handler,
    )


def create_split_geometry(
        output_folder: pathlib.Path, output_naming: str, fibers_per_bundle, rotation=None
):
    geometry_handler = GeometryFactory.get_geometry_handler(resolution, spacing)

    bundle = GeometryFactory.create_bundle(
        bundle_radius, 1, point_per_centroid, anchors
    )

    if rotation:
        _, bundle = GeometryFactory.rotate_bundle(
            bundle, [0.5, 0.5, 0.5], rotation, Plane.XY
        )

    specific_center = mean(bundle.get_anchors(), axis=0).tolist()

    cluster = GeometryFactory.create_cluster(
        GeometryFactory.create_cluster_meta(
            3, fibers_per_bundle, 1, specific_center, cluster_limits
        ),
        [bundle],
    )

    geometry_handler.add_cluster(cluster)

    return (
        geometry_handler.generate_json_configuration_files(
            output_naming, output_folder
        ),
        geometry_handler,
    )


def get_base_simulation_handler(geometry_handler, add_noise=False):
    fiber_compartment = SimulationFactory.generate_fiber_tensor_compartment(
        1.7e-3,
        0.4e-3,
        0.4e-3,
        780,
        110,
        SimulationFactory.CompartmentType.INTRA_AXONAL,
    )

    csf_compartment = SimulationFactory.generate_extra_ball_compartment(
        3e-3, 920, 80, SimulationFactory.CompartmentType.EXTRA_AXONAL_1
    )

    base_simulation_handler = SimulationFactory.get_simulation_handler(
        geometry_handler, [fiber_compartment, csf_compartment]
    )

    base_simulation_handler.set_acquisition_profile(
        SimulationFactory.generate_acquisition_profile(100, 1000, 10)
    )

    if add_noise:
        base_simulation_handler.set_artifact_model(
            SimulationFactory.generate_artifact_model(
                SimulationFactory.generate_noise_model(
                    SimulationFactory.NoiseType.RICIAN, 30
                )
            )
        )

    return base_simulation_handler


def create_simulation_b1000(geometry_handler, output_folder, output_naming):
    base_b1000_simulation_handler = get_base_simulation_handler(
        geometry_handler
    )

    b1000_dirs = SimulationFactory.generate_gradient_vectors([64])

    base_b1000_simulation_handler.set_gradient_profile(
        SimulationFactory.generate_gradient_profile(
            [1000 for i in range(64)],
            b1000_dirs,
            1,
            SimulationFactory.AcquisitionType.STEJSKAL_TANNER,
        )
    )

    return base_b1000_simulation_handler.generate_xml_configuration_file(
        output_naming, output_folder
    )


def create_simulation_multishell(
        geometry_handler, output_folder, output_naming
):
    base_multishell_simulation_handler = get_base_simulation_handler(
        geometry_handler
    )

    multishell_dirs = SimulationFactory.generate_gradient_vectors([30, 30, 30])

    b_values = [500, 1000, 1500]

    base_multishell_simulation_handler.set_gradient_profile(
        SimulationFactory.generate_gradient_profile(
            [b_val for i in range(30) for b_val in b_values], multishell_dirs, 1
        )
    )

    return base_multishell_simulation_handler.generate_xml_configuration_file(
        output_naming, output_folder
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Wall Effect Example Script")
    parser.add_argument(
        "--out", type=pathlib.Path, help="Output directory for the files"
    )

    args = parser.parse_args()
    if "out" in args and args.out:
        dest: pathlib.Path = args.out
        dest.mkdir(parents=True, exist_ok=True)
    else:
        dest = pathlib.Path(mkdtemp(prefix="wall_effect"))

    print("Script execution results are in : {}".format(dest))
    (dest / "runner_outputs").mkdir(parents=True, exist_ok=True)

    geometry_infos, geometry_handler = create_geometry(
        dest, "geometry", n_fibers_per_bundle
    )

    simulation_b1000_infos = create_simulation_b1000(
        geometry_handler, dest, "simulation_b1000"
    )

    SimulationRunner(
        "simulation_b1000", geometry_infos, simulation_b1000_infos
    ).run(dest / "runner_outputs", relative_fiber_compartment=False)

    geometry_infos, geometry_handler = create_split_geometry(
        dest, "geometry_split_b1", 3000
    )

    simulation_b1000_infos = create_simulation_b1000(
        geometry_handler, dest, "simulation_split_b1_b1000"
    )

    SimulationRunner(
        "simulation_split_b1_b1000", geometry_infos, simulation_b1000_infos
    ).run(dest / "runner_outputs")

    geometry_infos, geometry_handler = create_split_geometry(
        dest, "geometry_split_b2", 3000, pi
    )

    simulation_b1000_infos = create_simulation_b1000(
        geometry_handler, dest, "simulation_split_b2_b1000"
    )

    SimulationRunner(
        "simulation_split_b2_b1000", geometry_infos, simulation_b1000_infos
    ).run(dest / "runner_outputs")

    simulation_multishell_infos = create_simulation_multishell(
        geometry_handler, dest, "simulation_multishell"
    )

    SimulationRunner(
        "simulation_multishell", geometry_infos, simulation_b1000_infos
    ).run(dest / "runner_outputs")
