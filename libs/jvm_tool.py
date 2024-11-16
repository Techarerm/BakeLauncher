"""
1.0~1.16(Java 8)
1.17~1.20(Java 17)
1.21~(Java 21)
"""

import os
import subprocess
import platform
import time
import requests
import json
from libs.download_jvm import get_java_version_info
from LauncherBase import print_custom as print

Work_Dir = os.getcwd()


def write_json(path, JVM_VERSION):
    # Define how data should be written into the JSON file
    try:
        # Read existing data, or create an empty structure
        if os.path.isfile("data/Java_HOME.json"):
            with open("data/Java_HOME.json", "r") as file:
                try:
                    data = json.load(file)
                except json.JSONDecodeError:
                    print("Error: Corrupted JSON file. Recreating it.", color='red')
                    data = {}
        else:
            print("Java_HOME.json not found, creating a new file.", color='yellow')
            data = {}

        # Update or add new JVM version information
        data[JVM_VERSION] = path

        # Write the updated data back to the file
        with open("data/Java_HOME.json", "w") as file:
            json.dump(data, file, indent=4)
            print(f"Successfully saved JVM path for {JVM_VERSION}.", color='green')

    except Exception as e:
        print(f"Error: Failed to write JSON data due to {e}", color='red')


def using_downloaded_jvm():
    local = os.getcwd()
    runtimes_dir = "runtimes"  # Base directory for runtimes
    if os.path.exists(runtimes_dir):
        VERSIONLIST = [8, 16, 17, 18, 19, 20, 21]  # List of supported versions
        for java_version in VERSIONLIST:
            java_dir = os.path.join(runtimes_dir, "Java_" + str(java_version))  # Full path for Java version
            if os.path.exists(java_dir):
                if str(java_version) == "8":
                    RealJVMVersion = "Java_1.8"
                else:
                    RealJVMVersion = None
                print(f"JVMTool: Found downloaded Java {java_version}!", color='blue')
                if platform.system() == "Darwin":
                    jvm_path = os.path.join(local, java_dir, "jre.bundle", "Contents", "Home", "bin")
                    os.system(f"chmod 755 {jvm_path}/*")
                else:
                    jvm_path = os.path.join(local, java_dir, "bin")  # Path to the 'bin' directory

                if os.path.exists(jvm_path):
                    print(f"Java HOME: {jvm_path}")
                    # Write JVM path and version to a config file (or other use)
                    if platform.system() == 'Windows':
                        os.system(jvm_path + "/java.exe -version")
                    else:
                        os.system(jvm_path + "/java -version")
                    print("Saving path to Java_HOME.json...", color='green')
                    # Ensure Java_HOME.json exists or handle its creation
                    if os.path.isfile("data/Java_HOME.json"):
                        try:
                            with open("data/Java_HOME.json", "r") as file:
                                data = json.load(file)
                        except json.JSONDecodeError:
                            print("Error: Java_HOME.json contains invalid JSON, recreating file.", color='red')
                            data = {}

                        JVM_VERSION = RealJVMVersion if RealJVMVersion else "Java_" + str(java_version)

                        if JVM_VERSION in data:
                            print("JVMTool: Found existing JVM path!", color='purple')
                            old_version_path = data[JVM_VERSION]
                            print(f"Old Path: {old_version_path} to New Path: {jvm_path}", color='blue')
                            print("Want to overwrite it? Y/N", color='green')
                            user_input = input(":").upper()
                            if user_input == "Y":
                                print("Overwriting it....", color='green')
                                write_json(jvm_path, JVM_VERSION)
                        else:
                            print(f"JVM version {JVM_VERSION} not found. Saving new version.", color='yellow')
                            write_json(jvm_path, JVM_VERSION)

                    else:
                        print("Error: Java_HOME.json file not found! Creating a new one.", color='yellow')
                        write_json(jvm_path, RealJVMVersion if RealJVMVersion else "Java_" + str(java_version))


