from factory.simulation_factory.simulation_factory import SimulationFactory
from test.helpers.geometry_helper import GeometryHelper
from random import uniform

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

simulation_handler.set_gradient_profile(
    SimulationFactory.generate_gradient_profile(
        [0] + [500 for i in range(9)] + [1000 for i in range(10)] + [2000 for i in range(10)],
        [[0, 0, 0]] + [[uniform(-1, 1), uniform(-1, 1), uniform(-1, 1)] for i in range(30)],
        SimulationFactory.AcquisitionType.STEJSKAL_TANNER.value
    )
)

simulation_handler.generate_xml_configuration_file(
    "fiberfox_test_params",
    "/media/vala2004/b1f812ac-9843-4a1f-877a-f1f3bd303399/data/simu_factory_test"
)