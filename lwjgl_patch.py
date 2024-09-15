import zipfile
import os
import shutil
import __init__
from __init__ import GetPlatformName

def unzip_natives(version):
    PlatformName = GetPlatformName.check_platform_valid_and_return().lower()

    # Handle platform naming for macOS
    if PlatformName == 'darwin':
        PlatformName = 'macos'

    # Ensure the .minecraft/natives directory exists
    if not os.path.exists(".minecraft/natives"):
        os.makedirs(".minecraft/natives")

    # Find all natives and unzip
    print("LWJGLPatch: Unzipping Natives...")
    jar_files = []

    for root, dirs, files in os.walk('libraries'):
        for file in files:
            # Check for both natives-{PlatformName}.jar and legacy natives-osx.jar
            if file.endswith(f"natives-{PlatformName}.jar"):
                jar_files.append(os.path.join(root, file))
            elif PlatformName == 'macos' and file.endswith("natives-osx.jar"):
                # Add legacy natives-osx.jar if available
                jar_files.append(os.path.join(root, file))

    if jar_files:
        for jar_file in jar_files:
            print(f"Found: {jar_file}")

            # Extract files from the JAR to a temporary directory
            temp_dir = os.path.join(".minecraft", "temp_natives")
            os.makedirs(temp_dir, exist_ok=True)

            with zipfile.ZipFile(jar_file, 'r') as jar:
                jar.extractall(temp_dir)  # Extract to the temporary directory

            # Move all files from the subdirectories to the root .minecraft/natives
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    source_file = os.path.join(root, file)
                    target_file = os.path.join(".minecraft/natives", file)
                    shutil.move(source_file, target_file)  # Move the file to the natives directory
                    print(f"Moved: {source_file} to {target_file}")

            # Clean up the temporary directory
            shutil.rmtree(temp_dir)  # Remove the temporary directory and its contents
    else:
        print("LWJGLPatch: No natives found to unzip!")