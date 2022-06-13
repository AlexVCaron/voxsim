import json
from os.path import dirname, join, realpath


def get_config(path=dirname(realpath(__file__))):
    with open(join(path, "config.json")) as f:
        return json.load(f)


def override_global_config(config):
    print(config)
    with open(join(dirname(realpath(__file__)), "config.json"), "w+") as f:
        json.dump(config, f)
