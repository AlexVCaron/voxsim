from asyncio import get_event_loop, new_event_loop, set_event_loop
import logging
import pathlib
from multiprocessing import Process
from os import makedirs, path
from os.path import basename, exists
from shutil import copyfile
from subprocess import PIPE, Popen

import nibabel as nib
from numpy import ones_like, sum
import nrrd

from .config import SingularityConfig
from ..exceptions import SimulationRunnerException
from ..utils.logging import RTLogging

_logger = logging.getLogger(__name__)


class SimulationRunner:

    def __init__(
            self,
            base_naming,
            geometry_infos,
            simulation_infos=None,
            singularity_conf=SingularityConfig(),
            output_nifti=False,
    ):
        self._geometry_path: pathlib.Path = geometry_infos["file_path"]
        self._geometry_base_file: str = geometry_infos["base_file"]
        self._geometry_resolution = geometry_infos["resolution"]
        self._geometry_spacing = geometry_infos["spacing"]
        self._base_naming: str = base_naming
        self._geometry_base_naming: str = base_naming
        if simulation_infos:
            self._number_of_maps = len(simulation_infos["compartment_ids"])
            self._simulation_path: pathlib.Path = simulation_infos["file_path"]
            self._simulation_parameters: str = simulation_infos["param_file"]
            self._compartment_ids = simulation_infos["compartment_ids"]

        singularity_conf = (
            singularity_conf if singularity_conf else SingularityConfig()
        )
        self._singularity: pathlib.Path = singularity_conf.singularity
        self._singularity_exec: str = singularity_conf.singularity_exec

        self._run_simulation = True if simulation_infos else False
        self._extension = "nii.gz" if output_nifti else "nrrd"
        self._fib_extension_arg = " --nii" if output_nifti else ""

        self._load_image = self._load_nifti if output_nifti else self._load_nrrd
        self._save_image = self._save_nifti if output_nifti else self._save_nrrd
        self._event_loop = new_event_loop()

    def change_base_naming(self, name: str):
        self._base_naming = name

    def set_geometry_base_naming(self, name: str):
        self._geometry_base_naming = name

    def run_simulation_dwimage(
            self, output_folder: pathlib.Path, image_file: pathlib.Path, simulation_infos, test_mode=False
    ):
        self._start_loop_if_closed()

        simulation_output_folder: pathlib.Path = output_folder / "simulation_outputs"
        simulation_output_folder.mkdir(parents=True, exist_ok=True)

        simulation_command = (
            "{} run -B {} --app launch_mitk {} -p {} -i {} -o {} {}".format(
                self._singularity_exec,
                ",".join(
                    [str(simulation_infos["file_path"]), str(simulation_output_folder)]
                ),
                self._singularity,
                simulation_output_folder / "{}_simulation.ffp".format(self._base_naming),
                image_file,
                simulation_output_folder / "{}.{}".format(self._base_naming, self._extension),
                "-v" if test_mode else "",
            )
        )

        copyfile(
            simulation_infos["file_path"] / simulation_infos["param_file"],
            simulation_output_folder / "{}_simulation.ffp".format(self._base_naming),
        )

        set_event_loop(self._event_loop)
        async_loop = get_event_loop()
        log_file: pathlib.Path = output_folder / "{}.log".format(self._base_naming)

        _logger.info("Simulating DWI signal")
        return_code, log = async_loop.run_until_complete(
            self._launch_command(
                simulation_command, log_file, "[RUNNING FIBERFOX]"
            )
        )
        if not return_code == 0:
            raise SimulationRunnerException(
                "Simulation ended in error",
                SimulationRunnerException.ExceptionType.Fiberfox,
                return_code,
                (log,),
            )

        _logger.debug(
            "Simulation {} ended with code {}".format(
                self._base_naming, return_code
            )
        )
        async_loop.close()

    def run_simulation_standalone(
            self,
            output_folder: pathlib.Path,
            geometry_folder: pathlib.Path,
            simulation_infos,
            base_naming=None,
            test_mode=False,
    ):
        if not base_naming:
            base_naming = self._base_naming

        self._start_loop_if_closed()

        simulation_output_folder = output_folder / "simulation_outputs"
        geometry_output_folder = geometry_folder / "geometry_outputs"
        simulation_output_folder.mkdir(parents=True, exist_ok=True)

        simulation_command = (
            "{} run -B {} --app launch_mitk {} -p {} -i {} -o {} {}".format(
                self._singularity_exec,
                ",".join(
                    [
                        str(geometry_folder),
                        str(simulation_infos["file_path"]),
                        str(simulation_output_folder),
                    ]
                ),
                self._singularity,
                simulation_output_folder / "{}_simulation.ffp".format(base_naming),
                geometry_output_folder / (self._geometry_base_naming + "_merged_bundles.fib"),
                simulation_output_folder / "{}.{}".format(base_naming, self._extension),
                "-v" if test_mode else "",
            )
        )

        copyfile(
            simulation_infos["file_path"] / simulation_infos["param_file"],
            simulation_output_folder / "{}_simulation.ffp".format(base_naming),
        )

        set_event_loop(self._event_loop)
        async_loop = get_event_loop()
        log_file: pathlib.Path = output_folder / "{}.log".format(base_naming)

        self._rename_and_copy_compartments_standalone(
            simulation_infos,
            geometry_output_folder,
            simulation_output_folder,
            base_naming,
        )

        _logger.info("Simulating DWI signal")
        return_code, log = async_loop.run_until_complete(
            self._launch_command(
                simulation_command, log_file, "[RUNNING FIBERFOX]"
            )
        )
        if not return_code == 0:
            raise SimulationRunnerException(
                "Simulation ended in error",
                SimulationRunnerException.ExceptionType.Fiberfox,
                return_code,
                (log,),
            )

        _logger.debug(
            "Simulation {} ended with code {}".format(
                self._base_naming, return_code
            )
        )
        async_loop.close()

    def run(
            self, output_folder: pathlib.Path, test_mode=False, relative_fiber_compartment=True
    ):

        geometry_output_folder: pathlib.Path = output_folder / "geometry_outputs"
        geometry_output_folder.mkdir(parents=True, exist_ok=True)

        if self._run_simulation:
            simulation_output_folder: pathlib.Path = output_folder / "simulation_outputs"
            simulation_output_folder.mkdir(parents=True, exist_ok=True)

        geometry_command = (
            "singularity run -B {} --app launch_voxsim {} -f {} -r {} "
            "-s {} -o {} --comp-map {} --quiet{}".format(
                ",".join([str(self._geometry_path), str(geometry_output_folder)]),
                self._singularity,
                self._geometry_path / self._geometry_base_file,
                ",".join([str(r) for r in self._geometry_resolution]),
                ",".join([str(s) for s in self._geometry_spacing]),
                geometry_output_folder / self._geometry_base_naming,
                "rel" if relative_fiber_compartment else "abs",
                self._fib_extension_arg,
            )
        )

        if self._run_simulation:
            simulation_command = (
                "singularity run -B {} --app launch_mitk {} "
                "-p {} -i {} -o {} {}".format(
                    ",".join(
                        [
                            str(self._simulation_path),
                            str(geometry_output_folder),
                            str(simulation_output_folder),
                        ]
                    ),
                    self._singularity,
                    simulation_output_folder / "{}_simulation.ffp".format(self._base_naming),
                    geometry_output_folder / (self._geometry_base_naming + "_merged_bundles.fib"),
                    simulation_output_folder / "{}.{}".format(self._base_naming, self._extension),
                    "-v" if test_mode else "",
                )
            )

            copyfile(
                self._simulation_path / self._simulation_parameters,
                simulation_output_folder / "{}_simulation.ffp".format(self._base_naming),
            )

        set_event_loop(self._event_loop)
        async_loop = get_event_loop()
        log_file = output_folder / "{}.log".format(self._base_naming)

        _logger.info("Generating simulation geometry")
        async_loop.run_until_complete(
            self._launch_command(geometry_command, log_file, "[RUNNING VOXSIM]")
        )
        if self._run_simulation:
            self._rename_and_copy_compartments(
                geometry_output_folder, simulation_output_folder
            )
            _logger.info("Simulating DWI signal")
            if self._run_simulation:
                return_code, log = async_loop.run_until_complete(
                    self._launch_command(
                        simulation_command, log_file, "[RUNNING FIBERFOX]"
                    )
                )
                if not return_code == 0:
                    raise SimulationRunnerException(
                        "Simulation ended in error",
                        SimulationRunnerException.ExceptionType.Fiberfox,
                        return_code,
                        (log,),
                    )

            _logger.debug("Simulation ended with code {}".format(return_code))
        async_loop.close()

    def _execute_parallel(self, method, args):
        p = Process(target=method, args=args)
        p.start()
        p.join()

    def _rename_and_copy_compartments_standalone(
            self,
            simulation_infos,
            geometry_output_folder: pathlib.Path,
            simulation_output_folder: pathlib.Path,
            base_naming,
    ):
        copyfile(
            path.join(
                geometry_output_folder,
                self._geometry_base_naming
                + "_mergedBundlesMaps.{}".format(self._extension),
            ),
            path.join(
                simulation_output_folder,
                "{}_simulation.ffp_VOLUME{}.{}".format(
                    base_naming,
                    simulation_infos["compartment_ids"][0],
                    self._extension,
                ),
            ),
        )

        if len(simulation_infos["compartment_ids"]) > 1:
            merged_maps = exists(
                path.join(
                    geometry_output_folder,
                    self._geometry_base_naming
                    + "_mergedEllipsesMaps.{}".format(self._extension),
                )
            )
            base_map = (not merged_maps) and exists(
                path.join(
                    geometry_output_folder,
                    self._geometry_base_naming
                    + "_ellipsoid{}_cmap.{}".format(0, self._extension),
                )
            )
            if merged_maps:
                copyfile(
                    path.join(
                        geometry_output_folder,
                        self._geometry_base_naming
                        + "_mergedEllipsesMaps.{}".format(self._extension),
                    ),
                    path.join(
                        simulation_output_folder,
                        "{}_simulation.ffp_VOLUME{}.{}".format(
                            base_naming,
                            simulation_infos["compartment_ids"][1],
                            self._extension,
                        ),
                    ),
                )
            elif base_map:
                copyfile(
                    path.join(
                        geometry_output_folder,
                        self._geometry_base_naming
                        + "_ellipsoid1_cmap.{}".format(self._extension),
                    ),
                    path.join(
                        simulation_output_folder,
                        "{}_simulation.ffp_VOLUME{}.{}".format(
                            base_naming,
                            simulation_infos["compartment_ids"][1],
                            self._extension,
                        ),
                    ),
                )
            else:
                self._generate_background_map(
                    geometry_output_folder,
                    simulation_output_folder,
                    simulation_infos["compartment_ids"][1],
                    merged_maps,
                    base_map,
                    base_naming,
                )

            if len(simulation_infos["compartment_ids"]) > 2 and (
                    merged_maps or base_map
            ):
                self._generate_background_map(
                    geometry_output_folder,
                    simulation_output_folder,
                    simulation_infos["compartment_ids"][2],
                    merged_maps,
                    base_map,
                    base_naming,
                )
            else:
                raise SimulationRunnerException(
                    "3 compartments were supplied, but there is only a map "
                    "for fibers found. At least one other compartment "
                    "primitive must be generated by voxsim",
                    SimulationRunnerException.ExceptionType.Parameters,
                )

    def _rename_and_copy_compartments(
            self, geometry_output_folder, simulation_output_folder
    ):
        copyfile(
            path.join(
                geometry_output_folder,
                self._geometry_base_naming
                + "_mergedBundlesMaps.{}".format(self._extension),
            ),
            path.join(
                simulation_output_folder,
                "{}_simulation.ffp_VOLUME{}.{}".format(
                    self._base_naming, self._compartment_ids[0], self._extension
                ),
            ),
        )

        if self._number_of_maps > 1:
            merged_maps = exists(
                path.join(
                    geometry_output_folder,
                    self._geometry_base_naming
                    + "_mergedEllipsesMaps.{}".format(self._extension),
                )
            )
            base_map = (not merged_maps) and exists(
                path.join(
                    geometry_output_folder,
                    self._geometry_base_naming
                    + "_ellipsoid1_cmap.{}".format(self._extension),
                )
            )
            if merged_maps:
                copyfile(
                    path.join(
                        geometry_output_folder,
                        self._geometry_base_naming
                        + "_mergedEllipsesMaps.{}".format(self._extension),
                    ),
                    path.join(
                        simulation_output_folder,
                        "{}_simulation.ffp_VOLUME{}.{}".format(
                            self._base_naming,
                            self._compartment_ids[1],
                            self._extension,
                        ),
                    ),
                )
            elif base_map:
                copyfile(
                    path.join(
                        geometry_output_folder,
                        self._geometry_base_naming
                        + "_ellipsoid0_cmap.{}".format(self._extension),
                    ),
                    path.join(
                        simulation_output_folder,
                        "{}_simulation.ffp_VOLUME{}.{}".format(
                            self._base_naming,
                            self._compartment_ids[1],
                            self._extension,
                        ),
                    ),
                )
            else:
                self._generate_background_map(
                    geometry_output_folder,
                    simulation_output_folder,
                    self._compartment_ids[1],
                    merged_maps,
                    base_map,
                )

            if self._number_of_maps > 2 and (merged_maps or base_map):
                self._generate_background_map(
                    geometry_output_folder,
                    simulation_output_folder,
                    self._compartment_ids[2],
                    merged_maps,
                    base_map,
                )
            else:
                raise SimulationRunnerException(
                    "3 compartments were supplied, but there is only a map "
                    "for fibers found. At least one other compartment "
                    "primitive must be generated by voxsim",
                    SimulationRunnerException.ExceptionType.Parameters,
                )

    def _load_nifti(self, name):
        img = nib.load("{}.nii.gz".format(name))
        return img.get_fdata(), (img.affine, img.header)

    def _load_nrrd(self, name):
        return nrrd.read("{}.nrrd".format(name))

    def _save_nifti(self, data, header_pack, name):
        nib.save(nib.Nifti1Image(data, *header_pack), "{}.nii.gz".format(name))

    def _save_nrrd(self, data, header, name):
        nrrd.write("{}.nrrd".format(name), data, header)

    def _generate_background_map(
            self,
            geometry_output_folder,
            simulation_output_folder,
            compartment_id,
            merged_maps=False,
            base_map=False,
            base_naming=None,
    ):
        if not base_naming:
            base_naming = self._base_naming

        img, header = self._load_image(
            geometry_output_folder / "{}_mergedBundlesMaps".format(self._geometry_base_naming)
        )
        maps = [img]

        if merged_maps:
            maps.append(
                self._load_image(
                    geometry_output_folder / "{}{}".format(self._geometry_base_naming, "_mergedEllipsesMaps")
                )[0]
            )
        elif base_map:
            maps.append(
                self._load_image(
                    geometry_output_folder / "{}{}".format(self._geometry_base_naming, "_ellipsoid1_cmap")
                )[0]
            )

        extra_map = ones_like(maps[0]) - sum(maps, axis=0)
        extra_map[extra_map < 0] = 0

        self._save_image(
            extra_map,
            header,
            simulation_output_folder / "{}_simulation.ffp_VOLUME{}".format(base_naming, compartment_id),
        )

    def _start_loop_if_closed(self):
        if self._event_loop.is_closed():
            self._event_loop = new_event_loop()

    async def _launch_command(self, command, log_file: pathlib.Path, log_tag):
        process = Popen(command.split(" "), stdout=PIPE, stderr=PIPE)

        _logger = RTLogging(process, log_file, log_tag)
        _logger.start()
        _logger.join()

        return process.returncode, log_file
