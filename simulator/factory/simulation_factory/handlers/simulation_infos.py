from simulator.factory.common import AttributeAsDictClass


class SimulationInfos(AttributeAsDictClass):

    def __init__(self, file_path, simulation_file_name, ids):
        super().__init__()
        self.generate_new_key("file_path", file_path)
        self.generate_new_key("param_file", simulation_file_name)
        self.generate_new_key("compartment_ids", ids)

    def get_file_path(self):
        return self._file_path

    def set_file_path(self, file_path):
        self._file_path = file_path

    def get_simulation_file_name(self):
        return self._param_file

    def set_simulation_file_name(self, name):
        self._param_file = name
