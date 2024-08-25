''''
Is a small script to download game files.
(Minecraft file download from Mojang CDN)
'''

import requests
import os
import subprocess
import shutil
import zipfile
import time
import assets_grabber
from assets_grabber import get_asset
import launch_version_patcher
from launch_version_patcher import patcher_main
import print_color
from print_color import print

def get_lwjgl_version(minecraft_version):
    version_tuple = tuple(map(int, minecraft_version.split(".")))

    if version_tuple >= (1, 19, 0):
        return "LWJGL_3.3.3"
    elif version_tuple < (1, 7, 3):
        return "LWJGL_2.6.x"
    elif (1, 7, 3) <= version_tuple < (1, 8, 1):
        return "LWJGL_2.8.x(1.7)"
    elif version_tuple == (1, 8, 1):
        return "LWJGL_2.8.x(1.8)"
    elif (1, 8, 2) <= version_tuple <= (1, 8, 9):
        return "LWJGL_2.9.x(1.8.2)"
    elif (1, 9) <= version_tuple <= (1, 12, 2):
        return "LWJGL_2.9.4"
    elif version_tuple <= (1, 13, 2):
        return "LWJGL_3.1.6"
    elif version_tuple <= (1, 14, 2):
        return "LWJGL_3.2.1(1.14)"
    elif version_tuple <= (1, 14, 3):
        return "LWJGL_3.2.2(1.15)"
    elif version_tuple <= (1, 18, 2):
        return "LWJGL_3.2.2(1.16)"
    return None


def download_file(url, dest_path):
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()

        dest_dir = os.path.dirname(dest_path)
        if dest_dir:  # Check if dest_dir is not empty
            os.makedirs(dest_dir, exist_ok=True)

        with open(dest_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        print(f"Downloaded successfully: {dest_path}")
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

def download_lwjgl(version_id):
    lwjgl_version = get_lwjgl_version(version_id)

    if version_id == None:
        print(f"No LWJGL version found for Minecraft version {version_id}", color='yellow')
        return
    else:
        print(lwjgl_version)

    # Compute the SHA1 hash (as a placeholder example, use the version_id)
    sha1_hash = "455edb6b1454a7f3243f37b5f240f69e1b0ce4fa"  # Placeholder, use actual hash if needed
    extract_dir = os.path.join("LWJGL")

    # Define destination path for the zip file
    lwjgl_dest = os.path.join(f"{lwjgl_version}.zip")

    print(f"Downloading LWJGL {lwjgl_version} ...")
    download_success = download_file(f"https://github.com/Techarerm/LWJGL-Library/raw/main/{lwjgl_version}.zip", lwjgl_dest)

    if not download_success:
        print(f"Failed to download LWJGL {lwjgl_version}. Exiting...", color='red')
        return  # Exit the function or handle as needed

    # Extract the zip file to the desired directory structure
    extract_zip(lwjgl_dest, extract_dir)
    print(f"LWJGL Library has been extracted to {extract_dir}!")
    if os.path.exists(f"{lwjgl_version}.zip"):
        print("Cleaning up...")
        os.remove(f"{lwjgl_version}.zip")
def down_tool(version_data, version_id):
    version_dir = os.path.join("versions", version_id)
    libraries_dir = os.path.join(version_dir, "libraries")
    os.makedirs(libraries_dir, exist_ok=True)

    client_info = version_data['downloads']['client']
    client_url = client_info['url']
    client_dest = os.path.join(version_dir, 'client.jar')
    print(f"Downloading client.jar to {client_dest}...")
    download_file(client_url, client_dest)

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
                if action == 'allow' and (not os_info or os_info.get('name') == 'windows'):
                    allowed = True
                elif action == 'disallow' and os_info and os_info.get('name') == 'windows':
                    allowed = False
                    break
            if not allowed:
                continue

        if artifact:
            lib_path = artifact['path']
            lib_url = artifact['url']
            lib_dest = os.path.join(libraries_dir, lib_path)
            print(f"Downloading {lib_path} to {lib_dest}...")
            download_file(lib_url, lib_dest)


def download_main():
    url = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"
    response = requests.get(url)
    data = response.json()
    version_list = data['versions']

    release_versions = [version['id'] for version in version_list if version['type'] == 'release']
    formatted_versions = '\n'.join([f"{index + 1}: {version}"
                                    for index, version in enumerate(release_versions)])
    print("Activable version list:")
    print(formatted_versions + "\n")

    try:
        print("Example: 15: 1.12.2 , 15 is version 1.12's ID", color='green')
        user_input = int(input("Please enter the version ID: ")) - 1

        if 0 <= user_input < len(release_versions):
            selected_version_id = release_versions[user_input]
            selected_version = next((version for version in version_list if version['id'] == selected_version_id), None)

            if selected_version:
                version_url = selected_version['url']
                version_response = requests.get(version_url)
                version_data = version_response.json()

                print(f"DownoandTool: Version {selected_version_id} details:")
                print(selected_version_id)
                print("DownoandTool: Loading version info...")
                down_tool(version_data, selected_version_id)
                os.system("cls")
                print("DownoandTool: The required dependent libraries should have been downloaded :)", color='blue')
                print("DownoandTool: Now downloading LWJGL...", color='green')
                download_lwjgl(selected_version_id)
                print("DownoandTool: Now create assets...", color='green')
                get_asset(selected_version_id)
                print("DownoandTool: YAPPY! Now all files are download success :)",color='blue')
                print("DownoandTool: Exiting download tool....", color='green')
                time.sleep(1.2)
            else:
                print("DownoandTool: Version not found.", color='red')
                download_main()
        else:
            print("DownoandTool: Invalid version ID.", color='red')
            download_main()
    except ValueError:
        print("DownoandTool: Oops! Invalid input. Please enter a number corresponding to a version ID.")
        download_main()
