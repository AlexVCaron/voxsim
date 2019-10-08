from lxml.etree import SubElement

from .xml_tree_element import XmlTreeElement
from factory.simulation_factory.helpers.number_tag_to_placeholder import NumberTagToPlaceholder


class CompartmentModels(XmlTreeElement):
    def __init__(self, compartments):
        self._compartments = compartments

    def dump_to_xml(self, parent_element):
        compartment_element = SubElement(parent_element, "compartments")

        compartments = sorted(self._compartments, key=lambda cmp: cmp["ID"])
        for cmp in range(len(compartments)):
            ith_cmp = SubElement(compartment_element, NumberTagToPlaceholder.generate_placeholder(cmp))
            for elem, value in compartments[cmp].items():
                self._create_text_element(ith_cmp, elem, str(value))

        return parent_element
