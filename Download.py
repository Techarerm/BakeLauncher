''''
Is a small script to download game files.
(Minecraft file download from Mojang CDN)
'''
import sys
import platform
import requests
import os
import subprocess
import shutil
import zipfile
import time
import assets_grabber
import __init__
import lwjgl_patch
import print_color
import launch_version_patcher
from __init__ import ClearOutput
from __init__ import GetPlatformName
from assets_grabber import get_asset
from assets_grabber import get_assets_index_version
from launch_version_patcher import patcher_main
from print_color import print
from lwjgl_patch import unzip_natives


def download_file(url, dest_path):
    """
    Download file :)
    Hmm...just a normal function(also optimized
    """
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()

        dest_dir = os.path.dirname(dest_path)
        if dest_dir:  # Check if dest_dir is not empty
            os.makedirs(dest_dir, exist_ok=True)

        with open(dest_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        print(f"Download successful: {dest_path}", color='cyan')
        return True  # Indicate success
    except requests.exceptions.RequestException as e:
        print(f"Failed to download {url}: {e}", color='red')
        return False  # Indicate failure

def extract_zip(zip_path, extract_to):
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        print(f"Extracted {zip_path} to {extract_to}")
    except zipfile.BadZipFile as e:
        print(f"Error extracting {zip_path}: {e}", color='red')



def down_tool(version_data, version_id):
    """
    Create instances\\version_id\\folder and download game files
    """
    version_dir = os.path.join("instances", version_id)
    libraries_dir = os.path.join(version_dir, "libraries")
    os.makedirs(libraries_dir, exist_ok=True)

    # Download client.jar
    client_info = version_data['downloads']['client']
    client_url = client_info['url']
    client_dest = os.path.join(version_dir, 'client.jar')
    print(f"Downloading client.jar to {client_dest}...")
    download_file(client_url, client_dest)

    # Download libraries
    PlatformName = GetPlatformName.check_platform_valid_and_return()
    PlatformNameLW = PlatformName.lower()
    if PlatformNameLW == 'darwin':
        PlatformNameB = "macOS"
    if PlatformNameLW == 'darwin':
        PlatformNameLW == 'osx'

    libraries = version_data.get('libraries', [])
    print(PlatformNameLW)
    for lib in libraries:
        lib_downloads = lib.get('downloads', {})
        artifact = lib_downloads.get('artifact')

        rules = lib.get('rules')
        if rules:
            allowed = False
            for rule in rules:
                action = rule.get('action')
                os_info = rule.get('os')
                if action == 'allow' and (not os_info or os_info.get('name') == PlatformNameLW):
                    allowed = True
                elif action == 'disallow' and os_info and os_info.get('name') == PlatformNameLW:
                    allowed = False
                    break
            if not allowed:
                continue

        if artifact:
            lib_path = artifact['path']
            lib_url = artifact['url']
            lib_dest = os.path.join(libraries_dir, lib_path)
            os.makedirs(os.path.dirname(lib_dest), exist_ok=True)
            print(f"Downloading {lib_path} to {lib_dest}...")
            download_file(lib_url, lib_dest)

    # Detect current OS and prepare to download natives
    native_keys = {
        'windows': 'natives-windows',
        'linux': 'natives-linux',
        'osx': 'natives-macos',
    }
    native_key = native_keys.get(PlatformNameLW)

    if not native_key:
        print(f"DownloadTool: Warning! Can't find native key : {PlatformNameB} OS in list!", color='red')
        print("DownloadTool: This issue can cause the game to crash on launching!", color='yellow')
        print("DownloadTool: Please try again! If the issue persists, report it to GitHub (include your system name!)", color='yellow')
        return "NativeKeyCheckFailed"

    print(f"Detected OS: {PlatformNameB}. Looking for native key: {native_key}")

    # Check if any library has classifiers for the current OS
    found_any_classifier = False
    for lib in libraries:
        classifiers = lib.get('downloads', {}).get('classifiers', {})
        native_info = classifiers.get(native_key)

        # Fallback to 'natives-osx' if 'natives-macos' not found
        if not native_info and native_key == 'natives-macos':
            native_info = classifiers.get('natives-osx')

        if native_info:
            native_path = native_info['path']
            native_url = native_info['url']
            native_dest = os.path.join(libraries_dir, native_path)
            os.makedirs(os.path.dirname(native_dest), exist_ok=True)
            print(f"Downloading {native_path} to {native_dest}...")
            download_file(native_url, native_dest)
            found_any_classifier = True

    if not found_any_classifier:
        print(f"No native library information found for key: {native_key}")



def download_with_version_id(version_list, release_versions, formatted_versions):
    local = os.getcwd()
    print("DownloadTool: Using version_id method...", color='cyan')

    try:
        print("DownloadTool: Activable version list:", color='purple')
        print(formatted_versions)
        print("VersionID: MinecraftVersion", "\n", color='purple')
        print("Example: 15: 1.12.2 , 15 is version 1.12's ID", color='green')
        version_id = int(input("Please enter the version ID:"))

        if isinstance(version_id, int):
            version_id -= 1
            if 0 <= version_id < len(release_versions):

                # Check user type version_id are activable
                selected_version_id = release_versions[version_id]

                # Find minecraft_version after get version_id(IMPORTANT:version =/= version_id!)
                selected_version = next((version for version in version_list if version['id'] == selected_version_id),
                                        None)

                # Get version data
                if selected_version:
                    version_url = selected_version['url']
                    version_response = requests.get(version_url)
                    version_data = version_response.json()

                    # Download game file( libraries, .jar files...., and lwjgl!)
                    ClearOutput(GetPlatformName.check_platform_valid_and_return())
                    print("DownoandTool: Loading version info...")
                    down_tool(version_data, selected_version_id)
                    print("DownoandTool: The required dependent libraries should have been downloaded :)", color='blue')

                    # I know hosted lwjgl file on github is not a best way :) ( I will delete it when I found a nice way to simply download lwjgl library...)
                    print("DownoandTool: Now unzip natives...", color='green')
                    unzip_natives(selected_version_id)

                    # Download assets(Also it will check this version are use legacy assets or don't use)
                    print("DownoandTool: Now create assets...", color='green')
                    get_asset(selected_version_id)
                    get_assets_index_version(local, version_data, selected_version_id)
                    print("DownoandTool: YAPPY! Now all files are download success :)", color='blue')
                    print("DownoandTool: Exiting DownloadTool....", color='green')
                    # Add waiting time(If assets download failed it will print it?)
                    time.sleep(1.2)

                else:
                    # idk this thing would happen or not :)  , just leave it and see what happen....
                    print("DownoandTool: Version not found or can't getting this version of Minecraft :(", color='red')
                    print("DownoandTool: Please try again...if still can't please report this to GitHub",
                          color='yellow')
                    download_with_version_id(version_list, release_versions, formatted_versions)
            else:
                print(f"DownoandTool: You type Version{version_id} are not found :(", color='red')
                download_with_version_id(version_list, release_versions, formatted_versions)
        else:
            print("DownloadTool: You are NOT typing VersionID!")
            print("VersionID: MinecraftVersion", "\n")
            print(
                "Please type VersionID not MinecraftVersion or exit launcher and using '2:Type Minecraft version' method :)")
            print("Example: 15: 1.12.2 , 15 is version 1.12's ID", color='green')
            time.sleep(2)
            download_with_version_id(version_list, release_versions, formatted_versions)
    except ValueError:
        # Back to download_main avoid crash(when user type illegal thing
        print("DownoandTool: Oops! Invalid input. Please enter a number corresponding to a version ID.", color='red')
        download_with_version_id(version_list, release_versions, formatted_versions)


def download_with_version_tunple(version_list):
    local = os.getcwd()
    print("DownloadTool: Using MinecraftVersion method...", color='green')
    selected_version_id = str(input("Please enter Minecraft version:"))
    # Find minecraft_version after get version_id(IMPORTANT:version =/= version_id!)
    selected_version = next((version for version in version_list if version['id'] == selected_version_id), None)

    try:
        # Get version data
        if selected_version:
            version_url = selected_version['url']
            version_response = requests.get(version_url)
            version_data = version_response.json()

            # Download game file( libraries, .jar files...., and lwjgl!)
            ClearOutput(GetPlatformName.check_platform_valid_and_return())
            print("DownoandTool: Loading version info...")
            down_tool(version_data, selected_version_id)
            print("DownoandTool: The required dependent libraries should have been downloaded :)", color='blue')

            # Download assets(Also it will check this version are use legacy assets or don't use)
            print("DownoandTool: Now create assets...", color='green')
            get_asset(selected_version_id)
            get_assets_index_version(local, version_data, selected_version_id)

            # Finally....
            print("DownoandTool: Now unzip natives...", color='green')
            unzip_natives(selected_version_id)


            print("DownoandTool: YAPPY! Now all files are download success :)", color='blue')
            print("DownoandTool: Exiting download tool....", color='green')

            # Add waiting time(If assets download failed it will print it?)
            time.sleep(1.2)
        else:
            # idk this thing would happen or not :)  , just leave it and see what happen....
            print(f"DownoandTool: You type Minecraft version {selected_version_id} are not found :(", color='red')
            download_with_version_tunple(version_list)
    except ValueError:
        # Back to download_main avoid crash(when user type illegal thing
        print("DownoandTool: Oops! Invalid input :( Please enter Minecraft version.")
        download_with_version_tunple(version_list)

def download_main():
    # Get version_manifest_v2.json and list all version(also add version_id in version's left :)
    url = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"
    response = requests.get(url)
    data = response.json()
    version_list = data['versions']

    release_versions = [version['id'] for version in version_list if version['type'] == 'release']
    formatted_versions = '\n'.join([f"{index + 1}: {version}"
                                    for index, version in enumerate(release_versions)])

    print("Which method you wanna use?", color='green')
    print("1:List all available versions and download 2:Type Minecraft version and download")

    try:
        user_input = int(input(":"))
        if user_input == 1:
            download_with_version_id(version_list, release_versions, formatted_versions)
        elif user_input == 2:
            download_with_version_tunple(version_list)
        else:
            print("DownloadTool: Unknow options :( Please try again.", color='red')
            download_main()

    except ValueError:
        # Back to main avoid crash(when user type illegal thing)
        print("BakeLaunch: Oops! Invalid option :O  Please enter a number.", color='red')
        download_main()