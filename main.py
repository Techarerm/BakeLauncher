"""
Main
(BakeLauncher Main)
CheckArch(Call LauncherBase)>GetPlatformName>Load Main_Memu>Ended
"""
import os
import multiprocessing

import LauncherBase
from LauncherBase import GetPlatformName, ClearOutput, BetaWarningMessage
from LauncherBase import print_custom as print
from libs.main_memu import main_memu

class BakeLauncher:
    """
    Main(Just main :D )
    Check platform and arch support > check args > main_memu or parse_arguments > terminated
    """

    def __init__(self):
        self.CheckArchSupport = False
        self.PlatformSupportStatus = False
        self.ErrorStatus = False
        self.platformName = None
        self.LauncherMainDir = os.getcwd()

        # Load LauncherBase
        LauncherBase.initialize_base()


        # Check platform support
        print("BakeLauncher: Check running platform...", color='green')
        self.platformName = GetPlatformName.check_platform_valid_and_return()

        # Check if launcher is running on 64-bit OS (BakeLauncher doesn't support 32-bit files)
        self.CheckArchSupport = GetPlatformName.check_platform_arch_and_return()

        # Start launcher process if checks pass
        if self.CheckArchSupport:
            if self.platformName != "Unsupported":
                self.main(self.platformName)
            else:
                print("BakeLauncher: Your platform is unsupported.", color='red')
                print("BakeLauncher: Failed to load launcher due to an unknown platform.", color='red')
                self.PlatformSupportStatus = False
        else:
            print("BakeLauncher: Sorry :( BakeLauncher does not support other architectures.", color='red')
            print("BakeLauncher: Failed to load launcher due to unknown architecture.", color='red')

        print("BakeLauncher thread terminated!")
        input("Press any key to continue...")

    def main(self, platformName):
        # Set PlatformSupportStatus flag
        self.PlatformSupportStatus = True

        # DEBUG for platform check
        print(f"BakeLauncher: Launcher is running on platform: {platformName}", color='blue')
        ClearOutput(platformName)

        # Print BetaWarningMessage
        print(BetaWarningMessage, color='yellow')
        ClearOutput(platformName)


        # Load main menu
        main_memu(self.LauncherMainDir, platformName)

if __name__ == "__main__":
    # Added multitasking(?) support(for LaunchClient and pyinstaller...)
    multiprocessing.freeze_support()
    BakeLauncher()