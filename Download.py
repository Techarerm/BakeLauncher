import requests
import os
import subprocess
import shutil
import assets_tool
from assets_tool import get_asset
import zipfile

def get_lwjgl_version(major, minor):
    if major == 1:
        if minor <= 7:
            return "2.6.x"  # For versions 1.0 - 1.7.2
        elif minor == 7 and (patch and patch[0] <= 2):  # For 1.7.3
            return "2.8.x"
        elif minor <= 8:
            return "2.9.4"  # For versions 1.8 - 1.12
        elif minor == 13:
            return "3.1.6"  # For version 1.13
        elif minor <= 18:
            return "3.2.2"  # For versions 1.14 - 1.18
        elif minor >= 19:
            return "3.3.3"  # For versions 1.19 and newer
    return None


def download_file(url, dest_path):
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        with open(dest_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        print(f"Downloaded successfully: {dest_path}")
    except requests.exceptions.RequestException as e:
        print(f"Failed to download {url}: {e}")

def extract_zip(zip_path, extract_to):
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        print(f"Extracted {zip_path} to {extract_to}")
    except zipfile.BadZipFile as e:
        print(f"Error extracting {zip_path}: {e}")

def download_lwjgl(version_id):
    major, minor, *patch = map(int, version_id.split('.'))
    lwjgl_version = get_lwjgl_version(major, minor)

    if not lwjgl_version:
        print(f"No LWJGL version found for Minecraft version {version_id}")
        return

    lwjgl_url = f"https://github.com/Techarerm/LWJGL-Library/raw/main/LWJGL%20{lwjgl_version}.zip"
    lwjgl_dest = os.path.join("LWJGL", f"LWJGL_{lwjgl_version}.zip")

    print(f"Downloading LWJGL {lwjgl_version} to {lwjgl_dest}...")
    download_file(lwjgl_url, lwjgl_dest)
    extract_dir = os.path.join("LWJGL", lwjgl_version)  # Use LWJGL version for the folder name
    extract_zip(lwjgl_dest, extract_dir)
    print(f"LWJGL {lwjgl_version} downloaded and extracted to {extract_dir}.")


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


def request_version_url():
    global selected_version_id
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
        print("Example: 15: 1.12.2 , 15 is version 1.12's ID")
        user_input = int(input("Please enter the version ID: ")) - 1

        if 0 <= user_input < len(release_versions):
            selected_version_id = release_versions[user_input]
            selected_version = next((version for version in version_list if version['id'] == selected_version_id), None)

            if selected_version:
                version_url = selected_version['url']
                version_response = requests.get(version_url)
                version_data = version_response.json()

                print(f"Version {selected_version_id} details:")
                print(selected_version_id)
                print("Loading version info...")
                down_tool(version_data, selected_version_id)
                os.system("cls")
                print("The required dependent libraries should have been downloaded :)")
                print("Now downloading LWJGL...")
                download_lwjgl(selected_version_id)
                print("Now downloading McAssetExtractor...")
                print("Download success!")
                print("Create assets...")
                get_asset(selected_version_id)
                print("YAPPY! Now all files are download success :)")
                print("Exiting download tool....")
                return selected_version_id
            else:
                print("Error: Version not found.")
                request_version_url()
        else:
            print("Error: Invalid version ID.")
            request_version_url()
    except ValueError:
        print("Oops! Invalid input. Please enter a number corresponding to a version ID.")
        request_version_url()
