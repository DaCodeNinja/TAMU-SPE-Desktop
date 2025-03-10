import os
import yaml


def pull(filename: str) -> dict:
    if os.path.getsize(filename) > 0:
        with open(filename, "r") as fp:
            # Load data from YAML file
            b = yaml.safe_load(fp)
        return b
    else:
        print('This YAML file is empty')


def push(filename: str, pushing: dict):
    with open(filename, "w") as fp:
        # Dump data to YAML file
        yaml.dump(pushing, fp, default_flow_style=False)
