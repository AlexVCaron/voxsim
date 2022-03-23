from copy import deepcopy

from lxml.etree import SubElement

from .xml_tree_element import XmlTreeElement


class ArtifactModel(XmlTreeElement):
    def __init__(self, models_list=None):
        self._models = self._generate_default_dictionary()
        if models_list:
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
                "eddyStrength": 0.002,
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
                "value": False,
                "zeroringing": 0
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
            },
            "doAddDrift": {
                "value": False,
                "drift": 0.06
            }
        }

    def dump_to_xml(self, parent_element):
        artifacts_element = SubElement(parent_element, "artifacts")

        for artifact, data in self._models.items():
            self._create_text_element(artifacts_element, artifact, str(data.pop("value")).lower())
            if artifact == "addnoise" and "noisevariance" in data:
                self._create_text_element(parent_element, "noisevariance", str(data["noisevariance"]))
            for attr, value in data.items():
                self._create_text_element(artifacts_element, attr, str(value))

        self._alphabetical_ordering_of_attributes(artifacts_element)

        return parent_element
