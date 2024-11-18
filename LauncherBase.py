import os
import time
import platform
from print_color import print as print_color

# Beta "Version"("Dev"+"-"+"month(1~12[A~L])/date(Mon~Sun[A~G])"+"Years")
launcher_version = 'Beta 0.9(Dev-KA111824)'

BetaWarningMessage = ("You are running beta version of BakeLauncher.\n"
                      "This is an 'Experimental' version with potential instability.\n"
                      "Please run it only if you know what you are doing.\n")

ChangeLog = ("Changelog:\n"
             ""
             "\n")

global_config = """[BakeLauncher Configuration]

<Global>
DontPrintColor = false
DisableClearOutput = false
DefaultAccountID = 1
LauncherWorkDir = "None"

<MainMemu>
# Automatic open you want option when launcher load MainMemu
AutomaticOpenOptions = false
Option = None

# 
NoList = false

<LaunchManager>
Create a new terminal when launching Minecraft. The new terminal won't be killed when the main stop working.
EnableExperimentalMultitasking = true

# Automatic launch you want to launch instances
AutomaticLaunch = false
InstancesName = None

# Use old libraries.cfg
UseCustomLibrariesCFG = false
CustomLibrariesCFGPath = None

<AccountManager>
# Get token(Minecraft) from refresh token(or name "Microsoft Token")
RefreshCustomToken = false
RefreshToken = None

# Save the token given by the user
SaveCustomToken = false
Token = None
Username = None
UUID = None

<Create_Instance>
# Automatic download you want Minecraft version
AutomaticDownVersion = true

# If a same version is already installed in the runtimes folder, reinstall it(but bypass ask user)
OverwriteJVMIfExist = False
Version = None
"""

# Default value for some settings
DontPrintColor = False
DisableClearOutput = False
NoList = False
global_config_path = os.path.join("data/config.bakelh.cfg")


def print_custom(*args, **kwargs):
    if not Base.DontPrintColor:
        color = kwargs.pop('color', None)  # Remove color from kwargs if it exists
        print_color(*args, color=color, **kwargs)  # Pass remaining args and color
    else:
        print(*args)


def initialize_config():
    print_custom("Can't find config! Creating...", color='yellow')
    if not os.path.exists("data"):
        os.makedirs("data")
    if not os.path.exists(global_config_path):
        with open(global_config_path, "w") as config:
            config.write(global_config)


# Load config file if it exists
def load_setting():
    with open("data/config.bakelh.cfg", 'r') as file:
        for line in file:
            if "DisableClearOutput" in line:
                Base.DisableClearOutput = line.split('=')[1].strip().upper() == "TRUE"

            if "DontPrintColor" in line:
                Base.DontPrintColor = line.split('=')[1].strip().upper() == "TRUE"

            if "NoList" in line:
                Base.NoList = line.split('=')[1].strip().upper() == "TRUE"

            if "OverwriteJVMIfExist" in line:
                Base.OverwriteJVMIfExist = line.split('=')[1].strip().upper() == "TRUE"

            if "UsingLegacyDownloadOutput" in line:
                Base.UsingLegacyDownloadOutput = line.split('=')[1].strip().upper() == "TRUE"

            if "LauncherWorkDir" in line:
                Base.LauncherWorkDir = line.split('=')[1].strip().strip('"').strip("'")

    if Base.DontPrintColor:
        print_color("Colorful text has been disabled.", tag='Global')
    if Base.DisableClearOutput:
        print_color("Clear Output has been disabled.", tag='Global')
    if Base.NoList:
        print_color("Print list Has been disabled.", tag='Global')
    if Base.LauncherWorkDir is not None:
        if not Base.LauncherWorkDir == "None" or Base.LauncherWorkDir == "null":
            print_color("Launcher workDir has been set by exist config.", tag='Global')


def ClearOutput():
    if not DisableClearOutput:
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


def timer(seconds):
    for remaining in range(seconds, 0, -1):
        # Determine the color based on the remaining time
        if remaining <= 4:
            c = "red"  # Red
        else:
            c = "white"  # White

        # Print the remaining time with color and overwrite previous output
        print_custom(f"Back to main menu...{remaining} \033[0m", end='\r', color=c)

        # Wait for 1 second
        time.sleep(1)

    # To clear the line after the timer ends
    print(" " * 20, end='\r')


