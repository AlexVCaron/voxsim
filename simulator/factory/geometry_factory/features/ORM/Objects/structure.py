from abc import ABCMeta

from .json_data import JsonData


class Structure(JsonData, metaclass=ABCMeta):

    def __init__(self):
        super().__init__()
        self._values["center"] = [0, 0, 0]

        self._required += ["center"]

    def set_center_at(self, axe, value):
        self._get_key("center")[axe] = value
        return self

    def set_center(self, center):
        self._set_value("center", center)
        return self

    def get_center(self):
        return self._get_key("center")
