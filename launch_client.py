import os
import json
import sys

import launch_version_patcher
import time
from launch_version_patcher import patcher_main
import print_color
from print_color import print
import assets_grabber
from assets_grabber import get_assets_index_version
from legacy_patch import legacy_version_natives_fix
import requests
import platform


def read_assets_index_version(local, version_id):
    try:
        with open('.minecraft\\assets_index.json', 'r') as file:
            data = json.load(file)
        assetsIndex_version = data['id']
        return assetsIndex_version

    except FileNotFoundError:
        # Trying fix use old version BakeLaunch didn't save assetsIndex to .minecraft(It will ask user to fix it)
        # This functiom will be delete in the release
        print("LaunchManager: Oops! Can't getting assetsIndex :O", color='red')
        print("LaunchManager: Trying to fix it.....", color='green')
        assetsIndexFix(local, version_id)
        print("LaunchManager: Fixed assetsIndex config successfull!", color='blue')
        try:
            with open('.minecraft/assets_index.json', 'r') as file:
                data = json.load(file)
            assetsIndex_version = data['id']
            return assetsIndex_version

        except FileNotFoundError:
            # Trying to fix use old version BakeLaunch didn't save assetsIndex to .minecraft(It will ask user to fix it)
            # This functiom will be delete in the release
            print("LaunchManager: Still can't fix it :(", color='red')
            assetsIndexFix(local, version_id)


def get_assets_dir(version_id) -> str:
    version_tuple = tuple(map(int, version_id.split(".")))
    assets_dir = ".minecraft/assets"
    if version_tuple <= (1, 7, 2) and version_tuple > (1, 5, 2):
        return assets_dir + "/virtual/legacy"
    elif version_tuple >= (1, 0) and version_tuple <= (1, 5, 2):
        return assets_dir + "/virtual/legacy"
    elif version_tuple == (1, 0):
        return assets_dir + "/virtual/legacy"
    else:
        return assets_dir

def java_version_check(version):
    """
    Hmm...just a normal check....
    """
    print("LaunchManager: Trying to check this version of Minecraft requirement Java version....", color='green')
    version_tuple = tuple(map(int, version.split(".")))

    with open("Java_HOME.json", "r") as file:
        data = json.load(file)

    if version_tuple > (1, 16):
        if version_tuple >= (1, 20, 6):
            Java_path = data.get("Java_21")
            print("LaunchManager: Using Java 21!", color='blue')
        else:
            Java_path = data.get("Java_17")
            print("LaunchManager: Using Java 17!", color='blue')
    else:
        Java_path = data.get("Java_8")
        print("LaunchManager: Using Java 8!", color='blue')
    print(f"LaunchManager: Java runtime path is:{Java_path}", color='blue')
    return Java_path


def assetsIndexFix(local, selected_version_id):
    # Get version_manifest_v2.json and list all version(also add version_id in version's left :)
    url = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"
    response = requests.get(url)
    data = response.json()
    version_list = data['versions']
    release_versions = [version['id'] for version in version_list if version['type'] == 'release']
    selected_version = next((version for version in version_list if version['id'] == selected_version_id), None)

    try:
        # Get version data
        if selected_version:
            print("LaunchManager: Loading version info...", color='green')
            version_url = selected_version['url']
            version_response = requests.get(version_url)
            version_data = version_response.json()
            get_assets_index_version(local, version_data, selected_version_id)

    except ValueError:
        # Back to main avoid crash
        print("LaunchManager: Can't fix assetsIndex :(.", color='red')
        back_to_main()



