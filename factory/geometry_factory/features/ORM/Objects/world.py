from .json_data import JsonData
from factory.geometry_factory.features.ORM.orm_exception import ORMException


class World(JsonData):

    def __init__(self):
        super().__init__()
        self._values["resolution"] = []
        self._required += ["dimension"]

    def set_dimension(self, dimension):
        self._set_value("dimension", dimension)
        return self

    def set_resolution_at(self, axe, resolution):
        self._get_key("resolution")[axe] = resolution
        return self

    def add_resolution(self, resolution):
        self._append_value("resolution", resolution)
        return self

    def set_resolutions(self, resolutions):
        self._set_value("resolution", resolutions)
        return self

    def _validate_all_keys(self):
        if not len(self._get_key("resolution")) == self._get_key("dimension"):
            raise ORMException("Resolution list is not as long as there is dimensions")
        if self._get_key("dimension") <= 0:
            raise ORMException("Dimension must be greater than 0")
