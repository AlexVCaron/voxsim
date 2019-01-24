from ORM.utils.ORMException import ORMException
from .Structure import Structure


class Sphere(Structure):

    def __init__(self):
        super().__init__()
        self._values["type"] = "internal"
        self._values["object"] = "sphere"

        self._required += ["radius", "scalings"]

    def set_radius(self, radius):
        self._set_value("radius", radius)
        return self

    def get_radius(self):
        return self._get_key("radius")

    def set_scaling(self, scaling):
        self._set_value("scalings", scaling)
        return self

    def get_scaling(self):
        return self._get_key("scalings")

    def set_color(self, color):
        self._set_value("color", color)
        return self

    def get_color(self):
        return self._get_key("color")

    def copy(self):
        sphere = Sphere()
        sphere.set_scaling(self.get_scaling())
        sphere.set_center([c for c in self.get_center()])
        sphere.set_radius(self.get_radius())
        if "color" in self._values.keys():
            sphere.set_color(self.get_color())

        return sphere

    def _validate_all_keys(self):
        if self._get_key("radius") <= 0:
            raise ORMException("Radius must be greater than 0")
        if self._get_key("scalings") <= 0:
            raise ORMException("Scalings must be greater than 0")
