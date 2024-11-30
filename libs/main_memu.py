"""
BakeLaunch Main Memu
(Main memu has been separated from main since Beta 0.7(Pre-hg30824)
"""

import os
import time
from libs.__account_manager import account_manager
from LauncherBase import Base, bake_bake, ClearOutput, print_custom as print, timer
from libs.launch_manager import LaunchManager
from libs.__create_instance import create_instance
from libs.__duke_explorer import Duke
from libs.args_manager import argsman
from libs.__instance_manager import instance_manager
from libs.__args_manager import args_manager

ErrorMessageList = []
ErrorMessageOutputRange = 0


def error_return(ErrorMessage, mode):
    global ErrorMessageList, ErrorMessageOutputRange
    if ErrorMessage is None:
        return
    if mode == "Write":
        ErrorMessageList.append(ErrorMessage)
    elif mode == "Read":
        if ErrorMessageOutputRange == 3:
            ErrorMessageOutputRange = 0
            return
        if ErrorMessageList and len(ErrorMessageList[0].strip()) > 0:
            ErrorMessageOutputRange += 1
            print("Latest Error Message:", ErrorMessageList[-1], color='red')


def extra_memu():
    while True:
        if not Base.NoList:
            print("Extra list:")
            print("1: Custom Args             5: Convert Old Instance Structure ")
            print("2: Reset AccountData.json  6: Auto-Convert Old Instance Structure")
            print("3: Clear JVM config file   7: Search Java Runtimes(Duke)")
            print("4: Clear ErrorMessage      ", end='')
            print("8: [Exp]Custom Args", color='purple')
        user_input = str(input(":"))
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
            Duke.initialize_jvm_config()
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
        elif user_input.upper() == "7":
            Duke.duke_finder()
            return
        elif user_input.upper() == "8":
            print("Warning: This is a re-code version. Not sure all functions will working file", color='red')
            time.sleep(4)
            args_manager.ArgsMemu()
            return
        elif user_input.upper() == "9" or user_input.upper() == "EXIT":
            return True
        else:
            print("Unknown options :O", color='red')
            time.sleep(1.2)


def main_memu():
    while True:
        print('"BakeLauncher Main Menu"', color='blue')
        print("Version: " + Base.launcher_version_display, color='green')

        # Check login status
        account_manager.login_status()
        if Base.MainMemuResetFlag:
            ClearOutput()
            Base.MainMemuResetFlag = False
            return

        # Return error message(if it find)
        error_return("", "Read")
        if not Base.NoList:
            print("What would you like to do?")
            print("1. Launch Minecraft 2. AccountManager 3: Create Instance")
            print("4: Extra 5: About")

        user_input = str(input(":"))
        if user_input == "1":
            print("Launching Minecraft...", color='green')
            LaunchMessage = LaunchManager()
            error_return(LaunchMessage, "Write")
        elif user_input == "2":
            AccountMSCMessage = account_manager.AccountManager()
            error_return(AccountMSCMessage, "Write")
        elif user_input == "3":
            create_instance.create_instance()
        elif user_input == "4":
            extra_memu()
        elif user_input == "5":
            bake_bake()
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
        elif user_input.upper() == "DEBUG_CRASH":
            timer("Crash in 5 sec", 5)
            crash_me = user_input
            crash_me = int(crash_me)
        else:
            print(f"BakeLauncher: Can't found option {user_input} :( ", color='red')
            print("Please check you type option's number and try again!", color='yellow')
            time.sleep(1.8)

        # restore environment
        os.chdir(Base.launcher_root_dir)
        ClearOutput()
