from ...common import AttributeAsDictClass
import pathlib


class SimulationInfos(AttributeAsDictClass):
    def __init__(self, file_path: pathlib.Path, simulation_file_name: pathlib.Path, ids):
        super().__init__()
        self.generate_new_key("file_path", file_path)
        self.generate_new_key("param_file", simulation_file_name)
        self.generate_new_key("compartment_ids", ids)

    def get_file_path(self) -> pathlib.Path:
        return self._file_path

    def set_file_path(self, file_path: pathlib.Path):
        self._file_path = file_path

    def get_simulation_file_name(self) -> pathlib.Path:
        return self._param_file

    def set_simulation_file_name(self, name: pathlib.Path):
        self._param_file = name

    @classmethod
    def from_dict(cls, info):
        return SimulationInfos(**info)
