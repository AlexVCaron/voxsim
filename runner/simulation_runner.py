from os import path, makedirs
from subprocess import Popen, PIPE
from config import *


class SimulationRunner:

    def __init__(self, base_naming, geometry_infos, simulation_infos):
        self._geometry_path = geometry_infos["file_path"]
        self._geometry_base_file = geometry_infos["base_file"]
        self._geometry_resolution = geometry_infos["resolution"]
        self._geometry_spacing = geometry_infos["spacing"]
        self._base_naming = base_naming
        self._simulation_path = simulation_infos["file_path"]
        self._simulation_parameters = simulation_infos["param_file"]

    def run(self, output_folder, test_mode=False):
        geometry_output_folder = path.join(output_folder, "geometry_outputs")
        simulation_output_folder = path.join(output_folder, "simulation_outputs")

        if not path.exists(geometry_output_folder):
            makedirs(geometry_output_folder)

        if not path.exists(simulation_output_folder):
            makedirs(simulation_output_folder)

        singularity = path.join(singularity_path, singularity_name)
        geometry_command = "{} run -B {} --app launch_voxsim -f {} -r {} -s {} -o {} --comp-map {}".format(
            singularity,
            ",".join([self._geometry_path, geometry_output_folder]),
            path.join(self._geometry_path, self._geometry_base_file),
            ",".join(self._geometry_resolution),
            ",".join(self._geometry_spacing),
            path.join(geometry_output_folder, self._base_naming),
            "--no-process" if test_mode else "--quiet"
        )
        simulation_command = "{} run -B {} --app launch_fiberfox -p {} -i {} -o {} {}".format(
            singularity,
            ",".join([self._simulation_path, simulation_output_folder]),
            path.join(self._simulation_path, self._simulation_parameters),
            path.join(geometry_output_folder, self._base_naming) + ".fib",
            path.join(simulation_output_folder, self._base_naming),
            "-v" if test_mode else ""
        )

        with open(path.join(output_folder, "{}.log".format(self._base_naming))) as log_file:
            self._launch_command(geometry_command, log_file)
            self._launch_command(simulation_command, log_file)

    def _launch_command(self, command, log_file):
        process = Popen([command], stdout=PIPE, stderr=PIPE)
        while not process.wait(1000):
            out, err = process.communicate()
            log_file.write(out)
            log_file.write(err)

        log_file.write("Process ended with return code {}".format(process.returncode))
