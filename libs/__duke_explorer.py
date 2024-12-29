import os
import subprocess
import re
import json
import time
from LauncherBase import Base, print_custom as print
from libs.Utils.utils import get_version_data


class DukeCute:
    def __init__(self):
        self.ExecutableJavaList_CustomPath = None
        self.FoundJavaRuntimeInCustomPath = None
        self.FoundJavaRuntimeList_CustomPath = None
        self.ExecutableJavaList_LauncherInstalled = []
        self.ExecutableJavaList_SysInstalled = []
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

        # Using absolute path
        JavaExecutable = os.path.join(runtimes_dir, self.JavaExecutableName)

        # executable it
        result = subprocess.run([JavaExecutable, '-version'], stderr=subprocess.PIPE, stdout=subprocess.PIPE,
                                text=True)

        # Get output
        output = result.stderr

        # Get major version (e.g., "21.0.3") and full version in the output
        match = re.search(r'java version "(\d+)(?:\.(\d+))?', output)
        java_name = "Java"
        # Is for install by launcher runtimes(Because is openjdk not oracle java....)
        if not match:
            java_name = "OpenJDK"
            match = re.search(r'openjdk version "(\d+)(?:\.(\d+))?', output)

        if match:
            major_version = match.group(1)
            # Special case for Java 8 where we need to use the second part (8) instead of 1
            if major_version == "1" and match.group(2):
                major_version = match.group(2)
            if mode == "GetMajorVersion":
                return major_version
            else:
                print(f"{java_name} Major Version: {major_version}", color='blue')
            return True
        else:
            return False

    def duke_finder(self):
        print("Search available Java runtimes on your computer...")

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

        print("Now search Java runtimes in launcher root dir...")
        self.FoundJavaRuntimeList_LauncherInternal = self.file_search(self.JavaRuntime_LauncherInternal,
                                                                      self.JavaExecutableName)

        # Check if any Java runtime was found in launcher internal
        if len(self.FoundJavaRuntimeList_LauncherInternal) > 0:
            self.FoundJavaRuntimeInLauncherInternal = True
        else:
            print("Could not find available Java runtimes in the launcher 'runtimes' folder :0", color='yellow')

        if Base.SearchJVMInCustomPath:
            print("Now search Java runtimes in custom path...", color='purple')
            self.FoundJavaRuntimeList_CustomPath = self.file_search(Base.CustomJVMInstallPath,
                                                                          self.JavaExecutableName)

            # Check if any Java runtime was found in launcher internal
            if len(self.FoundJavaRuntimeList_CustomPath) > 0:
                self.FoundJavaRuntimeInCustomPath = True
            else:
                print("Could not find available Java runtimes in the launcher 'runtimes' folder :0", color='yellow')

        # Test executable
        print("Testing whether Java runtimes system-installed can execute normally...", color="orange")
        for RuntimeDir in self.FoundJavaRuntimeList:
            print(f"Testing runtime path {RuntimeDir} executable...", color='green')
            Status = self.test_java_executable(RuntimeDir, mode="normal")
            if Status:
                self.ExecutableJavaList_SysInstalled.append(RuntimeDir)
            else:
                print(f"Runtime directory {RuntimeDir} cannot be executed. Is it corrected?", color='yellow')

        if self.ExecutableJavaList_SysInstalled:
            self.FoundDuke = True
        else:
            print("Unable to find the JVM executable installed on the system :(", color='red')
            time.sleep(2)

        if self.FoundDuke:
            print("Saving data...", color='green')
            for RuntimeDir in self.ExecutableJavaList_SysInstalled:
                print(f"Getting runtimes major version...")
                major_version = self.test_java_executable(RuntimeDir, mode="GetMajorVersion")
                print("Saving Java HOME Path...", color='lightgreen')
                self.write_runtimes_data(RuntimeDir, major_version, "System-Installed")
            self.FoundDuke = False

        # Test "installed by the launcher" Java runtimes executable
        print("Testing whether Java runtimes installed by the launcher can execute normally...", color='lightyellow')
        for RuntimeDir in self.FoundJavaRuntimeList_LauncherInternal:
            print(f"Testing runtime path {RuntimeDir} executable...", color='green')
            Status = self.test_java_executable(RuntimeDir, mode="normal")
            if Status:
                self.ExecutableJavaList_LauncherInstalled.append(RuntimeDir)
            else:
                print(f"Runtime directory {RuntimeDir} cannot be executed. Is it corrected?", color='yellow')

        # Check length of the list
        if self.ExecutableJavaList_LauncherInstalled:
            self.FoundDuke = True
        else:
            print("Unable to find executable JVM which installed by launcher:(", color='red')
            time.sleep(2)

        if self.FoundDuke:
            print("Saving data...", color='green')
            for RuntimeDir in self.ExecutableJavaList_LauncherInstalled:
                print(f"Getting runtimes major version...", color='green')
                major_version = self.test_java_executable(RuntimeDir, mode="GetMajorVersion")
                print("Saving Java HOME Path...", color='lightgreen')
                self.write_runtimes_data(RuntimeDir, major_version, "Launcher-Installed")
            self.FoundDuke = False

        if Base.SearchJVMInCustomPath:
            print("Testing custom Java runtimes can execute normally...",color='lightyellow')
            for RuntimeDir in self.FoundJavaRuntimeList_CustomPath:
                print(f"Testing runtime path {RuntimeDir} executable...", color='green')
                Status = self.test_java_executable(RuntimeDir, mode="normal")
                if Status:
                    self.ExecutableJavaList_CustomPath.append(RuntimeDir)
                else:
                    print(f"Runtime directory {RuntimeDir} cannot be executed. Is it corrected?", color='yellow')

            # Check length of the list
            if self.ExecutableJavaList_CustomPath:
                self.FoundDuke = True
            else:
                print("Unable to find executable JVM in the custom JVM installed path :(", color='red')
                time.sleep(2)

            if self.FoundDuke:
                print("Saving data...", color='green')
                for RuntimeDir in self.ExecutableJavaList_CustomPath:
                    print(f"Getting runtimes major version...", color='green')
                    major_version = self.test_java_executable(RuntimeDir, mode="GetMajorVersion")
                    print("Saving Java HOME Path...", color='lightgreen')
                    self.write_runtimes_data(RuntimeDir, major_version, "Launcher-Installed")
        print("Search Java Runtimes process finished.", color='blue')
        time.sleep(3)

    def write_runtimes_data(self, java_bin_dir, runtime_version, mode):
        """
        Writes runtime data to config file.
        java_bin_dir : The path of the JVM binary directory.
        runtime_version : Runtime version.
        mode : Runtime mode. (System-Installed or Launcher-Installed)
        """
        global system_runtimes_path_data, launcher_runtimes_path_data

        system_runtimes_path_data = {
            "JVMPathType": "System-Installed"
        }

        launcher_runtimes_path_data = {
            "JVMPathType": "Launcher-Installed"
        }

        # Ensure the config file exists or initialize it
        if not os.path.exists(Base.jvm_setting_path):
            self.initialize_jvm_config()

        # Read the jvm_setting data
        try:
            with open(Base.jvm_setting_path, "r") as file:
                jvm_setting_data = json.load(file)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Failed to read the JVM settings file :( Cause by error {e}", color='red')
            print("Resting the JVM settings file...", color='green')
            self.initialize_jvm_config()
            with open(Base.jvm_setting_path, "r") as file:
                jvm_setting_data = json.load(file)

        # Prepare variables for existing data
        exist_system_runtimes_path_data = None
        exist_launcher_runtimes_path_data = None

        # Get exist data (If it can't find same value write new data)
        for entry in jvm_setting_data:
            if entry.get("JVMPathType") == "System-Installed":
                exist_system_runtimes_path_data = entry
            elif entry.get("JVMPathType") == "Launcher-Installed":
                exist_launcher_runtimes_path_data = entry

        # New data
        new_path = {runtime_version: java_bin_dir}

        if mode == "System-Installed":
            if exist_system_runtimes_path_data:
                # Overwrite or add new runtime version
                exist_system_runtimes_path_data.update(new_path)
            else:
                system_runtimes_path_data.update(new_path)
                jvm_setting_data.append(system_runtimes_path_data)
        else:
            if exist_launcher_runtimes_path_data:
                # Overwrite or add new runtime version
                exist_launcher_runtimes_path_data.update(new_path)
            else:
                launcher_runtimes_path_data.update(new_path)
                jvm_setting_data.append(launcher_runtimes_path_data)

        # Write updated configuration back to the file
        try:
            with open(Base.jvm_setting_path, "w") as file:
                json.dump(jvm_setting_data, file, indent=4)
            return True
        except Exception as e:
            print(f"Failed to write the JVM settings file. Error: {e}")
            return False

    @staticmethod
    def get_java_path_from_jvm_data(runtime_version, mode):
        if os.path.exists(Base.jvm_setting_path):
            with open(Base.jvm_setting_path, 'r') as f:
                try:
                    json_data = json.load(f)
                    # Loop through the data and find the matching ID
                    for entry in json_data:
                        if entry['JVMPathType'] == str(mode):
                            # Return the matching entry as part of a tuple
                            return True, entry.get(str(runtime_version), None)
                    # If no match is found
                    return False, None
                except json.JSONDecodeError:
                    return False, None
        else:
            return False, "JVMSettingDoesNotExist"

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
            if Base.PrioUseSystemInstalledJVM:
                Status, JVMPath = self.get_java_path_from_jvm_data(major_version, "System-Installed")
            else:
                Status, JVMPath = self.get_java_path_from_jvm_data(major_version, "Launcher-Installed")

            if not Status:
                print(f"Java version {major_version} not found in Java_HOME.json", color='red')
                return None
            else:
                print(f"Get Java Path successfully! | Using Java {major_version}!", color='blue')
                return JVMPath

        except Exception as e:
            if Exception is FileNotFoundError:
                print(f"Java_HOME.json file not found", color='red')
            elif Exception is json.JSONDecodeError:
                print(f"Error decoding JSON from Java_HOME.json", color='red')
            else:
                print("Failed to get Java runtimes path when reading setting :(", color='red')
                print(f"Error Message : {e}")
            time.sleep(2)
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
        if os.path.exists(Base.jvm_setting_path):
            try:
                os.remove(Base.jvm_setting_path)
            except PermissionError:
                return False

        with open(Base.jvm_setting_path, "w") as file:
            json.dump([], file, indent=4)
        print("JVM config file has been reset.", color='blue')
        time.sleep(2)


Duke = DukeCute()
