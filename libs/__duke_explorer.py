import os
import subprocess
import re
import json
import time
from LauncherBase import Base, print_custom as print
from libs.Utils.utils import get_version_data


class DukeCute:
    def __init__(self):
        self.ExecutableJavaList = []
        self.JavaRuntimeList = None
        self.JavaHomeDataPath = os.path.join(Base.launcher_root_dir, "data", "Java_HOME.json")
        self.JavaRuntime_Windows = ["C:\\Program Files\\Java"]
        self.JavaRuntime_macOS = ["/Library/Java/JavaVirtualMachines/"]
        self.JavaRuntime_Linux = ["/opt/java/", "/usr/lib/jvm/", "/usr/local/java/"]
        self.JavaRuntime_LauncherInternal = os.path.join(Base.launcher_root_dir, "runtimes")
        self.FoundJavaRuntimeList = []
        self.FoundJavaRuntimeList_LauncherInternal = []
        self.FoundJavaRuntimeInSystem = False
        self.FoundJavaRuntimeInLauncherInternal = False
        self.JavaExecutableName = None
        self.FoundDuke = False
        if Base.Platform == "Windows":
            self.JavaExecutableName = "java.exe"
        else:
            self.JavaExecutableName = "java"

    def file_search(self, java_runtime_dir, file_name):
        FindFileList = []
        for root, dirs, files in os.walk(java_runtime_dir):
            if self.JavaExecutableName in files:
                print(f'Found file name "{file_name}" in the dir {root}', color='blue')
                FindFileList.append(root)
        return FindFileList

    def test_java_executable(self, runtimes_dir, mode):
        # test java runtimes are executable
        os.chdir(runtimes_dir)

        # executable it
        result = subprocess.run([self.JavaExecutableName, '-version'], stderr=subprocess.PIPE, stdout=subprocess.PIPE,
                                text=True)

        # Get output
        output = result.stderr

        # Get major version (e.g., "21.0.3") and full version in the output
        match = re.search(r'java version "(\d+)(?:\.(\d+))?', output)
        os.chdir(Base.launcher_root_dir)
        if match:
            major_version = match.group(1)
            # Special case for Java 8 where we need to use the second part (8) instead of 1
            if major_version == "1" and match.group(2):
                major_version = match.group(2)
            if mode == "GetMajorVersion":
                return major_version
            else:
                print(f"Major Version: {major_version}", color='blue')
            return True
        else:
            return False

    def duke_finder(self):
        print("Search available Java runtimes on your computer...", color='green')

        # Set platform-specific directories
        if Base.Platform == "Windows":
            self.JavaRuntimeList = self.JavaRuntime_Windows
        elif Base.Platform == "Darwin":
            self.JavaRuntimeList = self.JavaRuntime_macOS
        elif Base.Platform == "Linux":
            self.JavaRuntimeList = self.JavaRuntime_Linux
        else:
            self.JavaRuntimeList = None

        if self.JavaRuntimeList:
            for workDir in self.JavaRuntimeList:
                self.FoundJavaRuntimeList = self.file_search(workDir, self.JavaExecutableName)
        else:
            print("Sorry :( Your platform seems like not supported search runtimes on your system", color='red')

        # Check if any Java runtime was found in the system
        if len(self.FoundJavaRuntimeList) > 0:
            self.FoundJavaRuntimeInSystem = True
        else:
            print("Could not find available Java runtimes on your computer.", color='yellow')

        print("Now search Java runtimes in launcher root dir...", color='green')
        self.FoundJavaRuntimeList_LauncherInternal = self.file_search(self.JavaRuntime_LauncherInternal,
                                                                      self.JavaExecutableName)

        # Check if any Java runtime was found in launcher internal
        if len(self.FoundJavaRuntimeList_LauncherInternal) > 0:
            self.FoundJavaRuntimeInLauncherInternal = True
        else:
            print("Could not find available Java runtimes in the launcher 'runtimes' folder :0", color='yellow')

        # test executable
        print("Testing Java runtimes executable...", color='green')
        for RuntimeDir in self.FoundJavaRuntimeList:
            Status = self.test_java_executable(RuntimeDir, mode="normal")
            if Status:
                self.ExecutableJavaList.append(RuntimeDir)
            else:
                print(f"Runtime directory {RuntimeDir} cannot be executed. Is it corrected?", color='yellow')

        if len(self.ExecutableJavaList) > 0:
            self.FoundDuke = True
        else:
            print("Could not find any Java runtimes in the launcher 'runtimes' folder :(", color='red')

        if self.FoundDuke:
            for RuntimeDir in self.ExecutableJavaList:
                major_version = self.test_java_executable(RuntimeDir, mode="GetMajorVersion")
                self.write_runtimes_data(RuntimeDir, major_version)
        print("Search Java Runtimes process finished.", color='blue')
        time.sleep(3)

    def write_runtimes_data(self, java_bin_dir, runtime_version):
        try:
            # Read existing data, or create an empty structure
            if os.path.isfile(self.JavaHomeDataPath):
                with open(self.JavaHomeDataPath, "r") as file:
                    try:
                        data = json.load(file)
                    except json.JSONDecodeError:
                        print("Error: Corrupted JSON file. Recreating it.", color='red')
                        data = {}
            else:
                print("Java_HOME.json not found, creating a new file.", color='yellow')
                data = {}

            # Update or add new JVM version information
            data[runtime_version] = java_bin_dir

            # Write the updated data back to the file
            with open(self.JavaHomeDataPath, "w") as file:
                json.dump(data, file, indent=4)
                print(f"Successfully saved JVM path for {java_bin_dir}.", color='green')

        except Exception as e:
            print(f"Error: Failed to write JSON data due to {e}", color='red')

    def java_version_check(self, version_id, **kwargs):
        """
        Check the Minecraft version requirements for Java version.
        """

        JAVA8 = kwargs.get("JAVA8", False)
        java_version = kwargs.get("java_version", None)
        print(f"Checking the required Java version for this Minecraft version...", color='green')

        if not JAVA8:
            if java_version is not None:
                major_version = java_version
            else:
                try:
                    # Get version data
                    version_data = get_version_data(version_id)

                    # Extract the Java version information
                    component, major_version = self.get_java_version_info(version_data)
                    if not major_version is None:
                        print(f"Required Java Component: {component}, Major Version: {major_version}", color='green')
                    else:
                        print("Could not found required java component. Using Java 8 without getting it in the version "
                              "data.", color='yellow')
                        major_version = "8"
                except Exception as e:
                    # If it can't get support Java version, using Java 8(some old version will get this error)
                    print(f"Error occurred while fetching version data: {e}", color='red')
                    print(f"Warning: BakeLauncher will using Java 8 instead original support version of Java.",
                          color='yellow')
                    major_version = str("8")
        else:
            major_version = str("8")

        try:
            with open("data/Java_HOME.json", "r") as file:
                data = json.load(file)

            Java_path = data.get(str(major_version))
            if Java_path:
                print(f"Get Java Path successfully! | Using Java {major_version}!", color='blue')
                return Java_path
            else:
                legacy_name = f"Java_{major_version}"
                Java_path = data.get(str(legacy_name))
                if Java_path:
                    print(f"Java version {major_version} not found in Java_HOME.json", color='red')
                    return None
                else:
                    return Java_path

        except FileNotFoundError:
            print(f"Java_HOME.json file not found", color='red')
            return None
        except json.JSONDecodeError:
            print(f"Error decoding JSON from Java_HOME.json", color='red')
            return None

    def get_java_version_info(self, version_data):
        global major_version
        try:
            java_version_info = version_data['javaVersion']
            component = java_version_info['component']
            major_version = java_version_info['majorVersion']
            return component, major_version
        except KeyError:
            return None, "8"

    @staticmethod
    def initialize_jvm_config():
        print("Cleaning JVM config file...")
        if os.path.exists("data/Java_HOME.json"):
            os.remove("data/Java_HOME.json")
            print("JVM config file has been removed.", color='blue')
            time.sleep(2)
        else:
            print("Failed to remove JVM config file. Cause by config file not found.", color='red')
            time.sleep(2)


Duke = DukeCute()
