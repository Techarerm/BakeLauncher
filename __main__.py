"""
Main
"""

import main_memu
import time
from print_color import print
from main_memu import main_memu
from __function__ import GetPlatformName, ClearOutput, BetaWarringMessage

def main():
    print("BakeLauncher: Check running platform...", color="green")
    platformName = GetPlatformName.check_platform_valid_and_return()
    ErrorCheck = GetPlatformName.check_platform_arch_and_return()
    try:
        if ErrorCheck:
            print(f"BakeLauncher: Launcher are running on platform name: {platformName}", color="blue")
            ClearOutput(GetPlatformName.check_platform_valid_and_return())
            print(BetaWarringMessage, color="yellow")
            time.sleep(1)
            ClearOutput(platformName)
            main_memu(platformName)
        else:
            print("BakeLauncher: Sorry :( BakeLauncher never plan for other arch system support :(", color="red")
    except ValueError:
        print("It working on my machine :( why you can't...", color="red")

    print("BakeLauncher thread terminated!")
    input("Press any key to continue...")

if __name__ == "__main__":
    main()
