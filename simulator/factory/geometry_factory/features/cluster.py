import json

from .ORM.Objects import JsonData, ORMException
from .cluster_meta import ClusterMeta
from .bundle import Bundle


class Cluster(JsonData):

    def __init__(self):
        super().__init__()
        self._values["meta"] = ClusterMeta()
        self._values["data"] = []
        self._world_center = None

        self._required += ["meta", "data"]

    def get_meta(self):
        return self._get_key("meta")

    def set_cluster_meta(self, cluster_meta):
        self._set_value("meta", cluster_meta)
        return self

    def set_bundles(self, bundles):
        self._set_value("data", bundles)
        return self

    def add_bundle(self, bundle):
        self._append_value("data", bundle)
        return self

    def get_world_center(self):
        return self._world_center

    def set_world_center(self, center):
        self._world_center = center
        return self

    def get_cluster_center(self):
        return self._values["meta"].get_center()

    def get_cluster_scaling(self, resolution):
        cluster_limits = self._values["meta"].get_limits()
        assert len(resolution) == len(cluster_limits)

        return [r / (l[1] - l[0]) for r, l in zip(resolution, cluster_limits)]

    def get_number_of_bundles(self):
        return len(self._values["data"])

    def _validate_all_keys(self):
        if len(self._get_key("data")) == 0:
            raise ORMException("No fiber present in the data")

    def serialize(self, encoder=json.JSONEncoder, indent=4):
        class MyEncoder(json.JSONEncoder):
            def default(self, o):
                if isinstance(o, ClusterMeta):
                    return o.get_values()
                if isinstance(o, Bundle):
                    return o.get_values()
                else:
                    return super().default(o)

        return super().serialize(MyEncoder, indent)
