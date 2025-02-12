"""
BakeLauncher Main Menu
(Main menu has been separated from main since Beta 0.7(Pre-HG30824)
"""

import traceback
from functools import partial
from libs.__account_manager import account_manager
from LauncherBase import *
from libs.launch_manager import launch_manager
from libs.__create_instance import create_instance
from libs.__duke_explorer import Duke
from libs.__instance_manager import instance_manager
from libs.__args_manager import args_manager
from libs.development.playground import *

ErrorMessageList = []
ErrorMessageOutputRange = 0
StopAutomaticProcess = False


class mainMenu:
    def __init__(self):
        # Flag
        self.ResetMainMenu = False
        self.StopReloadMainMenu = False
        self.OptionNotFound = True

        # Modify!
        self.PrintCustomMenu = []
        self.CustomOptions = []
        self.extra_custom_options = []

        # Limit
        self.max_character_in_one_line = 45

        # :) (Change it to you want!)
        self.input_symbol = ":"
        self.input_symbol_color = 'white'

        # Launcher Info
        self.menuTitle = "BakeLauncher Main Menu"
        self.launcher_version_info = f"Version : {Base.launcher_version_display}"

        # ErrorMessage Stuff
        self.no_error_message_output = False
        self.error_message_list = []
        self.error_message_output_time = 0

        # options MAPPINGS (Option key must be lowercase)
        self.options_mappings_dict = {
            "1": launch_manager.launch_game,
            "2": account_manager.AccountManager,
            "3": create_instance.create_instance,
            "4": instance_manager.ManagerMenu,
            "5": self.extraMain,
            "6": bake_bake,
            "exit": self.exit_the_menu,
            "playground" or "pg": self.enter_playground,
            "quicklaunch" or "qk": partial(launch_manager.launch_game, QuickLaunch=True)
        }

        self.extra_options_mappings_dict = {
            "1": args_manager.ManagerMenu,
            "2": self.clear_error_message,
            "3": Duke.ManagerMenu,
        }


    def menu(self):
        print("What would you like to do?")
        print("1. Launch Minecraft 2. AccountManager 3: Create Instance")
        print("4: Manage Instance 5: Extra Menu 6: About (Also Console)")

    def extra_menu(self):
        print("Extra list:", color='lightblue')
        print("1: [Exp]Custom Args")
        print("2: Clear ErrorMessage")
        print("3: DukeExplorer")

    def exit_the_menu(self):
        print("Exiting launcher...", color='lightyellow')
        # ???
        if Base.ChristmasPoint:
            print("Merry ", color='lightred', end="")
            print("Christmas !", color='lightgreen')
        else:
            print("Have a nice day !", color='lightblue')
            print("Bye :)", color='lightgreen')
        print(" ")
        self.StopReloadMainMenu = True
        return True

    def print_custom_options(self):
        current_line = ""

        for i, option in enumerate(self.CustomOptions, 1):
            new_option = f"{i}:{option} "

            if len(current_line) + len(new_option) > self.max_character_in_one_line:
                print(current_line.strip())  # Print current line and start new one
                current_line = new_option
            else:
                current_line += new_option

        if current_line:
            print(current_line.strip())

    def menuMain(self):
        global message
        while not self.StopReloadMainMenu:
            if self.ResetMainMenu:
                continue

            if Base.AutomaticLaunch:
                launch_manager.launch_game(QuickLaunch=True)

            # Print title and info
            print(self.menuTitle, color=Base.LauncherTitleColor)
            print(self.launcher_version_info, color='lightblue')

            # Load account status
            account_manager.login_status()

            # Finally, print error message
            if len(self.error_message_list) > 0:
                if not self.error_message_output_time > 3:
                    latest = len(self.error_message_list) - 1
                    print("Latest Error Message:", self.error_message_list[latest], color='red')
                    self.error_message_output_time += 1
                else:
                    self.error_message_output_time = 0
                    self.error_message_list.clear()

            # Print menu
            self.menu()

            # Print custom menu (If it available)
            if self.PrintCustomMenu:
                self.print_custom_options()

            if Base.AutomaticOpenOption:
                option = Base.AutoOpenOptionName
            else:
                print(f"{self.input_symbol}", end='', color=self.input_symbol_color)
                option = str(input(f" "))

            specified_function = self.mapping_input_to_options(option, options_dict=self.options_mappings_dict)
            if not self.OptionNotFound:
                message = specified_function()
            else:
                print(f"Option {option} not found :/", color='lightred')
                time.sleep(2)

            self.append_return_message(message)

            # restore environment
            os.chdir(Base.launcher_root_dir)


    def extraMain(self):
        self.extra_menu()

        print(f"{self.input_symbol}", end='', color=self.input_symbol_color)
        option = str(input(f" "))

        if option.lower() == "exit":
            return

        specified_function = self.mapping_input_to_options(option, options_dict=self.extra_options_mappings_dict)

        if not self.OptionNotFound:
            if specified_function is not None:
                message = specified_function()
                self.append_return_message(message)
        else:
            print(f"Option {option} not found :/", color='lightred')
            time.sleep(2)

        return

    def mapping_input_to_options(self, input_option, options_dict):
        input_option = input_option.lower()
        self.OptionNotFound = False

        specified_function_name = options_dict.get(input_option, None)

        if specified_function_name is not None:
            return specified_function_name
        else:
            self.OptionNotFound = False
            return None

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