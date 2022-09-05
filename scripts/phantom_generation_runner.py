#!/usr/bin/env python3

import argparse
import pathlib

from scripts.geometry_factory import get_geometry_parameters
from simulator.runner.simulation_runner import SimulationRunner


def run_simulation(output_folder: pathlib.Path):
    geometry_parameters = get_geometry_parameters(
        output_folder, "runner_test_geometry"
    )

    runner = SimulationRunner()
    runner.generate_phantom(
        run_name="runner_test_simulation_standalone",
        phantom_infos=geometry_parameters,
        output_folder=output_folder,
        output_nifti=False,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Simulation Runner Example Script")
    parser.add_argument(
        "--out", type=pathlib.Path, default="./out/", help="Output directory for the files"
    )

    args = parser.parse_args()
    dest: pathlib.Path = args.out
    dest.mkdir(parents=True, exist_ok=True)
    dest = dest.resolve(strict=True)

    print("Script execution results are in : {}".format(dest))
    run_simulation(dest)
