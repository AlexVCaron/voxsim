#!/usr/bin/env python

from simulator.factory import SimulationFactory
from simulator.utils.test_helpers import GeometryHelper
from random import uniform
from numpy.linalg import norm
from numpy import array


def run_simulation_factory_test(output_folder, output_naming):
    fiber_compartment = SimulationFactory.generate_fiber_stick_compartment(
        0.007,
        900,
        80,
        SimulationFactory.CompartmentType.INTRA_AXONAL
    )

    csf_compartment = SimulationFactory.generate_extra_ball_compartment(
        3.,
        4000,
        2000,
        SimulationFactory.CompartmentType.EXTRA_AXONAL_1
    )

    simulation_handler = SimulationFactory.get_simulation_handler(
        GeometryHelper.get_dummy_empty_geometry_handler(),
        [fiber_compartment, csf_compartment]
    )

    simulation_handler.set_acquisition_profile(
        SimulationFactory.generate_acquisition_profile(
            100,
            1000,
            10
        )
    )

    noise_artifact = SimulationFactory.generate_noise_model("gaussian", 30)
    motion_artifact = SimulationFactory.generate_motion_model(True, "random", [3.1415 / 6, 0, 0], [4, 0, 0])

    simulation_handler.set_artifact_model(
        SimulationFactory.generate_artifact_model(noise_artifact, motion_artifact)
    )

    normalize = lambda a: (array(a) / norm(a)).tolist()

    simulation_handler.set_gradient_profile(
        SimulationFactory.generate_gradient_profile(
            [500 for i in range(9)] + [1000 for i in range(10)] + [2000 for i in range(10)],
            [normalize([uniform(-1, 1), uniform(-1, 1), uniform(-1, 1)]) for i in range(30)],
            1,
            g_type=SimulationFactory.AcquisitionType.STEJSKAL_TANNER
        )
    )

    return simulation_handler.generate_xml_configuration_file(
        output_naming,
        output_folder
    )


if __name__ == "__main__":
    run_simulation_factory_test(
        "/media/vala2004/b1f812ac-9843-4a1f-877a-f1f3bd303399/data/simu_factory_test",
        "fiberfox_test_params"
    )
