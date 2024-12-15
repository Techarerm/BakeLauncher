import datetime
import os
import shutil
import textwrap
import time
import platform
from ping3 import ping
from modules.print_colorx.print_color import print as print_color

# Beta "Version"("Dev"+"-"+"month(1~12[A~L])/date(Mon~Sun[A~G])"+"Years")
# dev_version = "month(1~12[A~L])date(Mon~Sun[A~G])dd/mm/yy"
# Example = "LB041224" Years: 2024 Month: 12 Date: 04
dev_version = "LG151224-2"  # If version type is release set it blank
version_type = "Dev"
major_version = "0.9"

BetaWarningMessage = ("You are running beta version of BakeLauncher.\n"
                      "This is an 'Experimental' version with potential instability.\n"
                      "Please run it only if you know what you are doing.\n")

ChangeLog = ("Changelog:\n"
             "In Pre-0.9, launcher are unstable :( If you want to get a stable Dev version.\n"
             "Go to Github Actions and find version Dev-KB112624(Download Build version for you :).\n"
             "Is the last one not support installation of mod loaders (but it is indeed stable and supports"
             " the new instance structure).\n"
             "\n")

global_config = """[BakeLauncher Configuration]

<Global>
Debug = True
DontPrintColor = false
DisableClearOutput = false
DefaultAccountID = 1
LauncherWorkDir = None
PingServerIP = None
NoInternetConnectionCheck = false

<MainMemu>
# Automatic open you want option when launcher load MainMemu
AutomaticOpenOptions = false
Option = None
NoList = false
QuickLaunch = True

<LaunchManager>
# Create a new terminal when launching Minecraft. The new terminal will not be killed when the main stop working.
EnableExperimentalMultitasking = true
# If you Multitasking not working. Set LaunchMultiClientWithOutPut to False . It will create a new client without log
# output
LaunchMultiClientWithOutput = True
DefaultGameScreenWidth = 1280
DefaultGameScreenHeight = 720
JVMUsageRamSizeMinLimit = 2048
JVMUsageRamSizeMax = 4096


# Memu setting
# Set maximum number of instances name can be printed in one line
MaxInstancesPerRow = 20

# Automatic launch you want to launch instances(when launcher main memu load)
AutomaticLaunch = False

# Set Automatic launch instance
QuickInstancesName = None

# Use old libraries.cfg
UseCustomLibrariesCFG = false
CustomLibrariesCFGPath = None

<AccountManager>
# Get token(Minecraft) from refresh token(or name "Microsoft Token")
RefreshCustomToken = false
RefreshToken = None
BypassLoginStatusCheck = false

# Save the token given by the user
SaveCustomToken = false
Token = None
Username = None
UUID = None

<Create_Instance>
# Automatic download you want Minecraft version
# AutomaticDownVersion = true
MaxVersionPerRow = 40
MaxReleaseVersionPerRow = 100

# If a same version is already installed in the runtimes folder, reinstall it(but bypass ask user)
OverwriteJVMIfExist = false
DoNotAskJVMExist = false
UsingLegacyDownloadOutput = false
Version = None
"""

# Default value for some settings
DontPrintColor = False
DisableClearOutput = False
NoList = False


def print_custom(*args, **kwargs):
    if not Base.DontPrintColor:
        color = kwargs.pop('color', None)  # Remove color from kwargs if it exists
        print_color(*args, color=color, **kwargs)  # Pass remaining args and color
    else:
        print(*args)


def initialize_config(**kwargs):
    print_custom("Can't find config! Creating...", color='yellow')
    overwrite = kwargs.get('overwrite', False)
    if overwrite:
        with open(Base.global_config_path, "w") as config:
            config.write(Base.global_config_path)
        print("Global config has been reset.")
        return
    if not os.path.exists("data"):
        os.makedirs("data")
    if not os.path.exists(Base.global_config_path):
        with open(Base.global_config_path, "w") as config:
            config.write(global_config)


