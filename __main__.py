"""
Main
"""
import argparse
import main_memu
import time
import args_manager
import multiprocessing
from print_color import print
from main_memu import main_memu
from LauncherBase import GetPlatformName, ClearOutput, BetaWarringMessage


def args_check(platform, enable_args_check):
    # Create a basic ArgumentParser
    parser = argparse.ArgumentParser(description="BakeLauncher Custom Argument method.")

    # Add the `--args` flag
    parser.add_argument('--args', action='store_true', help="Enable BakeLauncher Custom Argument method.")

    # Parse only the `--args` flag (to see if it's present)
    args, remaining_args = parser.parse_known_args()

    # Check if `--args` was passed
    if args.args:
        enable_args_check = True

        # Pass remaining arguments to argsman if --args was found
        print("BakeLauncher Custom arguments are enabled!", color="purple")

        # Pass the remaining arguments to argsman
        custom_args = args_manager.parse_arguments(platform, remaining_args)

        return True  # Return parsed custom arguments from argsman
    else:
        enable_args_check = False
        print("BakeLauncher are running without custom arguments!", color='blue')
        return None


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

    # Call args_check to see if --args was provided and handle appropriately(if is it will call parse_arguments from
    # args_manager)
    enable_args_check = False
    custom_args = args_check(platformName, enable_args_check)
    try:
        # Running on without custom_args mode!
        if custom_args is None:
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
    except ValueError:
        # ?
        print("It working on my machine :( why you can't...", color="red")

    print("BakeLauncher thread terminated!")
    input("Press any key to continue...")


if __name__ == "__main__":
    # Added multitasking(?) support(for LaunchClient and pyinstaller...)
    multiprocessing.freeze_support()
    main()
