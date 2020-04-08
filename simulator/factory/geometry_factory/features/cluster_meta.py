from ast import literal_eval

from .ORM.Objects import JsonData, ORMException


class ClusterMeta(JsonData):

    def _get_base_object(self):
        return ClusterMeta()

    def __init__(self):
        super().__init__()
        self._values["limits"] = ""
        self._values["center"] = []

        self._required += ["dimensions", "density", "sampling"]

    def get_values(self):
        self._validate_all_keys()
        self._validate_required()
        return self._values

    def set_dimensions(self, dimensions):
        self._set_value("dimensions", dimensions)
        return self

    def set_limits(self, limits):
        self._set_value("limits", ".".join([str(lim) for lim in limits]).replace(" ", ""))
        return self

    def get_limits(self):
        return [literal_eval(lim) for lim in self._values["limits"].split(".")]

    def set_center(self, center):
        self._set_value("center", center)
        return self

    def get_center(self):
        return self._values["center"]

    def set_density(self, density):
        self._set_value("density", int(density))
        return self

    def set_sampling(self, sampling):
        self._set_value("sampling", sampling)
        return self

    def set_comment(self, comment):
        self._set_value("comments", comment)
        return self

    def _validate_all_keys(self):
        if self._get_key("dimensions") < 2:
            raise ORMException("Dimension must at least be 2")
        if not len(self._get_key("center")) == self._get_key("dimensions"):
            raise ORMException("Center size and dimension does not agree")
        if self._get_key("density") <= 0:
            raise ORMException("Density must be greater than 0")
        if self._get_key("sampling") <= 0:
            raise ORMException("Sampling must be greater than 0")
