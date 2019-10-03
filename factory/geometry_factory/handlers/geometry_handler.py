from os import path, makedirs

from factory.geometry_factory.features.ORM.config_builder import ConfigBuilder
from .geometry_infos import GeometryInfos


class GeometryHandler:
    def __init__(self, resolution, spacing):
        self._parameters_dict = {
            "resolution": resolution,
            "spacing": spacing,
            "bundles": [],
            "spheres": []
        }

    def add_sphere(self, sphere):
        self._parameters_dict["spheres"].append(sphere)
        return self

    def add_bundle(self, bundle):
        self._parameters_dict["bundles"].append(bundle)
        return self

    def get_resolution(self):
        return self._parameters_dict["resolution"]

    def get_spacing(self):
        return self._parameters_dict["spacing"]

    def _generate_bundle_base(self, naming, i):
        return ConfigBuilder.create_bundle_object(
            "",
            ["{}_f_{}.vspl".format(naming, i)],
            [1],
            [c * s for c, s in zip(
                self._parameters_dict["bundles"][i].get_bundle_center(),
                self._parameters_dict["bundles"][i].get_bundle_scaling(self.get_resolution())
            )]
        )

    def _get_number_of_bundles(self):
        return len(self._parameters_dict["bundles"])

    def generate_json_configuration_files(self, output_naming, simulation_path=""):

        if not path.exists(simulation_path):
            makedirs(simulation_path)

        with open(path.join(simulation_path, output_naming + "_base.json"), "w+") as base_file:

            world = ConfigBuilder.create_world(len(self.get_resolution()), self.get_resolution())
            structures = [self._generate_bundle_base(output_naming, i) for i in range(self._get_number_of_bundles())]
            structures += self._parameters_dict["spheres"]

            base_file.write(
                "{\n" +
                "    \"world\": " + world.serialize(indent=6) + ",\n" +
                "    \"path\": \"{0}\"".format(simulation_path) + ",\n" +
                "    \"structures\": [\n" + "      " + ",\n".join(
                    [structure.serialize(indent=8) for structure in structures]) + "\n    ]\n" +
                "}"
            )

        for bundle_idx in range(len(self._parameters_dict["bundles"])):
            with open(path.join(simulation_path, output_naming + "_f_{}.vspl".format(bundle_idx)), "w+") as f:
                f.write(self._parameters_dict["bundles"][bundle_idx].serialize())

        return GeometryInfos(
            simulation_path,
            output_naming + "_base.json",
            self.get_resolution(),
            self.get_spacing(),
            len(structures) - self._get_number_of_bundles() + 1
        )
