"""
Is a small script to download game files.
(Minecraft file download from Mojang CDN)
"""

import platform
import requests
import os
import zipfile
import time
import download_jvm
from __init__ import ClearOutput
from __init__ import GetPlatformName
from assets_grabber import get_asset
from assets_grabber import get_assets_index_version
from print_color import print
from natives_tool import unzip_natives
from download_jvm import download_jvm

def get_version_data(version_id):
    """
    This only using on other functions!
    """
    # Get version_manifest_v2.json and list all versions
    url = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"
    response = requests.get(url)
    data = response.json()
    version_list = data['versions']

    # Find the URL for the given version_id
    version_url = None
    for v in version_list:
        if v['id'] == version_id:
            version_url = v['url']
            break

    if version_url is None:
        print(f"DownloadTool: Invalid version ID", color='red')
        return None

    try:
        # Get version data
        version_response = requests.get(version_url)
        version_data = version_response.json()
        return version_data
    except Exception as e:
        print(f"DownloadTool: Error occurred while fetching version data: {e}", color='red')
        return None

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
        print(f"Download successful: {dest_path}", color='blue')
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

def download_natives(PlatformNameLib, PlatformNameLW, libraries, libraries_dir):
    print(f"DownloadTool: {PlatformNameLW}", tag='Debug', color='green')
    native_keys = {
        'windows': 'natives-windows',
        'linux': 'natives-linux',
        'darwin': 'natives-macos',
        'windows-arm64': 'natives-windows-arm64',
        'macos-arm64': 'natives-macos-arm64',
    }
    native_key = native_keys.get(PlatformNameLW)

    if not native_key:
        print(f"Warning: No native key found for {PlatformNameLW}", color='yellow')
        return "NativeKeyCheckFailed"

    found_any_native = False

    for lib in libraries:
        lib_downloads = lib.get('downloads', {})
        artifact = lib_downloads.get('artifact')

        # Check if the library has rules that allow it for the current platform
        rules = lib.get('rules')
        if rules:
            allowed = False
            for rule in rules:
                action = rule.get('action')
                os_info = rule.get('os')
                if action == 'allow' and (not os_info or os_info.get('name') == PlatformNameLib):
                    allowed = True
                elif action == 'disallow' and os_info and os_info.get('name') == PlatformNameLib:
                    allowed = False
                    break
            if not allowed:
                continue

        # Check if artifact exists and download it (for newer versions)
        if artifact:
            lib_name = lib.get('name', '')
            if native_key in lib_name or native_key in artifact.get('path', ''):
                native_path = artifact['path']
                native_url = artifact['url']
                native_dest = os.path.join(libraries_dir, native_path)
                os.makedirs(os.path.dirname(native_dest), exist_ok=True)
                print(f"Downloading {native_path} to {native_dest}...")
                download_file(native_url, native_dest)
                found_any_native = True

        # Check if classifiers exist and download natives (for legacy versions)
        classifiers = lib_downloads.get('classifiers')
        if classifiers and native_key in classifiers:
            classifier_info = classifiers[native_key]
            native_path = classifier_info['path']
            native_url = classifier_info['url']
            native_dest = os.path.join(libraries_dir, native_path)
            os.makedirs(os.path.dirname(native_dest), exist_ok=True)
            print(f"Downloading {native_path} to {native_dest}...")
            download_file(native_url, native_dest)
            found_any_native = True

    # Check for natives-osx fallback if natives-macos is not found
    if not found_any_native and PlatformNameLW == 'darwin':
        print("Attempting to download natives-osx as a fallback...")
        native_key_osx = 'natives-osx'  # Fallback key
        for lib in libraries:
            lib_downloads = lib.get('downloads', {})
            classifiers = lib_downloads.get('classifiers')

            if classifiers and native_key_osx in classifiers:
                classifier_info = classifiers[native_key_osx]
                native_path = classifier_info['path']
                native_url = classifier_info['url']
                native_dest = os.path.join(libraries_dir, native_path)
                os.makedirs(os.path.dirname(native_dest), exist_ok=True)
                print(f"Downloading {native_path} to {native_dest}...")
                download_file(native_url, native_dest)
                found_any_native = True
                break  # Exit after first successful download

    if not found_any_native:
        print(f"No native library found for key: {native_key}", color='yellow')
        return "NativeLibrariesNotFound"

def download_libraries(version_data, version_id):
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
        PlatformNameLib = 'osx'
    else:
        PlatformNameLib = PlatformNameLW
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

    print("DownloadTool: Now downloading natives...")
    download_natives(PlatformNameLib, PlatformNameLW, libraries, libraries_dir)


