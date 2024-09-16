"""
1.0~1.16(Java 8)
1.17~1.20(Java 17)
1.21~(Java 21)
"""

import os
import subprocess
import platform
import json
import print_color
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

def find_jvm_path(java_version, path):
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

    elif platform.system() == "Darwin":  # macOS

        try:
            # Run the command to list all Java versions and their paths
            result = subprocess.run(['/usr/libexec/java_home', '-V'], capture_output=True, text=True)

            # Check if the command was successful
            if result.returncode == 0:
                java_versions = result.stdout.splitlines()
                java_paths = []

                # Loop through each line of the output and extract the paths
                for line in java_versions:
                    if '/Library/Java/JavaVirtualMachines/' in line:
                        # Extract the path between quotation marks (or simply find the start)
                        path_start = line.find("/")  # Find the start of the path
                        java_path = line[path_start:].strip()  # Get the cleaned path
                        java_paths.append(java_path)  # Append the cleaned path

                # Add "bin" to each Java path
                java_bins = [os.path.join(java_path, "bin") for java_path in java_paths]

                # Output the found Java paths
                print("Java installation paths:")

                for bin_path in java_bins:
                    print(bin_path)

                # Run java -version to verify Java installation (using the first found bin path)
                if java_bins:
                    java_executable = os.path.join(java_bins[0], "java")  # Get the java executable path
                    os.system(f"{java_executable} -version")  # Check the version
                else:
                    print("No Java installations found.")

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
        Java_VERSION = [1.8, 17, 21]
        for jvm_version in Java_VERSION:
            jvm_version = str(jvm_version)
            find_jvm_path(jvm_version, path)

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

def java_version_check(Main, version):
    """
    Hmm...just a normal check....(Is for LaunchClient!)
    """
    print("LaunchManager: Trying to check this version of Minecraft requirement Java version....", color='green')
    version_tuple = tuple(map(int, version.split(".")))

    with open("Java_HOME.json", "r") as file:
        data = json.load(file)

    if version_tuple > (1, 16):
        if version_tuple >= (1, 20, 6):
            Java_path = data.get("Java_21")
            print(f"{Main}: Using Java 21!", color='blue')
        else:
            Java_path = data.get("Java_17")
            print(f"{Main}: Using Java 17!", color='blue')
    else:
        Java_path = data.get("Java_8")
        print(f"{Main}: Using Java 8!", color='blue')
    print(f"{Main}: Java runtime path is:{Java_path}", color='blue')
    return Java_path


def java_finder():
    system = platform.system()
    if os.path.isfile('Java_HOME.json'):
        print("Found Java path config! Do you want to reconfigure this file? (Yes=1, No=0)")
        user_input = int(input(":"))
        if user_input == 1:
            os.remove('Java_HOME.json')
            java_search()
        else:
            print("Bypass reconfiguration...")
            print("Back to main menu.....")
    else:
        java_search()

                 