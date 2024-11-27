import os
import subprocess
import re
import json
from LauncherBase import Base, print_custom as print


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
            print("Could not find available Java runtimes in the launcher 'runtimes' folder :(", color='red')

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


Duke = DukeCute()
