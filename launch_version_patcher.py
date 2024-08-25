import os
import shutil
import print_color
from print_color import print

def generate_jar_paths(version_id):
    libraries_dir = os.path.join("versions", version_id, "libraries")
    jar_paths_string = ""

    # Traverse the libraries directory
    for root, dirs, files in os.walk(libraries_dir):
        for file in files:
            if file.endswith('.jar'):
                # Construct the path with \libraries prefix
                relative_path = os.path.relpath(os.path.join(root, file), start=libraries_dir)
                full_path = os.path.join("libraries", relative_path)  # Add \libraries to the path
                # Append the path to the jar_paths_string with a semicolon
                jar_paths_string += full_path + ";"

    # Append just client.jar to the jar paths
    jar_paths_string += "client.jar"

    return jar_paths_string

def patcher_main(version):
    local = os.getcwd()
    print(local)
    Version_list = os.listdir('versions')
    print("LaunchPatcher: Now fixing version " + version + " of Minecraft...", color="green")
    jar_paths = generate_jar_paths(version)
    os.chdir(r'versions\\' + version)
    # Save the jar paths to a file or print them
    print(f"LaunchPatcher: Generated .jar paths for version {version}:", color="green")
    print(jar_paths)
    # Write to libraries_path.cfg file
    with open('libraries_path.cfg', 'w') as f:
        f.write(jar_paths)
    os.chdir(local)

"""
Note: This is old version of patcher_main :)
def patcher_main():
    local = os.getcwd()
    print(local)
    Version_list = os.listdir('versions')
    print(Version_list)
    print("Which one do you want to fix version? :)")
    version_id = str(input(":"))
    print("Now fixing version " + version_id + " of Minecraft...")
    jar_paths = generate_jar_paths(version_id)
    os.chdir(r'versions\\' + version_id)
    # Save the jar paths to a file or print them
    print(f"Generated .jar paths for version {version_id}:")
    print(jar_paths)
    # Write to libraries_path.cfg file
    with open('libraries_path.cfg', 'w') as f:
        f.write(jar_paths)
    os.chdir(local)
"""