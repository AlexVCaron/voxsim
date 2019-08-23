import json

from .ORM.Objects import json_data
from .bundle_meta import BundleMeta
from .fiber import Fiber
from .ORM.orm_exception import ORMException


class Bundle(json_data):

    def __init__(self):
        super().__init__()
        self._values["meta"] = BundleMeta()
        self._values["data"] = []

        self._required += ["meta", "data"]

    def get_meta(self):
        return self._get_key("meta")

    def set_bundle_meta(self, bundle_meta):
        self._set_value("meta", bundle_meta)
        return self

    def set_fibers(self, fibers):
        self._set_value("data", fibers)
        return self

    def add_fiber(self, fiber):
        self._append_value("data", fiber)
        return self

    def _validate_all_keys(self):
        if len(self._get_key("data")) == 0:
            raise ORMException("No fiber present in the data")

    def serialize(self, encoder=json.JSONEncoder, indent=4):
        class MyEncoder(json.JSONEncoder):
            def default(self, o):
                if isinstance(o, BundleMeta):
                    return o.get_values()
                if isinstance(o, Fiber):
                    return o.get_values()
                else:
                    return super().default(o)

        return super().serialize(MyEncoder, indent)
