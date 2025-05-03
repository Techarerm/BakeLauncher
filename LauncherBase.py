import datetime
import importlib.util
import importlib
import inspect
import json
import os
import re
import subprocess
import sys
import textwrap
import time
import platform
import threading

import libs.lib
from modules.print_colorx.print_color import print as print_color
from libs.Utils.config import config_loader

# Beta "Version"("Dev"+"-"+"month(1~12[A~L])/date(Mon~Sun[A~G])"+"Years")
# dev_version = "month(1~12[A~L])date(Mon~Sun[A~G])dd/mm/yy"
# Example = "LB041224" Years: 2024 Month: 12 Date: 04
dev_version = ""  # If version type is release set it blank
version_type = "Pre-Release"
major_version = "0.9.x FE"

BetaWarningMessage = ("You are running beta version of BakeLauncher.\n"
                      "This is an 'Experimental' version with potential instability.\n"
                      "Please run it only if you know what you are doing.\n")

ChangeLog = ("")

global_config = """[BakeLauncher Configuration]

<Global>
Debug = False
DontPrintColor = false
DisableClearOutput = false
DefaultAccountID = 1
# Custom launcher working Dir(Do not use non-English language paths unless you want to see Minecraft crash on launch)
LauncherWorkDir = ""
# When the launcher checks for an Internet connection, it will use this setting instead of the recommended IP address.
PingServerIP = ""
# Bypass internet connection check
NoInternetConnectionCheck = false

<MainMenu>
# Automatic open you want option when launcher load MainMenu
AutomaticOpenOptions = false
Option = ""
NoList = false
QuickLaunch = False
# Support red, orange, blue, green, yellow, white, gray, lightred, lightblue(recommended), lightyellow, lightgreen
# , lightyellow, indigo, pink....
LauncherTitleColor = lightblue

<LaunchManager>
# Create a new terminal when launching Minecraft. The new terminal will not be killed when the main stop working.
EnableExperimentalMultitasking = true
DefaultGameScreenWidth = 1280
DefaultGameScreenHeight = 720
JVMUsageRamSizeMinLimit = 2048
JVMUsageRamSizeMax = 4096

# Menu setting
# Set maximum number of instances name can be printed in one line
MaxInstancesPerRow = 10

# Automatic launch you want to launch instances(when launcher main menu loaded)
AutomaticLaunch = False

# Launch an instance when main menu loaded(Requires AutomaticLaunch or QuickLaunch is set to True)
QuickInstancesName = ""

<AccountManager>
# Bypass login status check when launcher loading main menu.
BypassLoginStatusCheck = false

<DukeExplorer>
PrioUseOfSpecifiedJVM = False
CustomJVMInstallPath = ""
SearchJVMInCustomPath = False

<Create_Instance>
# Automatic download you want Minecraft version
AutomaticDownVersion = true
MaxVersionPerLine = 5  # If the version list is not readable on your computer(When you use recommended setting),
# Set it to 3 (Or even 2, but I wouldn't recommend setting it to a value<3 number. Just use legacy version mode
# because is enough for most of people. But the list will be very long (more than >250 lines)
MaxInstancesPerRow = 10

# If the same version is already installed in the runtime folder, reinstall it instead of asking user.
OverwriteJVMIfExist = false
DoNotAskJVMExist = false
# Legacy output(Similar Versions>0.9 download output)
UsingLegacyDownloadOutput = false
"""


def print_custom(*args, **kwargs):
    thread_id = None
    if Base.PrintThreadInfo:
        thread_id = threading.get_ident()

    if not Base.DontPrintColor:
        color = kwargs.pop('color', None)  # Remove color from kwargs if it exists
        if not Base.PrintThreadInfo:
            print_color(*args, color=color, **kwargs)  # Pass remaining args and color
        else:
            print_color(f"[{thread_id}] ", *args, color=color, **kwargs)
    else:
        if not Base.PrintThreadInfo:
            print(*args)
        else:
            print(f"[{thread_id}] ", *args)


def initialize_config(**kwargs):
    print_custom("Can't find config! Creating...", color='yellow')
    overwrite = kwargs.get('overwrite', False)
    if overwrite:
        with open(Base.global_config_path, "w") as config:
            config.write(global_config)
        print("Global config has been reset.")
        return
    if not os.path.exists("data"):
        os.makedirs("data")
    if not os.path.exists(Base.global_config_path):
        with open(Base.global_config_path, "w") as config:
            config.write(global_config)


