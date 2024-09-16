"""
1.0~1.16(Java 8)
1.17~1.20(Java 17)
1.21~(Java 21)
"""

import os
import subprocess
import platform
import requests
import json
import print_color
import download_jvm
from download_jvm import get_java_version_info
from print_color import print

local = os.getcwd()

def write_json(path, version):
    # Load existing data if the file exists
    if os.path.exists("Java_HOME.json"):
        with open("Java_HOME.json", "r") as jsonFile:
            data = json.load(jsonFile)
    else:
        data = {}

    # Update the data with the new path
    data[version] = path

    # Write the updated data back to the file
    with open("Java_HOME.json", "w") as jsonFile:
        json.dump(data, jsonFile, indent=4)


def using_downloaded_jvm():
    print("BreakPoint!")
    runtimes_dir = "runtimes"  # Base directory for runtimes
    if os.path.exists(runtimes_dir):
        VERSIONLIST = [8, 16, 17, 18, 19, 20, 21]  # List of supported versions
        for java_version in VERSIONLIST:
            java_dir = os.path.join(runtimes_dir, "Java_" + str(java_version))  # Full path for Java version
            if os.path.exists(java_dir):
                print(f"JVMTool: Found Java {java_version}!")
                jvm_path = os.path.join(java_dir, "bin")  # Path to the 'bin' directory
                if os.path.exists(jvm_path):
                    print(f"Java HOME: {jvm_path}")
                    # Write JVM path and version to a config file (or other use)
                    write_json(jvm_path, "Java_" + str(java_version))
                else:
                    print(f"Error: 'bin' directory not found for Java {java_version}")
    else:
        print("Error: 'runtimes' directory not found!")



def find_jvm_path_windows(java_version, path):
    if platform.system() == "Windows":
        for root, dirs, files in os.walk(path):
            # Check for jdk or jre with the specific java version
            for dir_name in dirs:
                if dir_name.startswith(f'jdk-{java_version}') or dir_name.startswith(f'jre-{java_version}'):
                    version = f"Java_{java_version}"
                    print(f"Found Java {java_version} runtime on this computer :)")

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
        print(f"No Java {java_version} runtime found on this computer.")

def find_jvm_path_unix_like():
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
                write_json(java_bins, java_versions)
                # Run java -version to verify Java installations for each version
                for bin_path in java_bins:
                    java_executable = os.path.join(bin_path, "java")  # Get the java executable path
                    if os.path.exists(java_executable):  # Check if the executable exists
                        print(f"\nChecking version for: {java_executable}")
                        result = subprocess.run([java_executable, "-version"], capture_output=True, text=True)
                        print(result.stdout)
                    else:
                        print(f"Java executable not found at: {java_executable}")

            else:
                print(f"Error running command: {result.stderr}")
                return []

        except Exception as e:
            print(f"An error occurred: {str(e)}")
            return []



    elif platform.system() == "Linux":
        for Java_Folder in os.listdir(path):
            Java_Folder_Name = os.path.join(path, Java_Folder)

            # Find Java 21 and add it to the path
            if os.path.isdir(Java_Folder_Name) and (Java_Folder.startswith("jre-21") or Java_Folder.startswith("jdk-21") or Java_Folder.startswith("java-21")):
                version = "Java_21"
                print("Found Java 21 runtime on this computer :)")
                JVM_21 = os.path.join(path, Java_Folder, "bin")
                print(f"Java HOME: {JVM_21}")
                os.chdir(JVM_21)
                os.system("java -version")
                print("Saving path to Java_HOME.json...")
                os.chdir(local)
                write_json(JVM_21, version)
                print(" ")
                break
            else:
                print("No Java 21 runtime on this computer")
    else:
        print("Unsupported operating system :(")




def java_search():
    print("Trying to find JAVA_HOME...")
    CantSetJavaPath = 0
    if platform.system() == "Windows":
        path = r"C:\Program Files\Java"
    elif platform.system() == "Darwin":
        path =r"/Library/Java/JavaVirtualMachines/"
    elif platform.system() == "Linux":
        path =r"/usr/lib/jvm/"
    else:
        print("Unsupported Operating System :(")
        CantSetJavaPath = 1

    if CantSetJavaPath == 0:
        if platform.system() == "Windows":
            Java_VERSION = [1.8, 17, 21]
            for jvm_version in Java_VERSION:
                jvm_version = str(jvm_version)
                find_jvm_path_windows(jvm_version, path)
        else:
            find_jvm_path_unix_like()

        if os.path.exists("Java_HOME.json"):
                print("Java runtime config successful!!!")
                print("Press any key to back to the main menu...")
        else:
                print("Failed to configure Java runtime path :(")
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
        print("Failed to configure Java runtime path because JVM_Finder are not supported on your system!")

def java_version_check(Main, version_id):
    """
    Check the Minecraft version requirements for Java version.
    """
    print(f"{Main}: Trying to check the required Java version for this Minecraft version...", color='green')

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
        print(f"{Main}: Required Java Component: {component}, Major Version: {major_version}", color='green')

    except Exception as e:
        print(f"{Main}: Error occurred while fetching version data: {e}", color='red')
        return None

    Java_VERSION = "Java_" + str(major_version)

    try:
        with open("Java_HOME.json", "r") as file:
            data = json.load(file)

        Java_path = data.get(Java_VERSION)
        if Java_path:
            print(f"{Main}: Using Java {major_version}!", color='blue')
            print(f"{Main}: Java runtime path is: {Java_path}", color='blue')
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


def java_finder():
    system = platform.system()
    if os.path.isfile('Java_HOME.json'):
        print("Found Java path config! Do you want to reconfigure this file? (Yes=1, No=0)")
        user_input = int(input(":"))
        if user_input == 1:
            os.remove('Java_HOME.json')
            java_search()
            using_downloaded_jvm()
        else:
            print("Bypass reconfiguration...")
            print("Back to main menu.....")
    else:
        java_search()

                 