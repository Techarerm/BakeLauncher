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

def get_assets_index_version(version_data, version_id):
    """
    Get the assets index version from the version_data and save it to a JSON file
    LaunchManager need this when launching Minecraft(To set assetsIndex)
    """
    print("Trying to get assetsIndex version....", color='green')
    print(os.getcwd())
    asset_index = version_data.get("assetIndex", {})
    asset_index_id = asset_index.get("id")
    if asset_index_id:
        assets_index_file = os.path.join(".minecraft","assets_index.json")
        with open(assets_index_file, 'w') as f:
            json.dump(asset_index, f, indent=4)
        print(f"AssetsIndex config has been saved :)", color='blue')
    else:
        print("Failed to config AssetsIndex :(", color='red')
        print("Maybe is the server issue let DownloadTool can't getting AssetsIndex?", color='yellow')
        print("Please try again later(If still can't get assetsIndex please report this bug to GitHib!", color='yellow')
        print("IMPORANT:'Do not launch it if failed to get assetsIndex. You might get a broken version of Minecraft :D", color='yellow')
        print("Asset index not found.", color='red')

def get_asset(version_id):
    local = os.getcwd()
    os.chdir("instances/" + version_id)

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

    save_dir = minecraft + "/assets/" + "indexes"
    version_json = get_version_json(version_id)
    if version_json:
        asset_index = download_asset_index(version_json, save_dir)

        # Now download the actual asset files into the objects directory
        objects_dir = os.path.join(minecraft, "assets", "objects")
        download_assets(asset_index, objects_dir)
    os.chdir(local)
    if not os.path.exists("instances/" + version_id + "/.minecraft/" + "assets_index.json"):
        version_data = get_version_json(version_id)
        os.chdir("instances/" + version_id)
        get_assets_index_version(version_data, version_id)
        os.chdir(local)

    with open("instances/" + version_id + "/.minecraft/" + "assets_index.json", "r") as file:
        data = json.load(file)
        assetsIndex = data["id"]
    if assetsIndex == "pre-1.6" or assetsIndex == "legacy":
        print("Your want to download version's type are 'Legacy'!", color='green')
        print("Downloading Legacy assets now...", color='green')
        assets_dir = "instances/" + version_id + "/.minecraft/" + "assets"
        if assetsIndex == "pre-1.6":
            download_legacy_assets(version_id, assets_dir, assetsIndex)
        else:
            if assetsIndex == "legacy":
                download_legacy_assets(version_id, assets_dir, assetsIndex)
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

def assetsIndexFix(Main, local, selected_version_id):
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
            print(f"{Main}: Loading version info...", color='green')
            version_url = selected_version['url']
            version_response = requests.get(version_url)
            version_data = version_response.json()
            get_assets_index_version(version_data, selected_version_id)

    except ValueError:
        # Back to main avoid crash
        print(f"{Main}: Can't fix assetsIndex :(.", color='red')
        back_to_main()

def read_assets_index_version(Main, local, version_id):
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
        assetsIndexFix(Main, local, version_id)
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
            assetsIndexFix(Main, local, version_id)

def get_assets_dir(version_id):
    assets_dir = ".minecraft/assets"

    try:
        with open(".minecraft/assets_index.json", "r") as file:
            data = json.load(file)
            AsstesIndex = data['id']
            if AsstesIndex == "pre-1.6" or AsstesIndex == "legacy":
                return assets_dir + "/virtual/legacy"
            else:
                return assets_dir
    except FileNotFoundError:
        return "FailedToOpenAssetsIndexFile"

