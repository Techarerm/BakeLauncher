"""
BakeLauncher Main Memu
(Main memu has been separated from main since Beta 0.7(Pre-HG30824)
"""

import os
import time
from libs.__account_manager import account_manager
from LauncherBase import Base, bake_bake, ClearOutput, print_custom as print, timer
from libs.launch_manager import launch_manager
from libs.__create_instance import create_instance
from libs.__duke_explorer import Duke
from libs.__instance_manager import instance_manager
from libs.__args_manager import args_manager

ErrorMessageList = []
ErrorMessageOutputRange = 0
StopAutomaticProcess = False

def error_return(ErrorMessage, mode):
    global ErrorMessageList, ErrorMessageOutputRange
    if ErrorMessage is None:
        return
    if mode == "Write":
        Base.ErrorMessageList.append(ErrorMessage)
    elif mode == "Read":
        if ErrorMessageOutputRange == 3:
            ErrorMessageOutputRange = 0
            return
        if Base.ErrorMessageList and len(Base.ErrorMessageList[0].strip()) > 0:
            ErrorMessageOutputRange += 1
            print("Latest Error Message:", Base.ErrorMessageList[-1], color='red')

def extra_memu():
    while True:
        if not Base.NoList:
            print("Extra list:", color='lightblue')
            print("1: [Exp]Custom Args        5: Convert Old Instance Structure ")
            print("2: Reset AccountData.json  6: Auto-Convert Old Instance Structure")
            print("3: Clear JVM config file   7: Search Java Runtimes(Duke)")
            print("4: Clear ErrorMessage")
        user_input = str(input(":"))
        if user_input == "1":
            print("Warning: This is a re-code version. Not sure all functions will working fine.", color='red')
            time.sleep(2)
            args_manager.ArgsMemu()
            return
        elif user_input == "2":
            print("Resting AccountData.json...", color='purple')
            account_manager.initialize_account_data()
            print("AccountData.json has been cleared.", color='lightblue')
            time.sleep(3)
            return
        elif user_input == "3":
            print("Clear JVM config...", color='purple')
            Duke.initialize_jvm_config()
            print("JVM config has been cleared.", color='lightblue')
            time.sleep(3)
            return
        elif user_input == "4":
            print("Clearing ErrorMessage...", color='lightgreen')
            ErrorMessageList.clear()
            print("ErrorMessage has been cleared.", color='lightblue')
            time.sleep(3)
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
        elif user_input.upper() == "8" or user_input.upper() == "EXIT":
            return True
        else:
            print("Unknown options :O", color='red')
            time.sleep(1.2)


def automatic_process():
    global MemuReset
    if Base.AutomaticLaunch:
        print("Launching Minecraft...", color='m')
        LaunchMessage = launch_manager.launch_game(QuickLaunch=True)
        error_return(LaunchMessage, "Write")
        MemuReset = True
    else:
        MemuReset = False

    if MemuReset:
        Base.MainMemuResetFlag = True


    return True

def main_memu():
    global StopAutomaticProcess
    while True:
        print('"BakeLauncher Main Menu"', color='lightblue')
        print(f"Version: {Base.launcher_version_display}", color='lightgreen')

        # Start some automatic process
        if not StopAutomaticProcess:
            StopAutomaticProcess = automatic_process()

        # Check login status
        account_manager.login_status()
        if Base.MainMemuResetFlag:
            ClearOutput()
            Base.MainMemuResetFlag = False
            main_memu()
            return True

        # Return error message(if it find)
        error_return("", "Read")
        if not Base.NoList:
            print("What would you like to do?")
            print("1. Launch Minecraft 2. AccountManager 3: Create Instance")
            print("4: Extra 5: About")

        user_input = str(input(":"))
        user_input = user_input.strip()
        if user_input == "1":
            print("Launching Minecraft...", color='lightgreen')
            LaunchMessage = launch_manager.launch_game()
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
            print("Exiting launcher...", color='lightgreen')
            print("Bye :)", color='lightblue')
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
        elif user_input.upper() == "QUICKLAUNCH":
            if not Base.QuickLaunch:
                print("Quick Launch is not enable. Please check your config are setting correctly.", color='yellow')
                time.sleep(3)
            else:
                print("Quick launching Minecraft...", color='green')
                LaunchMessage = launch_manager.launch_game(QuickLaunch=True)
                error_return(LaunchMessage, "Write")
        else:
            print(f"BakeLauncher: Can't found option {user_input} :( ", color='lightred')
            print("Please check you type option's number and try again!", color='lightyellow')
            time.sleep(1.8)

        # restore environment
        os.chdir(Base.launcher_root_dir)
        ClearOutput()
