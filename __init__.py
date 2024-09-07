"""
Some stuff...
"""

import platform
import os

# Beta "Version"("Pre"+"-"+"month(1~12[A~L])/date(Mon~Sun[A~G])"+"Years")
launcher_version = "Beta 0.7(Pre-IF07924)"


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

class PlatformCheck:
    def __init__(self):
        self.platformName = "None"
        self.set_platform()

    def set_platform(self):
        self.platformName = platform.system()

    def check_platform_valid_and_return(self):
        if self.platformName == "Windows":
            return "Windows"
        elif self.platformName == "macOS":
            return "macOS"
        elif self.platformName == "Linux":
            return "Linux"
        else:
            return "Unsupported"
            print("Warning! BakeLauncher is not supported on this platform :(")
            print("Launcher can still run on this platform, but you may encounter serious issues with the file system!")
            return "Unsupported"

# Usage
GetPlatformName = PlatformCheck()