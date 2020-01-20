from asyncio import sleep, create_subprocess_shell, get_event_loop, new_event_loop, set_event_loop
from os import path, makedirs
from shutil import copyfile
from subprocess import PIPE
from numpy import sum, ones_like
import nrrd

from config import *


class SimulationRunner:

    def __init__(self, base_naming, geometry_infos, simulation_infos=None):
        self._geometry_path = geometry_infos["file_path"]
        self._geometry_base_file = geometry_infos["base_file"]
        self._geometry_resolution = geometry_infos["resolution"]
        self._geometry_spacing = geometry_infos["spacing"]
        self._base_naming = base_naming
        if simulation_infos:
            self._number_of_maps = len(simulation_infos["compartment_ids"])
            self._simulation_path = simulation_infos["file_path"]
            self._simulation_parameters = simulation_infos["param_file"]
            self._compartment_ids = simulation_infos["compartment_ids"]

        self._run_simulation = True if simulation_infos else False
        self._event_loop = new_event_loop()

    def run_simulation_standalone(self, output_folder, geometry_folder, simulation_infos, test_mode=False):
        simulation_output_folder = path.join(output_folder, "simulation_outputs")
        geometry_output_folder = path.join(geometry_folder, "geometry_outputs")
        singularity = path.join(singularity_path, singularity_name)

        if not path.exists(simulation_output_folder):
            makedirs(simulation_output_folder)

        simulation_command = "singularity run -B {} --app launch_mitk {} -p {} -i {} -o {} {}".format(
            ",".join([simulation_infos["file_path"], simulation_output_folder]),
            singularity,
            path.join(simulation_output_folder, "{}_simulation.ffp".format(self._base_naming)),
            path.join(geometry_output_folder, self._base_naming) + "_merged_bundles.fib",
            path.join(simulation_output_folder, self._base_naming),
            "-v" if test_mode else ""
        )

        copyfile(
            path.join(simulation_infos["file_path"], simulation_infos["param_file"]),
            path.join(simulation_output_folder, "{}_simulation.ffp".format(self._base_naming))
        )

        set_event_loop(self._event_loop)
        async_loop = get_event_loop()

        with open(path.join(output_folder, "{}.log".format(self._base_naming)), "w+") as log_file:
            print("Generating simulation geometry")
            self._rename_and_copy_compartments_standalone(simulation_infos, geometry_output_folder, simulation_output_folder)
            print("Simulating DWI signal")
            async_loop.run_until_complete(self._launch_command(simulation_command, log_file, "[RUNNING FIBERFOX]"))
            async_loop.close()

    def run(self, output_folder, test_mode=False, relative_fiber_compartment=True):
        geometry_output_folder = path.join(output_folder, "geometry_outputs")

        if not path.exists(geometry_output_folder):
            makedirs(geometry_output_folder)

        if self._run_simulation:
            simulation_output_folder = path.join(output_folder, "simulation_outputs")

            if not path.exists(simulation_output_folder):
                makedirs(simulation_output_folder)

        singularity = path.join(singularity_path, singularity_name)
        geometry_command = "singularity run -B {} --app launch_voxsim {} -f {} -r {} -s {} -o {} --comp-map {} {} --quiet".format(
            ",".join([self._geometry_path, geometry_output_folder]),
            singularity,
            path.join(self._geometry_path, self._geometry_base_file),
            ",".join([str(r) for r in self._geometry_resolution]),
            ",".join([str(s) for s in self._geometry_spacing]),
            path.join(geometry_output_folder, self._base_naming),
            "rel" if relative_fiber_compartment else "abs",
            "--no-process" if test_mode else "--quiet"
        )

        if self._run_simulation:
            simulation_command = "singularity run -B {} --app launch_mitk {} -p {} -i {} -o {} {}".format(
                ",".join([self._simulation_path, simulation_output_folder]),
                singularity,
                path.join(simulation_output_folder, "{}_simulation.ffp".format(self._base_naming)),
                path.join(geometry_output_folder, self._base_naming) + "_merged_bundles.fib",
                path.join(simulation_output_folder, self._base_naming),
                "-v" if test_mode else ""
            )

            copyfile(
                path.join(self._simulation_path, self._simulation_parameters),
                path.join(simulation_output_folder, "{}_simulation.ffp".format(self._base_naming))
            )

        set_event_loop(self._event_loop)
        async_loop = get_event_loop()

        with open(path.join(output_folder, "{}.log".format(self._base_naming)), "w+") as log_file:
            print("Generating simulation geometry")
            async_loop.run_until_complete(self._launch_command(geometry_command, log_file, "[RUNNING VOXSIM]"))
            if self._run_simulation:
                self._rename_and_copy_compartments(geometry_output_folder, simulation_output_folder)
                print("Simulating DWI signal")
                async_loop.run_until_complete(self._launch_command(simulation_command, log_file, "[RUNNING FIBERFOX]"))
            async_loop.close()

    def _rename_and_copy_compartments_standalone(self, simulation_infos, geometry_output_folder, simulation_output_folder):
        copyfile(
            path.join(geometry_output_folder, self._base_naming + "0.nrrd"),
            path.join(
                simulation_output_folder,
                "{}_simulation.ffp_VOLUME{}.nrrd".format(self._base_naming, simulation_infos["compartment_ids"][0])
            )
        )

        if len(simulation_infos["compartment_ids"]) > 1:
            copyfile(
                path.join(geometry_output_folder, self._base_naming + "_mergedMaps.nrrd"),
                path.join(
                    simulation_output_folder,
                    "{}_simulation.ffp_VOLUME{}.nrrd".format(self._base_naming, simulation_infos["compartment_ids"][1])
                )
            )

        if len(simulation_infos["compartment_ids"]) > 2:
            self._generate_background_map(geometry_output_folder, simulation_output_folder, simulation_infos["compartment_ids"])

    def _rename_and_copy_compartments(self, geometry_output_folder, simulation_output_folder):
        copyfile(
            path.join(geometry_output_folder, self._base_naming + "0.nrrd"),
            path.join(
                simulation_output_folder,
                "{}_simulation.ffp_VOLUME{}.nrrd".format(self._base_naming, self._compartment_ids[0])
            )
        )

        if self._number_of_maps > 1:
            copyfile(
                path.join(geometry_output_folder, self._base_naming + "_mergedMaps.nrrd"),
                path.join(
                    simulation_output_folder,
                    "{}_simulation.ffp_VOLUME{}.nrrd".format(self._base_naming, self._compartment_ids[1])
                )
            )

        if len(self._compartment_ids) > 2:
            self._generate_background_map(geometry_output_folder, simulation_output_folder, self._compartment_ids)

    def _generate_background_map(self, geometry_output_folder, simulation_output_folder, compartment_ids):
        maps = [
            nrrd.read(
                path.join(geometry_output_folder, "{}{}.nrrd".format(self._base_naming, 0))
            )[0],
            nrrd.read(
                path.join(geometry_output_folder, "{}{}.nrrd".format(self._base_naming, "_mergedMaps"))
            )[0]
        ]

        header = nrrd.read_header(path.join(geometry_output_folder, "{}{}.nrrd".format(self._base_naming, 0)))
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
            log_file.write("{} - {}".format(log_tag, out.decode("utf-8")))
            log_file.write("{} - {}".format(log_tag, err.decode("utf-8")))
            log_file.flush()
            await sleep(5)

        out, err = await process.communicate()
        log_file.write("{} - {}".format(log_tag, out.decode("utf-8")))
        log_file.write("{} - {}".format(log_tag, err.decode("utf-8")))
        log_file.write("Process ended with return code {}\n".format(process.returncode))
        log_file.flush()
