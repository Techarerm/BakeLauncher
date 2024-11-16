import os
import time
import requests
import psutil
import json
from libs.__create_instance import create_instance
from LauncherBase import print_custom as print
from libs.launch_manager import GetGameArgs
from LauncherBase import ClearOutput,timer

CustomGameArgsStatus = False
CustomJVMArgsStatus = True
GameArgsRequireValve = False

def write_config(path, mode, data, OriginalArgs):
    global updated
    updated = False
    config_file_path = os.path.join(path, 'instance.bakelh.cfg')

    def delete_item(data, lines):
        # If user input args is in line, delete it and overwrite
        for i in range(len(lines)):
            if "Delete>" in data:
                delete_item = data.split(">")[1].strip()  # Get the argument after 'Delete>' and strip any extra spaces
                if delete_item.lower() in lines[i].lower().strip():
                    lines[i] = lines[i].replace(delete_item, "").strip()  # Remove and clean up the line
                    updated = True
                    print(f"ArgsManager: Args '{delete_item}' has been deleted!", color='blue')
                    break
        else:
            return False
        return updated

    def add_data(data, lines):
        add_item = ""
        for i in range(len(lines)):
            if "Add>" in data:
                add_item = data.split(">")[1].strip()  # Get the argument after 'Add>' and strip any extra spaces

                # Check if the item is already in the line
                if add_item.lower() in lines[i].lower().strip():
                    print(f"ArgsManager: Args '{add_item}' already exists in line.", color='yellow')
                    print("Failed to append new args to config file! Cause by args already exist in the config.", color='red')
                    time.sleep(2)
                else:
                    lines[i] = lines[i].strip() + " " + add_item  # Add the item to the line with a space
                    updated = True
                    print(f"ArgsManager: Args '{add_item}' has been added!", color='blue')
                    break
        else:
            if add_item:  # Ensure that add_item was actually set
                print(f"ArgsManager: No match found for adding '{add_item}'", color='yellow')
            return False
        return updated


    # Check if the config file exists; if not, create it
    if not os.path.exists(config_file_path):
        print("ArgsManager: Can't find config file! Creating...", color='green')
        default_data = (
            '[BakeLauncher Instance Config]\n\n<Global>\n# Please DO NOT edit this file!\n\nVersion = '
            '\nCustomJVMArgs = \nCustomGameArgs = \n'
        )
        with open(config_file_path, 'w') as config_file:
            config_file.write(default_data)

    # Load lines from the existing config file
    with open(config_file_path, 'r') as config_file:
        lines = config_file.readlines()

    updated = False  # Flag to track if we've updated the args

    # Helper function to check if a similar argument exists
    def check_existing_argument(current_value, data):
        current_args = current_value.split()  # Split by spaces
        new_arg_name = data.split()[0]  # Get the argument name (e.g. --quickPlayMultiplayer)

        # Find and return the full argument (name + parameters)
        for i in range(len(current_args)):
            if current_args[i].startswith(new_arg_name):
                full_arg = ' '.join(current_args[i:i + 2])  # Assuming arguments have a name + one parameter
                return full_arg
        return None

    if mode == "WriteGameArgs":
        # Write game args (also check if the args already exist)
        delete_item(data, lines)  # For Create new game args (Advanced) (If Delete> is in data)
        add_data(data, lines)  # For Create new game args (Advanced) (If Add> is in data)
        found = False  # Track if CustomGameArgs has been found and updated
        updated = False  # Track if the update was successful

        for i in range(len(lines)):
            if 'CustomGameArgs' in lines[i]:
                current_value = lines[i].split('=', 1)[1].strip()  # Get the current args value
                print("Debug:", OriginalArgs)

                # Check if the argument already exists in CustomGameArgs
                if OriginalArgs in current_value:
                    if GameArgsRequireValve:  # If the argument requires valve (overwrite logic)
                        print(f"ArgsManager: Argument '{OriginalArgs}' already exists in CustomGameArgs.",
                              color='yellow')
                        print("Do you want to overwrite the existing argument? [Y/n]")
                        user_input = str(input(":"))
                        if user_input.lower() == "y":
                            # Identify the part after `OriginalArgs` (the "valve" part)
                            args_with_valve = current_value.split(OriginalArgs, 1)[1].strip()

                            # Remove the old argument and valve from the line
                            # This will strip `OriginalArgs` and its associated valve from the line
                            lines[i] = lines[i].replace(f"{OriginalArgs} {args_with_valve.split()[0]}", "").strip()

                            # Append new data (with space management)
                            lines[i] += f" {data.strip()}\n"
                            updated = True
                    else:
                        print(f"ArgsManager: Argument '{OriginalArgs}' already exists in CustomGameArgs.",
                              color='yellow')
                else:
                    # If argument doesn't exist, append it
                    lines[i] = f'CustomGameArgs = {current_value} {data.strip()}\n'  # Append new data
                    updated = True

                found = True  # Mark as found
                break

        # If no entry for CustomGameArgs was found, append the new CustomGameArgs
        if not found:
            lines.append(f'CustomGameArgs = {data.strip()}\n')  # Append new entry if no match was found
            updated = True

        if updated:
            print("ArgsManager: CustomGameArgs successfully updated.")
        else:
            print("ArgsManager: No changes were made to CustomGameArgs.")


    elif mode == "WriteJVMArgs":
        delete_item(data,lines)  # For Custom Args (Advanced) (If Delete> is in data)
        add_data(data, lines)  # For Custom Args (Advanced) (If Add> is in data)
        for i in range(len(lines)):
            if data in lines[i]:
                print(f"ArgsManager: Argument '{data}' already exists in line.", color='yellow')
                break
            elif 'CustomJVMArgs' in lines[i]:
                current_value = lines[i].split('=', 1)[1].strip()  # Get current value and strip whitespace
                new_value = current_value + ' ' + data  # Append new data
                lines[i] = f'CustomJVMArgs = {new_value.strip()}\n'  # Strip extra spaces
                updated = True
                break
        if not updated:
            # If not updated, append the new data
            lines.append(f'CustomJVMArgs = {data.strip()}\n')

    elif mode == "OverWriteJVMArgs":
        for i in range(len(lines)):
            if 'CustomJVMArgs' in lines[i]:
                current_value = lines[i].split('=', 1)[1].strip()  # Get current value and strip whitespace
                lines[i] = f'CustomJVMArgs = {data.strip()}\n'  # Overwrite the line with new data
                break  # Exit loop once found


    else:
        print("ArgsManager: ? Invalid mode!", color='red')
        return

    # Write the updated lines back to the config file
    with open(config_file_path, 'w') as config_file:
        config_file.writelines(lines)

    print("ArgsManager: Configuration updated successfully!", color='blue')



