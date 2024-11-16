import os
import time
import platform
from print_color import print as print_color

# Beta "Version"("Dev"+"-"+"month(1~12[A~L])/date(Mon~Sun[A~G])"+"Years")
launcher_version = 'Beta 0.9(Dev-KG111624)'

BetaWarningMessage = ("You are running beta version of BakeLauncher.\n"
                      "This is an 'Experimental' version with potential instability.\n"
                      "Please run it only if you know what you are doing.\n")

ChangeLog = ("Changelog:\n"
             ""
             "\n")

global_config = """[BakeLauncher Configuration]

<Global>
DisableClearOutput = false
DefaultAccountID = 1
DontPrintColor = false

<MainMemu>
# Automatic open you want option when launcher load MainMemu
AutomaticOpenOptions = false
Option = None

# ?
DontPrintList = false

<LaunchManager>
# New feature! :)  (Create a new terminal when launching Minecraft. The new terminal won't be killed when the main stop working!
EnableExperimentalMultitasking = true

%Ehh...under this line items have not been implemented yet.
# Automatic launch you want to launch instances
AutomaticLaunch = false
InstancesName = None

# Use old libraries.cfg
UseCustomLibrariesCFG = false
CustomLibrariesCFGPath = None

<AutoTool>
# Get token(Minecraft) from refresh token(or name "Microsoft Token")
RefreshCustomToken = false
RefreshToken = None

# Save the token given by the user
SaveCustomToken = false
Token = None
Username = None
UUID = None

<DownloadTool>
# Automatic download you want Minecraft version
AutomaticDownVersion = true
Version = None
"""

# Default value for some settings
DontPrintColor = False
DisableClearOutput = False
global_config_path = os.path.join("data/config.bakelh.cfg")


def print_custom(*args, **kwargs):
    if not DontPrintColor:
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
    global DontPrintColor, DisableClearOutput
    with open("data/config.bakelh.cfg", 'r') as file:
        for line in file:
            if "DisableClearOutput" in line:
                DisableClearOutput = line.split('=')[1].strip().upper() == "TRUE"
                break

            if "DontPrintColor" in line:
                DontPrintColor = line.split('=')[1].strip().upper() == "TRUE"

    if DontPrintColor:
        print_color("Colorful text has been disabled.", tag='Global')
    if DisableClearOutput:
        print_color("Clear Output has been disabled.", tag='Global')


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
        self.DontPrintColor = False
        self.DisableClearOutput = False
        self.EndLoadFlag = False
        self.MainMemuResetFlag = False
        self.global_config_path = os.path.join("data/config.bakelh.cfg")

    def Initialize(self):
        if self.EndLoadFlag:
            print("Launcher /")
            return

        # Check workdir(If launcher running in a non-ASCII path)
        try:
            work_dir = os.getcwd()
            work_dir.encode('ascii')
        except UnicodeEncodeError:
            print_color("Warning: The launcher is running in a directory with non-ASCII characters.", color='yellow')
            print_color("You may get failed to launch when you enable EnableExperimentalMultitasking support.",
                        color='yellow')
            print_color("This bug has been confirmed if the user are using Windows(other systems are unverified).",
                        color='yellow')
            continue_load = str(input("Enter Y to ignore this warning: "))
            if not continue_load.upper() == "Y":
                return

        # Load config
        if not os.path.exists("data/config.bakelh.cfg"):
            initialize_config()
        else:
            load_setting()

        # Set window(terminal?) title
        if self.Platform == "Windows":
            os.system(f"title BakeLauncher {launcher_version}")
        elif self.Platform == "Darwin":
            os.system(rf'echo -ne "\033]0;BakeLauncher {launcher_version}\007"')
        elif self.Platform == "Linux":
            os.system(f'echo -ne "\033]0;BakeLauncher {launcher_version}\007"')

        return True

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