def internal_functions_error_log_dump(error_data, main_function_name, crash_function_name, detailed_traceback):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    error_log_output = textwrap.dedent(f"""\
    ==================================================================================================
    [{main_function_name}] Time: {timestamp} Error: {error_data} | At function {crash_function_name} | 
    [{detailed_traceback}]
    ==================================================================================================
    """)

    if not os.path.exists("logs"):
        os.mkdir("logs")

    error_log_data = "\n".join(line.lstrip() for line in error_log_output.splitlines())
    timestamp_day = datetime.datetime.now().strftime("%Y-%m-%d")
    # Format the timestamp to avoid invalid characters
    log_name = f"error_{timestamp_day}.log"
    error_log_save_path = os.path.join(Base.launcher_root_dir, "logs", log_name)

    if os.path.exists(error_log_save_path):
        with open(error_log_save_path, "a") as f:
            f.write(f"\n{error_log_data}")
        print(f"Exception event output has been saved to the error log. Saved to: {error_log_save_path} ")
    else:
        with open(error_log_save_path, "w") as f:
            f.write(error_log_data)
        print(f"Exception event output has been saved to the existing error log. Saved to: {error_log_save_path}")

    return True


def ping_a_host(host):
    # Link: https://stackoverflow.com/questions/2953462/pinging-servers-in-python
    try:
        # Execute the ping command
        # Option for the number of packets as a function of
        param = '-n' if platform.system().lower() == 'windows' else '-c'

        # Building the command. Ex: "ping -c 1 google.com"
        command = (['ping', param, '1', host])

        # Check if the command was successful(grabber stdout)
        if subprocess.call(command, stdout=subprocess.DEVNULL) == 0:
            return True
        else:
            return False
    except Exception as e:
        print(f"Error while executing ping: {e}")
        return False


def timer(message, seconds):
    for remaining in range(seconds, 0, -1):
        # Determine the color based on the remaining time
        if remaining <= 4:
            c = "red"  # Red
        else:
            c = "white"  # White

        # Print the remaining time with color and overwrite previous output
        print_custom(f"{message}...{remaining} \033[0m", end='\r', color=c)

        # Wait for 1 second
        time.sleep(1)

    # To clear the line after the timer ends
    print(" " * 20, end='\r')


