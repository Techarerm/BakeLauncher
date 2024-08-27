import os
import json
import sys

import launch_version_patcher
import time
from launch_version_patcher import patcher_main
import print_color
from print_color import print

def get_lwjgl_version(version_id):
    """
    Check Minecraft support LWJGL version.
    Some version of Minecraft are REALLY WEIRD :( took me 2 days to get all...
    """
    version_tuple = tuple(map(int, version_id.split(".")))
    print("LaunchManager: Checking supported LWJGL version...", color='yellow')

    if version_tuple < (1, 7, 3):
        return "LWJGL 2.6.x"
    elif (1, 7, 3) <= version_tuple <= (1, 8, 1):
        return "LWJGL 2.8.x(1.7)"
    elif (1, 8, 1) <= version_tuple <= (1, 8, 9):
        return "LWJGL 2.9.x(1.8.2)"
    elif (1, 9) <= version_tuple <= (1, 12, 2):
        return "LWJGL 2.9.4"
    elif version_tuple <= (1, 13, 2):
        return "LWJGL 3.1.6"
    elif version_tuple <= (1, 14, 3):
        return "LWJGL 3.2.2(1.15)"
    elif version_tuple <= (1, 18, 2):
        return "LWJGL 3.2.2(1.16)"
    elif version_tuple >= (1, 19):
        return "LWJGL 3.3.3"
    else:
        print("LaunchManager: Unsupported Minecraft version :(")
        print("Maybe this version of Minecraft support's lwjgl didn't downloand!")
        print("You can report to GitHub at https://github.com")
        return 0

def get_assets_index_version(version_id):
    """
    Check assetsIndex and set it in game args...
    """
    version_tuple = tuple(map(int, version_id.split(".")))
    assets_dir = ".minecraft\\assets"
    if version_tuple >= (1, 21):
        return "17"
    elif version_tuple >= (1, 20) and version_tuple < (1, 21):
        return "12"
    elif version_tuple >= (1, 19) and version_tuple < (1, 20):
        return "3"
    elif version_tuple >= (1, 18) and version_tuple < (1, 19):
        return "1.18"
    elif version_tuple >= (1, 17) and version_tuple < (1, 18):
        return "1.17"
    elif version_tuple >= (1, 16) and version_tuple < (1, 17):
        return "1.16"
    elif version_tuple > (1, 15) and version_tuple < (1, 16):
        return "1.15"
    elif version_tuple >= (1, 14) and version_tuple < (1, 15):
        return "1.14"
    elif version_tuple == (1, 13):
        return "1.13"
    elif version_tuple > (1, 13) and version_tuple < (1, 14):
        return "1.13.1"
    elif version_tuple >= (1, 12) and version_tuple < (1, 13):
        return "1.12"
    elif version_tuple >= (1, 11) and version_tuple <= (1, 12):
        return "1.11"
    elif version_tuple >= (1, 10) and version_tuple <= (1, 11):
        return "1.10"
    elif version_tuple >= (1, 9) and version_tuple < (1, 10):
        return "1.9"
    elif version_tuple >= (1, 8) and version_tuple <= (1, 8, 9):
        return "1.8"
    elif version_tuple == (1, 7, 10):
        return "1.7.10"
    elif version_tuple >= (1, 7, 4) and version_tuple <= (1, 7, 9):
        return "1.7.4"
    elif version_tuple == (1, 7, 3):
        return version_id
    elif version_tuple <= (1, 7, 2) and version_tuple > (1, 5, 2):
        return "legacy"
        return assets_dir == assets_dir + "\\virtual\\legacy"
    elif version_tuple >= (1, 0) and version_tuple <= (1, 5, 2):
        return "pre-1.6"
        return assets_dir == assets_dir + "\\virtual\\legacy"
    elif version_tuple == (1, 0):
        return "pre-1.6"
        return assets_dir == assets_dir + "\\virtual\\legacy"


def get_assets_dir(version_id) -> str:
    version_tuple = tuple(map(int, version_id.split(".")))
    assets_dir = ".minecraft\\assets"
    if version_tuple <= (1, 7, 2) and version_tuple > (1, 5, 2):
        return assets_dir + "\\virtual\\legacy"
    elif version_tuple >= (1, 0) and version_tuple <= (1, 5, 2):
        return assets_dir + "\\virtual\\legacy"
    elif version_tuple == (1, 0):
        return assets_dir + "\\virtual\\legacy"
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
        print("Up to Java-17")
        if version_tuple >= (1, 21):
            Java_path = data.get("Java_21")
        else:
            Java_path = data.get("Java_17")
    else:
        Java_path = data.get("Java_8")
    print(f"LaunchManager: Java runtime path is:{Java_path}", color='green')
    return Java_path

