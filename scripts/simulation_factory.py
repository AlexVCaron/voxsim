#!/usr/bin/env python

import argparse
from os import makedirs
from tempfile import mkdtemp
from random import uniform

from numpy import array
from numpy.linalg import norm

from simulator.factory import SimulationFactory
from simulator.utils.test_helpers import GeometryHelper


def get_simulation_parameters(output_folder, output_naming):
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
        SimulationFactory.generate_acquisition_profile(100, 1000, 10)
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

    normalize = lambda a: (array(a) / norm(a)).tolist()

    simulation_handler.set_gradient_profile(
        SimulationFactory.generate_gradient_profile(
            [500 for i in range(9)]
            + [1000 for i in range(10)]
            + [2000 for i in range(10)],
            [
                normalize([uniform(-1, 1), uniform(-1, 1), uniform(-1, 1)])
                for i in range(30)
            ],
            1,
            g_type=SimulationFactory.AcquisitionType.STEJSKAL_TANNER,
        )
    )

    return simulation_handler.generate_xml_configuration_file(
        output_naming, output_folder
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Simulation Factory Example Script")
    parser.add_argument(
        "--out", type=str, required=False, help="Output directory for the files"
    )

    args = parser.parse_args()
    if "out" in args and args.out:
        dest = args.out
        makedirs(args.out, exist_ok=True)
    else:
        dest = mkdtemp(prefix="sim_factory")

    print("Script execution results are in : {}".format(dest))
    get_simulation_parameters(dest, "simulation")
