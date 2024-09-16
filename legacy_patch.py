import os
import print_color
import Download
import platform
import requests
import __init__
from print_color import print
from Download import download_with_version_tunple
from Download import download_file
from Download import download_natives
from assets_grabber import get_asset
from assets_grabber import get_assets_index_version
from natives_tool import unzip_natives
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
    Create instances\\version_id\\folder and download game files
    """
    libraries_dir = os.path.join("libraries")

    # Download "natives"

    PlatformName = GetPlatformName.check_platform_valid_and_return()
    PlatformNameLW = PlatformName.lower()

    # "Rules"
    if PlatformNameLW == 'darwin':
        PlatformNameLib = 'osx'
    else:
        PlatformNameLib = PlatformNameLW

    # Finding natives and download....
    libraries = version_data.get('libraries', [])
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

    print("DownloadTool: Now downloading natives...")
    download_natives(PlatformNameLib, PlatformNameLW, libraries, libraries_dir)

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