def download_with_version_id(version_list, release_versions, formatted_versions):
    local = os.getcwd()
    print("DownloadTool: Using version_id method...", color='blue')

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
                    download_libraries(version_data, selected_version_id)
                    print("DownoandTool: The required dependent libraries should have been downloaded :)", color='blue')

                    # Download assets(Also it will check this version are use legacy assets or don't use)
                    ClearOutput(GetPlatformName.check_platform_valid_and_return())
                    print("DownoandTool: Now create assets...", color='green')
                    get_assets_index_version(version_data, selected_version_id)
                    get_asset(selected_version_id)
                    os.chdir(local)

                    # Finally....
                    ClearOutput(GetPlatformName.check_platform_valid_and_return())
                    print("DownoandTool: Now unzip natives...", color='green')
                    unzip_natives(selected_version_id)

                    ClearOutput(GetPlatformName.check_platform_valid_and_return())
                    print("DownoandTool: Finally...download JVM!", color='green')
                    download_jvm(version_data)


                    print("DownoandTool: When you install a Java version that has never been installed before, you need to reconfig Java Path!", color='blue')
                    print("DownoandTool: YAPPY! Now all files are download success :)", color='blue')
                    print("DownoandTool: Exiting download tool....", color='green')

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
            download_libraries(version_data, selected_version_id)
            print("DownoandTool: The required dependent libraries should have been downloaded :)", color='blue')

            # Download assets(Also it will check this version are use legacy assets or don't use)
            ClearOutput(GetPlatformName.check_platform_valid_and_return())
            print("DownoandTool: Now create assets...", color='green')
            get_asset(selected_version_id)
            get_assets_index_version(version_data, selected_version_id)
            os.chdir(local)

            # Finally....
            ClearOutput(GetPlatformName.check_platform_valid_and_return())
            print("DownoandTool: Now unzip natives...", color='green')
            unzip_natives(selected_version_id)

            ClearOutput(GetPlatformName.check_platform_valid_and_return())
            print("DownoandTool: Finally...download JVM!", color='green')
            download_jvm(version_data)

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

def download_snapshot(version_list, snapshot_versions, total_versions, max_lines, num_columns):
    local = os.getcwd()
    selected_version_id = input("Please enter snapshot version:")
    # Find minecraft_version after get version_id(IMPORTANT:version =/= version_id!)
    selected_version = next((version for version in version_list if version['id'] == selected_version_id), None)
    try:
        # Get version data
        if selected_version:
            version_url = selected_version['url']
            version_response = requests.get(version_url)
            version_data = version_response.json()

            # Download game file( libraries, .jar files...., and lwjgl!)
            ClearOutput(platform)
            print("DownoandTool: Loading version info...")
            download_libraries(version_data, selected_version_id)
            print("DownoandTool: The required dependent libraries should have been downloaded :)", color='blue')

            # Download assets(Also it will check this version are use legacy assets or don't use)
            print("DownoandTool: Now create assets...", color='green')
            get_assets_index_version(version_data, selected_version_id)
            get_asset(selected_version_id)
            os.chdir(local)

            # Finally....
            ClearOutput(GetPlatformName.check_platform_valid_and_return())
            print("DownoandTool: Now unzip natives...", color='green')
            unzip_natives(selected_version_id)

            ClearOutput(GetPlatformName.check_platform_valid_and_return())
            print("DownoandTool: Finally...download JVM!", color='green')
            download_jvm(version_data)

            print("DownoandTool: YAPPY! Now all files are download success :)", color='blue')
            print("DownoandTool: Exiting download tool....", color='green')

            # Add waiting time(If assets download failed it will print it?)
            time.sleep(1.2)
            ClearOutput(GetPlatformName.check_platform_valid_and_return())
        else:
            # idk this thing would happen or not :)  , just leave it and see what happen....
            print(f"DownoandTool: You type snapshot version {selected_version_id} are not found :(", color='red')
            download_snapshot(version_list, snapshot_versions, total_versions, max_lines, num_columns)

    except ValueError:
        # Back to download_main avoid crash(when user type illegal thing
        print("DownoandTool: Oops! Invalid input :( Please enter a vaild snapshot version.")
        download_snapshot(version_list, snapshot_versions, total_versions, max_lines, num_columns)


def download_main():
    # Get version_manifest_v2.json and list all version(also add version_id in version's left :)
    url = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"
    response = requests.get(url)
    data = response.json()
    version_list = data['versions']

    release_versions = [version['id'] for version in version_list if version['type'] == 'release']
    formatted_versions = '\n'.join([f"{index + 1}: {version}"
                                    for index, version in enumerate(release_versions)])

    snapshot_versions = [version['id'] for version in version_list if version['type'] == 'snapshot']
    formatted_snapshot_versions = '\n'.join([f"{version}"
                                    for index, version in enumerate(snapshot_versions)])

    # Small test...
    total_versions = len(snapshot_versions)
    num_columns = 5
    max_lines = (total_versions + num_columns - 1)
    total_entries = num_columns * max_lines

    print("Which method you wanna use?", color='green')
    print("1:List all available versions and download 2:Type Minecraft version and download 3: Download snapshot")

    try:
        user_input = int(input(":"))
        if user_input == 1:
            download_with_version_id(version_list, release_versions, formatted_versions)
        elif user_input == 2:
            download_with_version_tunple(version_list)
        elif user_input == 3:
            print("DownloadTool: Download snapshot maybe unstable(You may get DownloadAssetsFailed!)")
            time.sleep(1.5)
            download_snapshot(version_list, snapshot_versions, total_versions, max_lines, max_lines)
        else:
            print("DownloadTool: Unknow options :( Please try again.", color='red')
            download_main()

    except ValueError:
        # Back to main avoid crash(when user type illegal thing)
        print("BakeLaunch: Oops! Invalid option :O  Please enter a number.", color='red')

        download_main()