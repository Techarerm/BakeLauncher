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

launcher_version = "Beta 0.7(Pre-ha26824)"

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

print("Warning: This is an 'Experimental' version with potential instability.", color='yellow')
print("NOW SUPPORTS ALL VERSIONS OF MINECRAFT!!!! (Still excludes snapshots :)", color='cyan')
print("ChangeLog:", color='cyan')
print("Fix some grammer problem and `ass more explain.")
print("Now all modules have their own names :)", color='blue')
print("Added 'some' color :)", color='blue')
print("Please run it only if you know what you are doing.", color='yellow')
print(" ")

def main():
    print('"BakeLauncher Main Menu"', color='blue')
    print("Version: " + launcher_version, color='green')

    """
    Check login status.
    Avoid Minecraft crash on auth... However, if the token expires, it will still crash on launch :)
    """
    username = "Unknown"  # Initialize username to avoid UnboundLocalError
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
        download_main()
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
        print("Exiting launcher...", color='purple')
        print("Bye :)", color='blue')
        return 0
    else:
        print(f"BakeLauncher: Can't found option {user_input} :( ", color='red')
        print("Please check you type option's number and try again!", color='yellow')
        back_to_main()
if __name__ == "__main__":
    main()
