import requests
from LauncherBase import print_custom as print

mojang_version_manifest_url = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"


def get_version_data(version_id, **kwargs):
    """
    Get version_manifest_v2.json and find requires version of json data
    """

    # parameter stuff
    version_manifest_url = kwargs.get("custom_version_manifest_url", mojang_version_manifest_url)

    response = requests.get(version_manifest_url)
    data = response.json()
    version_list = data['versions']

    version_url = None
    for v in version_list:
        if v['id'] == version_id:
            version_url = v['url']
            break

    if version_url is None:
        print(f"Unable to find same as requires version id: {version_id} in the version_manifest.", color='red',
              tag="[DEBUG]")
        print("Failed to get version data. Cause by unknown Minecraft version.", color='red', tag="[DEBUG]")
        return None

    try:
        # Get version data
        version_response = requests.get(version_url)
        version_data = version_response.json()
        return version_data
    except Exception as e:
        print(f"Error occurred while fetching version data: {e}", color='red', tag="[DEBUG]")
        print("Failed to get version data :(", color='red', tag="[DEBUG]")
        return None


def check_minecraft_version_are_valid(version_id):
    """Check minecraft version is valid"""

    version_data = get_version_data(version_id)
    if version_data is None:
        return False
    else:
        test = version_data.get('libraries', None)
        if test is None:
            return False
        else:
            return True


def get_minecraft_version_url(version_id, **kwargs):
    """
    Get minecraft version url using version_id
    """
    # parameter stuff
    version_manifest_url = kwargs.get("custom_version_manifest_url", mojang_version_manifest_url)

    response = requests.get(version_manifest_url)
    data = response.json()
    version_list = data['versions']

    version_url = None
    for v in version_list:
        if v['id'] == version_id:
            version_url = v['url']
            break

    if version_url is None:
        print(f"Unable to find same as requires version id: {version_id} in the version_manifest.", color='red',
              tag="[DEBUG]")
        print("Failed to get version data. Cause by unknown Minecraft version.", color='red', tag="[DEBUG]")
        return None

    return version_url


def get_minecraft_version_list(**args):
    """Get the full minecraft version list from version_manifest_v2.json"""

    # parameter stuff
    version_manifest_url = args.get("custom_version_manifest_url", mojang_version_manifest_url)

    response = requests.get(version_manifest_url)
    data = response.json()
    version_list = data['versions']

    version_id_list = []
    for v in version_list:
        v_id = v['id']
        version_id_list.append(v_id)

    return version_id_list


def get_stable_or_newest_minecraft_version(version_type, **kwargs):
    """Get the newest minecraft version from version_manifest_v2.json (key 'latest' > 'release' and 'snapshot'"""
    # parameter stuff
    version_manifest_url = kwargs.get("custom_version_manifest_url", mojang_version_manifest_url)

    response = requests.get(version_manifest_url)
    data = response.json()
    latest_data = data.get("latest", {})

    latest_release = latest_data.get("release", None)
    latest_snapshot = latest_data.get("snapshot", None)

    if version_type == 'stable' or version_type == 'release':
        return latest_release
    elif version_type == 'snapshot' or version_type == 'newest':
        return latest_snapshot
    else:
        return latest_data

