import requests
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import hashlib
import print_color
from print_color import print

def get_version_json(version):
    # Download the version manifest
    manifest_url = "https://launchermeta.mojang.com/mc/game/version_manifest_v2.json"
    response = requests.get(manifest_url)
    manifest = response.json()

    # Find the specific version JSON URL
    version_info = next((v for v in manifest['versions'] if v['id'] == version), None)
    if not version_info:
        raise ValueError(f"AssetsGarbber: Version {version} not found.", tag='Failed', tag_color='red')

    # Download the version JSON
    version_json_url = version_info['url']
    version_json_response = requests.get(version_json_url)
    return version_json_response.json()


def download_asset_index(version_json, save_dir):
    # Extract the asset index URL from the version JSON
    asset_index_url = version_json['assetIndex']['url']

    # Download the asset index JSON
    response = requests.get(asset_index_url)

    # Save the file to the specified directory
    asset_index_file = os.path.join(save_dir, f"{version_json['assetIndex']['id']}.json")
    with open(asset_index_file, 'wb') as f:
        f.write(response.content)

    print(f"AssetsGarbber: Asset index {version_json['assetIndex']['id']}.json downloaded successfully to {save_dir}", color='blue')
    return response.json()


def download_asset(asset_name, asset_info, objects_dir):
    asset_hash = asset_info['hash']
    hash_prefix = asset_hash[:2]
    url = f"https://resources.download.minecraft.net/{hash_prefix}/{asset_hash}"

    # Determine the path where the asset will be saved
    asset_save_path = os.path.join(objects_dir, hash_prefix, asset_hash)

    # Create the directory if it doesn't exist
    os.makedirs(os.path.dirname(asset_save_path), exist_ok=True)

    # Download and save the asset file
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()

        with open(asset_save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        print(f"Downloaded: {asset_name} -> {asset_hash}")
    except Exception as e:
        print(f"Failed to download: {asset_name}. Error: {e}",color='red')


def download_assets(asset_index, objects_dir):
    assets = asset_index['objects']

    # Use ThreadPoolExecutor to download assets concurrently
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(download_asset, asset_name, asset_info, objects_dir): asset_name for
                   asset_name, asset_info in assets.items()}
        for future in as_completed(futures):
            asset_name = futures[future]
            try:
                future.result()  # This will raise an exception if download_asset failed
            except Exception as e:
                print(f"Error downloading {asset_name}: {e}", color='red')


def get_asset(version_id):
    local = os.getcwd()
    os.chdir("versions\\" + version_id)

    if os.path.exists(".minecraft"):
        print(".minecraft already created!", color='green')
    else:
        print("Can't find .minecraft folder! Creating...", color='yellow')
        os.makedirs(".minecraft", exist_ok=True)

    os.chdir(".minecraft")
    minecraft = os.getcwd()

    if os.path.exists("assets"):
        print("Assets already created!", color='green')
    else:
        print("Can't find assets folder! Creating...", color='yellow')
        os.makedirs("assets", exist_ok=True)

    os.chdir("assets")
    if os.path.exists("indexes"):
        print("Indexes already created!", color='green')
    else:
        print("Can't find indexes folder! Creating...", color='yellow')
        os.makedirs("indexes", exist_ok=True)

    save_dir = minecraft + "\\assets\\" + "indexes"
    version_json = get_version_json(version_id)
    if version_json:
        asset_index = download_asset_index(version_json, save_dir)

        # Now download the actual asset files into the objects directory
        objects_dir = os.path.join(minecraft, "assets", "objects")
        download_assets(asset_index, objects_dir)
    os.chdir(local)
    version_tuple = tuple(map(int, version_id.split(".")))
    if version_tuple <= (1, 7, 2):
        print("Your want to download version's type are 'Legacy'!", color='green')
        print("Downloading Legacy assets now...", color='green')
        assets_dir = "versions\\" + version_id + "\\.minecraft\\" + "assets"
        if version_tuple < (1, 6, 0):
            Index = "pre-1.6"
            download_legacy_assets(version_id, assets_dir, Index)
        else:
            Index = "Legacy"
            if version_tuple < (1, 7, 3):
                Index = "legacy"
                download_legacy_assets(version_id, assets_dir, Index)
            else:
                print("??? Can't found assets name! Bypass it....)",color='red')

def download_legacy_assets(version, assets_dir, assetsIndex):
    # Load the asset index JSON file
    index_path = os.path.join(assets_dir, 'indexes', f"{assetsIndex}.json")  # Fix format here
    with open(index_path, 'r') as f:
        asset_index = json.load(f)

    objects = asset_index.get('objects', {})

    for asset_name, asset_info in objects.items():
        hash_value = asset_info['hash']
        hash_prefix = hash_value[:2]
        download_url = f'https://resources.download.minecraft.net/{hash_prefix}/{hash_value}'
        file_path = os.path.join(assets_dir, 'virtual', 'legacy', asset_name.replace("/", os.sep))

        # Create the directory if it doesn't exist
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # Download the asset if it doesn't already exist
        if not os.path.exists(file_path):
            print(f"Downloading {asset_name}...")
            response = requests.get(download_url, stream=True)
            if response.status_code == 200:
                with open(file_path, 'wb') as file:
                    file.write(response.content)

    print("Legacy assets have been downloaded :)", color='blue')