def load_old_config(config_path, item, argsname):
    with open(config_path, 'r') as config_file:
        lines = config_file.readlines()
        for line in lines:
            if item in line:
                item = line.split('=', 1)[1].strip()
                if len(item) > 0:
                    print(f"Found exist {argsname}:\n"
                          f" {item}", color='purple')
                    CustomGameArgsStatus = True

def get_args(version_id):
    """
    Check if the version data includes the -XstartOnFirstThread argument for macOS.
    """

    version_data = create_instance.get_version_data(version_id)

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
        print("ArgsManager: Your Minecraft version are not support custom game args :(", color='red')
        timer(5)

    # Create a list of features with numbers
    for idx, feature in enumerate(feature_dict.keys(), start=1):
        feature_list.append(f"{idx}: {feature}")

    return feature_list, feature_dict


def get_args_by_feature_choice(user_input, feature_dict):
    global GameArgsRequireValve
    try:
        index = int(user_input) - 1
        feature_name = list(feature_dict.keys())[index]  # Get the feature name based on the index

        # Create a copy of the args list to avoid modifying the original feature_dict(Reset after use)
        args = feature_dict[feature_name][:]

        # Check if any of the arguments require user input
        for i, arg in enumerate(args):
            if "${" in arg:  # Placeholder indicates it needs user input
                placeholder = arg
                # Ask the user to provide the necessary text for the placeholder
                user_input_text = input(f"Please provide input for {placeholder}: ")
                GameArgsRequireValve = True
                args[i] = user_input_text  # Replace placeholder with user-provided text

        return args
    except (IndexError, ValueError):
        print("Invalid selection! Please enter a valid number.", color='red')
        return None  # Return None to indicate an invalid choice



