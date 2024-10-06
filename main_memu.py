"""
BakeLaunch Main Memu
(Main memu has been separated from main since Beta 0.7(Pre-hg30824)
"""

import os
import time
import json
from auth_tool import AccountManager
from auth_tool import check_minecraft_token
from auth_tool import get_account_data
from launch_client import LaunchManager
from Download import download_main
from jvm_tool import java_finder
from args_manager import argsman
from print_color import print
from __function__ import ChangeLog
from __function__ import launcher_version
from __function__ import ClearOutput
from __function__ import timer


def back_to_memu(platform):
    if platform == "Windows":
        print("Clearing output...")
        os.system("cls")
        main_memu(platform)
    else:
        print("Clearing output...")
        os.system("clear")
        main_memu(platform)


def initialize_config():
    print("Can't find config! Creating...", color='yellow')
    default_data = "[BakeLauncher Configuration]\n\n<Global>\nEnableConfig = true\nDefaultAccountID = 1"
    if not os.path.exists('data'):
        os.makedirs('data')
    with open('data/config.bakelh.cfg', 'w') as file:
        file.write(default_data)


def initialize_account_data():
    if not os.path.exists('data'):
        os.makedirs('data')
    json_data = []

    default_data = {
        "id": 1,
        "Username": 'BakeLauncherLocalPlayer',
        "UUID": "Unknown",
        "RefreshToken": None,  # When auth_tool notice RefreshToken = None it will stop refresh
        "AccessToken": "Unknown",
        "tag": "LocalTESTPlayerDoNOTUSE"
    }

    json_data.append(default_data)

    with open("data/AccountData.json", "w") as jsonFile:
        json.dump(json_data, jsonFile, indent=4)



def login_status():
    """
    Check login status.
    Avoid Minecraft crash on auth... However, if the token expires, it will still crash on launch :)
    """
    username = "Player"  # Initialize username to avoid UnboundLocalError-
    try:
        with open("data/config.bakelh.cfg", 'r') as file:
            for line in file:
                if "DefaultAccountID" in line:
                    id = line.split('=')[1].strip()  # Extract the value if found
                    break  # Stop after finding the ID
    except FileNotFoundError:
        initialize_config()
        id = 1


    if os.path.exists('data/AccountData.json'):
        account_data = get_account_data(int(id))
        username = account_data['Username']  # Set username here
        if account_data['Username'] == "None":
            print("Login Status: Not logged in :(", color='red')
            print("Please log in to your account first!", color='red')
        elif account_data['Username'] == "BakeLauncherLocalPlayer":
            print("Warning: You are currently using a local account!", color='red')
            print("Login Status: Not logged in :(", color='red')
            print("Please log in to your account or switch to a different account.", color='red')
        else:
            ErrorCheck = check_minecraft_token(id)
            if ErrorCheck:
                print("Login Status: Already logged in :)", color='green')
                print("Hi,", username, color="blue")  # Now this should work correctly
            else:
                print("Login Status: Expired session :0", color='red')
                print("Please login your account again!", color='red')
                print("Hi,", username, color="blue")  # Now this should work correctly
    else:
        initialize_account_data()
        username = "Player"
        print("Login Status: Not logged in :(", color='red')
        print("Please log in to your account first!", color='red')

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
            print("Also check my website :) https://techarerm.com", color="blue")
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
            print("1: Custom JVM args 2: Reset AccountData.json")
            user_input = int(input(":"))
            if user_input == 1:
                argsman()
            elif user_input == 2:
                print("BakeLauncher: Resting AccountData.json...",color='purple')
                initialize_account_data()
                print("BakeLauncher: AccountData.json has been cleared.", color='blue')
            back_to_memu(platform)
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
