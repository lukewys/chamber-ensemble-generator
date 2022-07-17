"""Utilities for file loading and saving."""

import pickle
import json
import yaml


def pickle_dump(obj, path):
    with open(path, 'wb') as f:
        pickle.dump(obj, f)
        f.close()


def pickle_load(path):
    with open(path, 'rb') as f:
        data = pickle.load(f)
        f.close()
    return data


def json_dump(data_json, json_save_path):
    with open(json_save_path, 'w') as f:
        json.dump(data_json, f)
        f.close()


def json_load(json_path):
    with open(json_path, 'r') as f:
        data = json.load(f)
        f.close()
    return data


def yaml_load(yaml_path):
    with open(yaml_path, 'r') as f:
        data = yaml.safe_load(f)
        f.close()
    return data


def yaml_dump(data_yaml, yaml_save_path):
    with open(yaml_save_path, 'w') as f:
        yaml.dump(data_yaml, f, sort_keys=False)
        f.close()


def get_config():
    return yaml_load('augment_config.yaml')
