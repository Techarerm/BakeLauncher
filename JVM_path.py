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
    for root, dirs, files in os.walk(path):
        if "jre-1.8" in dirs:
            version = "Java_8"
            print("Found Java 8 runtime on this computer :)")
            JVM_8 = os.path.join(path, "jre-1.8", "bin")
            print(os.path.join(JVM_8, "java.exe"))
            os.chdir(JVM_8)
            os.system("java.exe -version")
            print("Saving path to Java_HOME.json")
            os.chdir(local)
            write_json(JVM_8, version)
            print(" ")
            break
    else:
        print("No Java 8 runtime on this computer")

def Java_17(path):
    for root, dirs, files in os.walk(path):
        if "jdk-17" in dirs:
            version = "Java_17"
            print("Found Java 17 runtime on this computer :)")
            JVM_17 = os.path.join(path, "jdk-17", "bin")
            print(os.path.join(JVM_17, "java.exe"))
            os.chdir(JVM_17)
            os.system("java.exe -version")
            print("Saving path to Java_HOME.json")
            os.chdir(local)
            write_json(JVM_17, version)
            print(" ")
            break
    else:
        print("No Java 17 runtime on this computer")

def Java_21(path):
    for root, dirs, files in os.walk(path):
        if "jdk-21" in dirs:
            version = "Java_21"
            print("Found Java 21 runtime on this computer :)")
            JVM_21 = os.path.join(path, "jdk-21", "bin")
            print(os.path.join(JVM_21, "java.exe"))
            os.chdir(JVM_21)
            os.system("java.exe -version")
            print("Saving path to Java_HOME.json")
            os.chdir(local)
            write_json(JVM_21, version)
            print(" ")
            break
    else:
        print("Can't find any Java runtime on this computer :(")

def java_search():
    print("System type: Windows")
    print("Trying to find JAVA_HOME...")
    os.chdir(r"C:\Program Files\Java")
    path = r"C:\Program Files\Java"
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
        print("Press any key to back to the main menu...")

def java_tool():
    system = platform.system()
    if system == 'Windows':
        if os.path.isfile('Java_HOME.json'):
            print("Found Java path config! Do you want to reconfigure this file? (Yes=1, No=0)")
            user_input = int(input(":"))
            if user_input == 1:
                os.remove('Java_HOME.json')
                java_search()
            else:
                print("Bypass reconfiguration...")
                print("Press any key to back to the main menu...")
        else:
            java_search()
    else:
        print("Sorry :( I didn't add support for other systems... (It will be supported in the next update)")


                 