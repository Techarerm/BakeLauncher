import os
import print_color
import Download
import platform
import requests
import __init__
from print_color import print
from Download import download_with_version_tunple
from Download import download_file
from assets_grabber import get_asset
from assets_grabber import get_assets_index_version
from lwjgl_patch import unzip_natives
from __init__ import GetPlatformName

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

def down_tool(version_data, version_id):
    """
    Only download libraries!
    """
    version_dir = os.getcwd()
    libraries_dir = os.path.join(version_dir, "libraries")
    # Download client.jar
    client_info = version_data['downloads']['client']
    client_url = client_info['url']
    client_dest = os.path.join(version_dir, 'client.jar')
    print(f"Downloading client.jar to {client_dest}...", color='green')
    download_file(client_url, client_dest)

    # Download libraries
    PlatformName = GetPlatformName.check_platform_valid_and_return()
    PlatformNameLW = PlatformName.lower()
    if PlatformName == 'darwin':
        PlatformNameLib = 'macos'
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
        'darwin': 'natives-macos'
    }
    native_key = native_keys.get(PlatformNameLW)

    if not native_key:
        print(f"DownoandTool(LP): Warring! Can't find native key : {PlatformNameLW} OS in list!", color='red')
        return "NativeKeyCheckFailed"

    print(f"Detected OS: {PlatformName}. Looking for native key: {native_key}")

    # Check if any library has classifiers for the current OS
    found_any_classifier = False
    for lib in libraries:
        classifiers = lib.get('downloads', {}).get('classifiers', {})
        native_info = classifiers.get(native_key)
        if native_info:
            native_path = native_info['path']
            native_url = native_info['url']
            native_dest = os.path.join(libraries_dir, native_path)
            os.makedirs(os.path.dirname(native_dest), exist_ok=True)
            print(f"Downloading {native_path} to {native_dest}...")
            download_file(native_url, native_dest)
            found_any_classifier = True

    if not found_any_classifier:
        print(f"DownoandTool(LP): No native library information found for key: {native_key}")


def fix_natives(selected_version_id):
    # Get version_manifest_v2.json and list all version(also add version_id in version's left :)
    url = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"
    response = requests.get(url)
    data = response.json()
    version_list = data['versions']
    selected_version = next((version for version in version_list if version['id'] == selected_version_id), None)

    # Get version data
    if selected_version:
        version_url = selected_version['url']
        version_response = requests.get(version_url)
        version_data = version_response.json()

        # Download game file( libraries, .jar files...., and lwjgl!)
        print("DownoandTool(LP): Loading version info...", color="green")

        ErrorCheck = down_tool(version_data, selected_version_id)
        if not ErrorCheck == "NativeKeyCheckFailed":
            print("DownoandTool(LP): The required dependent libraries should have been downloaded :)", color='blue')

            # Finally....
            print("DownoandTool(LP): Now unzip natives...", color='green')
            unzip_natives(selected_version_id)

            print("DownoandTool(LP): YAPPY! Now natives are download success :)", color='blue')
            print("DownoandTool(LP): Exiting download tool....", color='green')
        else:
            print("DownoandTool(LP): Cannot found natives :(", color='red', tag_color="red", tag='Error')
            print("DownoandTool(LP): This issus can cause the game crash on launching!", color='yellow')
            print(
                "DownoandTool(LP): Please try again ! If still got this error please report this issue to GitHub(also send your system name!)",
                color='yellow')
            print("DownoandTool(LP): Stopping launch...", color='red')
            return "FailedToFixNatives"

def legacy_version_natives_fix(version):
    instance_local = os.getcwd()
    if os.path.exists('.minecraft/natives'):
        item = os.listdir(".minecraft/natives")
        print('NativesTool: Natives folder exists :) Checking if is available...', color='blue')

        if len(item) <= 0:
            print("NativesTool: Natives are not unzip correctly!", color='red')
            print("NativesTool: Trying to fix it.....", color='green')
            ErrorCheck = fix_natives(version)
            os.chdir(instance_local)
            return ErrorCheck

        print('NativesTool: Natives folder exists :) Bypassing fix....', color='blue')
    else:

        print('NativesTool: Cannot find available natives!', color='red')
        print("NativesTool: Trying to fix it.....", color='green')
        ErrorCheck = fix_natives(version)
        os.chdir(instance_local)
        return ErrorCheck

