"""
Main
"""
import argparse
import main_memu
import time
import args_manager
import __function__
import multiprocessing
from args_manager import parse_arguments
from print_color import print
from main_memu import main_memu
from __function__ import GetPlatformName, ClearOutput, BetaWarringMessage


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
    enable_args_check = False
    print("BakeLauncher: Check running platform...", color="green")
    platformName = GetPlatformName.check_platform_valid_and_return()
    ErrorCheck = GetPlatformName.check_platform_arch_and_return()
    custom_args = args_check(platformName, enable_args_check)
    try:
        if custom_args is None:
            if ErrorCheck:
                # Call args_check to see if --args was provided and handle appropriately
                print(f"BakeLauncher: Launcher are running on platform name: {platformName}", color="blue")
                ClearOutput(GetPlatformName.check_platform_valid_and_return())
                print(BetaWarringMessage, color="yellow")
                time.sleep(1)
                ClearOutput(platformName)
                main_memu(platformName)
            else:
                print("BakeLauncher: Sorry :( BakeLauncher never plan for other arch system support :(",
                      color="red")
    except ValueError:
        print("It working on my machine :( why you can't...", color="red")

    print("BakeLauncher thread terminated!")
    input("Press any key to continue...")

if __name__ == "__main__":
    # Added multitasking(?) support(for LaunchClient)
    multiprocessing.freeze_support()
    main()
