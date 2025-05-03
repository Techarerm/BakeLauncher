"""
BakeLauncher Main Menu
(Main menu has been separated from main since Beta 0.7(Pre-HG30824)
"""
import os
import traceback
import time
from LauncherBase import bake_bake, internal_functions_error_log_dump, Base
from functools import partial
from launcher.cli.__account_manager import account_manager
from launcher.cli.launch_manager import launch_manager
from launcher.cli.__create_instance import create_instance
from launcher.cli.__duke_explorer import Duke
from launcher.cli.__instance_manager import instance_manager
from launcher.cli.__args_manager import args_manager
from launcher.cli.display_util.util import print_color as print, clear
from libs.Utils.config import config_loader


class mainMenu:
    def __init__(self):
        # Flag
        self.ResetMainMenu = False
        self.StopReloadMainMenu = False
        self.OptionNotFound = True

        # Modify!
        self.PrintCustomMenu = False

        # Limit
        self.max_character_in_one_line = 50

        # :) (Change it to you want!)
        self.input_symbol = ":"
        self.input_symbol_color = 'white'

        # Launcher Info
        self.menuTitle = "BakeLauncher Main Menu"
        self.launcher_version_info = f"Version : {Base.launcher_version}"
        self.ask_for_option_message = "What would you like to do?"

        # ErrorMessage Stuff
        self.no_error_message_output = False
        self.error_message_list = []
        self.error_message_output_time = 0

        # Style
        self.horizontal_display_options = True

        # options MAPPINGS (Option key must be lowercase)
        self.options_mappings_dict = {
            "1": ["Launch Minecraft", launch_manager.prepare_ask_for_instance],
            "2": ["Manage Accounts", account_manager.AccountManager],
            "3": ["Create Instance", create_instance.create_instance],
            "4": ["Manage Instances", instance_manager.ManagerMenu],
            "5": ["About", bake_bake],
            "6": ["Extra", self.extraMain],
            "7": ["Exit the launcher", self.exit_the_menu],
            "quicklaunch": [None, partial(launch_manager.quick_launch)],
            "qk": [None, partial(launch_manager.quick_launch)],
        }

        self.extra_options_mappings_dict = {
            "1": ["ArgsManager", args_manager.ManagerMenu],
            "2": ["Clear ErrorMessage", self.clear_error_message],
            "3": ["DukeExplorer", Duke.ManagerMenu],
        }

        # custom stuff
        self.no_options_print = False
        self.automatic_open_specified_options = False
        self.automatic_open_target_option_name = None  # Select option
        self.title_color = "lightblue"
        self.load_account_status = True
        self.automatic_launch_game = False

        self.setting_dict = {
            "BOOL%NoOptionsPrint": "no_options_print",
            "BOOL%AutomaticOpenSpecifiedOptions": "automatic_open_specified_options",
            "STR%AutomaticOpenTargetOptionName": "automatic_open_target_option_name",
            "STR%MainMenuTitleColor": "title_color",
            "BOOL%LoadAccountStatus": "load_account_status",
            "BOOL%HorizontalDisplayOptions": "horizontal_display_options",
            "BOOL%AutomaticLaunchGame": "automatic_launch_game"
        }

        self.load_config()

    def print_memu(self, target_options_dict, print_message=True):
        if print_message:
            print(self.ask_for_option_message)

        if self.horizontal_display_options:
            memu_lines = []
            current_line = ""

            for index, option in enumerate(target_options_dict.keys()):
                value = target_options_dict[option]
                option_info = value[0]
                if not option_info is None:
                    pair = f"{option}: {option_info}  "

                    if len(current_line) + len(pair) > self.max_character_in_one_line:
                        memu_lines.append(current_line)
                        current_line = pair
                    else:
                        current_line += pair

            if current_line:
                memu_lines.append(current_line)

            for line in memu_lines:
                print(line)
        else:
            for index, option in enumerate(target_options_dict.keys()):
                value = target_options_dict[option]
                option_info = value[0]
                if not option_info is None:
                    print(f"{option}: {option_info}")

    def exit_the_menu(self):
        print("Exiting launcher...", color='lightyellow')
        self.StopReloadMainMenu = True
        for child_thread in Base.DaemonPool:
            child_thread.cleanup()
        return True

    def menuMain(self):
        if self.automatic_launch_game:
            launch_manager.quick_launch()

        option = self.automatic_open_target_option_name if self.automatic_open_specified_options else None

        while not self.StopReloadMainMenu:
            clear()
            self.load_config()

            # Print title and info
            print(self.menuTitle, color=self.title_color)
            print(self.launcher_version_info, color='lightblue')

            # Load account status
            if self.load_account_status:
                account_manager.login_status()

            if self.ResetMainMenu:
                self.ResetMainMenu = False
                continue

            # Print menu
            if not self.no_options_print:
                self.print_memu(self.options_mappings_dict)

            if option is None:
                print(f"{self.input_symbol}", end='', color=self.input_symbol_color)
                option = str(input(f" "))

            Status, specified_function = self.mapping_input_to_options(option, options_dict=self.options_mappings_dict)
            if Status:
                if callable(specified_function):
                    message = specified_function()
                    self.append_return_message(message)
                else:
                    print(f"Option name '{option}' mappings function is not callable :/", color='lightred')
                    time.sleep(3)
            else:
                print(f"Option {option} not found :/", color='lightred')
                time.sleep(2)

            # restore environment
            os.chdir(Base.launcher_root_dir)
            option = None

    def extraMain(self):
        self.print_memu(self.extra_options_mappings_dict, print_message=False)

        print(f"{self.input_symbol}", end='', color=self.input_symbol_color)
        option = str(input(f" "))

        if option.lower() == "exit":
            return

        Status, specified_function = self.mapping_input_to_options(option, options_dict=self.extra_options_mappings_dict)

        if Status:
            if callable(specified_function):
                message = specified_function()
                self.append_return_message(message)
            else:
                print(f"Option name '{option}' mappings function is not callable :/", color='lightred')
        else:
            print(f"Option {option} not found :/", color='lightred')
            time.sleep(2)

        return

    def load_config(self):
        config_loader(self, self.setting_dict, Base.global_config_path)

    @staticmethod
    def mapping_input_to_options(input_option, options_dict):
        try:
            input_option = input_option.lower()
        except Exception as e:
            return False, None

        if input_option in options_dict:
            specified_function_info = options_dict[input_option]
            specified_function = specified_function_info[1]
            if Base.Debug:
                print(f"[Debug] Mapping option {input_option} to function {specified_function}")

            if specified_function_info is not None:
                return True, specified_function
            else:
                return False, None
        else:
            return False, None

    def register_new_option_to_memu(self, option_name, target_function):
        available_options_length = len(self.options_mappings_dict)
        index = available_options_length + 1

        self.options_mappings_dict[str(index)] = [option_name, target_function]

    def register_new_option_to_extra_memu(self, option_name, target_function):
        available_options_length = len(self.extra_options_mappings_dict)
        index = available_options_length + 1

        self.options_mappings_dict[str(index)] = [option_name, target_function]

    def get_length_of_the_options(self):
        return len(self.options_mappings_dict)

    def get_length_of_the_extra_options(self):
        return len(self.extra_options_mappings_dict)

    """
        def enter_playground(self):
        n = 1
        for function_name in all_funs:
            print(f"{n}: {function_name}")
            n += 1

        try:
            input_stuff = int(input("Which function you want to 'play' ?"))

            number = int(input_stuff) - 1

            function_name = all_funs[number]

            function_to_call = globals().get(function_name)  # Resolve function
            if callable(function_to_call):
                function_to_call()

        except Exception as e:
            print(f"Oops {e} :P", color='lightyellow')
            print("Dumping error log...", color='lightyellow')
            function_name = traceback.extract_tb(e.__traceback__)[-1].name
            detailed_traceback = traceback.format_exc()
            internal_functions_error_log_dump(e, "Playground", function_name, detailed_traceback)
            time.sleep(3)
    """

    def append_return_message(self, message):
        error_message = ""
        if list == type(message):
            Status = message[0]
            if not Status:
                try:
                    error_message = message[1]
                except IndexError:
                    error_message = ''
        elif str == type(message):
            error_message = message

        if not error_message is None:
            if not len(error_message) > 0:
                return
        else:
            return

        if self.error_message_output_time > 3:
            self.error_message_list.clear()
            self.error_message_output_time = 0

        self.error_message_list.append(error_message)

    def clear_error_message(self):
        print("Clearing error message...", color='lightgreen')
        self.error_message_list.clear()
        print("Error message has been cleared.", color='lightblue')
        time.sleep(3)
        return


main_menu = mainMenu()