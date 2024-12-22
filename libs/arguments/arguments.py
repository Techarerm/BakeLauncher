import os
import time
import json
import psutil
import requests
from libs.instance.instance import instance
from libs.Utils.utils import get_version_data


class class_argument:
    def __init__(self):
        self.BakeLibraryJVMConfigURL = ("https://github.com/Techarerm/BakeLauncher-Library/raw/refs/heads/main/JVM"
                                        "/JVM_ramConfigurations.json")

    @staticmethod
    def write_args(instance_custom_cfg, item, data, mode, **kwargs):
        key_map = {
            "customjvmargs": "CustomJVMArgs",
            "customgameargs": "CustomGameArgs",
        }
        item_key = key_map.get(item.lower())

        if not item_key:
            return False, f"Unknown item: {item}"

        if mode == "append":
            old_data = instance.read_custom_config(instance_custom_cfg, item)
            full_data = (old_data + " " + data) if old_data else data
            instance.write_custom_config(instance_custom_cfg, item, full_data)
            return True, None

        elif mode == "overwrite":
            instance.write_custom_config(instance_custom_cfg, item, data)
            return True, None

        if kwargs.get("CleanUP", False):
            instance.write_custom_config(instance_custom_cfg, item, data)
            return True, None

        return False, None

    def get_recommend_jvm_args(self, instance_custom_config):
        if not os.path.exists(instance_custom_config):
            return False, "CustomConfigNotFound"

        try:
            # Get recommend JVMConfig json data
            response = requests.get(self.BakeLibraryJVMConfigURL)

            if response.ok:
                jvm_configurations = response.json()
            else:
                return False, "GrabbingJVMConfigListFailed"

            # Get the total memory size and convert size bytes to GB
            memory_info = psutil.virtual_memory()
            total_ram_gb = memory_info.total / (1024 ** 3)

            int_total_ram = int(total_ram_gb) + (1 if (total_ram_gb % 1) > 0.5 else 0)

            if int_total_ram <= 4:
                selected_ram = '4GB'
            elif int_total_ram <= 8:
                selected_ram = '8GB'
            elif int_total_ram <= 16:
                selected_ram = '16GB'
            elif int_total_ram <= 32:
                selected_ram = '32GB'
            else:
                selected_ram = '32GB'

            jvm_args = jvm_configurations["ramConfigurations"].get(selected_ram)

            if jvm_args:
                full_args = ""
                for arg in jvm_args['JVMArgs']:
                    full_args += arg + " "
                self.write_args(instance_custom_config, "CustomJVMArgs", full_args, "overwrite")
                time.sleep(2)
                return True, full_args
            else:
                return False, "CannotFindRecommendArguments"

        except json.JSONDecodeError as e:
            return False, f"JSONDecodeError:{e}"
        except Exception as e:
            return False, f"GetArguments>Error:{e}"

    def get_support_game_args(self, client_version):
        version_data = get_version_data(client_version)

        feature_dict = {}  # Dictionary to store features with corresponding arguments
        feature_list = []  # List to store features for user selection

        try:
            # Loop through the game arguments
            for arg in version_data['arguments']['game']:
                if isinstance(arg, dict) and 'rules' in arg:
                    for rule in arg['rules']:
                        if 'features' in rule:
                            for feature in rule['features']:
                                if feature not in feature_dict:
                                    feature_dict[feature] = []  # Initialize a list for the feature's arguments
                                # Add the corresponding argument values (either string or list)
                                if isinstance(arg['value'], list):
                                    feature_dict[feature].extend(arg['value'])
                                else:
                                    feature_dict[feature].append(arg['value'])
        except KeyError:
            return False, "UnsupportedVersion"

        # Create a list of features with numbers
        for idx, feature in enumerate(feature_dict.keys(), start=1):
            feature_list.append(f"{idx}: {feature}")

        return feature_list, feature_dict


arguments = class_argument()
