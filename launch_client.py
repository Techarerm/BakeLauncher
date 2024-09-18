"""
InternalName: LaunchManager
In the file structure: launch_client.py

Just a tool to prepare command for launching clients...
"""


import os
import json
import time
from print_color import print
from __init__ import timer
from assets_grabber import read_assets_index_version, get_assets_dir
from jvm_tool import java_version_check
from legacy_patch import legacy_version_natives_fix
from launch_version_patcher import patcher_main
from Download import get_version_data

def SelectMainClass(version_id):
    version_data = get_version_data(version_id)
    main_class = version_data.get("mainClass")
    return main_class


def GetGameArgs(version_id, username, access_token, minecraft_path, assets_dir, assetsIndex, uuid):
    version_data = get_version_data(version_id)  # Fetch version data
    minecraftArguments = version_data.get("minecraftArguments", "")  # Get the arguments or an empty string
    userCustomArgs = 0
    user_properties = "{}"
    user_type = "msa"  # Set user type to 'msa'

    # Replace placeholders in minecraftArguments with actual values
    minecraft_args = minecraftArguments \
        .replace("${auth_player_name}", username) \
        .replace("${auth_session}", access_token) \
        .replace("${game_directory}", minecraft_path) \
        .replace("${assets_root}", assets_dir) \
        .replace("${version_name}", version_id) \
        .replace("${assets_index_name}", assetsIndex) \
        .replace("${auth_uuid}", uuid) \
        .replace("${auth_access_token}", access_token) \
        .replace("${user_type}", user_type) \
        .replace("${user_properties}", user_properties)  # Replace user_properties if present


    if "--userProperties" in minecraftArguments:
        # Properly replace ${user_properties} or add user properties if not present
        minecraft_args = minecraft_args.replace("${user_properties}", user_properties)
        if "${user_properties}" not in minecraftArguments:
            minecraft_args += f" --userProperties {user_properties}"
        userCustomArgs == 1

    # Handle special case where ${auth_player_name} and ${auth_session} are at the beginning
    elif minecraftArguments.startswith("${auth_player_name} ${auth_session}"):
        # Prepend the username and access token as per the special case
        print("Breakpoint!")
        print(assets_dir)
        minecraft_args = f"{username} {access_token} --gameDir {minecraft_path} " \
                         f"--assetsDir {assets_dir} --assetIndex {assetsIndex}"
        userCustomArgs == 1

    elif minecraftArguments.endswith("${game_assets}"):
        print("Breakpoint!")
        minecraft_args = f"--username {username} --session {access_token} --version {version_id} --gameDir {minecraft_path} " \
                         f"--assetsDir {assets_dir} --assetIndex {assetsIndex}"
        userCustomArgs == 1

    elif minecraftArguments.startswith("--username") and minecraftArguments.endswith("${auth_access_token}"):
        print("Breakpoint!")
        minecraft_args = f"--username {username} --version {version_id} --gameDir {minecraft_path} " \
                         f"--assetsDir {assets_dir} --assetIndex {assetsIndex} --accessToken {access_token}"
        userCustomArgs == 1


    # Fallback to standard argument format if placeholders are not used
    if userCustomArgs == 0:
        minecraft_args = f"--username {username} --version {version_id} --gameDir {minecraft_path} " \
                         f"--assetsDir {assets_dir} --assetIndex {assetsIndex} --uuid {uuid} " \
                         f"--accessToken {access_token} --userType {user_type}"

    return minecraft_args



