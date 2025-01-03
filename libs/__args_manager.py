import os
import time
import traceback
from libs.instance.instance import instance
from libs.Utils.utils import get_version_data
from libs.arguments.arguments import arguments
from libs.launch_manager import launch_manager
from libs.__instance_manager import instance_manager
from LauncherBase import print_custom as print, ClearOutput, internal_functions_error_log_dump


class ArgsManager:
    def __init__(self):
        self.updated = False
        self.GameArgsRequireValve = False

    def select_modify_instance(self, message):
        print(message, color='green')
        status, client_version, instance_path = instance_manager.select_instance(
            "Which instance is you want to modify?", client_version=True)
        if not instance_path:
            print("Could not get instance path. Exiting...", color='yellow')
            time.sleep(2)
            return instance_path, None, None

        instance_custom_config = os.path.join(instance_path, "instance.bakelh.cfg")
        if not os.path.exists(instance_path):
            instance.create_custom_config(instance_custom_config)
        return instance_path, instance_custom_config, client_version

    def args_editor(self):
        instance_path, instance_custom_config, client_version = self.select_modify_instance(
            "ArgsManager requires an instance to modify.")

        if not instance_path:
            return

        # Mode selection
        while True:
            print("Which mode do you want to use?", color='green')
            print("1: Edit Game Args")
            print("2: Edit JVM Args")
            user_input = input(": ").strip()
            if user_input == "1":
                mode = "CustomGameArgs"
                break
            elif user_input == "2":
                mode = "CustomJVMArgs"
                break
            else:
                print("Unknown mode :O", color='red')

        if not os.path.exists(instance_custom_config):
            instance.create_custom_config(instance_custom_config)
        else:
            status = instance.check_custom_config_valid(instance_custom_config)
            if not status:
                print("Custom config validation failed. Recreating it...", color='yellow')
                instance.create_custom_config(instance_custom_config, overwrite=True)

        # Editing menu
        while True:
            ClearOutput()
            exist_data = instance.read_custom_config(instance_custom_config, mode)
            if exist_data:
                print(f"Existing Custom config data for {mode}", color='lightgreen')
                print("Existing data:", exist_data, color='lightblue')
            print("Commands:")
            print('Add>"NewArgs" : Append new arguments', color='lightblue')
            print('W>"NewArgs" : Overwrite arguments', color='purple')
            print('CleanUP : Clear all arguments', color='red')
            print('Type "exit" to exit the editor', color='lightgreen')

            user_input = input(": ").strip()
            if user_input.lower() == "exit":
                print("Exiting...")
                return True
            elif user_input.startswith("Add>"):
                data = user_input.split("Add>")[1].strip()
                arguments.write_args(instance_custom_config, mode, data, "append")
                print(f"Arguments {data} has been saved to custom config :)", color='blue')
            elif user_input.startswith("W>"):
                data = user_input.split("W>")[1].strip()
                arguments.write_args(instance_custom_config, mode, data, "overwrite")
                print(f"Arguments {data} has been saved to custom config :)", color='blue')
            elif user_input.lower() == "cleanup":
                arguments.write_args(instance_custom_config, mode, "", "overwrite", CleanUP=True)
                print(f"{mode} data has been cleaned :)", color='blue')
            else:
                print("Unknown command. Try again.", color='red')

    def set_jvm_usage_ram_size(self, instance_custom_config, client_version):
        while True:
            try:
                print("This method will set required launch arguments for JVM RAM usage.", color='lightyellow')

                # Get and validate maximum RAM
                Xmx = int(input("Set the maximum RAM (GB): ").strip())
                if Xmx <= 0:
                    print("Maximum RAM must be greater than 0. Please try again.", color='red')
                    continue

                # Get and validate initial RAM
                Xms = int(input("Set the initial RAM (GB): ").strip())
                if Xms <= 0:
                    print("Initial RAM must be greater than 0. Please try again.", color='red')
                    continue
                if Xms > Xmx:
                    print("Initial RAM cannot be greater than maximum RAM. Please try again.", color='red')
                    continue

                # Prepare arguments
                RAMSize = f"-Xmx{Xmx}G -Xms{Xms}G"
                JVMArgs = launch_manager.generate_jvm_args(client_version, without_ram_args=True)
                FullArgs = f"{RAMSize} {JVMArgs}"

                # Display generated arguments and confirm with user
                print(f"Generated JVM arguments: {FullArgs}", color='blue')

                # Check custom config file status
                if not os.path.exists(instance_custom_config):
                    instance.create_custom_config(instance_custom_config)

                # Write arguments and display the result
                arguments.write_args(instance_custom_config, "CustomJVMArgs", FullArgs, "overwrite")
                data = instance.read_custom_config(instance_custom_config, "CustomJVMArgs")
                print(f"New JVM arguments: {data}", color='green')
                print("JVM RAM arguments set successfully!", color='blue')
                time.sleep(3)
                return True

            except ValueError:
                print("Invalid input. Please enter a valid integer for RAM size.", color='red')
            except Exception as e:
                print(f"An unexpected error occurred: {e}", color='red')
                return False

    def custom_jvm_args_menu(self):
        instance_path, instance_custom_config, client_version = self.select_modify_instance(
            "Modify JVM arguments requires an instance to modify.")

        if not instance_path:
            return

        while True:
            print("List:")
            print("1: Setting JVM usage ram size.", color='lightgreen')
            print("2: Get recommend JVM arguments.", color='lightblue')
            print("3: Clear JVM Config file", color='lightred')

            user_input = str(input(":"))

            if user_input.lower() == "exit":
                return True
            elif user_input == "1":
                self.set_jvm_usage_ram_size(instance_custom_config, client_version)
            elif user_input == "2":
                arguments.get_recommend_jvm_args(instance_custom_config)
            elif user_input == "3":
                arguments.write_args(instance_custom_config, "CustomJVMArgs", "", "overwrite")
            else:
                print(f"Unknown option {user_input} :O", color='red')
            break

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

    def get_game_args_and_edit(self, client_version, config_path, instance_path):
        username = "${username}"
        access_token = "${access_token}"
        gameDir = "${gameDir}"
        assetsIndex = "${assetsIndex}"
        assets_dir = "${assets_dir}"
        uuid = "${uuid}"

        GameArgs = launch_manager.generate_game_args(client_version, username, access_token, gameDir, assets_dir,
                                                     assetsIndex, uuid, instance_path)
        print("Original Game Args Example:", color='purple')
        print(GameArgs, color='green')

        feature_list, feature_dict = arguments.get_support_game_args(client_version)
        if not feature_list:
            print("Your Minecraft version are not support custom game args :(", color='red')
            time.sleep(5)
            return False

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
                return True

            # Get the corresponding arguments for the chosen feature(also return original args for write_config)
            args = self.get_game_args_by_feature_choice(user_input, feature_dict)

            if args is not None:
                formatted_args = ' '.join(args)
                print("New args:", formatted_args)
                print("Trying to add custom game args to config file...", color='green')
                arguments.write_args(config_path, "CustomGameArgs", formatted_args, "append")
                print(f"Game args {formatted_args} has been added to config file :)", color='blue')
                time.sleep(2)
            else:
                print("No valid arguments to process :(", color='red')

            ClearOutput()

    def custom_game_args_menu(self):
        instance_path, instance_custom_config, client_version = self.select_modify_instance(
            "Modify game arguments requires an instance to modify.")

        if not instance_path:
            return

        while True:
            print("Options list:", color='green')
            print("1: List support args and enter you want", color='blue')
            print("2: Clean game args", color='red')
            print("# Type 'exit' to exit the menu", color='orange')

            user_input = str(input(":"))

            if user_input == "1":
                self.get_game_args_and_edit(client_version,
                                            instance_custom_config,
                                            instance_path)  # Capture the return value from get_game_args_and_edit()
            elif user_input == "2":
                print("Cleaning...", color='green')
                arguments.write_args(instance_custom_config, "CustomGameArgs", "", "overwrite")
                print(f"Game args has been cleaned.", color='blue')
                time.sleep(2)
            elif user_input.lower() == "exit":
                print("Exiting...", color='green')
                return True
            else:
                print("Unknown option :0", color='red')

    def ManagerMenu(self):
        global user_input
        print("ArgsManager:", color='indigo')
        try:
            print("1: Custom JVM Args")
            print("2: Custom Game Args")
            print("3: Custom Args (Advanced User)")
            print("# Type 'exit' to exit the menu", color='orange')
            user_input = str(input(":"))

            if user_input == "1":
                self.custom_jvm_args_menu()
            elif user_input == "2":
                self.custom_game_args_menu()
            elif user_input == "3":
                self.args_editor()
            elif user_input.lower() == "exit":
                print("Exiting...", color='green')
                return True
            else:
                print(f"Invalid input {user_input}", color='red')
                time.sleep(1)
                self.ManagerMenu()

        except Exception as e:
            print(f"ArgsManager got a error when calling a internal functions.", color='red')
            print(f"Error output it crash internal function: {e}")
            function_name = traceback.extract_tb(e.__traceback__)[-1].name
            detailed_traceback = traceback.format_exc()
            internal_functions_error_log_dump(e, "ArgsManager", function_name, detailed_traceback)
            time.sleep(5)


args_manager = ArgsManager()
