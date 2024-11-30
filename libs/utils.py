import requests
import os
from LauncherBase import Base, print_custom as print

VersionManifestURl = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"
LegacyVersionManifestURl = ("https://github.com/Techarerm/BakeLauncher-Library/raw/refs/heads/main/Legacy"
                            "%20Manifest/version_manifest_legacy.json")


def get_version_data(version_id, **kwargs):
    """
    Get version_manifest_v2.json and find requires version of json data
    """
    use_legacy_json = kwargs.get("use_legacy_json", False)

    response = requests.get(VersionManifestURl)
    data = response.json()
    version_list = data['versions']

    version_url = None
    for v in version_list:
        if v['id'] == version_id:
            version_url = v['url']
            break

    if version_url is None:
        response = requests.get(LegacyVersionManifestURl)
        data = response.json()
        version_list = data['versions']

        version_url = None
        for v in version_list:
            if v['id'] == version_id:
                version_url = v['url']
                break

    # If the version_id not in version_list, return None
    if version_url is None:
        print(f"Unable to find same as requires version id: {version_id} in the version_manifest.", color='red')
        print("Failed to get version data. Cause by unknown Minecraft version.", color='red')
        return None

    try:
        # Get version data
        version_response = requests.get(version_url)
        version_data = version_response.json()
        return version_data
    except Exception as e:
        print(f"Error occurred while fetching version data: {e}", color='red')
        print("Failed to get version data. Cause by internet connect error or unknown issues.", color='red')
        return None


def download_file(url, dest_path):
    """
    Downloads a file from a URL and saves it to dest_path.
    """
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()

        # Create the directory if it doesn't exist
        dest_dir = os.path.dirname(dest_path)
        if dest_dir:
            os.makedirs(dest_dir, exist_ok=True)

        # Write the file to dest_path
        with open(dest_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        if Base.UsingLegacyDownloadOutput:
            print(f"Download successful: {dest_path}")
        return True  # Indicate success
    except requests.exceptions.RequestException as e:
        print(f"Failed to download {url}: {e}")
        return False  # Indicate failure