def get_instances_path():

    def create_config(path):
        config_path = os.path.join(path, "instance.bakelh.cfg")
        if not os.path.exists(config_path):
            print("ArgsManager: Can't find config file! Creating...", color='green')
            default_data = (
                '[BakeLauncher Instance Config]\n\n<Global>\n# Please DO NOT edit this file!\n\nVersion = '
                '\nCustomJVMArgs = \nCustomGameArgs = \n'
            )
            with open(config_path, 'w') as config_file:
                config_file.write(default_data)
    try:
        instances_list = os.listdir('instances')
        if len(instances_list) == 0:
            print("ArgsManager: No instances are available to modify :(", color='red')
            print("Try to using DownloadTool to download the Minecraft!", color='yellow')
            timer(4)
            return None, None  # Explicitly return None for both values

        print(instances_list, color='blue')
        print("ArgsManager: Which instance do you want to modify?", color='green')

        try:
            version_id = input(":")
            if version_id in instances_list:
                instances_path = os.path.join("instances", str(version_id))
                create_config(instances_path)
                return instances_path, version_id, True
            else:
                print("ArgsManager: Ouch :0 Invalid instance!", color='red')
                timer(2)
                return None, None, None  # Return None if invalid
        except ValueError:
            print("ArgsManager: Ouch :0 Invalid instance type!", color='red')
            timer(2)
            return None, None, None  # Return None if exception occurs
    except FileNotFoundError:
        print("ArgsManager: No instances directory found :(", color='red')
        timer(4)
        return None, None, False  # Return None if directory not found




def get_game_args_and_edit():
    path, version_id, status = get_instances_path()

    while path is None and status is None:
        path, version_id, status = get_instances_path()

    if path is None or version_id is None:
        print("ArgsManager: Failed to get instance path or version ID.", color='red')
        return

    config_path = os.path.join(path, 'instance.bakelh.cfg')
    username = "${username}"
    access_token = "${access_token}"
    gameDir = "${gameDir}"
    assetsIndex = "${assetsIndex}"
    assets_dir = "${assets_dir}"
    uuid = "${uuid}"

    GameArgs = GetGameArgs(version_id, username, access_token, gameDir, assets_dir, assetsIndex, uuid)
    print("Original Game Args Example:", color='purple')
    print(GameArgs, color='green')



    feature_list, feature_dict = get_args(version_id)

    if feature_dict is None or not feature_dict:
        return

    while True:
        load_old_config(config_path, "CustomGameArgs", 'Game Args')
        print("You can add these game args:", color='blue')

        for feature in feature_list:
            print(feature)

        print("You can type 'exit' to go back to the main menu.",color='green')
        user_input = input("Enter the number of the feature you want: ")

        if str(user_input).lower() == "exit":
            return "exit"  # Some weird thing let while loop...

        # Get the corresponding arguments for the chosen feature(also return original args for write_config)
        args = get_args_by_feature_choice(user_input, feature_dict)
        print(args)
        OriginalArgs = args[0]

        if args is not None:
            formatted_args = ' '.join(args)
            print("New args:", formatted_args)
            print("Trying to add custom Game Arguments to config file...", color='green')
            mode = "WriteGameArgs"
            write_config(path, mode, formatted_args, OriginalArgs)
        else:
            print("ArgsManager: No valid arguments to process :(", color='red')

        ClearOutput()