class LauncherBase:
    """
    BakeLauncher's Base
    .....
    """

    def __init__(self, **kwargs):
        # Set version
        if version_type == "Dev":
            self.launcher_version = f"Beta {major_version}({version_type}-{dev_version})"
            self.launcher_version_type = "Dev"
            self.launcher_internal_version = f'dev-beta-{major_version}-{dev_version}'
            self.launcher_version_display = f"Beta {major_version} ({version_type}-{dev_version})"
        else:
            if len(dev_version) != 0:
                self.launcher_version = f"Beta {major_version}({dev_version})"
                self.launcher_version_type = "Pre-Release"
                self.launcher_internal_version = f'beta-{major_version}-pre-release'
                self.launcher_version_display = f"Beta {major_version} ({dev_version})"
            else:
                self.launcher_version = f"Beta {major_version}"
                self.launcher_version_type = "Release"
                self.launcher_internal_version = f'beta-{major_version}-release'
                self.launcher_version_display = self.launcher_version
        # Other stuff (for create instance, platform check...)
        self.launcher_data_format = "Beta-0.9-PE"
        self.launcher_lib_version = libs.lib.LIB_VERSION
        self.PlatformSupportList = ["Windows", "Darwin", "Linux"]
        self.Platform = platform.system()
        self.Arch = platform.architecture()[0]
        self.FullArch = platform.uname().machine
        # ============================I'm a line==============================
        # Flag and list(Set by launcher)
        self.EndLoadFlag = False  # If the loading process failed (such as platform check failure), set to true.
        self.MainMenuResetFlag = False  # Set to true by check_account_data_are_valid or other functions
        self.InternetConnected = False
        self.StartUsingErrorLog = False
        self.RefreshTokenFailedFlag = False
        self.LauncherFullResetFlag = False
        self.UnknownPlatform = False
        self.DontLoadMainMemu = False
        self.DaemonPool = []
        # ============================I'm a line==============================
        # Config file stuff
        # Global stuff
        self.Debug = False
        self.DontPrintColor = False  # Stop print colorful text
        self.DisableClearOutput = False  # Debug
        self.DefaultAccountID = None
        self.LauncherWorkDir = None  # Setting from the global config file
        self.NoPrintConfigInfo = False
        self.NoInternetConnectionCheck = False
        self.PingServerIP = None
        self.BypassLoginStatusCheck = False
        # Duke
        self.PrioUseOfSpecifiedJVM = True  # When launching game, priority use specified JVM path (CustomJVMInstallPath)
        self.CustomJVMInstallPath = None  # Custom runtimes
        self.SearchJVMInCustomPath = False  # When searching available JVM, append it to the search list.
        # (Type = Custom-Installed)
        # Create Instance stuff
        self.OverwriteJVMIfExist = False  # Overwrite JVM runtimes without asking user
        # (If minecraft_version require jvm_version available in the 'runtimes' folder)
        self.DoNotAskJVMExist = False  # If the version requires an installed version of runtimes,
        # skip asking the user to reinstall it
        self.UsingLegacyDownloadOutput = False  # Legacy download output is good.
        self.MaxVersionPerLine = 5  # Check config to get more information!
        self.DarwinInstallWithRosetta = False
        # ============================I'm a line==============================
        # Launcher environment
        self.launcher_root_dir = os.getcwd()  # Set launcher root dir
        self.launcher_instances_dir = os.path.join(self.launcher_root_dir, "instances")  # instances
        self.launcher_tmp_dir = os.path.join(self.launcher_root_dir, "tmp")  # tmp(still under testing)
        self.launcher_tmp_session = os.path.join(self.launcher_root_dir, "tmp", "in.session")  # session file
        self.global_config_path = os.path.join(self.launcher_root_dir, "data/config.bakelh.cfg")  # config(global)
        self.account_data_path = os.path.join(self.launcher_root_dir, "data/AccountData.json")
        self.jvm_setting_path = os.path.join(self.launcher_root_dir, "data/java_home_list.json")
        self.assets_dir = os.path.join(self.launcher_root_dir, "assets")
        self.PingServerHostList = ["8.8.8.8", "210.2.4.8", "1.1.1.1"]  # Test internet Connection
        self.launcher_boot_args = sys.argv  # Debug
        self.launcher_loaded_time = datetime.datetime.today()
        if self.launcher_loaded_time.month == 12 and self.launcher_loaded_time.day == 25:
            self.ChristmasPoint = True
        else:
            self.ChristmasPoint = False
        # ============================I'm a line==============================
        # Dev stuff
        self.AllowModify = False
        self.AllowUnsafeImport = False
        self.AllowLoadCustomModules = False
        self.CustomModulesPathList = []
        self.BypassLoginRequire = False
        self.PrintThreadInfo = False
        self.DevelopmentMode = False
        if self.DevelopmentMode:
            self.AllowModify = True
        else:
            self.AllowModify = False

    @property
    def Initialize(self):
        # Initialize Launcher "Base"

        # Load config
        if not os.path.exists(self.global_config_path):
            initialize_config()
        else:
            self.load_setting()

        # Change workDir if it exists


        try:
            if self.LauncherWorkDir is not None:
                if len(self.LauncherWorkDir) > 0:
                    try:
                        os.chdir(self.LauncherWorkDir)
                        print(f'Launcher workDir now is "{self.LauncherWorkDir}"')
                        self.launcher_root_dir = self.LauncherWorkDir
                    except Exception as e:
                        print_color(f"Failed to change workDir :( Cause by error {e}", tag='ERROR', color='red')
                else:
                    print_color("Could not change workDir. The setting path is invalid.", tag='Warning')
            else:
                os.chdir(self.launcher_root_dir)

        except UnicodeEncodeError:
            # ???(Interesting thing is I even don't know which update patched it.)
            print_color("Warning: The launcher is running in a directory with non-ASCII characters.", tag='Warning')
            print_color("You may get failed to launch when you enable EnableExperimentalMultitasking support.")
            print_color("This bug has been confirmed if the user are using Windows(other systems are unverified).")
            continue_load = str(input("Enter Y to ignore this warning: "))
            if not continue_load.upper() == "Y":
                return False, "WorkDirUnicodeEncodeError"

        # Platform check
        if Base.Platform not in self.PlatformSupportList:
            print_color(f"You are running on a unsupported platform name {Base.Platform}", color='yellow',
                        tag_color='yellow', tag='Warning')
            print_color(
                "You can still continue running the launcher. However, you may get some error when you create "
                "instance.", color='yellow', tag_color='yellow', tag='Warning')
            print_color("If you still want to launch Minecraft. You need to build LWJGL and JDK for your platform.",
                        tag_color='blue', tag='Note')
            continue_running = str(input("Enter Y to ignore: "))
            if not continue_running.upper() == "Y":
                return False, "UnknownPlatformError"

        # Set window(terminal?) title
        if self.Platform == "Windows":
            os.system(f"title BakeLauncher {Base.launcher_version}")
        elif self.Platform == "Darwin":
            os.system(rf'echo -n -e "\033]0;BakeLauncher {Base.launcher_version}\007"')
        elif self.Platform == "Linux":
            os.system(f'echo -ne "\033]0;BakeLauncher {Base.launcher_version}\007"')

        if not Base.Arch.lower() == "64bit":
            print_color("Non-64Bit platform detected!")
            print_color(f"BakeLauncher for other architecture support is untested.", color='lightred')
            print_color(f"You can still continue running the launcher. But you may get some bug during use.",
                        color='lightyellow')
            continue_running = str(input("Enter Y to ignore: "))
            if not continue_running.upper == "Y":
                self.EndLoadFlag = True
                return

        Status, Message = self.check_internet_connect()

        if not Status:
            return False, Message

        # Create tmp folder
        # In pre-0.9, I'm trying to add temp folder for some functions (like mod loader installer).
        # But I have no luck when feature "add check tmp folder status" :(
        # Check if any other launchers are already running...
        if not os.path.exists(self.launcher_tmp_dir):
            os.makedirs(self.launcher_tmp_dir)

        if not os.path.exists(Base.launcher_tmp_session):
            with open(self.launcher_tmp_session, "w"):
                pass
        # else:
        # print_color("A launcher already running on your computer. Please close it and try again.", tag="Warning")
        # time.sleep(2)

        # Clean up tmp folder
        """
        if len(Base.launcher_tmp_dir) != 0:
            try:
                shutil.rmtree(self.launcher_tmp_dir)
            except Exception as e:
                print(f"Failed to clean tmp folder. Cause by error {e}")
            os.makedirs(self.launcher_tmp_dir, exist_ok=True)
        """
        # Check config file status
        if os.path.exists(self.global_config_path):
            with open(self.global_config_path, "r", encoding="utf-8") as file:
                cfg_data = file.read()  # Read the content of the file
                cfg_length = len(cfg_data)
            if cfg_length < 1:
                print_color("Warning: Your config file are corrupted :0 Do you want to reconfigure it?")
                user_input = str(input('Y/N :'))
                if user_input.upper() == "Y":
                    initialize_config(overwrite=True)
                    self.load_setting()
                else:
                    return False, "Global Config Corrupted"

        if not Status:
            return False, Message
        else:
            self.launcher_loaded_time = datetime.datetime.now()

        return True, ""

    def load_setting(self):
        setting_dict = {
            "BOOL%Debug": "Debug",
            "BOOL%DisableClearOutput": "DisableClearOutput",
            "BOOL%DontPrintColor": "DontPrintColor",
            "BOOL%NoList": "NoList",
            "BOOL%AutomaticOpenOption": "AutomaticOpenOption",
            "BOOL%QuickLaunch": "QuickLaunch",
            "BOOL%PrioUseOfSpecifiedJVM ": "PrioUseOfSpecifiedJVM",
            "BOOL%SearchJVMInCustomPath": "SearchJVMInCustomPath",
            "BOOL%DoNotAskJVMExist": "DoNotAskJVMExist",
            "BOOL%OverwriteJVMIfExist": "OverwriteJVMIfExist",
            "BOOL%UsingLegacyDownloadOutput": "UsingLegacyDownloadOutput",
            "BOOL%NoInternetConnectionCheck": "NoInternetConnectionCheck",
            "BOOL%BypassLoginStatusCheck": "BypassLoginStatusCheck",
            "BOOL%LaunchClientWithOutput": "LaunchClientWithOutput",
            "BOOL%LegacyLaunchMethod": "LegacyLaunchMethod",
            "BOOL%AutomaticLaunch": "AutomaticLaunch",
            "INT%DefaultAccountID": "DefaultAccountID",
            "STR%AutoOpenOptionName": "AutoOpenOptionName",
            "STR%LauncherTitleColor": "LauncherTitleColor",
            "STR%CustomJVMInstallPath": "CustomJVMInstallPath",
            "STR%LauncherWorkDir": "LauncherWorkDir",
            "STR%PingServerIP": "PingServerIP",
            "INT%MaxInstancesPerRow": "MaxInstancesPerRow",
            "INT%MaxVersionPerLine": "MaxVersionPerLine",
            "STR%QuickInstancesName": "QuickInstancesName",
            "INT%DefaultGameScreenWidth": "DefaultGameScreenWidth",
            "INT%DefaultGameScreenHeight": "DefaultGameScreenHeight",
            "INT%JVMUsageRamSizeMinLimit": "JVMUsageRamSizeMinLimit",
            "INT%JVMUsageRamSizeMax": "JVMUsageRamSizeMax",
            "STR%CustomModulesPathList": "CustomModulesPathList"
        }

        config_loader(self, setting_dict, self.global_config_path)

    def check_internet_connect(self):
        if self.PingServerIP is not None:
            if not self.PingServerIP == "None":
                host = self.PingServerIP
            else:
                host = "InternalList"
        else:
            host = "InternalList"

        if Base.NoInternetConnectionCheck:
            self.InternetConnected = True
            return True, "BypassCheckInternetConnection"

        if host == "InternalList":
            for host in self.PingServerHostList:
                host = str(host)
                # Try to establish a socket connection to the host and port
                try:
                    response = ping_a_host(host)
                    if response:
                        self.InternetConnected = True
                except Exception as e:
                    print_color(f"Ping to host {host} failed.", tag='Warning')
                continue
        else:
            print_color("Using exist host to check internet connection...", tag='INFO')
            try:
                response = ping_a_host(self.PingServerIP)
                if response is not None:
                    self.InternetConnected = True
            except Exception as e:
                print_color(f"Ping to host {self.PingServerIP} failed.", tag='Warning')

        if not self.InternetConnected:
            print_color("Internet connection failed :(", color='red', tag='Error')
            print("Unable to connect to the internet. Some features may be unavailable, including:")
            print("- AccountManager")
            print("- Instance Creation")
            print("- Any feature that requires an internet connection")

            print("\nWould you like to ignore this error or exit the launcher? (Y/N)")
            user_input = input(": ").strip().lower()

            if user_input.upper() == 'Y':
                return True, "IgnoreInternetConnectionError"
            else:
                self.EndLoadFlag = True
                return False, "InternetConnectionError"
        else:
            return True, "Pass"


