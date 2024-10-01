"""
Some stuff...
"""
import platform
import os
import time
from print_color import print

# Beta "Version"("Pre"+"-"+"month(1~12[A~L])/date(Mon~Sun[A~G])"+"Years")
launcher_version = "Beta 0.7"

BetaWarringMessage = ("You are running beta version of BakeLauncher.\n"
                      "This is an 'Experimental' version with potential instability.\n"
                      "Please run it only if you know what you are doing.\n")

ChangeLog = ("Changelog:\n"
             "Biggest Update!(I think)\n"
             "Now using local natives(When you download Minecraft it will automatic unzip to .minecraft/natives "
             "folder).\n"
             "Added download jvm after download game files.\n"
             "All old instances will be convert to new file structure(legacy_patch)\n"
             "Main Memu has been separated from main!\n"
             "Fully support Windows!"
             "Added experimental macOS, Linux(untested) support.\n"
             "Using unix-like system user launch use LWJGL 3.x version of Minecraft may got crash(unzip natives file "
             "structure are not correctly installed)\n"
             "Added experimental download snapshot support!\n"
             "Fix AssetsGrabber assets_index.json file not found error."
             "Linux user may got error when using internal jvm! (Please using BakeLauncher to download Java!)"
             "\n")


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
            return "Unsupported"
            print("Warning! BakeLauncher are not supported on this platform :(")
            print("Launcher can still run on this platform, but you may encounter serious issues with the file system!")
            return "Unsupported"

    def check_platform_arch_and_return(self):
        if self.platformArch == "64Bit":
            return "OK"
        else:
            return "Unsupported"


GetPlatformName = PlatformCheck()