def game_args_editor(mode):
    path, version_id, status = get_instances_path()
    config_path = os.path.join(path, 'instance.bakelh.cfg')
    if mode == "Edit":
        while True:
            load_old_config(config_path, '"CustomGameArgs"', "Game Args")
            print('"GameArgsEditor"', color='purple')
            print(
                "This function is mainly for advanced users. If you are not, please use Generate Args adapted to your computer!",
                color='yellow')
            print("Check wiki to get more information! (https://wiki.vg/Launching_the_game#Game_Arguments)", color='green')
            print("Use Delete>'DeleteArgs' to delete args.")
            print("Use Add>'AddArgs' to add args.")
            print("Type exit to back to main memu!")
            user_input = input(":")
            if user_input.upper() == "EXIT":
                return "exit"
            else:
                write_config(path, "WriteGameArgs", user_input, "")
                return "exit"
    if mode == "Clear":
        print("ArgsManager: Cleaning config file...", color='green')
        with open(config_path, 'r') as config_file:
            lines = config_file.readlines()
            for i in range(len(lines)):
                if "CustomGameArgs" in lines[i]:
                    # Use the new or existing account ID
                    lines[i] = f'CustomGameArgs = '
        with open(config_path, 'w') as file:
            file.writelines(lines)
        print("ArgsManager: Config file has been cleaned :)", color='blue')
        return "exit"






def modify_game_args():
    while True:
        try:
            print("ModifyGameArgs", color='purple')
            print("Options:", color='green')
            print("1: List support args and enter you want", color='blue')
            print("2: Custom Args (Advanced)", color='purple')
            print("3: Clean all Game Args", color='red')
            print("4: Exit")

            user_input = int(input(":"))

            if user_input == 1:
                exit_signal = get_game_args_and_edit()  # Capture the return value from get_game_args_and_edit()
            elif user_input == 2:
                exit_signal = game_args_editor("Edit")
            elif user_input == 3:
                exit_signal = game_args_editor("Clear")
            elif user_input == 4:
                return 'exit'
            else:
                print("ArgsManager: Unknown option :0", color='red')
        except ValueError:
            print("ArgsManager: Unknown input :0", color='red')
            time.sleep(2)



def get_best_jvm_args(path):
    json_url = 'https://github.com/Techarerm/BakeLauncher-Library/raw/refs/heads/main/JVM/JVM_ramConfigurations.json'
    try:
        # Fetch the JSON data from the URL
        response = requests.get(json_url)

        # Check for a successful response
        response.raise_for_status()  # Raise an error for bad responses

        # Load the JSON data
        jvm_configurations = response.json()

        # Get the total memory size and convert bytes to GB
        memory_info = psutil.virtual_memory()
        total_ram_gb = memory_info.total / (1024 ** 3)

        # Only print the integer value if the decimal part is greater than 0.5
        int_total_ram = int(total_ram_gb) + (1 if (total_ram_gb % 1) > 0.5 else 0)

        # Determine the matching configuration based on the total RAM
        if int_total_ram <= 4:
            selected_ram = '4GB'
        elif int_total_ram <= 8:
            selected_ram = '8GB'
        elif int_total_ram <= 16:
            selected_ram = '16GB'
        elif int_total_ram <= 32:
            selected_ram = '32GB'
        else:
            selected_ram = '32GB'  # Default to 32GB for larger systems

        # Get the corresponding JVM arguments
        jvm_args = jvm_configurations["ramConfigurations"].get(selected_ram)

        if jvm_args:
            print(f"Selected RAM Configuration: {selected_ram}", color='blue')
            full_args = ""
            for arg in jvm_args['JVMArgs']:
                full_args += arg + " "
            print(f"Full JVM Arguments: {full_args}]")
            write_config(path, "OverWriteJVMArgs", full_args, "")
            timer(2)
        else:
            print(f"No JVM arguments found for {selected_ram} configuration.")

    except requests.exceptions.RequestException as e:
        print(f"An error occurred while fetching the JSON data: {e}", color='red')
    except json.JSONDecodeError as e:
        print(f"JSON decoding error: {e}", color='red')

