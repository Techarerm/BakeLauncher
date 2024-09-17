import zipfile
import os
import print_color
import __init__
from __init__ import GetPlatformName
from print_color import print


def unzip_natives(version):
    PlatformName = GetPlatformName.check_platform_valid_and_return().lower()

    # Handle platform naming for macOS
    if PlatformName == 'darwin':
        PlatformName = 'macos'

    if not os.path.exists(".minecraft/natives"):
        os.mkdir(".minecraft/natives")

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