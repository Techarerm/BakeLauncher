import os
import json
import requests
from tqdm import tqdm
from LauncherBase import Base, print_custom as print
from concurrent.futures import ThreadPoolExecutor, as_completed
from libs.Utils.utils import get_version_data


class AssetsGrabber:
    def __init__(self):
        self.without_downloaded_output = None
        self.manifest_url = "https://launchermeta.mojang.com/mc/game/version_manifest_v2.json"
        self.minecraft_version = "1.20"
        self.version_data = []

    @staticmethod
    def grab_asset_index_file(version_data, save_dir):
        """
        Get assets index url from version data
        """
        asset_index_url = version_data['assetIndex']['url']

        # Download the asset index data
        response = requests.get(asset_index_url)

        # Save the file to the specified directory
        asset_index_file = os.path.join(save_dir, f"{version_data['assetIndex']['id']}.json")
        with open(asset_index_file, 'wb') as f:
            f.write(response.content)

        print(
            f"Asset index {version_data['assetIndex']['id']}.json downloaded successfully to {save_dir}",
            color='blue')
        return response.json()

    def get_assets_index_data(self, version_data, instance_path):
        """
        Get the assets index version from the version_data and save it to a JSON file
        LaunchManager needs this when launching Minecraft (To set assetsIndex)
        """
        print("Trying to get assetsIndex version....", color='green')
        asset_index = version_data.get("assetIndex", {})
        asset_index_id = asset_index.get("id")

        assets_index_file = os.path.join(instance_path, '.minecraft', "assets_index.json")

        if asset_index_id:
            with open(assets_index_file, 'w') as f:
                json.dump(asset_index, f, indent=4)
            print(f"AssetsIndex config has been saved :)", color='blue')
        else:
            print("Failed to config AssetsIndex :(", color='red')
            print("Please try again later (If still can't get assetsIndex please report this bug to GitHub!",
                  color='yellow')
            print(
                "IMPORTANT: 'Do not launch it if failed to get assetsIndex. You might get a broken version of "
                "Minecraft :D",
                color='yellow')
            print("Asset index not found.", color='red')

    @staticmethod
    def get_assets_index_version(version_id):
        try:
            with open('assets_index.json', 'r') as file:
                data = json.load(file)
            assetsIndex_version = data['id']
            return assetsIndex_version

        except FileNotFoundError:
            print("Failed to get assetsIndex version. Cause by FileNotFoundError.", color='red')

    def download_asset_file(self, asset_name, asset_info, objects_dir):

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
            if Base.UsingLegacyDownloadOutput:
                print(f"Downloaded: {asset_name} -> {asset_hash}")
        except Exception as e:
            print(f"Failed to download: {asset_name}. Error: {e}")

    def download_legacy_assets(self, asset_name, asset_info, assets_dir):
        hash_value = asset_info['hash']
        hash_prefix = hash_value[:2]
        download_url = f'https://resources.download.minecraft.net/{hash_prefix}/{hash_value}'
        file_path = os.path.join(assets_dir, 'virtual', 'legacy', asset_name.replace("/", os.sep))

        # Create the directory if it doesn't exist
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # Download the asset if it doesn't already exist
        if not os.path.exists(file_path):
            if Base.UsingLegacyDownloadOutput:
                print(f"Downloading {asset_name}...")
            response = requests.get(download_url, stream=True)
            if response.status_code == 200:
                with open(file_path, 'wb') as file:
                    file.write(response.content)
            else:
                print(f"Failed to download {asset_name}: Status code {response.status_code}")

    def download_assets_plus(self, asset_index, objects_dir, mode):
        if mode == "ModernAssets":
            assets = asset_index['objects']
            total_assets = len(assets)
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = {executor.submit(self.download_asset_file, asset_name, asset_info, objects_dir): asset_name
                           for asset_name, asset_info in assets.items()}
                if Base.UsingLegacyDownloadOutput:
                    for future in as_completed(futures):
                        asset_name = futures[future]
                        try:
                            future.result()
                        except Exception as e:
                            print(f"Error downloading {asset_name}: {e}", color='red')
                else:
                    with tqdm(total=total_assets, desc="Downloading Assets", colour='cyan') as pbar:
                        for future in as_completed(futures):
                            asset_name = futures[future]
                            try:
                                future.result()
                            except Exception as e:
                                print(f"Error downloading {asset_name}: {e}", color='red')
                            finally:
                                pbar.update(1)

        if mode == "LegacyAssets":
            # Load the asset index JSON file
            index_path = os.path.join(objects_dir, 'indexes', f"{asset_index}.json")

            with open(index_path, 'r') as f:
                asset_index = json.load(f)

            objects = asset_index.get('objects', {})
            total_assets = len(objects)

            # Use ThreadPoolExecutor to download concurrently
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = {
                    executor.submit(self.download_legacy_assets, asset_name, asset_info, objects_dir): asset_name
                    for asset_name, asset_info in objects.items()
                }
                if Base.UsingLegacyDownloadOutput:
                    for future in as_completed(futures):
                        asset_name = futures[future]
                        try:
                            future.result()
                        except Exception as e:
                            print(f"Error downloading {asset_name}: {e}", color='red')
                else:
                    with tqdm(total=total_assets, desc="Downloading Legacy Assets", colour='cyan') as pbar:
                        for future in as_completed(futures):
                            asset_name = futures[future]
                            try:
                                future.result()
                                pbar.update(1)  # Increment only if successful
                            except Exception as e:
                                print(f"Error downloading {asset_name}: {e}", color='red')

            print("Legacy assets have been downloaded :)", color='blue')

    @staticmethod
    def get_assets_dir(version_id):
        legacy_assets_dir = os.path.join("assets", "virtual", "legacy")
        try:
            with open("assets_index.json", "r") as file:
                data = json.load(file)
                AssetsIndex = data['id']
                if AssetsIndex == "pre-1.6" or AssetsIndex == "legacy":
                    return legacy_assets_dir
                else:
                    return "assets"
        except FileNotFoundError:
            print("Failed to get assets dir :( Try using the second method...", color='red')
            if version_id == "pre-1.6" or version_id == "legacy":
                return legacy_assets_dir
            else:
                return "assets"

    def assets_file_grabber(self, version_id, instance_dir):
        # Get version data
        version_data = get_version_data(version_id)

        # Set select instance, game_folder(.minecraft), assets_index_json, save_dir path
        game_folder = os.path.join(instance_dir, ".minecraft")
        assets_index_json = os.path.join(game_folder, "assets_index.json")
        save_dir = os.path.join(game_folder, "assets", "indexes")  # Assets file save path

        # Change work directory to instance(instances/{version_id})
        if not os.path.exists(instance_dir):
            os.makedirs(instance_dir, exist_ok=True)
        os.chdir(instance_dir)
        # If .minecraft does not exist, create it.
        if os.path.exists(".minecraft"):
            print(".minecraft already created!", color='green')
        else:
            print("Can't find .minecraft folder! Creating...", color='yellow')
            os.makedirs(".minecraft", exist_ok=True)

        # Change work directory to instance(instances/{version_id}/.minecraft)
        os.chdir(game_folder)
        # If assets does not exist, create it.
        if os.path.exists("assets"):
            print("Assets already created!", color='green')
        else:
            print("Can't find assets folder! Creating...", color='yellow')
            os.makedirs("assets", exist_ok=True)

        # Change work directory to instance(instances/{version_id}/.minecraft/assets) (preparing to download assets)
        os.chdir("assets")
        # If indexes does not exist, create it...
        if os.path.exists("indexes"):
            print("Indexes already created!", color='green')
        else:
            print("Can't find indexes folder! Creating...", color='yellow')
            os.makedirs("indexes", exist_ok=True)

        if version_data:
            asset_index = self.grab_asset_index_file(version_data, "indexes")

            # Now download the actual asset files into the objects directory
            objects_dir = os.path.join(game_folder, "assets", "objects")
            self.download_assets_plus(asset_index, objects_dir, "ModernAssets")
        else:
            print("Failed to get version_data! Cause by unknown Minecraft version.", color='red')

        # Change work directory back to instance path
        os.chdir(instance_dir)

        # Is for LaunchManager to get assets index version
        if not os.path.exists(assets_index_json):
            version_data = get_version_data(version_id)
            self.get_assets_index_data(version_data, instance_dir)

        # Read assets index version(prepare to check if this version of minecraft are using old assets?)
        try:
            with open(assets_index_json, "r") as file:
                data = json.load(file)
                assetsIndex = data["id"]
        except FileNotFoundError:
            print("Failed to get assets index! Trying to recreate it again...", color='red')

        if assetsIndex == "pre-1.6" or assetsIndex == "legacy":
            print("This version require legacy assets.", color='green', tag="DEBUG")
            print("Downloading legacy assets...", color='green')
            assets_dir = os.path.join(game_folder, "assets")
            if assetsIndex == "pre-1.6":
                self.download_assets_plus("pre-1.6", assets_dir, "LegacyAssets")
            else:
                if assetsIndex == "legacy":
                    self.download_assets_plus("legacy", assets_dir, "LegacyAssets")
                else:
                    print("??? Can't found assets name! Bypass it....)", color='red')


assets_grabber = AssetsGrabber()
