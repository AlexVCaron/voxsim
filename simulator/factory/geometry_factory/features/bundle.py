from .ORM.Objects import JsonData, ORMException


class Bundle(JsonData):

    def _get_base_object(self):
        return Bundle()

    def __init__(self):
        super().__init__()
        self._values["anchors"] = []

        self._required += ["sampling", "radius", "symmetry"]

    def set_n_point_per_centroid(self, pp_centroid):
        self._set_value("sampling", pp_centroid)
        return self

    def set_radius(self, radius):
        self._set_value("radius", radius)
        return self

    def set_symmetry(self, symmetry):
        self._set_value("symmetry", symmetry)
        return self

    def add_anchor(self, anchor):
        self._append_value("anchors", anchor)
        return self

    def _set_anchor_at(self, anchor, idx):
        self._get_key("anchors")[idx] = anchor

    def set_anchors(self, anchors):
        self._set_value("anchors", anchors)
        return self

    def get_anchors(self):
        return self._get_key("anchors")

    def get_radius(self):
        return self._get_key("radius")

    def get_symmetry(self):
        return self._get_key("symmetry")

    def get_n_point_per_centroid(self):
        return self._get_key("sampling")

    def get_values(self):
        return self._values

    def _validate_all_keys(self):
        if len(self._get_key("anchors")) == 0:
            raise ORMException("Anchors list empty")
        if self._get_key("sampling") <= 0:
            raise ORMException("Sampling must be greater than 0")
        if self._get_key("radius") <= 0:
            raise ORMException("Radius must be grater than 0")
        if abs(self._get_key("symmetry")) > 1:
            raise ORMException("Symmetry must be between -1 and 1")