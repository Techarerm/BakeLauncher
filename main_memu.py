"""
BakeLaunch Main Memu
(Main memu has been separated from main since Beta 0.7(Pre-hg30824)
"""
import platform




import os
import sys
import time
import print_color
import json
import __init__
from auth_tool import login
from launch_client import launch
from Download import download_main
from launch_version_patcher import patcher_main
from launch_version_patcher import generate_jar_paths
from jvm_path_finder import java_finder
from assets_grabber import get_asset
from print_color import print
from __init__ import ChangeLog
from __init__ import launcher_version
from __init__ import BetaWarringMessage
from __init__ import ClearOutput

def back_to_memu(platform):
    os.system('cls')
    main_memu(platform)


def timer(seconds):
    for remaining in range(seconds, 0, -1):
        if remaining < 4:
            p = "red"
        else:
            p = "white"
        print(f"Back to main memu...{remaining}", end='\r', color=p)
        time.sleep(1)

def login_status():
    """
    Check login status.
    Avoid Minecraft crash on auth... However, if the token expires, it will still crash on launch :)
    """
    username = "Player"  # Initialize username to avoid UnboundLocalError-
    try:
        with open('data/AccountData.json', 'r') as file:
            data = json.load(file)
            username = data['AccountName']  # Set username here
    except (FileNotFoundError, json.JSONDecodeError):
        initialize_account_data()
        with open('data/AccountData.json', 'r') as file:
            data = json.load(file)
            username = data['AccountName']

    if data['AccountName'] == "None":
        print("Login Status: Not logged in :(", color='red')
        print("Please log in to your account first!", color='red')
    else:
        print("Login Status: Already logged in :)", color='green')
        print("Hi,", username, color="blue")  # Now this should work correctly


def main_memu(platform):
    time.sleep(1)
    ClearOutput(platform)
    print('"BakeLauncher Main Menu"', color='blue')
    print("Version: " + launcher_version, color='green')

    # Check login status
    login_status()

    print("What would you like to do?")
    print("1. Launch Minecraft 2. Log in 3. Clear login data (for expired session)")
    print("4: DownloadTool 5: Configure Java 6: About 7: Exit launcher")

    try:
        user_input = int(input(":"))
        if user_input == int:
            print("BakeLauncher: Invalid type :(", color='red')
            print("Please check you type option is number and try again!", color='yellow')
            back_to_memu(platform)
        if user_input == 1:
            print("Launching Minecraft...", color='green')
            os.system('cls')
            launch()
            back_to_memu(platform)
        elif user_input == 2:
            login()
            back_to_memu(platform)
        elif user_input == 3:
            print("Cleaning login data...", color='purple')
            initialize_account_data()
            print("Login data cleared.", color='blue')
            back_to_memu(platform)
        elif user_input == 4:
            root = os.getcwd()
            download_main()
            os.chdir(root)
            back_to_memu(platform)
        elif user_input == 5:
            java_finder()
            back_to_memu(platform)
        elif user_input == 6:
            print("POWERED BY BAKE!", color="yellow")
            print("BakeLauncher " + launcher_version, color='yellow')
            print("Contact Me :) TedKai/@Techarerm", color="blue")
            print("Source code: https://github.com/Techarerm/BakeLauncher", color='yellow')
            print("Also check my website :) https://techarerm.com", color="blue")
            print(" ")
            print(ChangeLog, color='cyan')
            timer(10)
            back_to_memu(platform)
        elif user_input == 7:
            print("Exiting launcher...", color='green')
            print("Bye :)", color='blue')
            print(" ")
        else:
            print(f"BakeLauncher: Can't found option {user_input} :( ", color='red')
            print("Please check you type option's number and try again!", color='yellow')
            time.sleep(1.2)
            back_to_memu(platform)

    except ValueError:
        # Back to main avoid crash(when user type illegal thing)
        print("BakeLaunch: Oops! Invalid option :O  Please enter a number.", color='red')
        time.sleep(1.2)
        back_to_main()