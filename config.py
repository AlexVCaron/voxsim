from os.path import join, dirname, realpath
import json


def get_config():
    with open(join(dirname(realpath(__file__)), "config.json")) as f:
        return json.load(f)


def override_config(config):
    print(config)
    with open(join(dirname(realpath(__file__)), "config.json"), "w+") as f:
        json.dump(config, f)