def ClearOutput():
    if not Base.DisableClearOutput:
        if Base.Platform == "Windows":
            os.system("cls")
        elif Base.Platform == "Darwin":
            os.system("clear")
        elif Base.Platform == "Linux":
            os.system("clear")
        else:
            print("Unsupported platform! Bypassing ClearOutput...")
    else:
        return


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
    A good Launcher must have a good foundation.
    .....
    """

    def __init__(self):
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
        # Other stuff(for create instance, platform check...)
        self.launcher_data_format = "dev-beta-0.9-2"
        self.PlatformSupportList = ["Windows", "Darwin", "Linux"]
        self.Platform = self.get_platform("platform")
        self.LibrariesPlatform = self.get_platform("libraries")
        self.LibrariesPlatform2nd = self.get_platform("libraries_2nd")
        self.LibrariesPlatform2ndOld = self.get_platform("libraries_2nd_old")
        self.Arch = self.get_platform("Arch")
        # ============================I'm a line==============================
        # Flag and list(Set by launcher)
        self.EndLoadFlag = False  # If load process failed(platform check failed), Set to True
        self.MainMemuResetFlag = False  # Set to true by check_account_data_are_valid
        self.InternetConnected = False
        self.ErrorMessageList = []
        self.StartUsingErrorLog = False
        self.RefreshTokenFailedFlag = False
        # ============================I'm a line==============================
        # Config file stuff
        # Global stuff
        self.Debug = False
        self.DontPrintColor = False  # Stop print colorful text
        self.DisableClearOutput = False  # Debug
        self.DefaultAccountID = None
        self.LauncherWorkDir = None  # Setting from config file
        self.NoPrintConfigInfo = False
        self.NoInternetConnectionCheck = False
        self.PingServerIP = None
        self.BypassLoginStatusCheck = False
        # main_memu stuff
        self.NoList = False  # Make main_memu not print the list
        self.AutomaticOpenOptions = False  # Start selected option when load main_memu
        self.AutoOpenOptions = None  # Select option
        # LaunchManager stuff
        self.AutomaticLaunch = False
        self.QuickLaunch = None
        self.QuickInstancesName = None
        self.MaxInstancesPerRow = 20
        self.EnableExperimentalMultitasking = False
        self.LaunchMultiClientWithOutput = True
        self.DefaultGameScreenHeight = 720
        self.DefaultGameScreenWidth = 1280
        self.JVMUsageRamSizeMinLimit = 2048
        self.JVMUsageRamSizeMax = 4096
        # Create Instance stuff
        self.OverwriteJVMIfExist = False
        self.DoNotAskJVMExist = False
        self.UsingLegacyDownloadOutput = False
        self.MaxVersionPerRow = 40  # Not working
        self.MaxReleaseVersionPerRow = 9  # Not working
        # ============================I'm a line==============================
        # Other stuff
        self.launcher_root_dir = os.getcwd()  # Set launcher root dir
        self.launcher_instances_dir = os.path.join(self.launcher_root_dir, "instances")  # instances
        self.launcher_tmp_dir = os.path.join(self.launcher_root_dir, "tmp")  # tmp(still under testing)
        self.launcher_tmp_session = os.path.join(self.launcher_root_dir, "tmp", "in.session")  # session file
        self.global_config_path = os.path.join(self.launcher_root_dir, "data/config.bakelh.cfg")  # config(global)
        self.account_data_path = os.path.join(self.launcher_root_dir, "data/AccountData.json")
        self.PingServerHostList = ["8.8.8.8", "210.2.4.8", "1.1.1.1"]  # Test internet Connection

    def Initialize(self):
        # Initialize Launcher "Base"
        # Load config
        if not os.path.exists("data/config.bakelh.cfg"):
            initialize_config()
        else:
            self.load_setting()

        # Check workdir(If launcher running in a non-ASCII path)(Seems like it patched when BakeLauncher added
        # instance_info support?)
        try:
            if self.LauncherWorkDir is not None and self.LauncherWorkDir != "None":
                if len(self.LauncherWorkDir) > 0:
                    try:
                        os.chdir(self.LauncherWorkDir)
                        print(f'Launcher workDir now is "{self.LauncherWorkDir}"')
                        self.launcher_root_dir = self.LauncherWorkDir
                    except Exception as e:
                        print_color(f"Failed to change workDir :( Cause by error {e}", tag='ERROR', color='red')
                else:
                    print_color("Invalid LauncherWorkDir!", tag='Warning')
                    print_color("Stopped change workDir!", tag='INFO')
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

        # Set window(terminal?) title
        if self.Platform == "Windows":
            os.system(f"title BakeLauncher {Base.launcher_version}")
        elif self.Platform == "Darwin":
            os.system(rf'echo -ne "\033]0;BakeLauncher {Base.launcher_version}\007"')
        elif self.Platform == "Linux":
            os.system(f'echo -ne "\033]0;BakeLauncher {Base.launcher_version}\007"')

        Status, Message = self.check_internet_connect()

        if not Status:
            return False, Message

        # Create tmp folder
        # In pre-0.9, I'm trying to add temp folder for some functions(like mod loader installer).
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
        if len(Base.launcher_tmp_dir) != 0:
            try:
                shutil.rmtree(self.launcher_tmp_dir)
            except Exception as e:
                print(f"Failed to clean tmp folder. Cause by error {e}")
            os.makedirs(self.launcher_tmp_dir, exist_ok=True)

        # Check config file status
        if os.path.exists("data/config.bakelh.cfg"):
            with open("data/config.bakelh.cfg", "r", encoding="utf-8") as file:
                cfg_data = file.read()  # Read the content of the file
                cfg_length = len(cfg_data)
            if cfg_length < 10:
                print_color("Warning: Your config file are corrupted :( Do you want to reconfigure it?")
                user_input = str(input('Y/N :'))
                if user_input.upper() == "Y":
                    initialize_config(overwrite=True)
                    self.load_setting()

        if not Status:
            return False, Message

        return True, ""

    def load_setting(self, **kwargs):
        # Don't ask why LauncherBase has two load_setting. ONE is version lightweight!
        ConfigPath = kwargs.get('CfgPath', None)
        if not ConfigPath is None:
            self.global_config_path = ConfigPath

        with open(self.global_config_path, 'r') as file:
            for line in file:
                if "Debug" in line:
                    self.Debug = line.split('=')[1].strip().upper() == "TRUE"

                if "DefaultAccountID" in line:
                    self.DefaultAccountID = line.split('=')[1].strip().strip('"').strip("'")
                    try:
                        # Convert it to integer(if convert failed set it to 1)
                        self.DefaultAccountID = int(self.DefaultAccountID)
                    except ValueError:
                        self.ErrorMessageList.append("DefaultAccountIDNotAnInteger")
                        self.DefaultAccountID = 1

                if "DisableClearOutput" in line:
                    self.DisableClearOutput = line.split('=')[1].strip().upper() == "TRUE"

                if "DontPrintColor" in line:
                    self.DontPrintColor = line.split('=')[1].strip().upper() == "TRUE"

                if "NoList" in line:
                    self.NoList = line.split('=')[1].strip().upper() == "TRUE"

                if "AutomaticOpenOptions" in line:
                    self.AutomaticOpenOptions = line.split('=')[1].strip().upper() == "TRUE"

                if "AutoOpenOptions" in line:
                    if self.AutomaticOpenOptions:
                        self.AutoOpenOptions = line.split('=')[1].strip().strip('"').strip("'")

                if "QuickLaunch" in line:
                    self.QuickLaunch = line.split('=')[1].strip().upper() == "TRUE"

                if "OverwriteJVMIfExist" in line:
                    self.OverwriteJVMIfExist = line.split('=')[1].strip().upper() == "TRUE"

                if "DoNotAskJVMExist" in line:
                    self.DoNotAskJVMExist = line.split('=')[1].strip().upper() == "TRUE"

                if "UsingLegacyDownloadOutput" in line:
                    self.UsingLegacyDownloadOutput = line.split('=')[1].strip().upper() == "TRUE"

                if "LauncherWorkDir" in line:
                    self.LauncherWorkDir = line.split('=')[1].strip().strip('"').strip("'")

                if "PingServerIP" in line:
                    self.PingServerIP = line.split('=')[1].strip().strip('"').strip("'")

                if "NoInternetConnectionCheck" in line:
                    self.NoInternetConnectionCheck = line.split('=')[1].strip().upper() == "TRUE"

                if "BypassLoginStatusCheck" in line:
                    self.BypassLoginStatusCheck = line.split('=')[1].strip().upper() == "TRUE"

                if "MaxInstancesPerRow" in line:
                    MaxInstancesPerRow = line.split('=')[1].strip().strip('"').strip("'")
                    try:
                        self.MaxInstancesPerRow = int(MaxInstancesPerRow)
                    except ValueError:
                        print("ddddd")
                        self.ErrorMessageList.append("MaxInstancesPerRowNotAnInteger")
                        self.MaxInstancesPerRow = 20

                if "MaxVersionPerRow" in line:
                    MaxVersionPerRow = line.split('=')[1].strip().strip('"').strip("'")
                    try:
                        self.MaxVersionPerRow = int(MaxVersionPerRow)
                    except ValueError:
                        self.ErrorMessageList.append("MaxVersionPerRowNotAnInteger")
                        self.MaxVersionPerRow = 40

                if "MaxReleaseVersionPerRow" in line:
                    MaxReleaseVersionPerRow = line.split('=')[1].strip().strip('"').strip("'")
                    try:
                        self.MaxReleaseVersionPerRow = int(MaxReleaseVersionPerRow)
                    except ValueError:
                        self.ErrorMessageList.append("MaxReleaseVersionPerRowNotAnInteger")
                        self.MaxReleaseVersionPerRow = 9

                if "EnableExperimentalMultitasking" in line:
                    self.EnableExperimentalMultitasking = line.split('=')[1].strip().upper() == "TRUE"

                if "LaunchMultiClientWithOutput" in line:
                    self.LaunchMultiClientWithOutput = line.split('=')[1].strip().upper() == "TRUE"

                if "AutomaticLaunch" in line:
                    self.AutomaticLaunch = line.split('=')[1].strip().upper() == "TRUE"

                if "QuickInstancesName" in line:
                    self.QuickInstancesName = line.split('=')[1].strip().strip('"').strip("'")
                    if self.QuickInstancesName is None or self.QuickInstancesName == "None":
                        self.QuickLaunch = False
                        self.AutomaticLaunch = False

                if "DefaultGameScreenWidth" in line:
                    DefaultGameScreenWidth = line.split('=')[1].strip().strip('"').strip("'")
                    try:
                        self.DefaultGameScreenWidth = int(DefaultGameScreenWidth)
                    except ValueError:
                        self.DefaultGameScreenWidth = 1280

                if "DefaultGameScreenHeight" in line:
                    DefaultGameScreenHeight = line.split('=')[1].strip().strip('"').strip("'")
                    try:
                        self.DefaultGameScreenHeight = int(DefaultGameScreenHeight)
                    except ValueError:
                        self.DefaultGameScreenHeight = 720

                if "JVMUsageRamSizeMinLimit" in line:
                    JVMUsageRamSizeMinLimit = line.split('=')[1].strip().strip('"').strip("'")
                    try:
                        self.JVMUsageRamSizeMinLimit = int(JVMUsageRamSizeMinLimit)
                    except ValueError:
                        self.JVMUsageRamSizeMinLimit = 2048

                if "JVMUsageRamSizeMax" in line:
                    JVMUsageRamSizeMax = line.split('=')[1].strip().strip('"').strip("'")
                    try:
                        self.JVMUsageRamSizeMax = int(JVMUsageRamSizeMax)
                    except ValueError:
                        self.JVMUsageRamSizeMax = 4096

        if not self.NoPrintConfigInfo:
            if self.Debug:
                if self.DontPrintColor:
                    print_color("Colorful text has been disabled.", tag='Global')
                if self.DisableClearOutput:
                    print_color("Clear Output has been disabled.", tag='Global')
                if self.NoList:
                    print_color("Print list Has been disabled.", tag='Global')
                if self.LauncherWorkDir is not None:
                    if not self.LauncherWorkDir == "None" or Base.LauncherWorkDir == "null":
                        print_color("Launcher workDir has been set by exist config.", tag='Global')
                if self.NoInternetConnectionCheck:
                    print_color("Check internet connection has been disabled.", tag='Global')
                    self.NoInternetConnectionCheck = True
                if not isinstance(self.MaxInstancesPerRow, int):
                    print_color("MaxInstancesPerRow are not a valid number. Setting back to 20...", tag='Global')
                    self.MaxInstancesPerRow = 20

    def get_platform(self, mode):
        # Get "normal" platform name
        Platform = platform.system()
        Arch = platform.architecture()

        # Get special platform name for some method
        LibrariesPlatform = Platform.lower()
        if Platform == "Darwin":
            LibrariesPlatform2nd = "macos"
            LibrariesPlatform2ndOld = "osx"
        else:
            LibrariesPlatform2nd = LibrariesPlatform
            LibrariesPlatform2ndOld = LibrariesPlatform

        # Check platform support
        if Arch[0] == "64bit":
            if Platform not in self.PlatformSupportList:
                print_color(f"You are running on a unsupported platform name {Platform}", color='yellow',
                            tag_color='yellow', tag='Warning')
                print_color(
                    "You can still continue running the launcher. However, you may get some error when you create "
                    "instance.", color='yellow', tag_color='yellow', tag='Warning')
                print_color("If you still want to launch Minecraft. You need to build LWJGL and JDK for your platform.",
                            tag_color='blue', tag='Note')
                continue_running = str(input("Enter Y to ignore: "))
                if continue_running.upper() == "Y":
                    if mode.upper() == "PLATFORM":
                        return Platform
                    elif mode.upper() == "LIBRARIES":
                        return LibrariesPlatform
                    elif mode.upper() == "LIBRARIES_2ND":
                        return LibrariesPlatform2nd
                    elif mode.upper() == "LIBRARIES_2ND_OLD":
                        return LibrariesPlatform2ndOld
                    elif mode.upper() == "ARCH":
                        return Arch
                    else:
                        print_color(f"Base: Unknown args {mode}")
                else:
                    self.EndLoadFlag = True
                    return
            else:
                if mode.upper() == "PLATFORM":
                    return Platform
                elif mode.upper() == "LIBRARIES":
                    return LibrariesPlatform
                elif mode.upper() == "LIBRARIES_2ND":
                    return LibrariesPlatform2nd
                elif mode.upper() == "LIBRARIES_2ND_OLD":
                    return LibrariesPlatform2ndOld
                elif mode.upper() == "ARCH":
                    return Arch
                else:
                    print_color(f"Base: Unknown args {mode}")
                    self.EndLoadFlag = True
                    return None
        else:
            print_color(f"BakeLauncher for 32bit(or other arch) architecture support is untested.")
            print_color(f"You can still continue running the launcher. But you may get some weired bug during use.")
            continue_running = str(input("Enter Y to ignore: "))
            if not continue_running.upper == "Y":
                self.EndLoadFlag = True
                return
            else:
                return Arch

    def check_internet_connect(self):
        if self.PingServerIP is not None:
            if not self.PingServerIP == "None":
                host = self.PingServerIP
            else:
                host = "InternalList"
        else:
            host = "InternalList"

        if Base.NoInternetConnectionCheck:
            return True, "BypassCheckInternetConnection"

        if host == "InternalList":
            for host in self.PingServerHostList:
                host = str(host)
                # Try to establish a socket connection to the host and port
                response = ping(host)
                if not response:
                    print_color(f"Ping to host {host} failed.", tag='Warning')
                else:
                    self.InternetConnected = True
                continue
        else:
            print_color("Using exist host to check internet connection...", tag='INFO')
            response = ping(self.PingServerIP)
            if not response:
                print_color(f"Ping to host {self.PingServerIP} failed.", tag='Warning')
            else:
                self.InternetConnected = True

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
    print_color("Type 'exit' to back to main memu.", color='green')
    type_time = 1
    while True:
        user_input = str(input("BakeLauncher> "))

        if user_input.upper() == "EXIT":
            return True

        if "BAKE" in user_input.upper():
            bake_game()
            return True

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
