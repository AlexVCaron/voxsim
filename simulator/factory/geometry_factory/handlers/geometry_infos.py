from ...common import AttributeAsDictClass
import pathlib


class GeometryInfos(AttributeAsDictClass):
    def __init__(
            self, file_path: pathlib.Path, base_file: str, resolution, spacing, n_maps, **kwargs
    ):
        super().__init__(**kwargs)
        self.generate_new_key("file_path", file_path)
        self.generate_new_key("base_file", base_file)
        self.generate_new_key("resolution", resolution)
        self.generate_new_key("spacing", spacing)
        self.generate_new_key("n_maps", n_maps)

    def get_file_path(self) -> pathlib.Path:
        return self._file_path

    def set_file_path(self, path: pathlib.Path):
        self._file_path = path

    def get_base_file_name(self) -> str:
        return self._base_file

    def set_base_file_name(self, name: str):
        self._base_file = name

    def get_resolution(self):
        return self._resolution

    def set_resolution(self, resolution):
        self._resolution = resolution

    def get_spacing(self):
        return self._spacing

    def set_spacing(self, spacing):
        self._spacing = spacing

    @classmethod
    def from_dict(cls, info):
        return GeometryInfos(**info)
