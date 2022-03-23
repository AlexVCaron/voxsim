from lxml.etree import SubElement
from math import sqrt
from numpy.linalg import norm
from numpy import isclose, array

from .xml_tree_element import XmlTreeElement
from simulator.factory.simulation_factory.helpers.number_tag_to_placeholder import NumberTagToPlaceholder


class StejskalTannerType(XmlTreeElement):
    def __init__(self, fast=False):
        self._fast = fast

    def dump_to_xml(self, parent_element):
        self._create_text_element(
            parent_element, "acquisitiontype",
            "2" if self._fast else "1"
        )
        return parent_element


class TensorValuedByTensorType(XmlTreeElement):
    def __init__(self, tensor, fast=False):
        self._tensor = tensor
        self._fast = fast

    def get_bval(self):
        return self._tensor[0, 0] + self._tensor[1, 1] + self._tensor[2, 2]

    def dump_to_xml(self, parent_element):
        self._create_text_element(
            parent_element, "acquisitiontype",
            "4" if self._fast else "3"
        )

        md_element = SubElement(parent_element, "multidimensional")
        self._create_text_element(md_element, "definition", "3")
        self._create_text_element(md_element, "bdelta", "0")

        tensor_element = SubElement(parent_element, "btensor")
        self._create_text_element(tensor_element, "0", str(self._tensor[0, 0]))
        self._create_text_element(tensor_element, "1", str(self._tensor[0, 1]))
        self._create_text_element(tensor_element, "2", str(self._tensor[0, 2]))
        self._create_text_element(tensor_element, "3", str(self._tensor[1, 1]))
        self._create_text_element(tensor_element, "4", str(self._tensor[1, 2]))
        self._create_text_element(tensor_element, "5", str(self._tensor[2, 2]))

        return parent_element


class TensorValuedByEigsType(XmlTreeElement):
    def __init__(self, eigenvals, fast=False):
        self._eigenvals = eigenvals
        self._fast = fast

    def get_bval(self):
        return sum(self._eigenvals)

    def dump_to_xml(self, parent_element):
        self._create_text_element(
            parent_element, "acquisitiontype", "4" if self._fast else "3"
        )

        md_element = SubElement(parent_element, "multidimensional")
        self._create_text_element(md_element, "definition", "2")
        self._create_text_element(md_element, "bdelta", "0")

        tensor_element = SubElement(parent_element, "btensor")
        self._create_text_element(
            tensor_element, "eig1", str(self._eigenvals[0])
        )
        self._create_text_element(
            tensor_element, "eig2", str(self._eigenvals[1])
        )
        self._create_text_element(
            tensor_element, "eig3", str(self._eigenvals[2])
        )

        return parent_element


class TensorValuedByParamsType(XmlTreeElement):
    def __init__(self, b_iso, b_delta, fast=False):
        self._b_iso = b_iso
        self._b_delta = b_delta
        self._fast = fast

    def get_bval(self):
        return self._b_iso

    def dump_to_xml(self, parent_element):
        self._create_text_element(
            parent_element, "acquisitiontype", "4" if self._fast else "3"
        )

        md_element = SubElement(parent_element, "multidimensional")
        self._create_text_element(md_element, "definition", "1")
        self._create_text_element(md_element, "bdelta", str(self._b_delta))

        return parent_element


class GradientProfile(XmlTreeElement):
    def __init__(self, bvals, bvecs, g_type):
        self._nominal_bval = max(bvals) if type(g_type) is StejskalTannerType \
                        else g_type.get_bval()
        self._directions = self._scale_gradients(bvecs, bvals)
        self._num_gradients = self._get_number_of_gradients(self._directions)
        self._gtype = g_type

    def _scale_gradients(self, bvecs, bvals):
        return [
            (
                (sqrt(bval / self._nominal_bval) * array(bvec))
                if not (isclose(norm(bvec), 0) or isclose(bval, 0))
                else array(bvec)
            ).tolist() for bvec, bval, in zip(bvecs, bvals)
        ]

    def _get_number_of_gradients(self, directions):
        return len(list(filter(lambda d: not isclose(norm(d), 0.), directions)))

    def dump_to_xml(self, parent_element):
        self._create_text_element(parent_element, "bvalue", str(self._nominal_bval))

        basic_element = parent_element.find("basic")
        self._create_text_element(basic_element, "numgradients", str(self._num_gradients))

        gradients_element = SubElement(parent_element, "gradients")
        for direction in range(len(self._directions)):
            ith_element = SubElement(gradients_element, "d{}".format(direction))
            self._dump_xyz(ith_element, self._directions[direction])

        self._gtype.dump_to_xml(parent_element)

        return parent_element
