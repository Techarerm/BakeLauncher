"""
Main
"""

import os
import platform
import __init__
import main_memu
import time
from print_color import print
from main_memu import main_memu
from __init__ import GetPlatformName
from __init__ import ClearOutput
from __init__ import BetaWarringMessage

def main():
    print("BakeLauncher: Check running platform...", color="green")
    platformName = GetPlatformName.check_platform_valid_and_return()
    print(f"BakeLauncher: Launcher are running on platform name: {platformName}", color="blue")
    ClearOutput(platformName)
    print(BetaWarringMessage, color="yellow")
    time.sleep(1)
    ClearOutput(platformName)
    main_memu(platformName)
    print("BakeLauncher thread terminated!")
    input("Press any key to continue...")

if __name__ == "__main__":
    main()
