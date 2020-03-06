from collections.abc import MutableMapping


class AttributeAsDictClass(MutableMapping):
    def __init__(self, **kwargs):
        self._valid_keys = [self._generate_attr_key(k) for k in kwargs.keys()]
        self.__dict__.update({self._generate_attr_key(k): v for k, v in kwargs.items()})

    def generate_new_key(self, key, value):
        self._valid_keys.append(self._generate_attr_key(key))
        self.__dict__[self._generate_attr_key(key)] = value

    def __setitem__(self, key, value):
        if self._generate_attr_key(key) in self.__dict__:
            self.__dict__[self._generate_attr_key(key)] = value
        else:
            raise KeyError("To field is absent from simulation infos object {}".format(key))

    def __delitem__(self, key):
        if self._generate_attr_key(key) in self.__dict__:
            self.__dict__[self._generate_attr_key(key)] = ""

    def __getitem__(self, key):
        return self.__dict__[self._generate_attr_key(key)]

    def __len__(self):
        return len(self.__dict__)

    def __iter__(self):
        return iter(self.__dict__)

    def _generate_attr_key(self, key):
        return "_{}".format(key)

    def pop(self, k):
        self._valid_keys = list(filter(lambda key: not k == key, k))
        return super().pop(k)

    def __str__(self):
        return str({k: self.__dict__[k] for k in self._valid_keys})
