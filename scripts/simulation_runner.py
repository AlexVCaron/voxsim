#!/usr/bin/env python3

import argparse
from os import makedirs
from os.path import join
from tempfile import mkdtemp

from scripts.geometry_factory import get_geometry_parameters
from scripts.simulation_factory import get_simulation_parameters
from simulator.runner.legacy import SimulationRunner


def run_simulation(output_folder):
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
        output_nifti=True,
    )

    runner.run(output_folder, True)

    simulation_parameters = get_simulation_parameters(
        output_folder, "runner_test_simulation_standalone"
    )

    standalone_output = join(output_folder, "standalone_test")

    runner.run_simulation_standalone(
        standalone_output, output_folder, simulation_parameters, "standalone"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Simulation Runner Example Script")
    parser.add_argument(
        "--out", type=str, required=False, help="Output directory for the files"
    )

    args = parser.parse_args()
    if "out" in args and args.out:
        dest = args.out
        makedirs(args.out, exist_ok=True)
    else:
        dest = mkdtemp(prefix="sim_runner")

    print("Script execution results are in : {}".format(dest))
    run_simulation(dest)
