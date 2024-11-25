"""
BakeLaunch Main Memu
(Main memu has been separated from main since Beta 0.7(Pre-hg30824)
"""

import os
import time
from libs.__account_manager import account_manager
from LauncherBase import Base, ChangeLog, ClearOutput, bake_game, print_custom as print
from libs.launch_manager import LaunchManager
from libs.__create_instance import create_instance
from libs.jvm_tool import java_finder, initialize_jvm_config
from libs.args_manager import argsman
from libs.__instance_manager import instance_manager

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


def back_to_memu():
    ClearOutput()
    main_memu()


def bake_bake():
    print("POWERED BY BAKE!", color="yellow")
    print("BakeLauncher " + Base.launcher_version, color='yellow')
    print("Contact Me :) TedKai/@Techarerm", color="blue")
    print("Source code: https://github.com/Techarerm/BakeLauncher", color='yellow')
    if "Dev" in Base.launcher_version:
        print("This bread isn't baked yet?", color='blue')
    elif "Beta" in Base.launcher_version:
        print("Almost done? (Just wait...like 1 years?)", color='blue')
    print(" ")
    print(ChangeLog, color='cyan')
    print("Type 'exit' to back to main memu.", color='green')
    type_time = 1
    while True:
        user_input = str(input("BakeLauncher> "))

        if user_input.upper() == "EXIT":
            return True

        if "BAKE" in user_input.upper():
            bake_game()
            return True

        if type_time == 1:
            print(f"?{user_input}")
            type_time += 1
        elif type_time == 2:
            print(f"!{user_input}")
            type_time += 1
        elif type_time == 3:
            print(f"???{user_input}")
            type_time = 1


def extra_memu():
    if not Base.NoList:
        print("Extra list:")
        print("1: Custom Args             4: Clear ErrorMessage ")
        print("2: Reset AccountData.json  5: Convert Old Instance Structure")
        print("3: Clear JVM config file   6: Auto-Convert Old Instance Structure")
    user_input = str(input(":"))
    while True:
        if user_input == "1":
            argsman()
            return
        elif user_input == "2":
            print("Resting AccountData.json...", color='purple')
            account_manager.initialize_account_data()
            print("AccountData.json has been cleared.", color='blue')
            return
        elif user_input == "3":
            print("Clear JVM config...", color='purple')
            initialize_jvm_config()
            print("JVM config has been cleared.", color='blue')
            return
        elif user_input == "4":
            print("Clearing ErrorMessage...", color='green')
            ErrorMessageList.clear()
            print("ErrorMessage has been cleared.", color='green')
            return
        elif user_input == "5":
            instance_manager.legacy_instances_convert()
            return
        elif user_input == "6":
            instance_manager.legacy_instances_convert(automatic_convert=True)
            return
        elif user_input.upper() == "7" or user_input.upper() == "EXIT":
            return
        else:
            print("Unknown options :O", color='red')
            time.sleep(1.2)


def main_memu():
    print('"BakeLauncher Main Menu"', color='blue')
    print("Version: " + Base.launcher_version_display, color='green')

    # Check login status
    account_manager.login_status()
    if Base.MainMemuResetFlag:
        ClearOutput()
        Base.MainMemuResetFlag = False
        main_memu()
        return

    # Return error message
    error_return("", "Read")
    if not Base.NoList:
        print("What would you like to do?")
        print("1. Launch Minecraft 2. AccountManager 3: Create Instance")
        print("4: Extra 5: About")

    try:
        user_input = str(input(":"))
        if user_input == "1":
            print("Launching Minecraft...", color='green')
            LaunchMessage = LaunchManager()
            error_return(LaunchMessage, "Write")
            back_to_memu()
        elif user_input == "2":
            AccountMSCMessage = account_manager.AccountManager()
            error_return(AccountMSCMessage, "Write")
            back_to_memu()
        elif user_input == "3":
            root = os.getcwd()
            create_instance.create_instance()
            os.chdir(root)
            back_to_memu()
        elif user_input == "4":
            extra_memu()
            back_to_memu()
        elif user_input == "5":
            bake_bake()
            back_to_memu()
        elif user_input.upper() == "EXIT":
            print("Exiting launcher...", color='green')
            print("Bye :)", color='blue')
            print(" ")
            return
        elif user_input.upper() == "RELOAD":
            # Soft reload(reset?) launcher
            Base.load_setting()
            ErrorMessageList.clear()
            ClearOutput()
            main_memu()
            return
        else:
            print(f"BakeLauncher: Can't found option {user_input} :( ", color='red')
            print("Please check you type option's number and try again!", color='yellow')
            time.sleep(1.2)
            back_to_memu()

    except ValueError:
        # Back to main avoid crash(when user type illegal thing)
        print("BakeLauncher: Oops! Invalid option :O  Please enter a number.", color='red')
        time.sleep(1.2)
        back_to_memu()
