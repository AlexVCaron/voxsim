import logging
import glob
from asyncio import get_event_loop, new_event_loop, set_event_loop
from multiprocessing import Process
from os import path, makedirs, remove
from os.path import exists, join, basename
from shutil import copyfile
from subprocess import PIPE, Popen
from numpy import sum, ones_like, moveaxis, hstack, vstack
import nrrd
import nibabel as nib

from config import get_config
from simulator.exceptions import SimulationRunnerException
from simulator.utils.logging import RTLogging

logger = logging.getLogger(basename(__file__).split(".")[0])


class SimulationRunner:
    def __init__(self, base_naming, geometry_infos, simulation_infos=None, singularity_conf=get_config(), output_nifti=False):
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
        self._extension = "nii.gz" if output_nifti else "nrrd"
        self._fib_extension_arg = " --nii" if output_nifti else ""

    def set_geometry_base_naming(self, name):
        self._geometry_base_naming = name

    def run_simulation_dwimage(self, output_folder, image_file, simulation_infos, test_mode=False):
        self._start_loop_if_closed()
        simulation_output_folder = path.join(output_folder, "simulation_outputs")
        if not path.exists(simulation_output_folder):
            makedirs(simulation_output_folder, exist_ok=True)

        simulation_command = "singularity run -B {} --app launch_mitk {} -p {} -i {} -o {} {}".format(
            ",".join([simulation_infos["file_path"], simulation_output_folder]),
            self._singularity,
            path.join(simulation_output_folder, "{}_simulation.ffp".format(self._base_naming)),
            image_file,
            path.join(simulation_output_folder, "{}.{}".format(self._base_naming, self._extension)),
            "-v" if test_mode else ""
        )

        copyfile(
            path.join(simulation_infos["file_path"], simulation_infos["param_file"]),
            path.join(simulation_output_folder, "{}_simulation.ffp".format(self._base_naming))
        )

        set_event_loop(self._event_loop)
        async_loop = get_event_loop()
        log_file = path.join(output_folder, "{}.log".format(self._base_naming))

        logger.info("Simulating DWI signal")
        return_code, log = async_loop.run_until_complete(self._launch_command(simulation_command, log_file, "[RUNNING FIBERFOX]"))
        if not return_code == 0:
            raise SimulationRunnerException(
                "Simulation ended in error",
                SimulationRunnerException.ExceptionType.Fiberfox,
                return_code, (log,)
            )

        logger.debug("Simulation {} ended with code {}".format(self._base_naming, return_code))
        async_loop.close()

    def run_simulation_standalone(self, output_folder, geometry_folder, simulation_infos, test_mode=False):
        self._start_loop_if_closed()
        simulation_output_folder = path.join(output_folder, "simulation_outputs")
        geometry_output_folder = path.join(geometry_folder, "geometry_outputs")

        if not path.exists(simulation_output_folder):
            makedirs(simulation_output_folder, exist_ok=True)

        simulation_command = "singularity run -B {} --app launch_mitk {} -p {} -i {} -o {} {}".format(
            ",".join([geometry_folder, simulation_infos["file_path"], simulation_output_folder]),
            self._singularity,
            path.join(simulation_output_folder, "{}_simulation.ffp".format(self._base_naming)),
            path.join(geometry_output_folder, self._geometry_base_naming) + "_merged_bundles.fib",
            path.join(simulation_output_folder, "{}.{}".format(self._base_naming, self._extension)),
            "-v" if test_mode else ""
        )

        copyfile(
            path.join(simulation_infos["file_path"], simulation_infos["param_file"]),
            path.join(simulation_output_folder, "{}_simulation.ffp".format(self._base_naming))
        )

        set_event_loop(self._event_loop)
        async_loop = get_event_loop()
        log_file = path.join(output_folder, "{}.log".format(self._base_naming))

        self._rename_and_copy_compartments_standalone(simulation_infos, geometry_output_folder, simulation_output_folder)

        logger.info("Simulating DWI signal")
        return_code, log = async_loop.run_until_complete(self._launch_command(simulation_command, log_file, "[RUNNING FIBERFOX]"))
        if not return_code == 0:
            raise SimulationRunnerException(
                "Simulation ended in error",
                SimulationRunnerException.ExceptionType.Fiberfox,
                return_code, (log,)
            )

        logger.debug("Simulation {} ended with code {}".format(self._base_naming, return_code))
        async_loop.close()

    def run(self, output_folder, test_mode=False, relative_fiber_compartment=True):
        self._start_loop_if_closed()
        geometry_output_folder = path.join(output_folder, "geometry_outputs")

        if not path.exists(geometry_output_folder):
            makedirs(geometry_output_folder, exist_ok=True)

        if self._run_simulation:
            simulation_output_folder = path.join(output_folder, "simulation_outputs")

            if not path.exists(simulation_output_folder):
                makedirs(simulation_output_folder, exist_ok=True)

        geometry_command = "singularity run -B {} --app launch_voxsim {} -f {} -r {} -s {} -o {} --comp-map {} --quiet{}".format(
            ",".join([self._geometry_path, geometry_output_folder]),
            self._singularity,
            path.join(self._geometry_path, self._geometry_base_file),
            ",".join([str(r) for r in self._geometry_resolution]),
            ",".join([str(s) for s in self._geometry_spacing]),
            path.join(geometry_output_folder, self._geometry_base_naming),
            "rel" if relative_fiber_compartment else "abs",
            self._fib_extension_arg
        )
        print(geometry_command)
        if self._run_simulation:
            simulation_command = "singularity run -B {} --app launch_mitk {} -p {} -i {} -o {} {}".format(
                ",".join([self._simulation_path, geometry_output_folder, simulation_output_folder]),
                self._singularity,
                path.join(simulation_output_folder, "{}_simulation.ffp".format(self._base_naming)),
                path.join(geometry_output_folder, self._geometry_base_naming) + "_merged_bundles.fib",
                path.join(simulation_output_folder, "{}.{}".format(self._base_naming, self._extension)),
                "-v" if test_mode else ""
            )

            copyfile(
                path.join(self._simulation_path, self._simulation_parameters),
                path.join(simulation_output_folder, "{}_simulation.ffp".format(self._base_naming))
            )

        set_event_loop(self._event_loop)
        async_loop = get_event_loop()
        log_file = path.join(output_folder, "{}.log".format(self._base_naming))

        logger.info("Generating simulation geometry")
        async_loop.run_until_complete(self._launch_command(geometry_command, log_file, "[RUNNING VOXSIM]"))
        if self._run_simulation:
            self._rename_and_copy_compartments(geometry_output_folder, simulation_output_folder)
            logger.info("Simulating DWI signal")
            if self._run_simulation:
                return_code, log = async_loop.run_until_complete(self._launch_command(simulation_command, log_file, "[RUNNING FIBERFOX]"))
                if not return_code == 0:
                    raise SimulationRunnerException(
                        "Simulation ended in error",
                        SimulationRunnerException.ExceptionType.Fiberfox,
                        return_code, (log,)
                    )

            logger.debug("Simulation ended with code {}".format(return_code))
        async_loop.close()

    def _execute_parallel(self, method, args):
        p = Process(target=method, args=args)
        p.start()
        p.join()

    def _rename_and_copy_compartments_standalone(self, simulation_infos, geometry_output_folder, simulation_output_folder):
        copyfile(
            path.join(geometry_output_folder, self._geometry_base_naming + "_mergedBundlesMaps.{}".format(self._extension)),
            path.join(
                simulation_output_folder,
                "{}_simulation.ffp_VOLUME{}.{}".format(self._base_naming, simulation_infos["compartment_ids"][0], self._extension)
            )
        )

        if self._number_of_maps > 1:
            merged_maps = exists(path.join(geometry_output_folder, self._geometry_base_naming + "_mergedEllipsesMaps.{}".format(self._extension)))
            base_map = (not merged_maps) and exists(path.join(geometry_output_folder, self._geometry_base_naming + "_ellipsoid{}_cmap.{}".format(0, self._extension)))
            if merged_maps:
                copyfile(
                    path.join(geometry_output_folder, self._geometry_base_naming + "_mergedEllipsesMaps.{}".format(self._extension)),
                    path.join(
                        simulation_output_folder,
                        "{}_simulation.ffp_VOLUME{}.{}".format(self._base_naming, simulation_infos["compartment_ids"][1], self._extension)
                    )
                )
            elif base_map:
                copyfile(
                    path.join(geometry_output_folder, self._geometry_base_naming + "_ellipsoid1_cmap.{}".format(self._extension)),
                    path.join(
                        simulation_output_folder,
                        "{}_simulation.ffp_VOLUME{}.{}".format(self._base_naming, simulation_infos["compartment_ids"][1], self._extension)
                    )
                )
            else:
                self._generate_background_map(geometry_output_folder, simulation_output_folder, simulation_infos["compartment_ids"][1], merged_maps, base_map)

            if self._number_of_maps > 2 and (merged_maps or base_map):
                self._generate_background_map(geometry_output_folder, simulation_output_folder, simulation_infos["compartment_ids"][2], merged_maps, base_map)
            else:
                raise SimulationRunnerException("3 compartments were supplied, but there is only a map for fibers found. At least one other compartment primitive must be generated by voxsim", SimulationRunnerException.ExceptionType.Parameters)

    def _rename_and_copy_compartments(self, geometry_output_folder, simulation_output_folder):
        copyfile(
            path.join(geometry_output_folder, self._geometry_base_naming + "_mergedBundlesMaps.{}".format(self._extension)),
            path.join(
                simulation_output_folder,
                "{}_simulation.ffp_VOLUME{}.{}".format(self._base_naming, self._compartment_ids[0], self._extension)
            )
        )

        if self._number_of_maps > 1:
            merged_maps = exists(path.join(geometry_output_folder, self._geometry_base_naming + "_mergedEllipsesMaps.{}".format(self._extension)))
            base_map = (not merged_maps) and exists(path.join(geometry_output_folder, self._geometry_base_naming + "_ellipsoid1_cmap.{}".format(self._extension)))
            if merged_maps:
                copyfile(
                    path.join(geometry_output_folder, self._geometry_base_naming + "_mergedEllipsesMaps.{}".format(self._extension)),
                    path.join(
                        simulation_output_folder,
                        "{}_simulation.ffp_VOLUME{}.{}".format(self._base_naming, self._compartment_ids[1], self._extension)
                    )
                )
            elif base_map:
                copyfile(
                    path.join(geometry_output_folder, self._geometry_base_naming + "_ellipsoid0_cmap.{}".format(self._extension)),
                    path.join(
                        simulation_output_folder,
                        "{}_simulation.ffp_VOLUME{}.{}".format(self._base_naming, self._compartment_ids[1], self._extension)
                    )
                )
            else:
                self._generate_background_map(geometry_output_folder, simulation_output_folder, self._compartment_ids[1], merged_maps, base_map)

            if self._number_of_maps > 2 and (merged_maps or base_map):
                self._generate_background_map(geometry_output_folder, simulation_output_folder, self._compartment_ids[2], merged_maps, base_map)
            else:
                raise SimulationRunnerException("3 compartments were supplied, but there is only a map for fibers found. At least one other compartment primitive must be generated by voxsim", SimulationRunnerException.ExceptionType.Parameters)

    def _generate_background_map(self, geometry_output_folder, simulation_output_folder, compartment_id, merged_maps=False, base_map=False):
        if self._extension == "nrrd":
            maps = [
                nrrd.read(
                    path.join(geometry_output_folder, "{}_mergedBundlesMaps.nrrd".format(self._geometry_base_naming))
                )[0]
            ]
            header = (nrrd.read_header(path.join(geometry_output_folder, "{}_mergedBundlesMaps.nrrd".format(self._geometry_base_naming))),)
        else:
            img = nib.load(path.join(geometry_output_folder, "{}_mergedBundlesMaps.nii.gz".format(self._geometry_base_naming)))
            maps = [img.get_fdata()]
            header = (img.affine, img.header)

        if merged_maps:
            if self._extension == "nrrd":
                maps.append(nrrd.read(
                    path.join(geometry_output_folder, "{}{}.nrrd".format(self._geometry_base_naming, "_mergedEllipsesMaps"))
                )[0])

            else:
                img = nib.load(path.join(geometry_output_folder, "{}{}.nii.gz".format(self._geometry_base_naming, "_mergedEllipsesMaps")))
                maps.append(img.get_fdata())
        elif base_map:
            if self._extension == "nrrd":
                maps.append(nrrd.read(
                    path.join(geometry_output_folder, "{}{}.nrrd".format(self._geometry_base_naming, "_ellipsoid1_cmap"))
                )[0])

            else:
                img = nib.load(path.join(geometry_output_folder, "{}{}.nii.gz".format(self._geometry_base_naming, "_ellipsoid1_cmap")))
                maps.append(img.get_fdata())

        extra_map = ones_like(maps[0]) - sum(maps, axis=0)
        extra_map[extra_map < 0] = 0

        if self._extension == "nrrd":
            nrrd.write(
                path.join(
                    simulation_output_folder,
                    "{}_simulation.ffp_VOLUME{}.nrrd".format(self._base_naming, compartment_id)
                ),
                extra_map, *header
            )
        else:
            nib.save(
                nib.Nifti1Image(extra_map, *header),
                path.join(
                    simulation_output_folder,
                    "{}_simulation.ffp_VOLUME{}.nii.gz".format(self._base_naming, compartment_id)
                )
            )

    def _start_loop_if_closed(self):
        if self._event_loop.is_closed():
            self._event_loop = new_event_loop()

    async def _launch_command(self, command, log_file, log_tag):
        process = Popen(command.split(" "), stdout=PIPE, stderr=PIPE)

        logger = RTLogging(process, log_file, log_tag)
        logger.start()
        logger.join()

        return process.returncode, log_file