def find_jvm_path_windows(java_version, path):
    if platform.system() == "Windows":
        for root, dirs, files in os.walk(path):
            # Check for jdk or jre with the specific java version
            for dir_name in dirs:
                if dir_name.startswith(f'jdk-{java_version}') or dir_name.startswith(f'jre-{java_version}'):
                    version = f"Java_{java_version}"
                    print(f"Found Java {java_version} runtime on this computer!", color='blue')

                    # Get the JVM path
                    JVM_Path = os.path.join(root, dir_name, "bin")
                    print(f"Java HOME: {JVM_Path}")

                    # Check java version
                    os.system(f'"{os.path.join(JVM_Path, "java.exe")}" -version')

                    # Save to JSON file
                    print("Saving path to Java_HOME.json...")
                    write_json(JVM_Path, version)
                    print(" ")
                    return JVM_Path
        print(f"No Java {java_version} runtime found on this computer.", color='yellow')


def find_jvm_path_unix_like(path):
    global java_path
    if platform.system() == "Darwin":  # macOS
        try:
            # Run the command to list all Java versions and their paths
            result = subprocess.run(['/usr/libexec/java_home', '-V'], capture_output=True, text=True)

            # Check if the command was successful
            if result.returncode == 0:
                java_versions = result.stdout.splitlines()
                java_paths = []

                # Loop through each line of the output and extract the paths
                for line in java_versions:
                    # Extract the path from the output line
                    path_start = line.find("/")
                    if path_start != -1:  # Ensure we found a path start
                        java_path = line[path_start:].strip()  # Get the cleaned path
                        java_paths.append(java_path)  # Append the cleaned path

                # Output the found Java paths
                print("Found Java installations:")
                for java_path in java_paths:
                    print(java_path)

                # Add "bin" to each Java path to get the bin directory
                java_bins = [os.path.join(java_path, "bin") for java_path in java_paths]
                os.system(java_path + "/bin/java -version")
                write_json(java_bins, java_versions)
                # Run java -version to verify Java installations for each version
                for bin_path in java_bins:
                    java_executable = os.path.join(bin_path, "java")  # Get the java executable path
                    if os.path.exists(java_executable):  # Check if the executable exists
                        print(f"\nChecking version for: {java_executable}", color='green')
                        result = subprocess.run([java_executable, "-version"], capture_output=True, text=True)
                        print(result.stdout)
                    else:
                        print(f"Java executable not found at: {java_executable}", color='red')

            else:
                print(f"Error running command: {result.stderr}", color='red')
                return []

        except Exception as e:
            print(f"An error occurred: {str(e)}", color='red')
            return []



    elif platform.system() == "Linux":
        for Java_Folder in os.listdir(path):
            Java_Folder_Name = os.path.join(path, Java_Folder)

            # Find Java 21 and add it to the path
            if os.path.isdir(Java_Folder_Name) and (
                    Java_Folder.startswith("jre-21") or Java_Folder.startswith("jdk-21") or Java_Folder.startswith(
                    "java-21")):
                version = "Java_21"
                print("Found Java 21 runtime on this computer!", color='blue')
                JVM_21 = os.path.join(path, Java_Folder, "bin")
                print(f"Java HOME: {JVM_21}")
                os.chdir(JVM_21)
                os.system("java -version")
                print("Saving path to Java_HOME.json...")
                os.chdir(Work_Dir)
                write_json(JVM_21, version)
                print(" ")
                break
            else:
                print("No Java 21 runtime on this computer", color='yellow')
    else:
        print("Unsupported operating system :(", color='red')


