from lxml.etree import Element, SubElement, tostring
from os import path, makedirs

from factory.simulation_factory.helpers.number_tag_to_placeholder import NumberTagToPlaceholder
from factory.simulation_factory.parameters import AcquisitionProfile, CompartmentModels, DefaultProfile, ArtifactModel
from .simulation_infos import SimulationInfos


class SimulationHandler:
    def __init__(self, resolution, spacing, compartments=None):
        self._acq_profile = AcquisitionProfile(resolution, spacing)
        self._art_model = ArtifactModel()
        self._grad_profile = None
        self._compartments = compartments if compartments else []

    def set_compartments(self, compartments):
        self._compartments = compartments
        return self

    def set_acquisition_profile(self, acquisition_profile):
        self._acq_profile.set_echo(acquisition_profile.get_echo())\
                         .set_repetition(acquisition_profile.get_repetition())\
                         .set_n_coils(acquisition_profile.get_n_coils())\
                         .set_dwell(acquisition_profile.get_dwell())\
                         .set_partial_fourier(acquisition_profile.get_partial_fourier())\
                         .set_scale(acquisition_profile.get_scale())\
                         .set_reverse_phase(acquisition_profile.get_reverse_phase())\
                         .set_inhomogen_time(acquisition_profile.get_inhomogen_time())\
                         .set_axon_radius(acquisition_profile.get_axon_radius())
        return self

    def set_gradient_profile(self, gradient_profile):
        self._grad_profile = gradient_profile

    def set_artifact_model(self, artifact_model):
        self._art_model = artifact_model

    def add_compartment(self, compartment):
        self._compartments.append(compartment)

    def generate_xml_configuration_file(self, output_naming, simulation_path=""):
        if not path.exists(simulation_path):
            makedirs(simulation_path)

        data = Element("fiberfox")
        image_element = SubElement(data, "image")
        image_element = self._acq_profile.dump_to_xml(image_element)
        image_element = self._grad_profile.dump_to_xml(image_element)
        image_element = self._art_model.dump_to_xml(image_element)
        data = DefaultProfile().dump_to_xml(data)

        CompartmentModels(self._compartments).dump_to_xml(image_element)

        xml_string = NumberTagToPlaceholder.replace_placeholders(tostring(data, pretty_print=True).decode("utf-8"))

        with open(path.join(simulation_path, output_naming + ".ffp"), "w+") as f:
            f.write(xml_string)

        return SimulationInfos(simulation_path, output_naming + ".ffp", [cmp["ID"] for cmp in self._compartments])
