"""
BakeLaunch Main Memu
(Main memu has been separated from main since Beta 0.7(Pre-hg30824)
"""

import os
import time
from auth_tool import AccountManager, initialize_account_data, login_status
from LauncherBase import ChangeLog, launcher_version, ClearOutput, timer
from launch_client import LaunchManager
from Download import download_main
from jvm_tool import java_finder
from args_manager import argsman
from print_color import print



def back_to_memu(platform):
    if platform == "Windows":
        print("Clearing output...")
        os.system("cls")
        main_memu(platform)
    else:
        print("Clearing output...")
        os.system("clear")
        main_memu(platform)


def main_memu(platform):
    print('"BakeLauncher Main Menu"', color='blue')
    print("Version: " + launcher_version, color='green')

    # Check login status
    login_status()

    print("What would you like to do?")
    print("1. Launch Minecraft 2. AccountManager 3: DownloadTool")
    print("4: Configure Java 5: About 6: Exit launcher 7: Extra")

    try:
        user_input = int(input(":"))
        if user_input == int:
            print("BakeLauncher: Invalid type :(", color='red')
            print("Please check you type option is number and try again!", color='yellow')
            back_to_memu(platform)
        if user_input == 1:
            print("Launching Minecraft...", color='green')
            ClearOutput(platform)
            LaunchManager()
            ClearOutput(platform)
            back_to_memu(platform)
        elif user_input == 2:
            AccountManager()
            back_to_memu(platform)
        elif user_input == 3:
            root = os.getcwd()
            download_main()
            os.chdir(root)
            back_to_memu(platform)
        elif user_input == 4:
            java_finder()
            back_to_memu(platform)
        elif user_input == 5:
            print("POWERED BY BAKE!", color="yellow")
            print("BakeLauncher " + launcher_version, color='yellow')
            print("Contact Me :) TedKai/@Techarerm", color="blue")
            print("Source code: https://github.com/Techarerm/BakeLauncher", color='yellow')
            print(" ")
            print(ChangeLog, color='cyan')
            timer(10)
            back_to_memu(platform)
        elif user_input == 6:
            print("Exiting launcher...", color='green')
            print("Bye :)", color='blue')
            print(" ")
        elif user_input == 7:
            print("Extra list:")
            print("1: Custom Args 2: Reset AccountData.json")
            user_input = int(input(":"))
            try:
                if user_input == 1:
                    argsman()
                    back_to_memu(platform)
                    return
                elif user_input == 2:
                    print("BakeLauncher: Resting AccountData.json...", color='purple')
                    initialize_account_data()
                    print("BakeLauncher: AccountData.json has been cleared.", color='blue')
                    back_to_memu(platform)
                else:
                    print("Unknown options :O", color='red')
                    back_to_memu(platform)
            except ValueError:
                print("Invalid type :(", color='red')
        else:
            print(f"BakeLauncher: Can't found option {user_input} :( ", color='red')
            print("Please check you type option's number and try again!", color='yellow')
            time.sleep(1.2)
            back_to_memu(platform)

    except ValueError:
        # Back to main avoid crash(when user type illegal thing)
        print("BakeLaunch: Oops! Invalid option :O  Please enter a number.", color='red')
        time.sleep(1.2)
        back_to_memu(platform)
