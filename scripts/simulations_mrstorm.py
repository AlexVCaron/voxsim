import numpy as np
from scipy.stats import norm
import json
from os.path import join

from simulator.factory import SimulationFactory
from simulator.runner.simulation_runner import SimulationRunner


def generate_simulation(
        geometry_handler, geometry_infos, output_name, output_params, output_data,
        bvalues, shells=None, randomize_bvecs=True,
        n_simulations=100, artifacts_model=None, generate_noiseless=True,
        n_b0_mean=1., n_b0_var=0.,
        fib_adiff_range=np.arange(1.4E-3, 1.8E-3, 0.4E-5),
        fib_rdiff_range=np.arange(0.6E-3, 0.8E-3, 0.2E-5),
        fib_t1_range=np.arange(700., 1200., 5.),
        fib_t2_range=np.arange(70., 110., 2. / 5.),
        iso_diff_range=np.arange(2.E-3, 3.E-3, 1.E-5),
        iso_t1_range=np.arange(2000., 5000., 30.),
        iso_t2_range=np.arange(1000., 3000., 20.),
        echo_time_range=np.arange(70., 190., 3. / 5.),
        rep_time_range=np.arange(600., 1600., 5.),
        n_coils=30,
        singularity_conf=None
):
    if shells is None:
        shells = [10 for i in range(len(bvalues))]
    else:
        assert len(bvalues) == len(shells)

    assert (artifacts_model or generate_noiseless)

    n_b0 = int(norm.rvs(loc=n_b0_mean, scale=n_b0_var, size=1))

    if randomize_bvecs:
        get_gradients = lambda: SimulationFactory.generate_gradient_vectors(shells)
    else:
        gradients = SimulationFactory.generate_gradient_vectors(shells)
        get_gradients = lambda: gradients

    simulations = {
        "paths": {},
        "parameters": {}
    }

    for i in range(n_simulations):
        simulations["parameters"][i] = {
            "fiber": {
                "adiff": np.random.choice(fib_adiff_range),
                "rdiff": np.random.choice(fib_rdiff_range),
                "t1": np.random.choice(fib_t1_range),
                "t2": np.random.choice(fib_t2_range)
            },
            "iso": {
                "diff": np.random.choice(iso_diff_range),
                "t1": np.random.choice(iso_t1_range),
                "t2": np.random.choice(iso_t2_range)
            },
            "time": {
                "echo": np.random.choice(echo_time_range),
                "rep": np.random.choice(rep_time_range)
            },
            "n_coils": n_coils
        }

        if artifacts_model:
            simulations["parameters"][i]["artifacts"] = artifacts_model

        simulations["paths"][i] = []
        parameters = simulations["parameters"][i]

        fiber_compartment = SimulationFactory.generate_fiber_tensor_compartment(
            parameters["fiber"]["adiff"], parameters["fiber"]["rdiff"], parameters["fiber"]["rdiff"],
            parameters["fiber"]["t1"], parameters["fiber"]["t2"],
            SimulationFactory.CompartmentType.INTRA_AXONAL
        )

        csf_compartment = SimulationFactory.generate_extra_ball_compartment(
            parameters["iso"]["diff"], parameters["iso"]["t1"], parameters["iso"]["t2"],
            SimulationFactory.CompartmentType.EXTRA_AXONAL_1
        )

        simulation_handler = SimulationFactory.get_simulation_handler(
            geometry_handler, [fiber_compartment, csf_compartment]
        )

        simulation_handler.set_acquisition_profile(
            SimulationFactory.generate_acquisition_profile(
                parameters["time"]["echo"],
                parameters["time"]["rep"],
                n_coils
            )
        )

        simulation_handler.set_gradient_profile(
            SimulationFactory.generate_gradient_profile(
                bvalues, get_gradients(), n_b0
            )
        )

        if generate_noiseless:
            simulation_infos = simulation_handler.generate_xml_configuration_file(
                "noiseless_{}_sim_{}".format(output_name, i), output_params
            )

            simulations["paths"][i].append(join(output_data, "noiseless_{}_sim_{}.nii.gz".format(output_name, i)))

            runner = SimulationRunner(
                "noiseless_{}_sim_{}".format(output_name, i), geometry_infos, singularity_conf=singularity_conf
            )
            runner.set_geometry_base_naming(output_name)
            runner.run_simulation_standalone(output_data, geometry_infos["file_path"], simulation_infos)

        if artifacts_model:
            simulation_handler.set_artifact_model(*artifacts_model)

            simulation_infos = simulation_handler.generate_xml_configuration_file(
                "{}_sim_{}".format(output_name, i), output_params
            )

            simulations["paths"][i].append(join(output_data, "{}_sim_{}.nii.gz".format(output_name, i)))

            runner = SimulationRunner(
                "{}_sim_{}".format(output_name, i), geometry_infos, singularity_conf=singularity_conf
            )
            runner.set_geometry_base_naming(output_name)
            runner.run_simulation_standalone(output_data, geometry_infos["file_path"], simulation_infos)

    json.dump(simulations, open(join(output_data, "{}_description.json".format(output_name)), "w+"), indent=4)