class LauncherBase:
    def __init__(self):
        self.PlatformSupportList = ["Windows", "Darwin", "Linux"]
        self.Platform = self.get_platform("platform")
        self.LibrariesPlatform = self.get_platform("libraries")
        self.LibrariesPlatform2nd = self.get_platform("libraries_2nd")
        self.LibrariesPlatform2ndOld = self.get_platform("libraries_2nd_old")
        self.Arch = self.get_platform("Arch")
        self.DontPrintColor = False  # Stop print colorful text
        self.DisableClearOutput = False  # Debug
        self.EndLoadFlag = False  # If load process failed(platform check failed), Set to True
        self.MainMemuResetFlag = False  # Set to true by check_account_data_are_valid
        self.NoList = False  # Make main_memu not print the list
        self.AutomaticOpenOptions = False  # Start selected option when load main_memu
        self.AutoOpenOptions = None  # Select option
        self.OverwriteJVMIfExist = False
        self.UsingLegacyDownloadOutput = False
        self.LauncherWorkDir = None
        self.launcher_root_dir = os.getcwd()
        self.global_config_path = os.path.join(self.launcher_root_dir, "data/config.bakelh.cfg")

    def Initialize(self):
        global DontPrintColor

        if self.EndLoadFlag:
            print("Launcher /")
            return

        # Load config
        if not os.path.exists("data/config.bakelh.cfg"):
            initialize_config()
        else:
            load_setting()

        # Check workdir(If launcher running in a non-ASCII path)(Also
        try:
            if self.LauncherWorkDir is not None and self.LauncherWorkDir != "None":
                os.chdir(self.LauncherWorkDir)
                print_color(f'Launcher workDir now is "{self.LauncherWorkDir}"', color='green')
            else:
                os.chdir(self.launcher_root_dir)

        except UnicodeEncodeError:
            print_color("Warning: The launcher is running in a directory with non-ASCII characters.", color='yellow')
            print_color("You may get failed to launch when you enable EnableExperimentalMultitasking support.",
                        color='yellow')
            print_color("This bug has been confirmed if the user are using Windows(other systems are unverified).",
                        color='yellow')
            continue_load = str(input("Enter Y to ignore this warning: "))
            if not continue_load.upper() == "Y":
                return

        # Set window(terminal?) title
        if self.Platform == "Windows":
            os.system(f"title BakeLauncher {launcher_version}")
        elif self.Platform == "Darwin":
            os.system(rf'echo -ne "\033]0;BakeLauncher {launcher_version}\007"')
        elif self.Platform == "Linux":
            os.system(f'echo -ne "\033]0;BakeLauncher {launcher_version}\007"')

        DontPrintColor = self.DontPrintColor

        return True

    def load_setting_lightweight(self, **kwargs):
        # Don't ask why LauncherBase has two load_setting. ONE is version lightweight!
        ConfigPath = kwargs.get('CfgPath', None)
        if not ConfigPath is None:
            self.global_config_path = ConfigPath

        with open(self.global_config_path, 'r') as file:
            for line in file:
                if "DisableClearOutput" in line:
                    self.DisableClearOutput = line.split('=')[1].strip().upper() == "TRUE"

                if "DontPrintColor" in line:
                    self.DontPrintColor = line.split('=')[1].strip().upper() == "TRUE"

                if "NoList" in line:
                    self.NoList = line.split('=')[1].strip().upper() == "TRUE"

                if "OverwriteJVMIfExist" in line:
                    self.OverwriteJVMIfExist = line.split('=')[1].strip().upper() == "TRUE"

                if "UsingLegacyDownloadOutput" in line:
                    self.UsingLegacyDownloadOutput = line.split('=')[1].strip().upper() == "TRUE"

                if "LauncherWorkDir" in line:
                    self.LauncherWorkDir = line.split('=')[1].strip().strip('"').strip("'")

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


Base = LauncherBase()


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
