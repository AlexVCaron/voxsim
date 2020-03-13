from copy import deepcopy

from lxml.etree import SubElement

from .xml_tree_element import XmlTreeElement


class ArtifactModel(XmlTreeElement):
    def __init__(self, models_list=[]):
        self._models = self._generate_default_dictionary()
        for model in models_list:
            model = deepcopy(model)
            model_name = model.pop("descr")
            self._models[model_name] = model

    def _generate_default_dictionary(self):
        return {
            "doAddDistortions": {
                "value": False
            },
            "addeddycurrents": {
                "value": False,
                "eddyStrength": 0,
                "eddyTau": 70
            },
            "addspikes": {
                "value": False,
                "spikesnum": 0,
                "spikesscale": 1
            },
            "addaliasing": {
                "value": False,
                "aliasingfactor": 1
            },
            "addghosts": {
                "value": False,
                "kspaceLineOffset": 0
            },
            "addringing": {
                "value": False
            },
            "doAddMotion": {
                "value": False,
                "randomMotion": True,
                "motionvolumes": "random",
                "rotation0": 0,
                "rotation1": 0,
                "rotation2": 15,
                "translation0": 0,
                "translation1": 0,
                "translation2": 0,
            },
            "addnoise": {
                "value": False,
            }
        }

    def dump_to_xml(self, parent_element):
        artifacts_element = SubElement(parent_element, "artifacts")

        for artifact, data in self._models.items():
            self._create_text_element(artifacts_element, artifact, str(data.pop("value")).lower())
            for attr, value in data.items():
                self._create_text_element(artifacts_element, attr, str(value))

        artifacts_element = self._alphabetical_ordering_of_attributes(artifacts_element)

        return parent_element
