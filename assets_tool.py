import requests
import os


def get_version_json(version):
    # Download the version manifest
    manifest_url = "https://launchermeta.mojang.com/mc/game/version_manifest_v2.json"
    response = requests.get(manifest_url)
    manifest = response.json()

    # Find the specific version JSON URL
    version_info = next((v for v in manifest['versions'] if v['id'] == version), None)
    if not version_info:
        raise ValueError(f"Version {version} not found.")

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

    print(f"Asset index {version_json['assetIndex']['id']}.json downloaded successfully to {save_dir}")
    return response.json()


def download_assets(asset_index, objects_dir):
    assets = asset_index['objects']

    for asset_name, asset_info in assets.items():
        asset_hash = asset_info['hash']
        hash_prefix = asset_hash[:2]
        url = f"https://resources.download.minecraft.net/{hash_prefix}/{asset_hash}"

        # Determine the path where the asset will be saved
        asset_save_path = os.path.join(objects_dir, hash_prefix, asset_hash)

        # Create the directory if it doesn't exist
        os.makedirs(os.path.dirname(asset_save_path), exist_ok=True)

        # Download and save the asset file
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            with open(asset_save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            print(f"Downloaded: {asset_name} -> {asset_hash}")
        else:
            print(f"Failed to download: {asset_name}")


def get_asset(version_id):
    local = os.getcwd()
    os.chdir("versions\\" + version_id)

    if os.path.exists(".minecraft"):
        print(".minecraft already created!")
    else:
        print("Can't find .minecraft folder! Creating...")
        os.makedirs(".minecraft", exist_ok=True)

    os.chdir(".minecraft")
    minecraft = os.getcwd()

    if os.path.exists("assets"):
        print("Assets already created!")
    else:
        print("Can't find assets folder! Creating...")
        os.makedirs("assets", exist_ok=True)

    os.chdir("assets")
    if os.path.exists("indexes"):
        print("Indexes already created!")
    else:
        print("Can't find indexes folder! Creating...")
        os.makedirs("indexes", exist_ok=True)

    save_dir = minecraft + "\\assets\\" + "indexes"
    version_json = get_version_json(version_id)
    if version_json:
        asset_index = download_asset_index(version_json, save_dir)

        # Now download the actual asset files into the objects directory
        objects_dir = os.path.join(minecraft, "assets", "objects")
        download_assets(asset_index, objects_dir)
    os.chdir(local)