

class ConfigurationHandler:
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

    def add_fiber(self, bundle):
        self._parameters_dict["bundles"].append(bundle)
        return self

    def get_resolution(self):
        return self._parameters_dict["resolution"]

    def get_spacing(self):
        return self._parameters_dict["spacing"]

    def generate_json_configuration_files(self, output_path, simulation_path=None):
        pass
