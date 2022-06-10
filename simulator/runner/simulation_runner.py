import logging

from asyncio import get_event_loop, new_event_loop, set_event_loop
from os import path, makedirs
from os.path import basename
from subprocess import PIPE, Popen

from config import get_config
from .datastore import Datastore
from simulator.utils.logging import RTLogging


logger = logging.getLogger(basename(__file__).split(".")[0])


class AsyncRunner:
    def __init__(self):
        self._event_loop = new_event_loop()

    def start(self):
        self._start_loop_if_closed()

    def stop(self):
        if not self._event_loop.is_closed():
            self._event_loop.close()

    def _run_command(self, command, log_file, log_tag):
        set_event_loop(self._event_loop)
        async_loop = get_event_loop()
        async_loop.run_until_complete(
            self._run_async(command, log_file, log_tag)
        )
        async_loop.close()


    def _start_loop_if_closed(self):
        if self._event_loop.is_closed():
            self._event_loop = new_event_loop()

    async def _run_async(self, command, log_file, log_tag):
        process = Popen(command.split(" "), stdout=PIPE, stderr=PIPE)

        logger = RTLogging(process, log_file, log_tag)
        logger.start()
        logger.join()

        return process.returncode, log_file


class SimulationRunner(AsyncRunner):
    _apps = {
        "phantom": "launch_voxsim",
        "diffusion mri": "launch_mitk"
    }

    def __init__(self, singularity_conf=get_config()):
            self._singularity = path.join(
                singularity_conf["singularity_path"],
                singularity_conf["singularity_name"]
            )

            self._singularity_exec = "singularity"
            if "singularity_exec" in singularity_conf:
                self._singularity_exec = singularity_conf["singularity_exec"]

    def _bind_singularity(self, step, paths, arguments):
        return "{} run -B {} --app {} {} {}".format(
            self._singularity_exec,
            paths,
            self._apps[step],
            self._singularity,
            arguments
        )

    def _create_outputs(self, path):
        if not path.exists(path):
            makedirs(path, exist_ok=True)

        return path

    def run(
        self,
        run_name,
        phantom_infos,
        simulation_infos,
        output_folder,
        output_nifti=True,
        relative_fiber_fraction=True,
        inter_axonal_fraction=None
    ):
        self.start()

        self.generate_phantom(
            run_name,
            phantom_infos,
            output_folder,
            relative_fiber_fraction,
            output_nifti,
            loop_managed=True
        )

        datastore = Datastore(
            path.join(output_folder, "simulation"),
            path.join(
                output_folder,
                "phantom",
                "{}_phantom_merged_bundles.fib".format(run_name)
            ),
            simulation_infos["compartment_ids"],
            inter_axonal_fraction
        )

        datastore.load_compartments(
            path.join(output_folder, "phantom"), run_name, output_nifti
        )
        datastore.stage_compartments(run_name)

        self.simulate_diffusion_mri(
            run_name,
            simulation_infos,
            output_folder,
            datastore.fibers,
            datastore.compartments,
            datastore.get_bind_paths(False),
            output_nifti,
            loop_managed=True,
            compartments_staged=True
        )

        self.stop()

    def generate_phantom(
        self,
        run_name,
        phantom_infos,
        output_folder,
        relative_fiber_fraction=True,
        output_nifti=True,
        loop_managed=False
    ):

        loop_managed or self.start()

        base_output_folder = output_folder
        output_folder = self._create_outputs(
            path.join(output_folder, "phantom")
        )

        phantom_def = path.join(
            phantom_infos["file_path"], phantom_infos["base_file"]
        )

        resolution = ",".join([str(r) for r in phantom_infos["resolution"]])
        spacing = ",".join([str(s) for s in phantom_infos["spacing"]])
        fiber_fraction = "rel" if relative_fiber_fraction else "abs"
        out_name = path.join(
            output_folder, "phantom, ""{}_phantom".format(run_name)
        )

        arguments = "-f {} -r {} -s {} -o {} --comp-map {} --quiet".format(
            phantom_def,
            resolution,
            spacing,
            out_name,
            fiber_fraction
        )

        if output_nifti:
            arguments += " --nii"

        bind_paths = ",".join([phantom_infos["file_path"], output_folder])
        command = self._bind_singularity("phantom", bind_paths, arguments)
        log_file = path.join(base_output_folder, "{}.log".format(run_name))
        self._run_command(command, log_file, "[PHANTOM]")

        loop_managed or self.stop()

    def simulate_diffusion_mri(
        self,
        run_name,
        simulation_infos,
        output_folder,
        fibers_file,
        compartment_maps=None,
        bind_paths=None,
        output_nifti=True,
        loop_managed=False,
        compartments_staged=True
    ):
        loop_managed or self.start()

        bind_paths = [] if bind_paths is None else bind_paths
        base_output_folder = output_folder
        output_folder = self._create_outputs(
            path.join(output_folder, "simulation")
        )

        name = "{}_simulation".format(run_name)

        bind_paths += [simulation_infos["file_path"], output_folder]
        bind_paths = ",".join(bind_paths)
        ffp_file = path.join(
            simulation_infos["file_path"], simulation_infos["param_file"]
        )
        extension = "nii.gz" if output_nifti else "nrrd"
        out_name = path.join(output_folder, "{}.{}".format(name, extension))

        if not compartments_staged and compartment_maps is not None:
            datastore = Datastore(
                output_folder,
                fibers_file,
                simulation_infos["compartment_ids"],
                None
            )
            datastore.compartments = compartment_maps
            datastore.stage_compartments(run_name)

        arguments = "-p {} -i {} -o {}".format(
            ffp_file, fibers_file, out_name
        )

        command = self._bind_singularity("diffusion mri", bind_paths, arguments)
        log_file = path.join(base_output_folder, "{}.log".format(run_name))
        self._run_command(command, log_file, "[DIFFUSION MRI]")

        loop_managed or self.stop()
