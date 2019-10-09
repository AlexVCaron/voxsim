from simulator.factory.common import AttributeAsDictClass


class GeometryInfos(AttributeAsDictClass):
    def __init__(self, file_path, base_file, resolution, spacing, n_maps):
        super().__init__()

        self._file_path = file_path
        self._base_file = base_file
        self._resolution = resolution
        self._spacing = spacing
        self._number_of_maps = n_maps

    def get_file_path(self):
        return self._file_path

    def set_file_path(self, path):
        self._file_path = path

    def get_base_file_name(self):
        return self._base_file

    def set_base_file_name(self, name):
        self._base_file = name

    def get_resolution(self):
        return self._resolution

    def set_resolution(self, resolution):
        self._resolution = resolution

    def get_spacing(self):
        return self._spacing

    def set_spacing(self, spacing):
        self._spacing = spacing
