"""
Warring:This is a "Experimental" version and has many immature features.
So...Run it if you know what you are doing :)
PyLauncher AKA BakeLauncher
A Minecraft java launcher code on python.
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

laucnher_version = "Beta 6"

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

print("Warring:This is a 'Experimental' version and has many immature features.", color='yellow')
print("NOW SUPPORT ALL VERSIONS OF MINECRAFT!!!!(Still except snapshots :)", color='cyan')
print("ChangeLog here :)", color='cyan')
print("Repair some old LWJGL file (Thanks Mojang let me took 5 hours...).", color='green')
print("Fix old version still can't load icon.", color='green')
print("Fix old version login problem and can't join server.", color='green')
print("Using new way to get assetsIndex and assetsDir.", color='green')
print("Using new way to get LWJGL version and path.", color='green')
print("CLeaned some command and remove some old methods.", color='green')
print("Optimized downloading methods and accelerated speed.", color='blue')
print("Optimized LaunchClient's code.", color='blue')
print("Now all modules have their own names :)", color='blue')
print("Add 'some' color :)", color='blue')
print("Please run it if you know what you are doing.", color='yellow')
print(" ")

def main():
    print('"BakeLauncher Main Menu"', color='blue')
    print("Version: " + laucnher_version, color='green')

    """
    Check login status.
    Avoid Minecraft crash on auth....However, if the token expired, it will still crash on launch :)
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
        print("Login Status: Not logged :(", color='red')
        print("Please login your account first!", color='red')
    else:
        print("Login Status: Already logged :)", color='green')
        print("Hi," , username, color="blue")  # Now this should work correctly
    print("Which thing you want to do?")
    print("1.Launch Minecraft 2.Login account 3.Clear login data(for session expired)")
    print("4:DownloadTool 5:Config Java 6:About 7:Exit launcher")
    user_input = int(input(":"))
    if user_input == 1:
        print("Launching Minecraft...", color='green')
        os.system('cls')
        launch()
        back_to_main_without_cls()
    if user_input == 2:
        login()
        back_to_main()
    if user_input == 3:
        print("Cleaning login data...", color='purple')
        initialize_account_data()
        print("Login data cleared.", color='blue')
        back_to_main()
    if user_input == 4:
        download_main()
        back_to_main()
    if user_input == 5:
        java_finder()
        back_to_main_without_cls()
    if user_input == 6:
        print("POWER BY BAKE!", color="yellow")
        print("BakeLauncher " + laucnher_version, color='yellow')
        print("ContectMe :) TedKai/@Techarerm", color="blue")
        print("Source code : https://github.com/Techarerm/BakeLauncher", color='yellow')
        print("Also check my website :) https://techarerm.com", color="blue")
        time.sleep(10)
        back_to_main()
    if user_input == 7:
        print("Exiting launcher...", color='purple')
        print("Bye :)",color='blue')
        return 0
if __name__ == "__main__":
    main()