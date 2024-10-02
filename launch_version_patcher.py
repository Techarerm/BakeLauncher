import os
import shutil
import print_color
import __function__
from __function__ import GetPlatformName
from print_color import print

def generate_jar_paths(version_id):
    print("LaunchPatcher: Generating dependent libraries path for " + version_id + " of Minecraft...", color="green")
    libraries_dir = os.path.join("instances", version_id, "libraries")
    jar_paths_string = ""
    PlatformName = GetPlatformName.check_platform_valid_and_return()
    # Traverse the libraries directory
    for root, dirs, files in os.walk(libraries_dir):
        for file in files:
            if file.endswith('.jar'):
                # Construct the path with /libraries prefix
                relative_path = os.path.relpath(os.path.join(root, file), start=libraries_dir)
                full_path = os.path.join("libraries", relative_path)  # Add \libraries to the path
                # Append the path to the jar_paths_string with a semicolon
                if PlatformName == "Windows":
                    jar_paths_string += full_path + ";"
                else:
                    jar_paths_string += full_path + ":"

    # Append just client.jar to the jar paths
    jar_paths_string += "client.jar"

    return jar_paths_string

def patcher_main(version):
    local = os.getcwd()
    Version_list = os.listdir('instances')
    print("LaunchPatcher: Generating dependent libraries path for " + version + " of Minecraft...", color="green")
    jar_paths = generate_jar_paths(version)
    os.chdir(r'instances/' + version)
    # Save the jar paths to a file or print them
    print(f"LaunchPatcher: Generated .jar paths for version {version}", color="green")
    # Write to libraries_path.cfg file
    with open('libraries_path.cfg', 'w') as f:
        f.write(jar_paths)
    os.chdir(local)