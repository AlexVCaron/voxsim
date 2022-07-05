#!/usr/bin/env python3

import argparse
import pathlib
from tempfile import mkdtemp

from scripts.geometry_factory import get_geometry_parameters
from scripts.simulation_factory import get_simulation_parameters
from simulator.runner.legacy import SimulationRunner


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
        output_nifti=True,
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
        dest = pathlib.Path(mkdtemp(prefix="sim_runner"))

    print("Script execution results are in : {}".format(dest))
    run_simulation(dest)
