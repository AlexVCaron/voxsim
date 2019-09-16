from asyncio import sleep, create_subprocess_shell, get_event_loop
from os import path, makedirs
from shutil import copyfile
from subprocess import Popen, PIPE
from config import *
import nrrd
from numpy import sum, ones_like
from shlex import split


class SimulationRunner:

    def __init__(self, base_naming, geometry_infos, simulation_infos):
        self._geometry_path = geometry_infos["file_path"]
        self._geometry_base_file = geometry_infos["base_file"]
        self._geometry_resolution = geometry_infos["resolution"]
        self._geometry_spacing = geometry_infos["spacing"]
        self._number_of_maps = geometry_infos["number_of_maps"]
        self._base_naming = base_naming
        self._simulation_path = simulation_infos["file_path"]
        self._simulation_parameters = simulation_infos["param_file"]
        self._compartment_ids = simulation_infos["compartment_ids"]

    def run(self, output_folder, test_mode=False):
        geometry_output_folder = path.join(output_folder, "geometry_outputs")
        simulation_output_folder = path.join(output_folder, "simulation_outputs")

        if not path.exists(geometry_output_folder):
            makedirs(geometry_output_folder)

        if not path.exists(simulation_output_folder):
            makedirs(simulation_output_folder)

        singularity = path.join(singularity_path, singularity_name)
        geometry_command = "singularity run -B {} --app launch_voxsim {} -f {} -r {} -s {} -o {} --comp-map {} --quiet".format(
            ",".join([self._geometry_path, geometry_output_folder]),
            singularity,
            path.join(self._geometry_path, self._geometry_base_file),
            ",".join([str(r) for r in self._geometry_resolution]),
            ",".join([str(s) for s in self._geometry_spacing]),
            path.join(geometry_output_folder, self._base_naming),
            "--no-process" if test_mode else "--quiet"
        )
        simulation_command = "singularity run -B {} --app launch_mitk {} -p {} -i {} -o {} {}".format(
            ",".join([self._simulation_path, simulation_output_folder]),
            singularity,
            path.join(simulation_output_folder, self._simulation_parameters),
            path.join(geometry_output_folder, self._base_naming) + "_merged_bundles.fib",
            path.join(simulation_output_folder, self._base_naming),
            "-v" if test_mode else ""
        )

        copyfile(
            path.join(self._simulation_path, self._simulation_parameters),
            path.join(simulation_output_folder, self._simulation_parameters)
        )

        async_loop = get_event_loop()

        with open(path.join(output_folder, "{}.log".format(self._base_naming)), "w+") as log_file:
            async_loop.run_until_complete(self._launch_command(geometry_command, log_file, "[RUNNING VOXSIM]"))
            self._rename_and_copy_compartments(geometry_output_folder, simulation_output_folder)
            async_loop.run_until_complete(self._launch_command(simulation_command, log_file, "[RUNNING FIBERFOX]"))
            async_loop.close()

    def _rename_and_copy_compartments(self, geometry_output_folder, simulation_output_folder):
        for i in range(self._number_of_maps):
            copyfile(
                path.join(geometry_output_folder, self._base_naming + "{}.nrrd".format(i)),
                path.join(
                    simulation_output_folder,
                    "{}_simulation.ffp_VOLUME{}.nrrd".format(self._base_naming, self._compartment_ids[i])
                )
            )

        if len(self._compartment_ids) > self._number_of_maps:
            self._generate_background_map(geometry_output_folder, simulation_output_folder)

    def _generate_background_map(self, geometry_output_folder, simulation_output_folder):
        maps = [
            nrrd.read(
                path.join(geometry_output_folder, "{}{}.nrrd".format(self._base_naming, i))
            )[0] for i in range(self._number_of_maps)
        ]

        header = nrrd.read_header(path.join(geometry_output_folder, "{}{}.nrrd".format(self._base_naming, 0)))
        extra_map = ones_like(maps[0]) - sum(maps, axis=0)

        nrrd.write(
            path.join(
                simulation_output_folder,
                "{}_simulation.ffp_VOLUME{}.nrrd".format(self._base_naming, self._compartment_ids[-1])
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
