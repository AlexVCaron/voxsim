from lxml.etree import SubElement

from factory.simulation_factory.parameters.xml_tree_element import XmlTreeElement
from factory.simulation_factory.helpers.number_tag_to_placeholder import NumberTagToPlaceholder


class AcquisitionProfile(XmlTreeElement):
    def __init__(self, resolution, spacing):
        self._resolution = resolution
        self._spacing = spacing
        self._echo_time = None
        self._repetition = None
        self._n_coils = None
        self._dwell = 1
        self._partial = 1
        self._scale = 100
        self._reverse = False
        self._inhom = 50
        self._axon_rad = 0

    def set_echo(self, echo_time):
        self._echo_time = echo_time
        return self

    def get_echo(self):
        return self._echo_time

    def set_repetition(self, repetition_time):
        self._repetition = repetition_time
        return self

    def get_repetition(self):
        return self._repetition

    def set_inhomogen_time(self, inhom_time):
        self._inhom = inhom_time
        return self

    def get_inhomogen_time(self):
        return self._inhom

    def set_axon_radius(self, radius):
        self._axon_rad = radius
        return self

    def get_axon_radius(self):
        return self._axon_rad

    def set_n_coils(self, n_coils):
        self._n_coils = n_coils
        return self

    def get_n_coils(self):
        return self._n_coils

    def set_dwell(self, dwell_time):
        self._dwell = dwell_time
        return self

    def get_dwell(self):
        return self._dwell

    def set_partial_fourier(self, partial_fourier):
        self._partial = partial_fourier
        return self

    def get_partial_fourier(self):
        return self._partial

    def set_scale(self, scale):
        self._scale = scale
        return self

    def get_scale(self):
        return self._scale

    def set_reverse_phase(self, reverse_phase):
        self._reverse = reverse_phase
        return self

    def get_reverse_phase(self):
        return self._reverse

    def dump_to_xml(self, parent_element):
        basic_element = SubElement(parent_element, "basic")

        size_element = SubElement(basic_element, "size")
        self._dump_xyz(size_element, self._resolution)

        spacing_element = SubElement(basic_element, "spacing")
        self._dump_xyz(spacing_element, self._spacing)

        origin_element = SubElement(basic_element, "origin")
        self._dump_xyz(origin_element, [0, 0, 0])

        direction_element = SubElement(basic_element, "direction")
        self._create_text_element(direction_element, NumberTagToPlaceholder.generate_placeholder(1), "1")
        self._create_text_element(direction_element, NumberTagToPlaceholder.generate_placeholder(2), "0")
        self._create_text_element(direction_element, NumberTagToPlaceholder.generate_placeholder(3), "0")
        self._create_text_element(direction_element, NumberTagToPlaceholder.generate_placeholder(4), "0")
        self._create_text_element(direction_element, NumberTagToPlaceholder.generate_placeholder(5), "1")
        self._create_text_element(direction_element, NumberTagToPlaceholder.generate_placeholder(6), "0")
        self._create_text_element(direction_element, NumberTagToPlaceholder.generate_placeholder(7), "0")
        self._create_text_element(direction_element, NumberTagToPlaceholder.generate_placeholder(8), "0")
        self._create_text_element(direction_element, NumberTagToPlaceholder.generate_placeholder(9), "1")

        self._create_text_element(parent_element, "coilsensitivityprofile", "2")
        self._create_text_element(parent_element, "numberofcoils", str(self._n_coils))
        self._create_text_element(parent_element, "reversephase", str(self._reverse).lower())
        self._create_text_element(parent_element, "partialfourier", str(self._partial))
        self._create_text_element(parent_element, "trep", str(self._repetition))
        self._create_text_element(parent_element, "signalScale", str(self._scale))
        self._create_text_element(parent_element, "tEcho", str(self._echo_time))
        self._create_text_element(parent_element, "tLine", str(self._dwell))
        self._create_text_element(parent_element, "tInhom", str(self._inhom))
        self._create_text_element(parent_element, "simulatekspace", str(True).lower())
        self._create_text_element(parent_element, "axonRadius", str(self._axon_rad))
        self._create_text_element(parent_element, "doSimulateRelaxation", str(True).lower())
        self._create_text_element(parent_element, "doDisablePartialVolume", str(False).lower())

        return parent_element
