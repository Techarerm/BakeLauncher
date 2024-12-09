import os
import time
import requests
import psutil
import json
from LauncherBase import print_custom as print, ClearOutput
from libs.__instance_manager import instance_manager
from libs.launch_manager import launch_manager
from libs.Utils.utils import get_version_data


class ArgsManager:
    def __init__(self):
        self.updated = False
        self.GameArgsRequireValve = False

    def write_config(self, instance_path, mode, data, OriginalArgs):
        """
        Updates or manages a configuration file with game or JVM arguments.

        Args:
            instance_path (str): Path to the instance folder.
            mode (str): Mode for configuration operation (e.g., "WriteGameArgs", "WriteJVMArgs").
            data (str): Data to add, remove, or overwrite in the configuration.
            OriginalArgs (str): Original arguments used for reference.
        """
        config_file_path = os.path.join(instance_path, 'instance.bakelh.cfg')

        def delete_item(data, lines):
            """Deletes an item from the configuration if specified in `data`."""
            for i, line in enumerate(lines):
                if "Delete>" in data:
                    delete_item = data.split(">")[1].strip()
                    if delete_item.lower() in line.lower():
                        lines[i] = line.replace(delete_item, "").strip()
                        self.updated = True
                        print(f"Argument '{delete_item}' has been deleted!")
                        break
            else:
                return False
            return self.updated

        def add_data(data, lines):
            """Adds an item to the configuration if it does not already exist."""
            for i, line in enumerate(lines):
                if "Add>" in data:
                    add_item = data.split("Add>")[1].strip()
                    if add_item.lower() in line.lower():
                        print(f"Argument '{add_item}' already exists.")
                        return False
                    else:
                        lines[i] = line.strip() + " " + add_item
                        self.updated = True
                        print(f"Argument '{add_item}' has been added!")
                        break
            return self.updated

        # Ensure the config file exists
        if not os.path.exists(config_file_path):
            instance_manager.create_custom_config(config_file_path)

        # Load lines from the existing config file
        with open(config_file_path, 'r') as config_file:
            lines = config_file.readlines()

        self.updated = False

        def check_existing_argument(current_value, data):
            """Checks if a similar argument already exists."""
            current_args = current_value.split()
            new_arg_name = data.split()[0]
            for i, arg in enumerate(current_args):
                if arg.startswith(new_arg_name):
                    return ' '.join(current_args[i:i + 2])
            return None

        if mode == "WriteGameArgs":
            delete_item(data, lines)
            add_data(data, lines)

            for i, line in enumerate(lines):
                if 'CustomGameArgs' in line:
                    current_value = line.split('=', 1)[1].strip()
                    if OriginalArgs in current_value:
                        if self.GameArgsRequireValve:
                            print(f"Argument '{OriginalArgs}' already exists. Overwriting...")
                            args_with_valve = current_value.split(OriginalArgs, 1)[1].strip()
                            lines[i] = line.replace(f"{OriginalArgs} {args_with_valve.split()[0]}", "").strip()
                            lines[i] += f" {data.strip()}\n"
                            self.updated = True
                        else:
                            print(f"Argument '{OriginalArgs}' already exists. Skipping.")
                    else:
                        lines[i] = f'CustomGameArgs = {current_value} {data.strip()}\n'
                        self.updated = True
                    break
            else:
                lines.append(f'CustomGameArgs = {data.strip()}\n')
                self.updated = True

        elif mode == "WriteJVMArgs":
            delete_item(data, lines)
            add_data(data, lines)
            for i, line in enumerate(lines):
                if 'CustomJVMArgs' in line:
                    current_value = line.split('=', 1)[1].strip()
                    new_value = f"{current_value} {data.strip()}"
                    lines[i] = f'CustomJVMArgs = {new_value.strip()}\n'
                    self.updated = True
                    break
            if not self.updated:
                lines.append(f'CustomJVMArgs = {data.strip()}\n')

        elif mode == "OverWriteJVMArgs":
            for i, line in enumerate(lines):
                if 'CustomJVMArgs' in line:
                    lines[i] = f'CustomJVMArgs = {data.strip()}\n'
                    self.updated = True
                    break

        else:
            print("Invalid mode!")
            return

        # Write the updated lines back to the config file
        with open(config_file_path, 'w') as config_file:
            config_file.writelines(lines)

        print("Configuration updated successfully!")

    def get_best_jvm_args(self, instance_path):
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
                self.write_config(instance_path, "OverWriteJVMArgs", full_args, "")
                time.sleep(2)
            else:
                print(f"No JVM arguments found for {selected_ram} configuration.")

        except requests.exceptions.RequestException as e:
            print(f"An error occurred while fetching the JSON data: {e}", color='red')
        except json.JSONDecodeError as e:
            print(f"JSON decoding error: {e}", color='red')

    def custom_jvm_args(self, modify_instance_path, mode):
        config_path = os.path.join(modify_instance_path, 'instance.bakelh.cfg')
        instance_manager.load_custom_config(config_path, '"CustomJVMArgs"', 'JVM Args')
        if mode == "EditRAMSize":
            print("JVM Ram Size Editor:")
            print("IMPORTANT: Backup your old JVM Args! Is really important if you want to restore your old args.\n")
            print("If you enter exceeds the size of your computer's memory, you may get crash when you launch "
                  "Minecraft!", color='red')
            print("This function is mainly for advanced users.]"
                  " If you are not, please use Generate Args adapted to your computer!", color='yellow')
            print("Also use this method will overwrite your old config."
                  " After doing this, you may need to go CustomEdit to paste your old args and restore.",
                  color='yellow')

            while True:
                try:
                    Xmx = int(input("Sets the maximum RAM:"))
                    Xms = int(input("Sets the initial RAM:"))
                    RAMSize = f"-Xmx{str(Xmx)}G -Xms{str(Xms)}G"
                    self.write_config(modify_instance_path, "OverWriteJVMArgs", RAMSize, '')
                    return True
                except ValueError:
                    print("Unknown input :0", color='red')
                    time.sleep(2)

        elif mode == "CustomEdit":
            print("This function is mainly for advanced users."
                  " If you are not, please use Generate Args adapted to your computer!", color='yellow')
            print("Check GitHub 'BakeLauncher-Library' to get more information!"
                  " (https://github.com/Techarerm/BakeLauncher-Library/blob/main/JVM/JVM_Args_List.json)",
                  color='green')
            while True:
                print("[JVM Args Edit Mode]", color='blue')
                print("Use Delete>'DeleteArgs' to delete args.")
                print("Use Add>'AddArgs' to add args.")
                print("Type exit to back to main memu!")
                user_input = input(":")
                if user_input.upper() == "EXIT":
                    return
                else:
                    self. write_config(modify_instance_path, "WriteJVMArgs", user_input, '\n')

        if mode == "Clear":
            print("Cleaning config file...", color='green')
            with open(config_path, 'r') as config_file:
                lines = config_file.readlines()
                for i in range(len(lines)):
                    if "CustomJVMArgs" in lines[i]:
                        # Use the new or existing account ID
                        lines[i] = f'CustomJVMArgs = \n'
            with open(config_path, 'w') as file:
                file.writelines(lines)
            print("Config file has been cleaned :)", color='blue')
        return "exit"

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
            print("Your Minecraft version are not support custom game args :(", color='red')
            time.sleep(5)

        # Create a list of features with numbers
        for idx, feature in enumerate(feature_dict.keys(), start=1):
            feature_list.append(f"{idx}: {feature}")

        return feature_list, feature_dict


    def get_game_args_by_feature_choice(self, selected_args_number, feature_dict):
        global GameArgsRequireValve
        try:
            index = int(selected_args_number) - 1
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

    def get_game_args_and_edit(self):
        Status, client_version, instance_path = instance_manager.select_instance("Which instance you want to modify?"
                                                                                 , client_version=True)
        if instance_path is None:
            print("No instance selected.", color='red')
            return

        config_path = os.path.join(instance_path, 'instance.bakelh.cfg')
        username = "${username}"
        access_token = "${access_token}"
        gameDir = "${gameDir}"
        assetsIndex = "${assetsIndex}"
        assets_dir = "${assets_dir}"
        uuid = "${uuid}"

        GameArgs = launch_manager.generate_game_args(client_version, username, access_token, gameDir, assets_dir, assetsIndex, uuid)
        print("Original Game Args Example:", color='purple')
        print(GameArgs, color='green')

        feature_list, feature_dict = self.get_support_game_args(client_version)

        if feature_dict is None or not feature_dict:
            return

        while True:
            instance_manager.load_custom_config(config_path, "CustomGameArgs", 'Game Args')
            print("You can add these game args:", color='blue')

            for feature in feature_list:
                print(feature)

            print("You can type 'exit' to go back to the main menu.", color='green')
            user_input = input("Enter the number of the feature you want: ")

            if str(user_input).lower() == "exit":
                return "exit"  # Some weird thing let while loop...

            # Get the corresponding arguments for the chosen feature(also return original args for write_config)
            args = self.get_game_args_by_feature_choice(user_input, feature_dict)
            OriginalArgs = args[0]

            if args is not None:
                formatted_args = ' '.join(args)
                print("New args:", formatted_args)
                print("Trying to add custom Game Arguments to config file...", color='green')
                mode = "WriteGameArgs"
                self.write_config(instance_path, mode, formatted_args, OriginalArgs)
            else:
                print("No valid arguments to process :(", color='red')

            ClearOutput()

    def game_args_editor(self, mode):
        Status, client_version, instance_path = instance_manager.select_instance("Which instance you want to modify?"
                                                                                 , client_version=True)
        if instance_path is None:
            print("No instance selected.", color='red')
            return

        config_path = os.path.join(instance_path, 'instance.bakelh.cfg')
        if mode == "Edit":
            while True:
                instance_manager.load_custom_config(config_path, '"CustomGameArgs"', "Game Args")
                print('"GameArgsEditor"', color='purple')
                print(
                    "This function is mainly for advanced users."
                    " If you are not, please use Generate Args adapted to your computer!",
                    color='yellow')
                print("Check wiki to get more information! (https://wiki.vg/Launching_the_game#Game_Arguments)",
                      color='green')
                print("Use Delete>'DeleteArgs' to delete args.")
                print("Use Add>'AddArgs' to add args.")
                print("Type exit to back to main memu!")
                user_input = input(":")
                if user_input.upper() == "EXIT":
                    return True

                self.write_config(instance_path, "WriteGameArgs", user_input, "")

        elif mode == "Clear":
            print("Cleaning config file...", color='green')
            if not os.path.exists(config_path):
                print("Config file does not exist!", color='red')
                time.sleep(2)
                return

            with open(config_path, 'r') as config_file:
                lines = config_file.readlines()
                for i in range(len(lines)):
                    if "CustomGameArgs" in lines[i]:
                        # Use the new or existing account ID
                        lines[i] = f'CustomGameArgs = '
            with open(config_path, 'w') as file:
                file.writelines(lines)
            print("Config file has been cleaned :)", color='blue')

    def modify_game_args(self):
        while True:
            print("ModifyGameArgs", color='purple')
            print("Options:", color='green')
            print("1: List support args and enter you want", color='blue')
            print("2: Custom Args (Advanced)", color='purple')
            print("3: Clean all Game Args", color='red')
            print("4: Exit")

            user_input = int(input(":"))

            if user_input == 1:
                self.get_game_args_and_edit()  # Capture the return value from get_game_args_and_edit()
            elif user_input == 2:
                self.game_args_editor("Edit")
            elif user_input == 3:
                self.game_args_editor("Clear")
            elif user_input == 4:
                return True
            else:
                print("Unknown option :0", color='red')
    def modify_jvm_args(self):
        Status, client_version, instance_path = instance_manager.select_instance("Which instance you want to modify?"
                                                                                 , client_version=True)
        if instance_path is None:
            print("No instance selected.", color='red')
            return

        while True:
            ClearOutput()
            print("ModifyJVMArgs", color='purple')
            print("1: Edit JVM Allocation RAM Size (Advanced)", color='green')
            print("2: Custom Args (Advanced)", color='purple')
            print("3: Generate Args adapted to your computer", color='blue')
            print("4: Clear JVM Config file", color='red')
            print("5: Exit")  # Option to exit the loop

            user_input = str(input(":"))

            if user_input == "1":
                self.custom_jvm_args(instance_path, "EditRAMSize")
            elif user_input == "2":
                self.custom_jvm_args(instance_path, "CustomEdit")
            elif user_input == "3":
                self.get_best_jvm_args(instance_path)
            elif user_input == "4":
                self.custom_jvm_args(instance_path, "Clear")
            elif user_input == "5":
                print("Exiting JVM Args modification...", color='yellow')
                return True
            else:
                print("Unknown option :0", color='red')

    def ArgsMemu(self):
        print("[ArgsManager]", color='magenta')
        print("1: Modify Game Args 2: Modify JVM Args 3: Exit")

        try:
            user_input = str(input(":"))
            if user_input == "1":
                self.modify_game_args()
            elif user_input == "2":
                self.modify_jvm_args()
            elif user_input == "3" or user_input.upper() == "EXIT":
                return
            else:
                print("ArgsManager: Unknown option :0", color='red')
        except ValueError:
            print("ArgsManager: Unknown type :0", color='red')


args_manager = ArgsManager()