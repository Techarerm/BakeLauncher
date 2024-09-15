import zipfile
import os
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

            # Extract files from the JAR to the .minecraft/natives directory
            with zipfile.ZipFile(jar_file, 'r') as jar:
                for member in jar.namelist():
                    if not member.endswith('/'):  # Ensure not to unzip directories
                        # Get just the file name
                        file_name = os.path.basename(member)

                        # Only extract files that end with .dylib or other specific extensions
                        if file_name.endswith('.dylib'):
                            target_path = os.path.join(".minecraft/natives", file_name)
                            jar.extract(member, ".minecraft/natives")  # Extract to the target directory
                            print(f"Extracted: {member} to {target_path}")

    else:
        print("LWJGLPatch: No natives found to unzip!")
