from ...common import AttributeAsDictClass
import pathlib


class GeometryInfos(AttributeAsDictClass):
    def __init__(
            self, file: pathlib.Path, resolution, spacing, n_maps, **kwargs
    ):
        super().__init__(**kwargs)
        self.generate_new_key("file", file)
        self.generate_new_key("resolution", resolution)
        self.generate_new_key("spacing", spacing)
        self.generate_new_key("n_maps", n_maps)

    @property
    def file(self) -> pathlib.Path:
        return self._file

    @file.setter
    def file(self, file: pathlib.Path):
        self._file = file

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
