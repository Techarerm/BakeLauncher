"""
LauncherBase
Some stuff...
"""
import platform
import os
import time
from print_color import print

# Beta "Version"("Dev"+"-"+"month(1~12[A~L])/date(Mon~Sun[A~G])"+"Years")
launcher_version = "Beta 0.8(Dev-JG102024)"

BetaWarringMessage = ("You are running beta version of BakeLauncher.\n"
                      "This is an 'Experimental' version with potential instability.\n"
                      "Please run it only if you know what you are doing.\n")

ChangeLog = ("Changelog:\n"
             "MultiTask+ Update!\n"
             ""
             "AccountManager(AutoTool): Added support for multiple accounts!\n"
             "LaunchClient: Added support for multiple client! Now you can launch several clients at same time!\n"
             "ArgsManager: Added support for custom args! Now you can go to Extra > 1: Custom Args to set custom args!\n"
             "\n")

def initialize_config():
    print("Can't find config! Creating...", color='yellow')
    default_data = ('[BakeLauncher Configuration]\n\n<Global>\nEnableConfig = true\nDefaultAccountID = 1\n<LaunchManager>'
                    '\nEnableExperimentalMultitasking = true')
    if not os.path.exists('data'):
        os.makedirs('data')
    with open('data/config.bakelh.cfg', 'w') as file:
        file.write(default_data)


def ClearOutput(platform):
    if platform == "Windows":
        print("Clearing output...")
        os.system("cls")
    elif platform == "Darwin":
        print("Clearing output...")
        os.system("clear")
    elif platform == "Linux":
        print("Clearing output...")
        os.system("clear")
    else:
        print("Unsupported platform! Bypassing ClearOutput...")


def timer(seconds):
    for remaining in range(seconds, 0, -1):
        # Determine the color based on the remaining time
        if remaining <= 4:
            c = "red"  # Red
        else:
            c = "white"  # White

        # Print the remaining time with color and overwrite previous output
        print(f"Back to main menu...{remaining} \033[0m", end='\r', color=c)

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


GetPlatformName = PlatformCheck()


cfg_text = """[BakeLauncher Configuration]

<Global>
EnableConfig = true
DefaultAccountID = 1

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