def custom_jvm_args(path, mode):
    config_path = os.path.join(path, 'instance.bakelh.cfg')
    if mode == "EditRAMSize":
        load_old_config(config_path, '"CustomJVMArgs"', 'JVM Args')
        print("JVM Ram Size Editor:")
        print("IMPORTANT: Backup your old JVM Args(without memory args)! Is really important if you want to restore your old args.\n"
              "If you enter exceeds the size of your computer's memory, you may get crash when you launch Minecraft!", color='red')
        print("This function is mainly for advanced users. If you are not, please use Generate Args adapted to your computer!", color='yellow')
        print("Also use this method will overwrite your old config. After doing this, you may need to go CustomEdit to paste your old args and restore.", color='yellow')
        while True:
            try:
                Xmx = int(input("Sets the maximum RAM:"))
                Xms = int(input("Sets the initial RAM:"))
                RAMSize = f"-Xmx{str(Xmx)}G -Xms{str(Xms)}G"
                write_config(path, "OverWriteJVMArgs", RAMSize, '')
                return
            except ValueError:
                print("ArgsManager: Unknown input :0", color='red')
                timer(2)
    elif mode == "CustomEdit":
        load_old_config(config_path, "CustomJVMArgs", 'JVM Args')
        print("This function is mainly for advanced users."
              " If you are not, please use Generate Args adapted to your computer!",color='yellow')
        print("Check GitHub 'BakeLauncher-Library' to get more information!"
              " (https://github.com/Techarerm/BakeLauncher-Library/blob/main/JVM/JVM_Args_List.json)", color='green')
        print("Use Delete>'DeleteArgs' to delete args.")
        print("Use Add>'AddArgs' to add args.")
        print("Type exit to back to main memu!")
        user_input = input(":")
        if user_input.upper() == "EXIT":
            return
        else:
            write_config(path, "WriteJVMArgs", user_input, '')

    if mode == "Clear":
        print("ArgsManager: Cleaning config file...", color='green')
        with open(config_path, 'r') as config_file:
            lines = config_file.readlines()
            for i in range(len(lines)):
                if "CustomJVMArgs" in lines[i]:
                    # Use the new or existing account ID
                    lines[i] = f'CustomJVMArgs = ""'
        with open(config_path, 'w') as file:
            file.writelines(lines)
        print("ArgsManager: Config file has been cleaned :)", color='blue')
    return "exit"


def modify_jvm_args():
    path, version_id, status = get_instances_path()

    # Keep asking for the path until it's found (first while loop)
    while path is None and status is None:
        path, version_id, status = get_instances_path()

    if path is None or version_id is None:
        print("ArgsManager: Failed to get instance path or version ID.", color='red')
        return

    # Start the second while loop for continuous input
    while True:
        ClearOutput()
        print("ModifyJVMArgs", color='purple')
        print("1: Edit JVM Allocation RAM Size (Advanced)", color='green')
        print("2: Custom Args (Advanced)", color='purple')
        print("3: Generate Args adapted to your computer", color='blue')
        print("4: Clear JVM Config file", color='red')
        print("5: Exit")  # Option to exit the loop

        try:
            user_input = int(input(":"))

            if user_input == 1:
                exit_signal = custom_jvm_args(path, "EditRAMSize")
            elif user_input == 2:
                exit_signal = custom_jvm_args(path, "CustomEdit")
            elif user_input == 3:
                exit_signal = get_best_jvm_args(path)
            elif user_input == 4:
                exit_signal = custom_jvm_args(path, "Clear")
            elif user_input == 5:
                print("Exiting JVM Args modification...", color='yellow')
                return "exit"
            else:
                print("ArgsManager: Unknown option :0", color='red')

            time.sleep(1)  # Short delay before showing the menu again

        except ValueError:
            print("ArgsManager: Invalid input. Please enter a number.", color='red')
            time.sleep(1)


def argsman():
    exit_program = False
    ClearOutput()
    print("[ArgsManager]", color='magenta')
    print("1: Modify Game Args 2: Modify JVM Args 3: Exit Modify Args")

    while True:
        try:
            user_input = int(input(":"))
            if user_input == 1:
                exit_signal = modify_game_args()  # Capture the return value from modify_game_args()
                if exit_signal == "exit":
                    return  # Exit the entire flow if the exit signal is received
            elif user_input == 2:
                exit_signal = modify_jvm_args()
                if exit_signal == "exit":
                    return  # Exit the entire flow if the exit signal is received
            elif user_input == 3:
                return  # Exit the program or menu
            else:
                print("ArgsManager: Unknown option :0", color='red')
        except ValueError:
            print("ArgsManager: Unknown type :0", color='red')