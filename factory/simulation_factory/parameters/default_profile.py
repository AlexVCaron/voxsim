from lxml.etree import SubElement

from factory.simulation_factory.parameters.xml_tree_element import XmlTreeElement


class DefaultProfile(XmlTreeElement):
    def dump_to_xml(self, parent_element):
        fibers_element = SubElement(parent_element, "fibers")
        self._create_text_element(fibers_element, "distribution", str(0))
        self._create_text_element(fibers_element, "variance", str(0.1))
        self._create_text_element(fibers_element, "density", str(100))
        self._create_text_element(fibers_element, "realtime", str(True).lower())
        self._create_text_element(fibers_element, "showadvanced", str(False).lower())
        self._create_text_element(fibers_element, "constantradius", str(False).lower())
        self._create_text_element(fibers_element, "includeFiducials", str(True).lower())

        spline_element = SubElement(fibers_element, "spline")
        self._create_text_element(spline_element, "sampling", str(1))
        self._create_text_element(spline_element, "tension", str(0))
        self._create_text_element(spline_element, "continuity", str(0))
        self._create_text_element(spline_element, "bias", str(0))

        rotation_element = SubElement(fibers_element, "rotation")
        self._dump_xyz(rotation_element, [0, 0, 0])

        translation_element = SubElement(fibers_element, "translation")
        self._dump_xyz(translation_element, [0, 0, 0])

        scale_element = SubElement(fibers_element, "scale")
        self._dump_xyz(scale_element, [1, 1, 1])

        image_element = parent_element.find("image")
        self._create_text_element(image_element, "outputvolumefractions", str(True).lower())
        self._create_text_element(image_element, "showadvanced", str(False).lower())
        self._create_text_element(image_element, "signalmodelstring", "simulation_done_via_voxsim")
        self._create_text_element(image_element, "artifactmodelstring", "_artifacts_unkown")

        SubElement(image_element, "outpath")

        return parent_element
