import logging
import pathlib
import typing

from asyncio import get_event_loop, new_event_loop, set_event_loop
from subprocess import PIPE, Popen

from .config import SingularityConfig
from .datastore import Datastore
from ..utils.logging import RTLogging
from ..factory.geometry_factory.handlers import GeometryInfos
from ..factory.simulation_factory.handlers import SimulationInfos

_logger = logging.getLogger(__name__)


class AsyncRunner:
    _custom_log_handlers: typing.Set[logging.Handler]  # TODO : WIP. See ..utils.logging

    def __init__(self):
        self._event_loop = new_event_loop()
        self._custom_log_handlers = set()  # TODO : WIP. See ..utils.logging

    def start(self):
        self._start_loop_if_closed()

    def stop(self):
        if not self._event_loop.is_closed():
            self._event_loop.close()

    def _run_command(self, command: str, log_file: pathlib.Path, log_tag: str) -> int:
        set_event_loop(self._event_loop)
        async_loop = get_event_loop()

        returncode = async_loop.run_until_complete(
            self._run_async(command, log_file, log_tag)
        )

        async_loop.close()
        return returncode

    def _start_loop_if_closed(self):
        if self._event_loop.is_closed():
            self._event_loop = new_event_loop()

    async def _run_async(self, command: str, log_file, log_tag) -> int:
        process = Popen(command.split(" "), stdout=PIPE, stderr=PIPE)

        _logger = RTLogging(process, log_file, log_tag)
        _logger.start()
        _logger.join()

        return process.returncode


class SimulationRunner(AsyncRunner):
    _apps = {"phantom": "launch_voxsim", "diffusion mri": "launch_mitk"}

    def __init__(self, singularity_conf=SingularityConfig()):
        self._singularity = singularity_conf.singularity.resolve(strict=True)
        super().__init__()

        self._singularity_exec = singularity_conf.singularity_exec

    def _bind_singularity(self, step, paths, arguments) -> str:
        return "{} run -B {} --app {} {} {}".format(
            self._singularity_exec,
            paths,
            self._apps[step],
            self._singularity,
            arguments,
        )

    @staticmethod
    def _create_outputs(path: pathlib.Path):
        path.mkdir(parents=True, exist_ok=True)
        return path.resolve(strict=True)

    def run(
        self,
        run_name: str,
        phantom_infos: GeometryInfos,
        simulation_infos: SimulationInfos,
        output_folder: pathlib.Path,
        output_nifti=True,
        relative_fiber_fraction=True,
        inter_axonal_fraction=None,
    ):
        self.start()

        output_folder = output_folder.resolve(strict=True)

        self.generate_phantom(
            run_name,
            phantom_infos,
            output_folder,
            relative_fiber_fraction,
            output_nifti,
            loop_managed=True,
        )

        datastore = Datastore(
            output_folder / "simulation",
            output_folder / "phantom" / "{}_phantom_merged_bundles.fib".format(run_name),
            simulation_infos["compartment_ids"],
            inter_axonal_fraction,
        )

        datastore.load_compartments(output_folder / "phantom", run_name, output_nifti)
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
            compartments_staged=True,
        )

        self.stop()

    def generate_phantom(
        self,
        run_name: str,
        phantom_infos: GeometryInfos,
        output_folder: pathlib.Path,
        relative_fiber_fraction=True,
        output_nifti=True,
        loop_managed=False,
    ):

        loop_managed or self.start()

        base_output_folder: pathlib.Path = self._create_outputs(output_folder)
        output_folder: pathlib.Path = self._create_outputs(output_folder / "phantom")

        phantom_def: pathlib.Path = phantom_infos["file_path"] / phantom_infos["base_file"]

        resolution = ",".join([str(r) for r in phantom_infos["resolution"]])
        spacing = ",".join([str(s) for s in phantom_infos["spacing"]])
        fiber_fraction = "rel" if relative_fiber_fraction else "abs"
        out_name: pathlib.Path = output_folder / "{}_phantom".format(run_name)

        arguments = "-f {} -r {} -s {} -o {} --comp-map {} --quiet".format(
            phantom_def, resolution, spacing, out_name, fiber_fraction
        )

        if output_nifti:
            arguments += " --nii"

        bind_paths = ",".join([str(phantom_infos["file_path"]), str(output_folder)])
        command = self._bind_singularity("phantom", bind_paths, arguments)
        log_file: pathlib.Path = base_output_folder / "{}.log".format(run_name)
        self._run_command(command, log_file, "[PHANTOM]")

        loop_managed or self.stop()

    def simulate_diffusion_mri(
        self,
        run_name: str,
        simulation_infos: SimulationInfos,
        output_folder: pathlib.Path,
        fibers_file: pathlib.Path,
        compartment_maps=None,
        bind_paths=None,
        output_nifti=True,
        loop_managed=False,
        compartments_staged=True,
    ):
        loop_managed or self.start()

        bind_paths = [] if bind_paths is None else bind_paths
        fibers_file = fibers_file.resolve(strict=True)
        base_output_folder: pathlib.Path = self._create_outputs(output_folder)
        output_folder: pathlib.Path = self._create_outputs(output_folder / "simulation")

        name = "{}_simulation".format(run_name)

        bind_paths += [str(simulation_infos["file_path"]), str(output_folder)]
        bind_paths = ",".join(bind_paths)
        ffp_file = simulation_infos["file_path"] / simulation_infos["param_file"]

        extension = "nii.gz" if output_nifti else "nrrd"
        out_name = output_folder / "{}.{}".format(name, extension)

        if not compartments_staged and compartment_maps is not None:
            datastore = Datastore(
                output_folder,
                fibers_file,
                simulation_infos["compartment_ids"],
                None,
            )
            datastore.compartments = compartment_maps
            datastore.stage_compartments(run_name)

        arguments = "-p {} -i {} -o {}".format(ffp_file, fibers_file, out_name)

        command = self._bind_singularity("diffusion mri", bind_paths, arguments)
        log_file: pathlib.Path = base_output_folder / "{}.log".format(run_name)
        self._run_command(command, log_file, "[DIFFUSION MRI]")

        loop_managed or self.stop()
