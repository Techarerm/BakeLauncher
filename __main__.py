"""
Warning: This is an 'Experimental' version with potential instability.
So... Run it only if you know what you are doing :)
PyLauncher AKA BakeLauncher
A Minecraft Java launcher written in Python.
"""

import os
import sys
import time

from auth_tool import login
from launch_client import launch
import json
import Download
from Download import download_main
import shutil
from launch_version_patcher import patcher_main
from launch_version_patcher import generate_jar_paths
import jvm_path_finder
from jvm_path_finder import java_finder
from assets_grabber import get_asset
import print_color
from print_color import print

launcher_version = "Beta 0.7(Pre-hc28824)"

def back_to_main():
    os.system('cls')
    main()

def back_to_main_without_cls():
    main()

def initialize_account_data():
    default_data = {
        "AccountName": "None",
        "UUID": "None",
        "Token": "None"
    }
    if not os.path.exists('data'):
        os.makedirs('data')
    with open('data\\AccountData.json', 'w') as file:
        json.dump(default_data, file)

def legacy_version_file_structure_fix():
    if os.path.exists('versions'):
        try:
            print('BakeLaunch: Found Legacy version file structure!', color='green')
            print('BakeLaunch: Trying to convert it......', color='cyan')
            os.renames("versions", "instances")
        except WindowsError:
            print("BakeLaunch:Failed to convert file structure :(", color='red')
            print('BakeLaunch: You may get crash when you try to launch game.', color='red')
    else:
        print('BakeLaunch: Your folder structure are already converted :)', color='blue')

# This function will delete in new update
legacy_version_file_structure_fix()

print("Warning: This is an 'Experimental' version with potential instability.", color='yellow')
print("If you have old instances, BakeLauncher will convert it to Beta 0.7 file structure.", color='purple')
print("NOW SUPPORTS ALL VERSIONS OF MINECRAFT!!!! (Still excludes snapshots :)", color='cyan')
print("Changelog:", color='cyan')
print("Fix some grammer problem and add more explain.", color='green')
print("Fix 1.14~1.14.2 can't launch(forgot add LWJGL 3.2.1 in support list) Sorry :(", color='green')
print("Recoding some DownloadTool code and add more method :)", color='green')
print("Using new function to get assetsIndex(Don't need to code version support list....)", color='green')
print("Versions folder has been renamed to instances!", color='green')
print("Added 'more' color :)", color='blue')
print("Added license(GPLv3) to Github page.", color='blue')
print("Please run it only if you know what you are doing.", color='yellow')
print(" ")

def main():

    print('"BakeLauncher Main Menu"', color='blue')
    print("Version: " + launcher_version, color='green')

    """
    Check login status.
    Avoid Minecraft crash on auth... However, if the token expires, it will still crash on launch :)
    """
    username = "Player"  # Initialize username to avoid UnboundLocalError
    try:
        with open('data\\AccountData.json', 'r') as file:
            data = json.load(file)
            username = data['AccountName']  # Set username here
    except (FileNotFoundError, json.JSONDecodeError):
        initialize_account_data()
        with open('data\\AccountData.json', 'r') as file:
            data = json.load(file)
            username = data['AccountName']

    if data['AccountName'] == "None":
        print("Login Status: Not logged in :(", color='red')
        print("Please log in to your account first!", color='red')
    else:
        print("Login Status: Already logged in :)", color='green')
        print("Hi,", username, color="blue")  # Now this should work correctly
    print("What would you like to do?")
    print("1. Launch Minecraft 2. Log in 3. Clear login data (for expired session)")
    print("4: DownloadTool 5: Configure Java 6: About 7: Exit launcher")

    try:
        user_input = int(input(":"))
        if user_input == int:
            print("BakeLauncher: Invalid type :(", color='red')
            print("Please check you type option is number and try again!", color='yellow')
            back_to_main()
        if user_input == 1:
            print("Launching Minecraft...", color='green')
            os.system('cls')
            launch()
            back_to_main_without_cls()
        elif user_input == 2:
            login()
            back_to_main()
        elif user_input == 3:
            print("Cleaning login data...", color='purple')
            initialize_account_data()
            print("Login data cleared.", color='blue')
            back_to_main()
        elif user_input == 4:
            root = os.getcwd()
            download_main()
            os.chdir(root)
            back_to_main()
        elif user_input == 5:
            java_finder()
            back_to_main_without_cls()
        elif user_input == 6:
            print("POWERED BY BAKE!", color="yellow")
            print("BakeLauncher " + launcher_version, color='yellow')
            print("Contact Me :) TedKai/@Techarerm", color="blue")
            print("Source code: https://github.com/Techarerm/BakeLauncher", color='yellow')
            print("Also check my website :) https://techarerm.com", color="blue")
            time.sleep(10)
            back_to_main()
        elif user_input == 7:
            print("Exiting launcher...", color='green')
            print("Bye :)", color='blue')
            return 0
        else:
            print(f"BakeLauncher: Can't found option {user_input} :( ", color='red')
            print("Please check you type option's number and try again!", color='yellow')
            time.sleep(1.2)
            back_to_main()

    except ValueError:
        # Back to main avoid crash(when user type illegal thing)
        print("BakeLaunch: Oops! Invalid option :O  Please enter a number.", color='red')
        time.sleep(1.2)
        back_to_main()

if __name__ == "__main__":
    main()
