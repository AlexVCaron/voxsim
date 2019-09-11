import json
from abc import abstractclassmethod, ABCMeta

from factory.geometry_factory.features.ORM.orm_exception import ORMException

from json import encoder
encoder.FLOAT_REPR = lambda o: format(o, '.10f')


class JsonData(metaclass=ABCMeta):

    def __init__(self):
        self._values = {}
        self._required = []

    def _type(self):
        return self.__class__.__name__

    def _set_value(self, key, value):
        self._values[key] = value
        return self

    def _get_key(self, key):
        return self._values[key]

    def _append_value(self, key, value):
        self._values[key].append(value)

    @abstractclassmethod
    def _validate_all_keys(self):
        pass

    def _validate_required(self):
        for required in self._required:
            try:
                self._get_key(required)
            except KeyError:
                raise ORMException("Class {0} requires field {1}".format(self._type(), required))

    def serialize(self, encoder=json.JSONEncoder, indent=4):
        self._validate_required()
        self._validate_all_keys()
        return json.dumps(self._values, sort_keys=True, indent=indent, separators=(',', ': '), cls=encoder)
