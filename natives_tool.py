import zipfile
import os
import requests
from __function__ import GetPlatformName
from print_color import print

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

def unzip_natives(version):
    PlatformName = GetPlatformName.check_platform_valid_and_return().lower()

    # Handle platform naming for macOS
    if PlatformName == 'darwin':
        PlatformName = 'macos'

    local = os.getcwd()
    if not os.path.exists(f"instances/{version}/.minecraft/natives"):
        os.mkdir(f"instances/{version}/.minecraft/natives")

    os.chdir(f"instances/{version}")
    # Find all natives and unzip
    print("LWJGLPatch: Unzipping Natives...")
    jar_files = []

    for root, dirs, files in os.walk('libraries'):
        for file in files:
            if file.endswith(f"natives-{PlatformName}.jar"):
                jar_files.append(os.path.join(root, file))
            elif PlatformName == 'macos' and file.endswith("natives-osx.jar"):
                # Fallback to natives-osx.jar if natives-macos.jar is not found
                jar_files.append(os.path.join(root, file))

    if jar_files:
        for jar_file in jar_files:
            print(f"Found: {jar_file}", color='blue')

            # Create "natives" folder in libraries
            base_dir_name = os.path.basename(os.path.dirname(jar_file))
            natives_dir = os.path.join(os.path.dirname(jar_file), f"natives_{base_dir_name}")
            os.makedirs(natives_dir, exist_ok=True)

            # Extract only files from the JAR to the unique 'natives' directory
            with zipfile.ZipFile(jar_file, 'r') as jar:
                for member in jar.namelist():
                    if not member.endswith('/'):
                        jar.extract(member, ".minecraft/natives")
                        print(f"Extracted: {member} to {natives_dir}", color='green')

    else:
        print("LWJGLPatch: No natives found to unzip!")
    os.chdir(local)

def Legacy_natives_bug_fix(Java_version, minecraft_version):
    # Patch for some idiot version bug
    if GetPlatformName.check_platform_valid_and_return() == "Darwin":
        print("NativesTool:Patching MC-118506...")
        directory = f"instances/{minecraft_version}/libraries/ca/weblite/1.0.0"
        if not os.path.exists(directory):
            os.makedirs(directory)  # Create intermediate directories if needed
            url = "https://libraries.minecraft.net/ca/weblite/java-objc-bridge/1.0.0/java-objc-bridge-1.0.0.jar"
            try:
                download_file(url, f"{directory}java-objc-bridge-1.0.0.jar")
            except Exception as e:
                print(f"An error occurred: {e}")