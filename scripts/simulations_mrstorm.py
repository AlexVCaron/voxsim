import logging
import copy
import glob
import json

from os import remove, listdir
from time import time
from os.path import join, dirname, basename

import numpy as np

from scipy.stats import norm

from simulator.exceptions import SimulationRunnerException
from simulator.factory import SimulationFactory
from simulator.runner.simulation_runner import SimulationRunner

logger = logging.getLogger(basename(__file__).split(".")[0])


def cleanup_failed_simulation(path):
    directory = dirname(path)
    pattern = basename(path).split(".")[0]
    for item in glob.glob1(directory, pattern):
        remove(join(directory, item))


def generate_simulation(
        geometry_handler, geometry_infos, output_name, output_params,
        output_data, bvalues, shells=None, randomize_bvecs=True,
        n_simus=100, artifacts_models=None, generate_noiseless=True,
        n_b0_mean=1., n_b0_var=0., b0_base_bvec=(0., 0., 0.), n_coils=30,
        fib_adiff_range=np.arange(1.4E-3, 1.8E-3, 0.4E-5),
        fib_rdiff_range=np.arange(0.3E-3, 0.5E-3, 0.2E-5),
        fib_t1_range=np.arange(700., 900., 5.),
        fib_t2_range=np.arange(90., 130., 2. / 5.),
        iso_diff_range=np.arange(2.E-3, 3.E-3, 1.E-5),
        iso_t1_range=np.arange(1000., 2000., 30.),
        iso_t2_range=np.arange(60., 100., 2. / 5.),
        echo_time_range=np.arange(70., 190., 3. / 5.),
        rep_time_range=np.arange(600., 1600., 5.),
        singularity_conf=None,
        sim_ready_callback=lambda *args, **kwargs: None,
        callback_stride=-1, callback_signal_end=False,
        n_retry=3, get_timings=False
):
    logger.debug("Generating simulations to {}".format(output_data))

    extra_package = {}
    if get_timings:
        extra_package["timings"] = {}

    if shells is None:
        shells = [10 for i in range(len(bvalues))]
    else:
        assert len(bvalues) == len(shells)

    assert (artifacts_models or generate_noiseless)

    n_b0 = int(norm.rvs(loc=n_b0_mean, scale=n_b0_var, size=1))

    if randomize_bvecs:
        get_gradients = lambda: SimulationFactory.generate_gradient_vectors(
            shells
        )
    else:
        gradients = SimulationFactory.generate_gradient_vectors(shells)
        get_gradients = lambda: gradients

    simulations = {
        "paths": {},
        "parameters": {}
    }

    failed_samples = []

    for i in range(n_simus):
        if get_timings:
            extra_package["timings"][i] = []

        simulations["parameters"][i] = {
            "fiber": {
                "adiff": np.random.choice(fib_adiff_range),
                "rdiff": np.random.choice(fib_rdiff_range),
                "t1": int(np.random.choice(fib_t1_range)),
                "t2": int(np.random.choice(fib_t2_range))
            },
            "iso": {
                "diff": np.random.choice(iso_diff_range),
                "t1": int(np.random.choice(iso_t1_range)),
                "t2": int(np.random.choice(iso_t2_range))
            },
            "time": {
                "echo": int(np.random.choice(echo_time_range)),
                "rep": int(np.random.choice(rep_time_range))
            },
            "n_coils": n_coils
        }

        if artifacts_models:
            simulations["parameters"][i]["artifacts"] = artifacts_models

        simulations["paths"][i] = []
        parameters = simulations["parameters"][i]

        fib_compartment = SimulationFactory.generate_fiber_tensor_compartment(
            parameters["fiber"]["adiff"], parameters["fiber"]["rdiff"],
            parameters["fiber"]["rdiff"], parameters["fiber"]["t1"],
            parameters["fiber"]["t2"],
            SimulationFactory.CompartmentType.INTRA_AXONAL
        )

        csf_compartment = SimulationFactory.generate_extra_ball_compartment(
            parameters["iso"]["diff"],
            parameters["iso"]["t1"],
            parameters["iso"]["t2"],
            SimulationFactory.CompartmentType.EXTRA_AXONAL_1
        )

        sim_handler = SimulationFactory.get_simulation_handler(
            geometry_handler, [fib_compartment, csf_compartment]
        )

        sim_handler.set_acquisition_profile(
            SimulationFactory.generate_acquisition_profile(
                parameters["time"]["echo"],
                parameters["time"]["rep"],
                n_coils
            )
        )

        sim_handler.set_gradient_profile(
            SimulationFactory.generate_gradient_profile(
                np.repeat(bvalues, shells).tolist(), get_gradients(),
                n_b0, b0_bvec=b0_base_bvec
            )
        )

        failed_sample = False
        simulation_infos = sim_handler.generate_xml_configuration_file(
            "noiseless_{}_sim_{}".format(output_name, i), output_params
        )

        simulations["paths"][i].append(join(
            output_data, "simulation_outputs",
            "{}_noiseless_sim_{}.nii.gz".format(output_name, i)
        ))

        noiseless_image_name = simulations["paths"][i][-1]

        for trial in range(n_retry):
            try:
                geo_infos = copy.deepcopy(geometry_infos)
                runner = SimulationRunner(
                    "{}_noiseless_sim_{}".format(output_name, i),
                    geo_infos, singularity_conf=singularity_conf
                )
                runner.set_geometry_base_naming(output_name)

                if get_timings:
                    extra_package["timings"][i].append(time())

                runner.run_simulation_standalone(
                    output_data, geo_infos["file_path"], simulation_infos
                )

                if get_timings:
                    extra_package["timings"][i][-1] = (
                        time() - extra_package["timings"][i][-1]
                    )
                    logger.debug("Simulation took {} s".format(extra_package["timings"][i][-1]))
                break
            except SimulationRunnerException as e:
                logging.debug("There was an error generating {}".format(
                    simulations["paths"][i][-1])
                )

                if get_timings:
                    extra_package["timings"][i].pop()

                ex = SimulationRunnerException.ExceptionType.Fiberfox
                if e.err_type is ex:
                    cleanup_failed_simulation(simulations["paths"][i][-1])
                    if trial == (n_retry - 1):
                        logging.warning(
                            "Simulation discarded (Reached retry count)"
                            " : {}".format(simulations["paths"][i][-1])
                        )
                        simulations["paths"].pop(i)
                        simulations["parameters"].pop(i)
                        failed_sample = True
                        failed_samples.append(i)
                    continue
                raise e

        if not failed_sample and artifacts_models:
            for name, model in artifacts_models.items():
                artifacts_model = SimulationFactory.generate_artifact_model(
                    *model
                )
                sim_handler.set_artifact_model(artifacts_model)

                simulation_infos = sim_handler.generate_xml_configuration_file(
                    "{}_model_{}_sim_{}".format(output_name, name, i),
                    output_params
                )

                simulations["paths"][i].append(join(
                    output_data, "simulation_outputs",
                    "{}_model_{}_sim_{}.nii.gz".format(output_name, name, i)
                ))

                for trial in range(n_retry):
                    try:
                        geo_infos = copy.deepcopy(geometry_infos)
                        runner = SimulationRunner(
                            "{}_model_{}_sim_{}".format(output_name, name, i),
                            geo_infos, singularity_conf=singularity_conf
                        )
                        runner.set_geometry_base_naming(output_name)

                        if get_timings:
                            extra_package["timings"][i].append(time())

                        runner.run_simulation_dwimage(
                            output_data, noiseless_image_name,
                            simulation_infos, remove_nrrd=True
                        )

                        if get_timings:
                            extra_package["timings"][i][-1] = (
                                    time() - extra_package["timings"][i][-1]
                            )
                            logger.debug("Simulation took {} s".format(
                                extra_package["timings"][i][-1]
                            ))

                        # runner.run_simulation_standalone(
                        #     output_data, geo_infos["file_path"],
                        #     simulation_infos
                        # )
                        break
                    except SimulationRunnerException as e:
                        logging.debug("There was an error generating {}".format(
                            simulations["paths"][i][-1])
                        )

                        if get_timings:
                            extra_package["timings"][i].pop()

                        e.str_tbk = True
                        logging.debug(str(e))

                        ex = SimulationRunnerException.ExceptionType.Fiberfox
                        if e.err_type is ex:
                            cleanup_failed_simulation(simulations["paths"][i][-1])
                            if trial == (n_retry - 1):
                                logging.warning(
                                    "Simulation discarded (Reached retry count)"
                                    " : {}".format(simulations["paths"][i][-1])
                                )
                                if generate_noiseless:
                                    cleanup_failed_simulation(
                                        simulations["paths"][i][-2]
                                    )
                                simulations["paths"].pop(i)
                                simulations["parameters"].pop(i)
                                failed_samples.append(i)
                            continue
                        raise e

        if callback_stride > 0 and (i + 1) % callback_stride == 0:
            kwargs = {}
            if i + 1 == n_simus:
                kwargs["meta"] = filter(
                    lambda it: ".log" in it or ".json" in it,
                    listdir(output_data)
                )

            sim_ready_callback(
                [simulations['paths'][j]
                 for j in range(i - callback_stride + 1, i + 1)
                 if j not in failed_samples],
                [copy.deepcopy(simulations['parameters'][j])
                 for j in range(i - callback_stride + 1, i + 1)
                 if j not in failed_samples],
                (i + 1) % callback_stride,
                **kwargs
            )
            failed_samples.clear()

    json.dump(
        simulations,
        open(join(
            output_data, "{}_description.json".format(output_name)
        ), "w+"),
        indent=4
    )

    if callback_stride > 0:
        args = ()
        if n_simus % callback_stride > 0:
            args += (
                [simulations['paths'][j]
                 for j in range(n_simus - (n_simus % callback_stride), n_simus)
                 if j not in failed_samples],
                [copy.deepcopy(simulations['parameters'][j])
                 for j in range(n_simus - (n_simus % callback_stride), n_simus)
                 if j not in failed_samples],
                n_simus % callback_stride
            )
        sim_ready_callback(
            *args, end=callback_signal_end, extra=extra_package,
            meta=[join(output_data, it) for it in filter(
                lambda it: ".log" in it or ".json" in it, listdir(output_data)
            )]
        )