def launch(platform):
    local = os.getcwd()
    # Check folder "versions" are activable in root (To avoid some user forgot to install)
    if not os.path.exists("instances"):
        os.makedirs("instances")
    instances_list = os.listdir('instances')
    if len(instances_list) == 0:
        print("LaunchManager: No versions are activable to launch :(", color='red')
        print("Try to using DownloadTool to download the Minecraft!", color='yellow')
        return 0
    else:
        print(f"LaunchManager: This version are activable to launch :D", color='blue')
    print(instances_list, color='blue')

    # Ask user wanna launch version...
    print("LaunchManager: Which one is you wanna launch version ? :)", color='green')
    version_id = input(":")

    if version_id not in instances_list:
        print("Can't found version " + version_id + " of Minecraft :(", color='red')
        print("Please check you type version and try again or download it om DownloadTool!", color='yellow')
        time.sleep(1.5)
    else:
        # Patch launch version path...(maybe I need to use .cfg not .json ?)
        patcher_main(version_id)
        print("Getting JVM path from saved config.....", color='green')

        # Get requirement JVM version and path (If can't found it will stop and ask user to config Java path)
        if os.path.isfile('Java_HOME.json'):

            # Check Java_HOME.json file are activable to use(and getting jvm path from this file)
            Java_path = java_version_check(version_id)
            if platform == 'Windows':
                Java_path = f'"{Java_path + "/java.exe"}"'
            else:
                Java_path = f'"{Java_path + "/java"}"'

            # Set some .minecraft path...
            os.chdir(r'instances/' + version_id)
            minecraft_path = f".minecraft"

            # JVM args
            jvm_args1 = r"-XX:HeapDumpPath=MojangTricksIntelDriversForPerformance_javaw.exe_minecraft.exe.heapdump "

            # Set this to prevent the windows too small
            window_size = "-Dorg.lwjgl.opengl.Window.undecorated=false -Dorg.lwjgl.opengl.Display.width=1280 -Dorg.lwjgl.opengl.Display.height=720"

            # Get requirement lwjgl version :)
            print("LaunchManager: Checking natives...", color='green')
            ErrorCheck = legacy_version_natives_fix(version_id)
            if ErrorCheck == "FailedToFixNatives":
                print("LaunchManager: Stopping launch... Cause by GetNativesFailed!", color='red')
                return
            natives_library = '.minecraft/natives'
            jvm_args2 = "-Djava.library.path={}".format(natives_library)

            # Set Xms and Xmx ram size (Maybe I can add change ram size in memu,,,hmm :)
            jvm_argsRAM = r" -Xms1024m -Xmx4096m"

            # Get download libraries path (Is really important when launch Minecraft : )
            with open('libraries_path.cfg', 'r', encoding='utf-8') as file:
                libraries = file.read()

            # Check use "old" or "new" main class
            version_tuple = tuple(map(int, version_id.split(".")))
            if version_tuple > (1, 5, 2):
                RunClass = " -cp {} net.minecraft.client.main.Main ".format(libraries)
                print("LaunchManager: Using modern methods to run Main Class", color='blue')
            else:
                RunClass = " -cp {} net.minecraft.launchwrapper.Launch ".format(libraries)
                print("LaunchManager: Using old methods to run Main Class :)", color='purple')

            # Get assetsIndex version....and set assets dir

            assetsIndex = read_assets_index_version(local, version_id)
            assets_dir = get_assets_dir(version_id)
            print(f"LaunchManager: assetsIndex: {assetsIndex}", color='blue')
            print(f"LaunchManager: Using Index {assetsIndex}", color='blue')



            # Get access token and username, uuid to set game args
            print("Reading account data....", color='green')
            os.chdir(local)
            with open('data/AccountData.json', 'r') as file:
                data = json.load(file)
            username = data['AccountName']
            uuid = data['UUID']
            access_token = data['Token']
            os.chdir(r'instances/' + version_id)

            # Add --UserProperties if version_id is high than 1.7.2 but low than 1.8.1
            # Btw...Idk why some old version need this...if I don't add it will crash on lauch
            if (version_tuple > (1, 7, 2)) and (version_tuple < (1, 8, 1)):
                user_properties = "{}"
                minecraft_args = f"--username {username} --version {version_id} --gameDir {minecraft_path} --assetsDir {assets_dir} --assetIndex {assetsIndex} --uuid {uuid} --accessToken {access_token} --userProperties {user_properties}"
            else:
                minecraft_args = f"--username {username} --version {version_id} --gameDir {minecraft_path} --assetsDir {assets_dir} --assetIndex {assetsIndex} --uuid {uuid} --accessToken {access_token}"

            # Really old version's token are place on head
            # But idk why some version think token are null
            if (version_tuple >= (1, 0)) and (version_tuple < (1, 6)):
                user_properties = "{}"
                minecraft_args = f" {username} {access_token} --version {version_id} --gameDir {minecraft_path} --assetsDir {assets_dir} --session {access_token} --userProperties {user_properties}"
            if (version_tuple >= (1, 6)) and (version_tuple < (1, 7)):
                user_properties = "{}"
                minecraft_args = f" --username {username} --version {version_id} --gameDir {minecraft_path} --assetsDir {assets_dir} --session {access_token} --userProperties {user_properties}"

            # Preparaing command...
            RunCommand = Java_path + " " + jvm_args1 + window_size + jvm_argsRAM + " " + jvm_args2 + RunClass + minecraft_args
            print("Preparations completed! Generating command.....", color='green')
            print("Launch command: " + RunCommand, color='blue')
            print("Baking Minecraft! :)", color='cyan')
            print(" ")
            print("Minecraft Log Start Here :)", color='green')
            os.system(RunCommand)
            os.chdir(local)

            # Check login status :)
            if username == "None":
                print("You didn't login!!!", color='red')
                print("Although you can launch some old version of Minecraft but is illegal!!! ", color='red')
                print("Some old version will crash when you try to join server if it already turn on online mode!", color='red')
            print("Back to main menu.....", color='green')
        else:
            print("You didn't configure your Java path!", color='red')
            print("Please go back to the main menu and select 5: Config Java!", color='yellow')
            print("Back to main menu.....", color='green')


