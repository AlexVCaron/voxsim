from os import path, makedirs

from simulator.factory.geometry_factory.features.ORM.config_builder import ConfigBuilder
from .geometry_infos import GeometryInfos


class GeometryHandler:
    def __init__(self, resolution, spacing, clusters=[], spheres=[]):
        self._parameters_dict = {
            "resolution": resolution,
            "spacing": spacing,
            "clusters": clusters,
            "spheres": spheres
        }

    def __reduce__(self):
        return (GeometryHandler, (
            self._parameters_dict["resolution"],
            self._parameters_dict["spacing"],
            self._parameters_dict["clusters"],
            self._parameters_dict["spheres"]
        ))

    def add_sphere(self, sphere):
        self._parameters_dict["spheres"].append(sphere)
        return self

    def add_cluster(self, cluster):
        self._parameters_dict["clusters"].append(cluster)
        return self

    def get_resolution(self):
        return self._parameters_dict["resolution"]

    def get_spacing(self):
        return self._parameters_dict["spacing"]

    def _generate_cluster_base(self, naming, i):
        return ConfigBuilder.create_cluster_object(
            "",
            ["{}_f_{}.vspl".format(naming, i)],
            [1],
            self._parameters_dict["clusters"][i].get_world_center()
        )

    def _get_number_of_clusters(self):
        return len(self._parameters_dict["clusters"])

    def generate_json_configuration_files(self, output_naming, simulation_path=""):
        if not path.exists(simulation_path):
            makedirs(simulation_path, exist_ok=True)

        with open(path.join(simulation_path, output_naming + "_base.json"), "w+") as base_file:

            world = ConfigBuilder.create_world(len(self.get_resolution()), self.get_resolution())
            structures = [self._generate_cluster_base(output_naming, i) for i in range(self._get_number_of_clusters())]
            structures += self._parameters_dict["spheres"]

            base_file.write(
                "{\n" +
                "    \"world\": " + world.serialize(indent=6) + ",\n" +
                "    \"path\": \"{0}\"".format(simulation_path) + ",\n" +
                "    \"structures\": [\n" + "      " + ",\n".join(
                    [structure.serialize(indent=8) for structure in structures]) + "\n    ]\n" +
                "}"
            )

        for cluster_idx in range(len(self._parameters_dict["clusters"])):
            with open(path.join(simulation_path, output_naming + "_f_{}.vspl".format(cluster_idx)), "w+") as f:
                f.write(self._parameters_dict["clusters"][cluster_idx].serialize())

        return GeometryInfos(
            simulation_path,
            output_naming + "_base.json",
            self.get_resolution(),
            self.get_spacing(),
            len(structures) - self._get_number_of_clusters() + 1
        )