def get_lwjgl_path(lwjgl_version ,local):
    # Determine natives_library based on LWJGL version
    print(f"Trying to get LWJGL version {lwjgl_version}'s path....", color='green')
    if lwjgl_version == "LWJGL 2.6.x":
        return local + "\\LWJGL\\2.6.x\\1.0(6d0e9e5bfb61b441b31cff10aeb801ab64345a7d)"
    elif lwjgl_version == "LWJGL 2.8.x(1.7)":
        return local + "\\LWJGL\\2.8.x(1.7)\\1.7.3(455edb6b1454a7f3243f37b5f240f69e1b0ce4fa)"
    elif lwjgl_version == "LWJGL 2.9.x(1.8)":
        return local + "\\LWJGL\\2.8.x(1.8)\\1.8(7a28f1c296715db4d5f08cbcc92023ee7ed3fc9f)"
    elif lwjgl_version == "LWJGL 2.9.x(1.8.2)":
        return local + "\\LWJGL\\2.9.x(1.8.2)\\1.8.2(0388afd4a2e8cb544cd69a8b25802d75e905c94d)"
    elif lwjgl_version == "LWJGL 2.9.4":
        return local + "\\LWJGL\\2.9.4\\1.12(91d80911a67c3f95b232483aa2646ad7663a2976)"
    elif lwjgl_version == "LWJGL 3.1.6":
        return local + "\\LWJGL\\3.1.6\\362f886f0e087997ece5e8b064ff34886b378668"
    elif lwjgl_version == "LWJGL 3.2.1(1.14)":
        return local + "\\LWJGL\\3.2.1(1.14)\\476a2617ce0938d8559f61d5a7505fad49424892"
    elif lwjgl_version == "LWJGL 3.2.2(1.15)":
        return local + "\\LWJGL\\3.2.2(1.15)\\b093bae93ae5e9ae4c39d10a11624faef91d9061"
    elif lwjgl_version == "LWJGL 3.2.2(1.16)":
        return local + "\\LWJGL\\3.2.2(1.16)\\b093bae93ae5e9ae4c39d10a11624faef91d9061"
    elif lwjgl_version == "LWJGL 3.3.3":
        return local + "\\LWJGL\\3.3.3\\44685878b69bb36a6fb05390c06c8b0243d34f57"
    else:
        print("LaucnhManager: This version of LWJGL are not recognized!", color='red')
        print("Trying to redownload in DownloadTools!", color='yellow')
        print("If still can't launch Minecraft please report this issue to GitHub!", color='yellow')
        return 0

def launch():
    local = os.getcwd()
    # Check folder "versions" are activable in root (To avoid some user forgot to install)
    if not os.path.exists("versions"):
        os.makedirs("versions")
    Version_list = os.listdir('versions')
    if len(Version_list) == 0:
        print("LaunchManager: No versions are activable to launch :(", color='red')
        print("Try to using DownloadTool to download the Minecraft!", color='yellow')
        return 0
    else:
        print(f"LaunchManager: This version are activable to launch :D", color='blue')
    print(Version_list, color='blue')

    # Ask user wanna launch version...
    print("LaunchManager: Which one is you wanna launch version ? :)", color='green')
    print("Or you can type 'Exit' to go back to the main menu :)", color='cyan')
    version_id = input(":")

    if version_id not in Version_list:
        print("Can't found version " + version_id + " of Minecraft :(", color='red')
        print("Please check you type version and try again or download it om DownloadTool!", color='yellow')
        time.sleep(1.5)
    else:
        # Patch launch version path...
        patcher_main(version_id)
        print("Getting JVM path...", color='green')

        # Get requirement JVM version and path (If can't found it will stop and ask user to config Java path)
        if os.path.isfile('Java_HOME.json'):
            Java_path = java_version_check(version_id)
            Java_path = f'"{Java_path + "\\java.exe"}"'

            # Set some "normal" game path...
            os.chdir(r'versions/' + version_id)
            minecraft_path = f".minecraft"

            # JVM args
            jvm_args1 = r"-XX:HeapDumpPath=MojangTricksIntelDriversForPerformance_javaw.exe_minecraft.exe.heapdump "
            window_size = "-Dorg.lwjgl.opengl.Window.undecorated=false -Dorg.lwjgl.opengl.Display.width=1280 -Dorg.lwjgl.opengl.Display.height=720"

            # Get requirement lwjgl version :)
            lwjgl_version = get_lwjgl_version(version_id)
            natives_library = get_lwjgl_path(lwjgl_version, local)
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
            assetsIndex = get_assets_index_version(version_id)
            assets_dir = get_assets_dir(version_id)
            print(f"LaunchManager: assetsIndex: {assetsIndex}", color='blue')
            print(f"LaunchManager: Using Index {assetsIndex}", color='blue')

            # Get access token and username, uuid to set game args
            print("Reading account data....", color='green')
            os.chdir(local)
            with open('data\\AccountData.json', 'r') as file:
                data = json.load(file)
            username = data['AccountName']
            uuid = data['UUID']
            access_token = data['Token']
            os.chdir(r'versions/' + version_id)

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