def java_search():
    global path
    print("Trying to find JAVA_HOME...")
    CantSetJavaPath = 0
    if platform.system() == "Windows":
        path = r"C:\Program Files\Java"
    elif platform.system() == "Darwin":
        path = r"/Library/Java/JavaVirtualMachines/"
    elif platform.system() == "Linux":
        if os.path.exists("/usr/lib/jvm/"):
            path = r"/usr/lib/jvm/"
        else:
            path = None

    else:
        print("Unsupported Operating System :(", color='red')
        CantSetJavaPath = 1

    if CantSetJavaPath == 0:
        if platform.system() == "Windows":
            Java_VERSION = [1.8, 17, 21]
            for jvm_version in Java_VERSION:
                jvm_version = str(jvm_version)
                find_jvm_path_windows(jvm_version, path)
            using_downloaded_jvm()
        elif platform.system() == "Darwin":
            find_jvm_path_unix_like(path)
            using_downloaded_jvm()
        elif platform.system() == "Linux":
            if not path is None:
                find_jvm_path_unix_like(path)
                using_downloaded_jvm()
            else:
                print("Warning: Your platform is not supported search local JVM!", color='yellow')
                print("Launcher will use recommended JVM instead local JVM when you launch Minecraft!", color='yellow')
                using_downloaded_jvm()
        else:
            print("Warning: Your platform is not supported search local JVM!", color='yellow')
            print(
                "Launcher will use recommended JVM(If launcher failed to download jvm you may get crash when you launch)",
                color='yellow')
            using_downloaded_jvm()

        # Check config file is exist
        if os.path.exists("data/Java_HOME.json"):
            print("Java runtime config successful!!!", color='green')
            print("Press any key to back to the main menu...")
        else:
            print("Failed to configure Java runtime path :(", color='red')
            print("Trying to install JRE or JDK")
            print("Minecraft Java version requirement list:")
            print("1.0~1.16 - Java 8")
            print("Download Link: https://www.java.com/download/manual.jsp")
            print("1.17~1.20 - Java 17")
            print("Download Link: https://www.oracle.com/java/technologies/javase/jdk17-archive-downloads.html")
            print("1.21~1.22 - Java 21")
            print("Download Link: https://www.oracle.com/java/technologies/downloads/#java21")
            print("Back to main menu.....")
    else:
        print("Failed to configure Java runtime path because JVM_Finder are not supported on your system!", color='red')


def java_version_check(Main, version_id):
    """
    Check the Minecraft version requirements for Java version.
    """
    print(f"Trying to check the required Java version for this Minecraft version...", color='green')

    # Get version_manifest_v2.json and list all versions
    url = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"
    response = requests.get(url)
    data = response.json()
    version_list = data['versions']

    # Find the URL for the given version_id
    version_url = None
    for v in version_list:
        if v['id'] == version_id:
            version_url = v['url']
            break

    if version_url is None:
        print(f"{Main}: Invalid version ID", color='red')
        return None

    try:
        # Get version data
        version_response = requests.get(version_url)
        version_data = version_response.json()

        # Extract the Java version information
        component, major_version = get_java_version_info(version_data)
        print(f"Required Java Component: {component}, Major Version: {major_version}", color='green')

    except Exception as e:
        # If it can't get support Java version, using Java 8(some old version will get this error)
        print(f"{Main}: Error occurred while fetching version data: {e}", color='red')
        print(f"Warning: BakeLauncher will using Java 8 instead original support version of Java.", color='yellow')
        major_version = str("8")

    Java_VERSION = "Java_" + str(major_version)
    if Java_VERSION == "Java_8":
        Java_VERSION = "Java_1.8"

    try:
        with open("data/Java_HOME.json", "r") as file:
            data = json.load(file)

        Java_path = data.get(Java_VERSION)
        if Java_path:
            print(f"Using Java {major_version}!", color='blue')
            print(f"Java runtime path is: {Java_path}", color='blue')
            return Java_path
        else:
            print(f"{Main}: Java version {Java_VERSION} not found in Java_HOME.json", color='red')
            return None

    except FileNotFoundError:
        print(f"{Main}: Java_HOME.json file not found", color='red')
        return None
    except json.JSONDecodeError:
        print(f"{Main}: Error decoding JSON from Java_HOME.json", color='red')
        return None


def initialize_jvm_config():
    print("Cleaning JVM config file...")
    if os.path.exists("data/Java_HOME.json"):
        os.remove("data/Java_HOME.json")
        print("JVM config file has been removed", color='green')
        time.sleep(2)
    else:
        print("Failed to remove JVM config file. Cause by config file not found.", color='red')
        time.sleep(2)

def java_finder():
    system = platform.system()
    if os.path.isfile('data/Java_HOME.json'):
        print("Found old jvm path config! Do you want to reconfigure this file? (Yes=1, No=0)", color='purple')
        user_input = int(input(":"))
        if user_input == 1:
            os.remove('data/Java_HOME.json')
            java_search()
        else:
            print("Bypass reconfiguration...", color='green')
            print("Back to main menu.....")
    else:
        java_search()
