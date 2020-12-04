#!/usr/bin/env python3

from scripts.new_geometry_factory_test import run_geometry_factory_test
from scripts.new_simulation_factory_test import run_simulation_factory_test
from simulator.runner import SimulationRunner

output_folder = "/media/vala2004/b1f812ac-9843-4a1f-877a-f1f3bd303399/data/simu_factory_test"


def run_simulation_runner_test():
    geometry_parameters = run_geometry_factory_test(
        output_folder,
        "runner_test_geometry"
    )

    simulation_parameters = run_simulation_factory_test(
        output_folder,
        "runner_test_simulation"
    )

    runner = SimulationRunner("runner_test", geometry_parameters, simulation_parameters, output_nifti=True)

    runner.run(output_folder, True)

    simulation_parameters = run_simulation_factory_test(
        output_folder,
        "runner_test_simulation_standalone"
    )

    runner.run_simulation_standalone(output_folder, output_folder, simulation_parameters)


if __name__ == "__main__":
    run_simulation_runner_test()
