"""
Some stuff...
"""
import print_color
import platform
import os
import time
from print_color import print


# Beta "Version"("Pre"+"-"+"month(1~12[A~L])/date(Mon~Sun[A~G])"+"Years")
launcher_version = "Beta 0.7(Pre-IG15924)"


# Some repo....
LWJGL_Maven = f"https://repo1.maven.org/maven2/org/lwjgl/lwjgl/"




BetaWarringMessage = ("You are running beta version of BakeLauncher.\n"
                      "This is an 'Experimental' version with potential instability.\n"
                      "Please run it only if you know what you are doing.\n")

ChangeLog = ("Changelog:\n"
             "Fix some grammer problem and add more explain.\n"
             "Fix 1.14~1.14.2 can't launch(forgot add LWJGL 3.2.1 in support list) Sorry :(\n"
             "Recoding some DownloadTool code and add more method :)\n"
             "Using new function to get assetsIndex(Don't need to code version support list....)\n"
             "Versions folder has been renamed to instances!\n"
             "Added license(GPLv3) to Github page.\n")

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

    def check_platform_valid_and_return(self):
        if self.platformName == "Windows":
            return "Windows"
        elif self.platformName == "Darwin":
            return "Darwin"
        elif self.platformName == "Linux":
            return "Linux"
        else:
            return "Unsupported"
            print("Warning! BakeLauncher is not supported on this platform :(")
            print("Launcher can still run on this platform, but you may encounter serious issues with the file system!")
            return "Unsupported"


GetPlatformName = PlatformCheck()
