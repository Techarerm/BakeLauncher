import json
import os
import shutil
import subprocess
import requests
import xml.etree.ElementTree as ET
import time
from LauncherBase import Base, print_custom as print
from libs.__instance_manager import instance_manager
from libs.__duke_explorer import Duke
from libs.Utils.utils import download_file, multi_thread_download, extract_zip


class ModInstaller:
    def __init__(self):
        self.loader_version = "None"
        self.client_version = "None"
        self.libraries_path = "None"
        self.ForgeMetadataURL = "https://maven.minecraftforge.net/net/minecraftforge/forge/maven-metadata.xml"

    def download_fabric_loader(self, libraries_path, loader_version):
        print("Downloading fabric loader...", color='yellow')
        fabric_loader_dest = os.path.join(libraries_path, "net", "fabricmc", "fabric-loader",
                                          f"fabric_loader_{loader_version}.jar")
        FabricLoaderURL = (f"https://maven.fabricmc.net/net/fabricmc/fabric-loader/{loader_version}/fabric"
                           f"-loader-{loader_version}.jar")
        fabric_loader_url = FabricLoaderURL.format(loader_version=loader_version)
        download_file(fabric_loader_url, fabric_loader_dest)

    def download_fabric_libraries(self, libraries, libraries_path, client_version):
        if not os.path.exists(libraries_path):
            os.makedirs(libraries_path)

        download_queue = []

        for lib in libraries:
            group_id, artifact_id, version = lib["name"].split(":")

            # Create directory structure (use '/' for URL paths)
            group_path = group_id.replace(".", "/")  # Convert groupId to folder structure using "/"
            library_path = os.path.join(libraries_path, group_path, artifact_id, version)

            # Ensure the target folder exists
            os.makedirs(library_path, exist_ok=True)

            # Construct the download URL using the corrected path
            url = f"https://maven.fabricmc.net/{group_path}/{artifact_id}/{version}/{artifact_id}-{version}.jar"

            # Full path where the JAR will be saved
            destination = os.path.join(library_path, f"{artifact_id}-{version}.jar")

            # Download the library
            fabric_lib_url_and_dest = [
                (url, destination)
            ]
            download_queue.append(fabric_lib_url_and_dest)
        print(download_queue)
        multi_thread_download(download_queue, "Fabric Libraries")

        print("Downloading intermediary...", color='green')
        intermediary_url = (f"https://maven.fabricmc.net/net/fabricmc/intermediary/"
                            f"{client_version}/intermediary-{client_version}.jar")
        intermediary_dest = os.path.join(libraries_path, "net", "fabric", "intermediary", client_version,
                                         f"intermediary-{client_version}.jar")
        download_file(intermediary_url, intermediary_dest)

    def download_forge_libraries(self, version_data_path, libraries_path):
        forge_maven_url = "https://files.minecraftforge.net/maven/"
        download_queue = []

        with open(version_data_path, "r") as file:
            data = json.load(file)

            for library in data["libraries"]:
                # Extract the 'name' key which is in the format 'group:artifact:version'
                library_name = library["name"]

                # Split the 'name' into group_id, artifact_id, and version
                group_id, artifact_id, version = library_name.split(":")

                # Construct the file path
                path = f"{group_id.replace('.', '/')}/{artifact_id}/{version}/{artifact_id}-{version}.jar"
                url = forge_maven_url + path

                destination = os.path.join(libraries_path, path)

                # Ensure the directories exist before downloading
                os.makedirs(os.path.dirname(destination), exist_ok=True)

                forge_lib_url_and_dest = [
                    (url, destination)
                ]
                download_queue.append(forge_lib_url_and_dest)
        print(forge_lib_url_and_dest)
        multi_thread_download(download_queue, "Forge Libraries")

    def install_fabric_loader(self, instance_path):
        def get_support_fabric_loader_list(client_version):
            url = f"https://meta.fabricmc.net/v2/versions/loader/{client_version}"

            # Get the list of all loader versions
            response = requests.get(url)
            if response.status_code != 200:
                print(f"Failed to retrieve data: {response.status_code}")
                return

            loader_data = response.json()

            # Collect the available Fabric loader versions
            loader_versions = [
                loader["loader"]["version"]
                for loader in loader_data
                if loader["loader"]["stable"]  # Only include stable versions(Add this rule to except user install
                # unsupported version)
            ]

            if not loader_versions:
                print(f"No stable loader versions available for Minecraft version {client_version} :(", color='red')
                return None

            return loader_versions

        # Setting some variable
        instance_libraries = os.path.join(instance_path, ".minecraft", "libraries")
        os.chdir(instance_path)

        if not os.path.exists(instance_libraries):
            print("Libraries are not found. Trying to move it...", color='yellow')
            try:
                shutil.move("libraries", ".minecraft")
            except Exception as e:
                print(f"Failed to move libraries to .minecraft folder. Cause by error {e}", color='red')

        instance_info = os.path.join(instance_path, "instance.bakelh.ini")
        Status, client_version = instance_manager.get_instance_info(instance_info, info_name="client_version")
        game_dir = os.path.join(instance_path, ".minecraft")
        if not os.path.exists(game_dir):
            os.makedirs(game_dir)

        if not Status:
            print("Failed to get instance client version.", color='red')
            return

        # Start install process
        loader_versions = get_support_fabric_loader_list(client_version)
        loader_version = self.select_loader_version("Fabric Loader", loader_versions, client_version)

        url = f"https://meta.fabricmc.net/v2/versions/loader/{client_version}/{loader_version}"
        response = requests.get(url)
        fabric_data = response.json()

        if "launcherMeta" not in fabric_data:
            print("Failed to download fabric loader :( Cause by fetch data are not valid.", color='red')
            return

        libraries_data = fabric_data["launcherMeta"]["libraries"]["common"]
        print("Downloading Fabric loader...", color='green')
        self.download_fabric_loader(instance_libraries, loader_version)
        self.download_fabric_libraries(libraries_data, instance_libraries, client_version)

        print("Confining Fabric setting...", color='green')
        instance_cfg = os.path.join(instance_path, "instance.bakelh.cfg")
        instance_manager.create_custom_config(instance_cfg)

        instance_manager.write_custom_config(instance_cfg, "modloderclass"
                                             , "net.fabricmc.loader.impl.launch.knot.KnotClient")

        print("Install Fabric loader successfully!", color='blue')

    def install_forge_loader(self, instance_path):
        def fetch_support_forge_versions(client_version):
            print("Fetching Forge metadata...", color='lightgreen')

            # Fetch metadata(xml)
            response = requests.get(self.ForgeMetadataURL)
            if response.status_code != 200:
                print(f"Failed to fetch Forge metadata. Status code: {response.status_code}", color='red')
                return []
            root = ET.fromstring(response.content)
            versions = root.find("./versioning/versions")
            all_versions = [version.text for version in versions.findall("version")]

            if client_version:
                filtered_versions = [
                    v for v in all_versions if v.startswith(client_version)
                ]
                return filtered_versions
            return None

        # Setting some variable
        instance_libraries = os.path.join(instance_path, ".minecraft", "libraries")
        os.chdir(instance_path)

        if not os.path.exists(instance_libraries):
            print("Libraries are not found. Trying to move it...", color='yellow')
            try:
                shutil.move("libraries", ".minecraft")
            except Exception as e:
                print(f"Failed to move libraries to .minecraft folder. Cause by error {e}", color='red')
        os.chdir(Base.launcher_root_dir)
        instance_info = os.path.join(instance_path, "instance.bakelh.ini")
        Status, client_version = instance_manager.get_instance_info(instance_info, info_name="client_version")
        game_dir = os.path.join(instance_path, ".minecraft")
        if not os.path.exists(game_dir):
            os.makedirs(game_dir)

        if not Status:
            print("Failed to get instance client version.", color='red')
            return False

        # Fetch support forge version
        forge_versions = fetch_support_forge_versions(client_version)
        if len(forge_versions) == 0:
            print(f"Can't Minecraft version {client_version} support Forge version :(", color='red')
            time.sleep(3)
            return False
        loader_version = self.select_loader_version("Forge", forge_versions, client_version)

        print("Downloading forge installer...", color='green')
        ForgeInstallerURL = (f"https://maven.minecraftforge.net/net/minecraftforge/forge/"
                             f"{loader_version}/forge-{loader_version}-installer.jar")
        ForgeInstallerURL = ForgeInstallerURL.format(loader_version)
        ForgeInstallerDest = os.path.join(Base.launcher_tmp_dir, "forge-installer.jar")
        if os.path.exists(ForgeInstallerDest):
            os.remove(ForgeInstallerDest)
        download_file(ForgeInstallerURL, ForgeInstallerDest)
        if os.path.exists(ForgeInstallerDest):
            print("Downloaded forge installer successfully!", color='green')
        else:
            print("Failed to download forge installer :(", color='red')
            return False

        print("Preparing to install Forge...", color='green')
        print("Searching exist java config...", color='green')
        JavaPath = Duke.java_version_check("", JAVA8=True)
        print("Checking installer type...", color='cyan')
        ExecutableName = "java.exe" if Base.Platform == "Windows" else "java"
        JavaExecutable = os.path.join(JavaPath, ExecutableName)
        try:
            result = subprocess.run(
                [JavaExecutable, "-jar", ForgeInstallerDest, "-help"], stderr=subprocess.PIPE, stdout=subprocess.PIPE,
                text=True)
            output = result.stderr
            SupportInCLI = any("installClient" in line for line in output.splitlines())

            if SupportInCLI:
                print("Install forge installer using modern method...", color='green')
                subprocess.run(
                    [JavaExecutable, "-jar", ForgeInstallerDest, "--installClient", "--installDir", game_dir],
                    check=True
                )
            else:
                print("Install forge installer using legacy method...", color='green')
                subprocess.run([JavaExecutable, "-jar", ForgeInstallerDest, "--extract"])
                ForgeInstallerUniversal = os.path.join(Base.launcher_tmp_dir, f"forge-{loader_version}-universal.jar")
                if os.path.exists(f"{Base.launcher_tmp_dir}/UniversalTmp"):
                    shutil.rmtree(f"{Base.launcher_tmp_dir}/UniversalTmp")
                extract_zip(ForgeInstallerUniversal, f"{Base.launcher_tmp_dir}/UniversalTmp")
                forge_version_data = os.path.join(Base.launcher_tmp_dir, "UniversalTmp", "version.json")
                self.download_forge_libraries(forge_version_data, instance_libraries)
        except subprocess.CalledProcessError as e:
            print(f"An error occurred: {e}")

    def select_loader_version(self, loader_name, loader_versions, client_version):
        # Display available versions to the user
        print(f"Available {loader_name} versions for Minecraft version {client_version}:")
        for idx, version in enumerate(loader_versions, start=1):
            print(f"{idx}. {version}")

        # Prompt the user to select a version
        try:
            choice = int(input(f"Select a {loader_name} version (1-{len(loader_versions)}): "))
            if 1 <= choice <= len(loader_versions):
                selected_version = loader_versions[choice - 1]
                return selected_version
            else:
                print("Invalid choice. Please select a valid number.")
        except ValueError:
            print("Invalid input. Please enter a number.")

    def install_mode_loader(self):
        print("Warning: This feature is under testing. Not sure all method will working fine.", color='red')
        Status, client_version, instance_path = instance_manager.select_instance(
            "Which instance is you want to install mode loader?", client_version=True)

        if Status is None:
            print("Failed to get instance path.", color='red')
            return

        while True:
            print("Mode Loader List:", color='blue')
            print("1: Fabric", color='yellow')
            print("2: Forge(Not Working)", color='darkgray')

            user_input = str(input("Which loader is you want to install?"))

            if user_input == "1":
                self.install_fabric_loader(instance_path)
                return True
            if user_input == "2":
                # self.install_forge_loader(instance_path)
                print("The install forge method has been discontinued in this version.", color='yellow')
                time.sleep(5)
                return True
            elif user_input.upper() == "EXIT":
                return True
            else:
                print("Unknown Options :(", color='red')


mod_installer = ModInstaller()