def launch(platform):

    Main = "LaunchManager"
    local = os.getcwd()
    # Check folder "versions" are activable in root (To avoid some user forgot to install)
    if not os.path.exists("instances"):
        os.makedirs("instances")
    instances_list = os.listdir('instances')
    if len(instances_list) == 0:
        print("LaunchManager: No instances are activable to launch :(", color='red')
        print("Try to using DownloadTool to download the Minecraft!", color='yellow')
        timer(4)
        return 0
    else:
        print(f"LaunchManager: Instances list are activable :D", color='blue')
    print(instances_list, color='blue')

    # Ask user wanna launch version...
    print("LaunchManager: Which instances is you want to launch instances ?", color='green')
    version_id = input(":")

    # Check user type version of Minecraft are activable
    if version_id not in instances_list:
        print("Can't found instances " + version_id + " of Minecraft :(", color='red')
        print("Please check you type instances version and try again or download it on DownloadTool!", color='yellow')
        time.sleep(1.5)
    else:
        # Patch launch version path...(maybe I need to use .cfg not .json ?)
        patcher_main(version_id)
        print("Getting JVM path from saved config.....", color='green')

        # Get requirement JVM version and path (If can't found it will stop and ask user to config Java path)
        if os.path.isfile('Java_HOME.json'):

            # Check Java_HOME.json file are activable to use(and getting jvm path from this file)
            Java_path = java_version_check(Main, version_id)
            if Java_path is None:
                print("LaunchManager: Set Java_path failed! Cause by None path!", color='red')
                print("Please download thid version of MInecraft support Java(In DownloadTool)!", color='yellow')
                timer(5)
                return "FailedToCheckJavaPath"
            else:
                if platform == 'Windows':
                    Java_path = f'"{Java_path + "/java.exe"}"'
                else:
                    Java_path = f'"{Java_path + "/java"}"'

                # Set some .minecraft path...

                os.chdir(r'instances/' + version_id)
                minecraft_path = ".minecraft"

                # JVM argsWin(? Only for Windows)
                jvm_argsWin = r"-XX:HeapDumpPath=MojangTricksIntelDriversForPerformance_javaw.exe_minecraft.exe.heapdump "

                # Set this to prevent the windows too small
                window_size = "-Dorg.lwjgl.opengl.Window.undecorated=false -Dorg.lwjgl.opengl.Display.width=1280 -Dorg.lwjgl.opengl.Display.height=720"

                # Get requirement lwjgl version :)
                print("LaunchManager: Checking natives...", color='green')

                # Check user's instances are already downloaded natives(If not it will redownload it and unzip to .minecraft\natives)
                ErrorCheck = legacy_version_natives_fix(version_id)
                if ErrorCheck == "FailedToFixNatives":
                    print("LaunchManager: Stopping launch... Cause by GetNativesFailed", color='red', tag_color='red',
                          tag="Error")
                    return "FailedToFixNatives"

                # Set natives path
                natives_library = '.minecraft/natives'
                jvm_args2 = "-Djava.library.path={}".format(natives_library)

                # Set Xms and Xmx ram size (Maybe I can add change ram size in memu...hmm...)
                jvm_argsRAM = r" -Xms1024m -Xmx4096m"

                # Get download libraries path (Is really important when launch Minecraft
                with open('libraries_path.cfg', 'r', encoding='utf-8') as file:
                    libraries = file.read()

                # Check use "old" or "new" main class
                main_class = SelectMainClass(version_id)
                print(f"LaunchManager: Using {main_class} as the Main Class.",
                      color='blue' if "net.minecraft.client.main.Main" in main_class else 'purple')
                RunClass = f"-cp {libraries} {main_class}"

                # Get assetsIndex version....and set assets dir
                assetsIndex = read_assets_index_version(Main, local, version_id)
                assets_dir = get_assets_dir(version_id)
                if assets_dir == "FailedToOpenAssetsIndexFile":
                    print("LaunchManager: Failed to get assets directory :( Cause by FailedToOpenAssetsIndexFile", color='red', tag_color='red', tag='error')

                print(f"LaunchManager: assetsIndex: {assetsIndex}", color='blue')
                print(f"LaunchManager: Using Index {assetsIndex}", color='blue')

                # Get access token and username, uuid to set game args
                print("LaunchManager: Reading account data....", color='green')
                os.chdir(local)
                with open('data/AccountData.json', 'r') as file:
                    data = json.load(file)
                username = data['AccountName']
                uuid = data['UUID']
                access_token = data['Token']
                os.chdir(r'instances/' + version_id)

                # Add --UserProperties if version_id is high than 1.7.2 but low than 1.8.1
                # Btw...idk why some old version need this...if I don't add it will crash on lauch
                game_args = GetGameArgs(version_id, username, access_token, minecraft_path, assets_dir, assetsIndex, uuid)
                # Preparaing command...(unix-like os don't need jvm_argsWin)
                if platform == "Windows":
                    RunCommand = Java_path + " " + jvm_argsWin + window_size + jvm_argsRAM + " " + jvm_args2 + " " + RunClass + " " + game_args
                else:
                    RunCommand = Java_path + " " + window_size + jvm_argsRAM + " " + jvm_args2 + " " + RunClass + " " + game_args

                print("LaunchManager: Preparations completed! Generating command.....", color='green')
                print("Launch command: " + RunCommand, color='blue')
                print("Baking Minecraft! :)", color='cyan')
                print(" ")
                print("Minecraft Log Start Here :)", color='green')
                os.system(RunCommand)
                os.chdir(local)

                # Check login status (But is after Minecraft close?)
                if username == "None":
                    print("LaunchManager: You didn't login!!!", color='red')
                    print("LaunchManager: Although you can launch some old version of Minecraft but is illegal!!! ",
                          color='red')
                    print(
                        "LaunchManager: Some old version will crash when you try to join server if it already turn on online mode!",
                        color='red')
                print("Back to main menu.....", color='green')

        else:
            # Can't find Java_HOME.json user will got this message.
            print("LaunchManager: You didn't configure your Java path!", color='red')
            print("If you already install jvm please go back to the main menu and select 5: Config Java!",
              color='yellow')
            timer(5)



