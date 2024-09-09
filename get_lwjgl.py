import os
import requests
from bs4 import BeautifulSoup
from __init__ import GetPlatformName, LWJGL_Maven
from Download import download_file
from print_color import print

def get_lwjgl_version(version_id):
    """
    Check Minecraft support LWJGL version.
    """
    version_tuple = tuple(map(int, version_id.split(".")))
    print("LaunchManager: Checking supported LWJGL version...", color='green')

    if version_tuple < (1, 7, 3):
        print("LaunchManager: Using LWJGL 2.9.0", color='blue')
        return "2.9.0"
    elif (1, 7, 3) <= version_tuple <= (1, 8, 1):
        print("LaunchManager: Using LWJGL 2.9.1", color='blue')
        return "2.9.1"
    elif (1, 8, 2) <= version_tuple <= (1, 12, 2):
        print("LaunchManager: Using LWJGL 2.9.4", color='blue')
        return "2.9.4"
    elif (1, 9) <= version_tuple <= (1, 12, 2):
        print("LaunchManager: Using LWJGL 2.9.4", color='blue')
        return "2.9.4"
    elif version_tuple <= (1, 13, 2):
        print("LaunchManager: Using LWJGL 3.1.6", color='blue')
        return "3.1.6"
    elif version_tuple <= (1, 14, 2):
        print("LaunchManager: Using LWJGL 3.2.1", color='blue')
        return "3.2.1"
    elif version_tuple <= (1, 14, 3):
        print("LaunchManager: Using LWJGL 3.2.2", color='blue')
        return "3.2.2"
    elif version_tuple >= (1, 19):
        print("LaunchManager: Using LWJGL 3.3.3", color='blue')
        return "3.3.3"
    else:
        print("LaunchManager: Unsupported Minecraft version :(")
        return None

def download_lwjgl(lwjgl_version, platform_name):
    platform_name = platform_name.lower()
    lwjgl_maven_version = f"{LWJGL_Maven}{lwjgl_version}/"  # Fixed the URL format
    response = requests.get(lwjgl_maven_version)

    # Ensure LWJGL and tmp directories exist
    if not os.path.exists("LWJGL"):
        os.makedirs("LWJGL")
    if not os.path.exists("LWJGL/tmp"):
        os.makedirs("LWJGL/tmp")

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        jar_files = [a['href'] for a in soup.find_all('a', href=True) if f"natives-{platform_name}.jar" in a['href']]

        # Download each matching file
        for jar_file in jar_files:
            download_url = f"{lwjgl_maven_version}{jar_file}"  # Construct the full download URL
            file_path = os.path.join("LWJGL/tmp", jar_file)  # Specify the full path to save the file
            download_file(download_url, file_path)  # Pass the full path to the download_file function
    else:
        print(f"Failed to fetch the LWJGL version page: {lwjgl_maven_version}", color='red')

def get_lwjgl_main(version):
    print("DownloadTools(LWJGL): Checking platform for LWJGL...", color='green')
    platform_name = GetPlatformName.check_platform_valid_and_return()

    if platform_name == "Darwin":
        platform_name = "macos"

    lwjgl_version = get_lwjgl_version(version)

    if lwjgl_version:
        download_lwjgl(lwjgl_version, platform_name)
    else:
        print("LaunchManager: Unsupported LWJGL version for Minecraft.", color='red')

get_lwjgl_main("1.14")
