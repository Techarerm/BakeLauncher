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

print("BakeLauncher Beta v1.0")
print("Warring:This is a 'Experimental' version and has many immature features.")
print("Warring:Only tested on 1.21")
print("Please run it if you know what you are doing.")
print("Launch Minecraft(1.21) required Java 21.")
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
    print("1.Launch Minecraft 2.Login account 3.Clear login data(for session expired) 4:Exit launcher")
    user_input = int(input(":"))
    if user_input == 1:
        print("Launching Minecraft...")
        os.system('cls')
        launch()
        back()
    if user_input == 2:
            login()
            back()
    if user_input == 3:
        print("Cleaning login data...")
        initialize_account_data()
        print("Login data cleared.")
        back()
    if user_input == 4:
        exit(0)


if __name__ == "__main__":
    main()
