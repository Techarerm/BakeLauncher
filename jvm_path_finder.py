"""
1.0~1.16(Java 8)
1.17~1.20(Java 17)
1.21~(Java 21)
"""

import os
import subprocess
import platform
import json

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


def Java_8(path):
    if platform.system() == "Windows":
        for root, dirs, files in os.walk(path):
            if "jre-1.8" in dirs:
                version = "Java_8"
                print("Found Java 8 runtime on this computer :)")
                JVM_8 = os.path.join(path, "jre-1.8", "bin")
                print(f"Java HOME: {JVM_8}")
                os.chdir(JVM_8)
                os.system("java.exe -version")
                print("Saving path to Java_HOME.json...")
                os.chdir(local)
                write_json(JVM_8, version)
                print(" ")
                break
            else:
                print("No Java 8 runtime on this computer")

    elif platform.system() == "Darwin":
        for Java_Folder in os.listdir(path):
            Java_Folder_Name = os.path.join(path, Java_Folder)
            # Find Java 8 and add it to the path
            if os.path.isdir(Java_Folder_Name) and (Java_Folder.startswith("jdk-1.8") or Java_Folder.startswith("jre-1.8")):
                version = "Java_8"
                print("Found Java 8 runtime on this Mac :)")
                JVM_8 = os.path.join(path, Java_Folder, "Contents", "Home", "bin")
                print(f"Java HOME: {JVM_8}")
                os.chdir(JVM_8)
                os.system("java -version")
                print("Saving path to Java_HOME.json...")
                os.chdir(local)
                write_json(JVM_8, version)
                print(" ")
                break
            else:
                print("No Java 17 runtime on this Mac")

    elif platform.system() == "Linux":
        for Java_Folder in os.listdir(path):
            Java_Folder_Name = os.path.join(path, Java_Folder)

            # Find Java 8 and add it to the path
            if os.path.isdir(Java_Folder_Name) and (Java_Folder.startswith("jre-1.8") or Java_Folder.startswith("jdk-1.8") or Java_Folder.startswith("java-1.8")):
                version = "Java_8"
                print("Found Java 8 runtime on this computer :)")
                JVM_21 = os.path.join(path, Java_Folder, "bin")
                print(f"Java HOME: {JVM_8}")
                os.chdir(JVM_8)
                os.system("java -version")
                print("Saving path to Java_HOME.json...")
                os.chdir(local)
                write_json(JVM_8, version)
                print(" ")
                break
            else:
                print("No Java 8 runtime on this computer")
    else:
        print("Unsupported operating system :(")


def Java_17(path):
    if platform.system() == "Windows":
        for root, dirs, files in os.walk(path):
            if "jdk-17" in dirs:
                version = "Java_17"
                print("Found Java 17 runtime on this computer :)")
                JVM_17 = os.path.join(path, "jdk-17", "bin")
                print(f"Java HOME: {JVM_17}")
                os.chdir(JVM_17)
                os.system("java.exe -version")
                print("Saving path to Java_HOME.json...")
                os.chdir(local)
                write_json(JVM_17, version)
                print(" ")
                break
            else:
                print("No Java 17 runtime on this computer")

    elif platform.system() == "Darwin":
        for Java_Folder in os.listdir(path):
            Java_Folder_Name = os.path.join(path, Java_Folder)

            # Find Java 17 and add it to the path
            if os.path.isdir(Java_Folder_Name) and (Java_Folder.startswith("jdk-17") or Java_Folder.startswith("jre-17")):
                version = "Java_17"
                print("Found Java 17 runtime on this Mac :)")
                JVM_17 = os.path.join(path, Java_Folder, "Contents", "Home", "bin")
                print(f"Java HOME: {JVM_17}")
                os.chdir(JVM_17)
                os.system("java -version")
                print("Saving path to Java_HOME.json...")
                os.chdir(local)
                write_json(JVM_17, version)
                print(" ")
                break
            else:
                print("No Java 17 runtime on this Mac")

    elif platform.system() == "Linux":
        for Java_Folder in os.listdir(path):
            Java_Folder_Name = os.path.join(path, Java_Folder)

            # Find Java 17 and add it to the path
            if os.path.isdir(Java_Folder_Name) and (Java_Folder.startswith("jre-17") or Java_Folder.startswith("jdk-17") or Java_Folder.startswith("java-17")):
                version = "Java_17"
                print("Found Java 17 runtime on this computer :)")
                JVM_21 = os.path.join(path, Java_Folder, "bin")
                print(f"Java HOME: {JVM_17}")
                os.chdir(JVM_17)
                os.system("java -version")
                print("Saving path to Java_HOME.json...")
                os.chdir(local)
                write_json(JVM_17, version)
                print(" ")
                break
            else:
                print("No Java 17 runtime on this computer")
    else:
        print("Unsupported operating system :(")


def Java_21(path):
    if platform.system() == "Windows":
        for root, dirs, files in os.walk(path):
            if "jdk-21" in dirs:
                version = "Java_21"
                print("Found Java 21 runtime on this computer :)")
                JVM_21 = os.path.join(path, "jdk-21", "bin")
                print(f"Java HOME: {JVM_21}")
                os.chdir(JVM_21)
                os.system("java.exe -version")
                print("Saving path to Java_HOME.json...")
                os.chdir(local)
                write_json(JVM_21, version)
                print(" ")
                break
            else:
                print("No Java 21 runtime on this computer")

    elif platform.system() == "Darwin":
        for Java_Folder in os.listdir(path):
            Java_Folder_Name = os.path.join(path, Java_Folder)

            # Find Java 21 and add it to the path
            if os.path.isdir(Java_Folder_Name) and (Java_Folder.startswith("jdk-21") or Java_Folder.startswith("jre-21")):
                version = "Java_21"
                print("Found Java 21 runtime on this Mac :)")
                JVM_21 = os.path.join(path, Java_Folder, "Contents", "Home", "bin")
                print(f"Java HOME: {JVM_21}")
                os.chdir(JVM_21)
                os.system("java -version")
                print("Saving path to Java_HOME.json...")
                os.chdir(local)
                write_json(JVM_21, version)
                print(" ")
                break
            else:
                print("No Java 21 runtime on this Mac")

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
        Java_8(path)
        Java_17(path)
        Java_21(path)
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

                 