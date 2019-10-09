from .structure import Structure
from .orm_exception import ORMException


class Cluster(Structure):

    def __init__(self):
        super().__init__()
        self._values["type"] = "external"
        self._values["scalings"] = []
        self._values["names"] = []

        self._required += ["type", "scalings", "names"]

    def set_extension_from_path(self, extension):
        self._set_value("extension", extension)
        return self

    def add_scaling(self, scaling):
        self._append_value("scalings", scaling)
        return self

    def set_scaling(self, idx, scaling):
        self._get_key("scalings")[idx] = scaling
        return self

    def set_scalings(self, scalings):
        self._set_value("scalings", scalings)
        return self

    def add_bundle_name(self, name):
        self._append_value("names", name)
        return self

    def set_bundle_name(self, idx, name):
        self._get_key("names")[idx] = name
        return self

    def set_bundles_names(self, names):
        self._set_value("names", names)
        return self

    def add_bundle(self, name, scaling=1):
        self.add_bundle_name(name)
        self.add_scaling(scaling)
        return self

    def _validate_all_keys(self):
        if self._get_key("names") == 0:
            raise ORMException("Fiber with no names")
        if not len(self._get_key("names")) == len(self._get_key("scalings")):
            print(self._get_key("names"), self._get_key("scalings"))
            raise ORMException("Inconsistent size between 'names' and 'scalings' lists")
