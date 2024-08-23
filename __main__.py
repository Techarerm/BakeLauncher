"""
Warring:This is a "Experimental" version and has many immature features.
So...Run it if you know what you are doing :)
PyLauncher AKA BakeLauncher
A Minecraft java launcher code on python.
"""

import os
import sys
from Auth_tool import login
from launch_client import launch
import json
import Download
from Download import request_version_url
import shutil
from path_tool import path_main
from path_tool import generate_jar_paths
import JVM_path
from JVM_path import java_tool
from assets_tool import get_asset
print("BakeLauncher Beta 5(Pre)")
print("Warring:This is a 'Experimental' version and has many immature features.")
print("Warring:This version not support  1.16 because it will crash when you launch it :(")
print("NOW SUPPORT 'ALL' VERSIONS OF MINECRAFT!!!!(Except snapshots :)")
print("Add multi-version support.")
print("Using assets_tool instead McAssetExtractor.")
print("Fixed JVM_path not working on Windows(Other system still not supported :(")
print("Please run it if you know what you are doing.")
print(" ")
def back():
    os.system('cls')
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

def main():
    print('"BakeLauncher Main Memu"')
    print("Status:")
    try:
        with open('data\\AccountData.json', 'r') as file:
            data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        initialize_account_data()
        with open('data\\AccountData.json', 'r') as file:
            data = json.load(file)

    if data['AccountName'] == "None":
        print("Login: Not logged :(")
    else:
        print("Login: Already logged :)")

    print("Which thing you want to do?")
    print("1.Launch Minecraft 2.Login account 3.Clear login data(for session expired)")
    print("4:DownloadTools 5:Config Java 6:Fix launch version 7:Exit launch")
    user_input = int(input(":"))
    if user_input == 1:
        print("Launching Minecraft...")
        os.system('cls')
        launch()
        print("Press any key to back main memu....")
        back()
    if user_input == 2:
            login()
            print("Press any key to back main memu....")
            back()
    if user_input == 3:
        print("Cleaning login data...")
        initialize_account_data()
        print("Login data cleared.")
        print("Press any key to back main memu....")
        back()
    if user_input == 4:
        request_version_url()
        print("Repair Minecraft version to you download version(Yes=1/No=0) ?")
        repair_version = int(input(":"))
        if repair_version == 1:
            path_main()
            back()
        else:
            print("Bypass repair...")
            back()
    if user_input == 5:
        java_tool()
        print("Press any key to back main memu....")
        back()
    if user_input == 6:
        path_main()
        print("Press any key to back main memu....")
        back()
    if user_input == 7:
        exit(0)
if __name__ == "__main__":
    main()
