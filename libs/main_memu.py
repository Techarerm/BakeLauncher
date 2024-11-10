"""
BakeLaunch Main Memu
(Main memu has been separated from main since Beta 0.7(Pre-hg30824)
"""

import os
import time
from libs.auth_tool import AccountManager, initialize_account_data, login_status
from LauncherBase import ChangeLog, launcher_version, ClearOutput, timer
from libs.launch_manager import LaunchManager
from libs.__create_instance import game_files_grabber
from libs.jvm_tool import java_finder, initialize_jvm_config
from libs.args_manager import argsman
from LauncherBase import print_custom as print

ErrorMessageList = []


def error_return(ErrorMessage, mode):
    global ErrorMessageList
    if ErrorMessage is None:
        return
    if mode == "Write":
        ErrorMessageList.append(ErrorMessage)
    elif mode == "Read":
        if ErrorMessageList and len(ErrorMessageList[0].strip()) > 0:
            print("Latest Error Message:", ErrorMessageList[-1], color='red')


def back_to_memu(platform, workdir):
    ClearOutput(platform)
    main_memu(workdir, platform)


def extra_memu():
    print("Extra list:")
    print("1: Custom Args 2: Reset AccountData.json 3: Clear JVM config file 4: Exit")
    user_input = int(input(":"))
    while True:
        try:
            if user_input == 1:
                argsman()
                return
            elif user_input == 2:
                print("BakeLauncher: Resting AccountData.json...", color='purple')
                initialize_account_data()
                print("BakeLauncher: AccountData.json has been cleared.", color='blue')
                return
            elif user_input == 3:
                print("BakeLauncher: Clear JVM config...", color='purple')
                initialize_jvm_config()
                print("BakeLauncher: JVM config has been cleared.", color='blue')
                return
            elif user_input == 4:
                return
            else:
                print("Unknown options :O", color='red')
                time.sleep(1.2)
        except ValueError:
            print("Invalid type :(", color='red')


def main_memu(workdir, platform):
    print('"BakeLauncher Main Menu"', color='blue')
    print("Version: " + launcher_version, color='green')

    # Check login status
    login_status()
    # Return error message
    error_return("", "Read")
    print("What would you like to do?")
    print("1. Launch Minecraft 2. AccountManager 3: Create Instance")
    print("4: Configure Java 5: About 6: Extra 7: Exit Launcher")

    try:
        user_input = int(input(":"))
        if user_input == int:
            print("BakeLauncher: Invalid type :(", color='red')
            print("Please check you type option is number and try again!", color='yellow')
            back_to_memu(platform, workdir)
        if user_input == 1:
            print("Launching Minecraft...", color='green')
            LaunchMessage = LaunchManager()
            error_return(LaunchMessage, "Write")
            back_to_memu(platform, workdir)
        elif user_input == 2:
            AccountMSCMessage = AccountManager()
            error_return(AccountMSCMessage, "Write")
            back_to_memu(platform, workdir)
        elif user_input == 3:
            root = os.getcwd()
            game_files_grabber.create_instance()
            os.chdir(root)
            back_to_memu(platform, workdir)
        elif user_input == 4:
            java_finder()
            back_to_memu(platform, workdir)
        elif user_input == 5:
            print("POWERED BY BAKE!", color="yellow")
            print("BakeLauncher " + launcher_version, color='yellow')
            print("Contact Me :) TedKai/@Techarerm", color="blue")
            print("Source code: https://github.com/Techarerm/BakeLauncher", color='yellow')
            print(" ")
            print(ChangeLog, color='cyan')
            timer(10)
            back_to_memu(platform, workdir)
        elif user_input == 6:
            extra_memu()
            back_to_memu(platform, workdir)
        elif user_input == 7:
            print("Exiting launcher...", color='green')
            print("Bye :)", color='blue')
            print(" ")
            return
        else:
            print(f"BakeLauncher: Can't found option {user_input} :( ", color='red')
            print("Please check you type option's number and try again!", color='yellow')
            time.sleep(1.2)
            back_to_memu(platform, workdir)

    except ValueError:
        # Back to main avoid crash(when user type illegal thing)
        print("BakeLauncher: Oops! Invalid option :O  Please enter a number.", color='red')
        time.sleep(1.2)
        back_to_memu(platform, workdir)
