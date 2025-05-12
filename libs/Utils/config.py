import json
import logging
import os


def config_loader(target_object, setting_dict, target_config_path, allow_undefined=False, json_config=False):
    cleaned_lines = []
    illegal_setting_list = []
    variable_to_value_dict = {}

    # Check if the config exists.
    if not os.path.exists(target_config_path):
        return False, "Target config does not exist"

    if json_config:
        try:
            with open(target_config_path, "r", encoding="utf-8") as file:
                json.load(file)
                file.close()
        except Exception as e:
            print(f"[ERROR] Error while reading the config file : {e}")
            return False, e
    else:
        try:
            with open(target_config_path, "r", encoding="utf-8") as file:
                file.read()
                file.close()
        except Exception as e:
            print(f"[ERROR] Error while reading the config file : {e}")
            return False, e

    # Start reading the target config
    if json_config:
        with open(target_config_path, "r", encoding="utf-8") as file:
            data = json.load(file)
            for setting in data:
                info = f"{setting} = {data[setting]}"
                cleaned_lines.append(info)
    else:
        with open(target_config_path, 'r') as file:
            for line in file:
                line = line.strip()
                if not line or line.startswith('#'):
                    # Filter all comments
                    continue

                line = line.split('#', 1)[0].strip()
                if line:
                    cleaned_lines.append(line)
            file.close()

    for setting_key in setting_dict:
        variable_name = setting_dict[setting_key]
        try:
            data_type, setting_name = setting_key.split("%")
            if len(data_type) == 0:
                # illegal_setting_list.append(f"TYPE_UNDEFINED:{setting_key}")
                continue

            if len(setting_name) == 0:
                # illegal_setting_list.append(f"SETTING_KEY_NOT_FOUND:{setting_key}")
                continue

        except ValueError:
            # illegal_setting_list.append(f"ILLEGAL_VALUE:{setting_key}")
            continue
        except TypeError:
            # illegal_setting_list.append(f"ILLEGAL_SYNTAX:{setting_key}")
            continue
        except Exception as e:
            # illegal_setting_list.append(f"UNKNOWN_ERROR:{e}")
            continue

        for line in cleaned_lines:
            if line.startswith(setting_name):
                new_value = line.split('=')[1].strip().strip('"').strip("'")
                value = new_value
                if not len(value) > 0:
                    continue

                if data_type.lower() == "bool":
                    new_value = line.split('=')[1].strip().upper()
                    if new_value.upper() == 'TRUE':
                        value = True
                    elif new_value.upper() == 'FALSE':
                        value = False
                    else:
                        value = None

                    if value is None:
                        illegal_setting_list.append(f"BOOL%{setting_name}={new_value}")
                        continue
                    else:
                        variable_to_value_dict[variable_name] = value

                elif data_type.lower() == "str":
                    if new_value == "None":
                        illegal_setting_list.append(f"STR%{setting_name}={new_value}")
                        continue
                    variable_to_value_dict[variable_name] = new_value

                elif data_type.lower() == "int":
                    try:
                        # Convert it to integer
                        new_value_converted = int(new_value)
                        variable_to_value_dict[variable_name] = new_value_converted
                    except ValueError:
                        illegal_setting_list.append(f"INT%{setting_name}={new_value}")
                        continue

                elif data_type.lower() == "float":
                    try:
                        # Convert it to float
                        new_value_converted = float(new_value)
                        variable_to_value_dict[variable_name] = new_value_converted
                    except ValueError:
                        illegal_setting_list.append(f"FLOAT%{setting_name}={new_value}")
                        continue

                elif data_type is None:
                    illegal_setting_list.append(f"UNDEFINED%{setting_name}={new_value}")
                    continue

                else:
                    illegal_setting_list.append(f"UNKNOWN_TYPE%{setting_name}={new_value}")
                    continue

    for variable_name, new_value in variable_to_value_dict.items():
        if allow_undefined or hasattr(target_object, variable_name):
            logging.log(logging.DEBUG, f"Set {variable_name} ==> {new_value} | Type  {type(new_value)}")
            setattr(target_object, variable_name, new_value)

    if not len(illegal_setting_list) > 0:
        return True, None

    # Print illegal_setting info
    print("***ConfigurationLoader Output***")
    for item in illegal_setting_list:
        print(item)
        item_type, name_and_value = item.split("%")
        name, value = name_and_value.split("=")
        if item_type.lower() == "bool":
            print(f"WARNING: Setting name '{name}' value is not legal. Value must be boolean.")
        elif item_type.lower() == "str":
            print(f"WARNING: Setting name '{name}' value is not legal.")
            print("INFO: If you want to use the recommended setting. Please set it to ''")
        elif item_type.lower() == "int":
            print(f"WARNING: Setting name '{name}' value is not legal. Value must be int.")
        elif item_type.lower() == "undefined":
            print(f"WARNING: Setting name '{name}' item type undefined.")
        elif item_type.lower() == "float":
            print(f"WARNING: Setting name '{name}' value is not legal. Value must be float.")
        elif item_type.lower() == "unknown_type":
            print(f"WARNING: Unknown type '{name}'")
        elif item_type.lower() == "illegal_value":
            print(f"WARNING: Setting name '{name}' value has a syntax problem.")
        elif item_type.lower() == "illegal_syntax":
            print(f"WARNING: Setting name '{name}' value has a syntax problem.")
        else:
            print(f"WARNING: Unknown error {name}")
    print(f"Config : {target_object}")
    return True, None