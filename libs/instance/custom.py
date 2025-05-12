import os
import json

from libs.version.version import get_version_data


def create_instance_custom_config(minecraft_version: str):
    version_data = get_version_data(minecraft_version)

    if not version_data:
        return False

    bake_json = {
        "_commit": {
            "BakeLauncher Instance Config"
        },
        "minecraftVersion": minecraft_version,
        "type": version_data["type"],
        "mainClass": version_data["mainClass"],
        "jvmArguments": version_data.get("arguments", []).get("jvm", []),
        "gameArguments": version_data.get("arguments", []).get("game", []),
        "modLoader": {
            "modLoaderName": None,
            "modLoaderVersion": None,
            "mainClass": None,
            "classPath": None,
            "jvmArguments": None,
            "gameArguments": None,
        },
        "custom": {
            "mainClass": None,
            "classPath": None,
            "jvmArguments": None,
            "gameArguments": None,
        },
        "settings": {
            "enableModLoader": False,
            "_commit": "The following settings are all for '_custom' item.",
            "replaceMainClass": False,
            "replaceClassPath": False,
            "replaceJVMArguments": False,
            "replaceGameArguments": False,
        }
    }


def get_key_value_from_instance_json(instance_json_path, key):
    try:
        with open(instance_json_path, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        return False, None, "File not found"

    value = data.get(key, None)

    return True, value, None


def set_key_value_from_instance_json(instance_json_path, key, value):
    try:
        with open(instance_json_path, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        return False, "File not found"

    data[key] = value

    try:
        with open(instance_json_path, "w") as f:
            json.dump(data, f)
    except FileNotFoundError:
        return False, "File not found"
    except PermissionError:
        return False, "Permission denied"

    return True, None
