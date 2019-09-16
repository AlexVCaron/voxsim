from factory.common.common import AttributeAsDictClass


class SimulationInfos(AttributeAsDictClass):

    def __init__(self, file_path, simulation_file_name, ids):
        super().__init__()
        self._file_path = file_path
        self._param_file = simulation_file_name
        self._compartment_ids = ids

    def get_file_path(self):
        return self._file_path

    def set_file_path(self, file_path):
        self._file_path = file_path

    def get_simulation_file_name(self):
        return self._simulation_file

    def set_simulation_file_name(self, name):
        self._simulation_file = name
