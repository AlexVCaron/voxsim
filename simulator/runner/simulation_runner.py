import logging
import glob
from asyncio import sleep, create_subprocess_shell, get_event_loop, new_event_loop, set_event_loop
from multiprocessing import Process
from os import path, makedirs, remove
from os.path import exists, join, basename
from shutil import copyfile
from subprocess import PIPE
from numpy import sum, ones_like, moveaxis, hstack, vstack
import nrrd
import nibabel as nib

from config import get_config
from simulator.exceptions import SimulationRunnerException

logger = logging.getLogger(basename(__file__).split(".")[0])


class SimulationRunner:
    def __init__(self, base_naming, geometry_infos, simulation_infos=None, singularity_conf=get_config()):
        self._geometry_path = geometry_infos["file_path"]
        self._geometry_base_file = geometry_infos["base_file"]
        self._geometry_resolution = geometry_infos["resolution"]
        self._geometry_spacing = geometry_infos["spacing"]
        self._base_naming = base_naming
        self._geometry_base_naming = base_naming
        if simulation_infos:
            self._number_of_maps = len(simulation_infos["compartment_ids"])
            self._simulation_path = simulation_infos["file_path"]
            self._simulation_parameters = simulation_infos["param_file"]
            self._compartment_ids = simulation_infos["compartment_ids"]

        singularity_conf = singularity_conf if singularity_conf else get_config()
        self._singularity = path.join(singularity_conf["singularity_path"], singularity_conf["singularity_name"])

        self._run_simulation = True if simulation_infos else False
        self._event_loop = new_event_loop()

    def set_geometry_base_naming(self, name):
        self._geometry_base_naming = name

    def run_simulation_dwimage(self, output_folder, image_file, simulation_infos, test_mode=False, remove_nrrd=False):
        simulation_output_folder = path.join(output_folder, "simulation_outputs")
        if not path.exists(simulation_output_folder):
            makedirs(simulation_output_folder, exist_ok=True)

        simulation_command = "singularity run -B {} --app launch_mitk {} -p {} -i {} -o {} {}".format(
            ",".join([simulation_infos["file_path"], simulation_output_folder]),
            self._singularity,
            path.join(simulation_output_folder, "{}_simulation.ffp".format(self._base_naming)),
            image_file,
            path.join(simulation_output_folder, "{}.nii.gz".format(self._base_naming)),
            "-v" if test_mode else ""
        )

        copyfile(
            path.join(simulation_infos["file_path"], simulation_infos["param_file"]),
            path.join(simulation_output_folder, "{}_simulation.ffp".format(self._base_naming))
        )

        set_event_loop(self._event_loop)
        async_loop = get_event_loop()

        with open(path.join(output_folder, "{}.log".format(self._base_naming)), "w+") as log_file:
            logger.info("Simulating DWI signal")
            return_code, out, err = async_loop.run_until_complete(self._launch_command(simulation_command, log_file, "[RUNNING FIBERFOX]"))
            if not return_code == 0:
                raise SimulationRunnerException(
                    "Simulation ended in error",
                    SimulationRunnerException.ExceptionType.Fiberfox,
                    return_code, (out, err)
                )

            # self._convert_nrrd_to_nifti(simulation_output_folder, remove_nrrd)
            logger.debug("Simulation {} ended with code {}".format(self._base_naming, return_code))
            async_loop.close()

    def run_simulation_standalone(self, output_folder, geometry_folder, simulation_infos, test_mode=False, remove_nrrd=False):
        simulation_output_folder = path.join(output_folder, "simulation_outputs")
        geometry_output_folder = path.join(geometry_folder, "geometry_outputs")

        if not path.exists(simulation_output_folder):
            makedirs(simulation_output_folder, exist_ok=True)

        simulation_command = "singularity run -B {} --app launch_mitk {} -p {} -i {} -o {} {}".format(
            ",".join([geometry_folder, simulation_infos["file_path"], simulation_output_folder]),
            self._singularity,
            path.join(simulation_output_folder, "{}_simulation.ffp".format(self._base_naming)),
            path.join(geometry_output_folder, self._geometry_base_naming) + "_merged_bundles.fib",
            path.join(simulation_output_folder, "{}.nii.gz".format(self._base_naming)),
            "-v" if test_mode else ""
        )

        copyfile(
            path.join(simulation_infos["file_path"], simulation_infos["param_file"]),
            path.join(simulation_output_folder, "{}_simulation.ffp".format(self._base_naming))
        )

        set_event_loop(self._event_loop)
        async_loop = get_event_loop()

        with open(path.join(output_folder, "{}.log".format(self._base_naming)), "w+") as log_file:
            self._rename_and_copy_compartments_standalone(simulation_infos, geometry_output_folder, simulation_output_folder)
            logger.info("Simulating DWI signal")
            return_code, out, err = async_loop.run_until_complete(self._launch_command(simulation_command, log_file, "[RUNNING FIBERFOX]"))
            if not return_code == 0:
                raise SimulationRunnerException(
                    "Simulation ended in error",
                    SimulationRunnerException.ExceptionType.Fiberfox,
                    return_code, (out, err)
                )

            # self._convert_nrrd_to_nifti(simulation_output_folder, remove_nrrd)
            logger.debug("Simulation {} ended with code {}".format(self._base_naming, return_code))
            async_loop.close()

    def _convert_nrrd_to_nifti(self, root, remove_nrrd=False):
        for item in glob.glob1(root, "{}*.nrrd".format(self._base_naming)):
            data, header = nrrd.read(join(root, item))

            if header["space directions"].shape[0] == 4:
                data = moveaxis(data, 0, -1)
                rotation = header["space directions"][1:, :]
                bottom = [[0, 0, 0, 1]]
            else:
                rotation = header["space directions"]
                bottom = [[0, 0, 0, 1]]

            affine = vstack((hstack((
                rotation, header["space origin"][:, None]
            )), bottom))

            nib.save(
                nib.Nifti1Image(data.astype(header["type"]), affine),
                join(root, "{}.nii.gz".format(item.split(".")[0]))
            )

            if remove_nrrd:
                remove(join(root, item))

    def run(self, output_folder, test_mode=False, relative_fiber_compartment=True, remove_nrrd=False):
        geometry_output_folder = path.join(output_folder, "geometry_outputs")

        if not path.exists(geometry_output_folder):
            makedirs(geometry_output_folder, exist_ok=True)

        if self._run_simulation:
            simulation_output_folder = path.join(output_folder, "simulation_outputs")

            if not path.exists(simulation_output_folder):
                makedirs(simulation_output_folder, exist_ok=True)

        geometry_command = "singularity run -B {} --app launch_voxsim {} -f {} -r {} -s {} -o {} --comp-map {} {} --quiet".format(
            ",".join([self._geometry_path, geometry_output_folder]),
            self._singularity,
            path.join(self._geometry_path, self._geometry_base_file),
            ",".join([str(r) for r in self._geometry_resolution]),
            ",".join([str(s) for s in self._geometry_spacing]),
            path.join(geometry_output_folder, self._geometry_base_naming),
            "rel" if relative_fiber_compartment else "abs",
            "--no-process" if test_mode else "--quiet"
        )

        if self._run_simulation:
            simulation_command = "singularity run -B {} --app launch_mitk {} -p {} -i {} -o {} {}".format(
                ",".join([self._simulation_path, simulation_output_folder]),
                self._singularity,
                path.join(simulation_output_folder, "{}_simulation.ffp".format(self._base_naming)),
                path.join(geometry_output_folder, self._geometry_base_naming) + "_merged_bundles.fib",
                path.join(simulation_output_folder, "{}.nii.gz".format(self._base_naming)),
                "-v" if test_mode else ""
            )

            copyfile(
                path.join(self._simulation_path, self._simulation_parameters),
                path.join(simulation_output_folder, "{}_simulation.ffp".format(self._base_naming))
            )

        set_event_loop(self._event_loop)
        async_loop = get_event_loop()

        with open(path.join(output_folder, "{}.log".format(self._base_naming)), "w+") as log_file:
            logger.info("Generating simulation geometry")
            async_loop.run_until_complete(self._launch_command(geometry_command, log_file, "[RUNNING VOXSIM]"))
            if self._run_simulation:
                self._execute_parallel(self._rename_and_copy_compartments, (geometry_output_folder, simulation_output_folder))
                logger.info("Simulating DWI signal")
                return_code, out, err = async_loop.run_until_complete(self._launch_command(simulation_command, log_file, "[RUNNING FIBERFOX]"))
                if not return_code == 0:
                    raise SimulationRunnerException(
                        "Simulation ended in error",
                        SimulationRunnerException.ExceptionType.Fiberfox,
                        return_code, (out, err)
                    )
                # self._convert_nrrd_to_nifti(simulation_output_folder, remove_nrrd)
                logger.debug("Simulation ended with code {}".format(return_code))
            async_loop.close()

    def _execute_parallel(self, method, args):
        p = Process(target=method, args=args)
        p.start()
        p.join()

    def _rename_and_copy_compartments_standalone(self, simulation_infos, geometry_output_folder, simulation_output_folder):
        merged_maps = False

        copyfile(
            path.join(geometry_output_folder, self._geometry_base_naming + "0.nrrd"),
            path.join(
                simulation_output_folder,
                "{}_simulation.ffp_VOLUME{}.nrrd".format(self._base_naming, simulation_infos["compartment_ids"][0])
            )
        )

        if len(simulation_infos["compartment_ids"]) > 1:
            if exists(path.join(geometry_output_folder, self._geometry_base_naming + "_mergedMaps.nrrd")):
                merged_maps = True
                copyfile(
                    path.join(geometry_output_folder, self._geometry_base_naming + "_mergedMaps.nrrd"),
                    path.join(
                        simulation_output_folder,
                        "{}_simulation.ffp_VOLUME{}.nrrd".format(self._base_naming, simulation_infos["compartment_ids"][1])
                    )
                )
            elif exists(path.join(geometry_output_folder, self._geometry_base_naming + "{}.nrrd".format(simulation_infos["compartment_ids"][1]))):
                copyfile(
                    path.join(geometry_output_folder, self._geometry_base_naming + "{}.nrrd".format(simulation_infos["compartment_ids"][1])),
                    path.join(
                        simulation_output_folder,
                        "{}_simulation.ffp_VOLUME{}.nrrd".format(self._base_naming, simulation_infos["compartment_ids"][1])
                    )
                )
            elif not simulation_infos["compartment_ids"][1] == "2":
                self._generate_background_map(geometry_output_folder, simulation_output_folder, simulation_infos["compartment_ids"])

        if len(simulation_infos["compartment_ids"]) > 2:
            self._generate_background_map(geometry_output_folder, simulation_output_folder, simulation_infos["compartment_ids"], merged_maps)

    def _rename_and_copy_compartments(self, geometry_output_folder, simulation_output_folder):
        copyfile(
            path.join(geometry_output_folder, self._geometry_base_naming + "0.nrrd"),
            path.join(
                simulation_output_folder,
                "{}_simulation.ffp_VOLUME{}.nrrd".format(self._base_naming, self._compartment_ids[0])
            )
        )

        if self._number_of_maps > 1:
            if exists(path.join(geometry_output_folder, self._geometry_base_naming + "_mergedMaps.nrrd")):
                copyfile(
                    path.join(geometry_output_folder, self._geometry_base_naming + "_mergedMaps.nrrd"),
                    path.join(
                        simulation_output_folder,
                        "{}_simulation.ffp_VOLUME{}.nrrd".format(self._base_naming, self._compartment_ids[1])
                    )
                )
            else:
                copyfile(
                    path.join(geometry_output_folder, self._geometry_base_naming + "{}.nrrd".format(self._compartment_ids[1])),
                    path.join(
                        simulation_output_folder,
                        "{}_simulation.ffp_VOLUME{}.nrrd".format(self._base_naming, self._compartment_ids[1])
                    )
                )

        if len(self._compartment_ids) > 2:
            self._generate_background_map(geometry_output_folder, simulation_output_folder, self._compartment_ids)

    def _generate_background_map(self, geometry_output_folder, simulation_output_folder, compartment_ids, merged_maps=False):
        maps = [
            nrrd.read(
                path.join(geometry_output_folder, "{}{}.nrrd".format(self._geometry_base_naming, 0))
            )[0]
        ]

        if merged_maps:
            maps.append(nrrd.read(
                path.join(geometry_output_folder, "{}{}.nrrd".format(self._geometry_base_naming, "_mergedMaps"))
            )[0])

        header = nrrd.read_header(path.join(geometry_output_folder, "{}{}.nrrd".format(self._geometry_base_naming, 0)))
        extra_map = ones_like(maps[0]) - sum(maps, axis=0)
        extra_map[extra_map < 0] = 0

        nrrd.write(
            path.join(
                simulation_output_folder,
                "{}_simulation.ffp_VOLUME{}.nrrd".format(self._base_naming, compartment_ids[-1])
            ),
            extra_map,
            header
        )

    async def _launch_command(self, command, log_file, log_tag):
        process = await create_subprocess_shell(command, stdout=PIPE, stderr=PIPE)
        while process.returncode is None:
            out, err = await process.communicate()
            logger.debug(
                "[ERROR OUTPUT FROM SIMULATION RUNNER]{} - {}".format(
                    log_tag, err.decode("utf-8")
                ))
            logger.debug(
                "[STANDARD OUTPUT FROM SIMULATION RUNNER]{} - {}".format(
                    log_tag, out.decode("utf-8")
                ))
            log_file.write("{} - {}".format(log_tag, out.decode("utf-8")))
            log_file.write("{} - {}".format(log_tag, err.decode("utf-8")))
            log_file.flush()
            await sleep(5)

        out, err = await process.communicate()
        err_str, out_str = err.decode("utf-8"), out.decode("utf-8")
        logger.debug("[ERROR OUTPUT FROM SIMULATION RUNNER]{} - {}".format(log_tag, err_str))
        logger.debug("[STANDARD OUTPUT FROM SIMULATION RUNNER]{} - {}".format(log_tag, out_str))
        log_file.write("{} - {}".format(log_tag, out_str))
        log_file.write("{} - {}".format(log_tag, err_str))
        log_file.write("Process ended with return code {}\n".format(process.returncode))
        log_file.flush()

        return process.returncode, out_str, err_str
