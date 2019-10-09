from abc import ABCMeta, abstractmethod
from lxml.etree import SubElement


class XmlTreeElement(metaclass=ABCMeta):
    def _create_text_element(self, parent, tag, text):
        elem = SubElement(parent, tag)
        elem.text = text
        return elem

    def _dump_xyz(self, parent_element, xyz):
        self._create_text_element(parent_element, "x", str(xyz[0]))
        self._create_text_element(parent_element, "y", str(xyz[1]))
        self._create_text_element(parent_element, "z", str(xyz[2]))

        return parent_element

    def _alphabetical_ordering_of_attributes(self, parent):
        parent[:] = sorted(parent, key=lambda x: x.tag)

        return parent

    @abstractmethod
    def dump_to_xml(self, parent_element):
        pass