Base = LauncherBase()


def load_custom_modules():
    mods_folder = os.path.join(Base.launcher_root_dir, "mods")
    if not os.path.exists(mods_folder):
        return

    folder_list = os.listdir(mods_folder)

    mod_paths_list = []
    for name in folder_list:
        path = os.path.join(mods_folder, name)
        mod_paths_list.append(path)

    for mod_path in mod_paths_list:
        mod_info = os.path.join(mod_path, "mod.info.json")
        if not os.path.exists(mod_info):
            continue

        try:
            with open(mod_info, "r") as f:
                mod_info = json.load(f)
        except Exception as e:
            continue

        mod_main_name = mod_info.get("modMain", None)
        mod_main_file = mod_info.get("modMainFile", None)
        mod_main_file_path = os.path.join(mod_path, mod_main_file)
        mod_group_id = mod_info.get("groupID", None)

        if not os.path.exists(mod_main_file_path):
            continue

        if mod_main_name is None:
            continue

        # Define a unique module name based on file path
        module_name = f"mod_{hash(mod_main_file_path)}"

        # Load mod
        spec = importlib.util.spec_from_file_location(module_name, mod_main_file_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module  # Register module in sys.modules
        spec.loader.exec_module(module)

        # Get the function dynamically
        if hasattr(module, mod_main_name):
            mod_function = getattr(module, mod_main_name)
            if callable(mod_function):
                print(f"Mod name {mod_group_id} has been loaded.")
                mod_function()  # Call the function
            else:
                print(f"Mod Name {mod_group_id} load failed. Not callable.")
        else:
            continue


def get_all_classes():
    class_list = {name: obj for name, obj in globals().items() if inspect.isclass(obj)}
    return class_list


def bake_bake():
    print_color("POWERED BY BAKE!", color="yellow")
    print_color("BakeLauncher " + Base.launcher_version, color='yellow')
    print_color("Contact Me :) TedKai/@Techarerm", color="blue")
    print_color("Source code: https://github.com/Techarerm/BakeLauncher", color='yellow')
    if "Dev" in Base.launcher_version:
        print_color("This bread isn't baked yet?", color='blue')
    elif "Beta" in Base.launcher_version:
        print_color("Almost done? (Just wait...like 1 years?)", color='blue')
    print_color(" ")
    print_color(ChangeLog, color='cyan')
    print_color("You are in launcher terminal mode!", color='lightyellow')
    print_color("Type 'exit' to back to main menu.", color='green')
    print_color('"Details" for more information.', color='purple')
    print_color('"PrintInternalInfo" for full internal variable data output (dev-only)', color='lightgreen')
    print_color('"DumpBaseData" to dumps base-obj.bakelh.json (For debug, create new issue on Github use)',
                color='lightyellow')
    type_time = 1
    while True:
        user_input = str(input("BakeLauncher> "))

        if user_input.upper() == "EXIT":
            return True

        if "BAKE" in user_input.upper():
            bake_game()
            return True

        if "details" in user_input.lower():
            print(f"Launcher Version : {Base.launcher_version}")
            print(f"Launcher Version Type : {Base.launcher_version_type}")
            print(f"Using Lib Version : {libs.lib.LIB_VERSION}")
            print(f"WorkDir : {Base.launcher_root_dir}")
            print(f"Debug : {Base.Debug}")
            print("")
            print("System Info")
            print(f"OS Name : {Base.Platform}")
            print(f"Architecture : {Base.FullArch}, {Base.Arch[0]}")
            print(f"Internet Connection : {Base.InternetConnected}")
            print(f"")
            print("Setting & Flag")
            print(f"Debug : {Base.Debug}")
            print(f"DontPrintColor : {Base.DontPrintColor}")
            print(f"DisableClearOutput : {Base.DisableClearOutput}")
            print(f"DefaultAccountID : {Base.DefaultAccountID}")
            print(f"LauncherWorkDir : {Base.LauncherWorkDir}")
            print(f"PingServerIP : {Base.PingServerIP}")
            print(f"NoInternetConnectionCheck : {Base.NoInternetConnectionCheck}")
            while True:
                input("Press any key to continue...")
                return True

        if 'printinternalinfo' in user_input.lower():
            base_obj = LauncherBase()
            data = base_obj.__dict__

            for keys, values in data.items():
                print_color(f"{keys}: {values}", color='yellow')

            input("Press any key to continue...")
            return True

        if 'dumpbasedata' in user_input.lower():
            base_obj = LauncherBase()
            data = base_obj.__dict__

            try:
                with open("base-obj.bakelh.json", "w") as f:
                    json.dump(data, f, indent=4)
                print("Base data dumped.")
            except Exception as e:
                print(f"Error while writing json data {e}")

            input("Press any key to continue...")
            return True

        if "CE~" in user_input:
            match = re.match(r"CE~(\w+)\.(\w+)=(.+)", user_input)
            if match:
                class_name, variable, value = match.groups()
                try:
                    value = eval(value)
                except:
                    pass
                print(Base.__class__.__name__)
                if class_name == Base.__class__.__name__:  # Check if class name matches
                    setattr(Base, variable, value)  # Update variable dynamically
                    print(f"Variable name '{class_name}.{variable}' has been updated to {value}")
                    return
                else:
                    print(f"Class name {class_name} not support change ")
                    return

        if type_time == 1:
            print(f"?{user_input}")
            type_time += 1
        elif type_time == 2:
            print(f"!{user_input}")
            type_time += 1
        elif type_time == 3:
            print(f"???{user_input}")
            type_time = 1


def bake_game():
    count = 0
    texts = ""
    print_custom("Bake Game", color='yellow', tag_color='yellow', tag=':)')
    print_custom("If you feel crush. You can press Ctrl+C to end the launcher :)", color='green')

    while True:
        user_input = input("Bake> ")

        if user_input.upper() == 'EXIT':
            return

        occurrences = user_input.split().count('Bake')
        count += occurrences

        if count == 1:
            print("?Bake")
        elif count == 2:
            texts = "Bake "
            print(texts)  # Print "Bake " with newline
        elif count == 3:
            texts += "Bake "
            print(texts)  # Print "Bake " with newline
        else:
            times = texts.count("Bake") ** 2
            if times > 65536:
                print("Ouch!")
            for _ in range(times):  # Print one "Bake " at a time with delay
                print("Bake ", end='', flush=True)
                time.sleep(0.001)  # Wait 0.001 seconds between each print
            texts = "Bake " * times  # Update texts to the final result
            print()  # Add a final newline to end the sequence
