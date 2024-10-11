"""
Main
(BakeLauncher Main)
CheckArch(Call LauncherBase)>GetPlatformName>Load Main_Memu>Ended
"""
import main_memu
import time
import multiprocessing
from print_color import print
from main_memu import main_memu
from LauncherBase import GetPlatformName, ClearOutput, BetaWarringMessage




def main():
    """
    Main(Just main :D )
    Check platform and arch support > check args > main_memu or parse_arguments > terminated
    """
    global CheckArchSupport
    # Just check running platform name :) (Only support Windows, macOS, Linux and arch must be 64Bit!)
    print("BakeLauncher: Check running platform...", color="green")
    platformName = GetPlatformName.check_platform_valid_and_return()

    # Check launcher are running on 64Bit os(BakeLauncher not support to Download 32Bit necessary file)
    CheckArchSupport = False
    CheckArchSupport = GetPlatformName.check_platform_arch_and_return()

    if CheckArchSupport == True:
        print(f"BakeLauncher: Launcher are running on platform name: {platformName}", color="blue")
        ClearOutput(GetPlatformName.check_platform_valid_and_return())
        print(BetaWarringMessage, color="yellow")
        time.sleep(1.5)
        ClearOutput(platformName)
        main_memu(platformName)
    else:
        print("BakeLauncher: Sorry :( BakeLauncher never plan for other arch system support :(",
              color="red")

    print("BakeLauncher thread terminated!")
    input("Press any key to continue...")


if __name__ == "__main__":
    # Added multitasking(?) support(for LaunchClient and pyinstaller...)
    multiprocessing.freeze_support()
    main()
