"""
LauncherBase
Some stuff...
"""
import platform
import os
import time
from print_color import print as print_color


# Beta "Version"("Dev"+"-"+"month(1~12[A~L])/date(Mon~Sun[A~G])"+"Years")
launcher_version = 'Beta 0.9(Dev-KG111024)'

BetaWarningMessage = ("You are running beta version of BakeLauncher.\n"
                      "This is an 'Experimental' version with potential instability.\n"
                      "Please run it only if you know what you are doing.\n")

ChangeLog = ("Changelog:\n"
             ""
             "\n")

# Default value for some settings
DontPrintColor = False
DisableClearOutput = False


# Load config file if it exists
def load_setting():
    global DontPrintColor
    global DisableClearOutput
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
        if not os.path.exists("data/config.bakelh.cfg"):
            with open("data/config.bakelh.cfg", "w") as config:
                config.write(cfg_text)


def ClearOutput(platform):
    if not DisableClearOutput:
        if platform == "Windows":
            os.system("cls")
        elif platform == "Darwin":
            os.system("clear")
        elif platform == "Linux":
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


class PlatformCheck:
    def __init__(self):
        self.platformArch = "None"
        self.platformName = "None"
        self.set_platform()

    def set_platform(self):
        self.platformName = platform.system()
        self.platformArch = platform.architecture()

    def check_platform_valid_and_return(self):
        if self.platformName == "Windows":
            return "Windows"
        elif self.platformName == "Darwin":
            return "Darwin"
        elif self.platformName == "Linux":
            return "Linux"
        else:
            print("Warning! BakeLauncher are not supported on this platform :(")
            print("Launcher can still run on this platform, but you may encounter serious issues with the file system!")
            return "Unsupported"

    def check_platform_arch_and_return(self):
        if self.platformArch[0] == "64bit":
            return True
        else:
            return False

def initialize_base():
    if not os.path.exists("data/config.bakelh.cfg"):
        initialize_config()
    else:
        load_setting()

    if GetPlatformName.check_platform_valid_and_return() == "Windows":
        os.system(f"title BakeLauncher {launcher_version}")
    elif GetPlatformName.check_platform_valid_and_return() == "Darwin":
        os.system(rf'echo -ne "\033]0;BakeLauncher {launcher_version}\007"')
    elif GetPlatformName.check_platform_valid_and_return() == "Linux":
        os.system(f'echo -ne "\033]0;BakeLauncher {launcher_version}\007"')



GetPlatformName = PlatformCheck()

cfg_text = """[BakeLauncher Configuration]

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
