import json
import lzma
import os
import re
import shutil
import subprocess
import requests
import xml.etree.ElementTree as ET
import time
from LauncherBase import Base, print_custom as print
from libs.__instance_manager import instance_manager
from libs.Utils.utils import download_file, multi_thread_download, extract_zip
from libs.Utils.libraries import libraries_check
from libs.instance.instance import instance


class ModInstaller:
    def __init__(self):
        self.loader_version = "None"
        self.client_version = "None"
        self.libraries_path = "None"
        self.ForgeMetadataURL = "https://maven.minecraftforge.net/net/minecraftforge/forge/maven-metadata.xml"

    def download_fabric_loader(self, libraries_path, loader_version):
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
        multi_thread_download(download_queue, "Fabric libraries")

        print("Downloading intermediary...", color='green')
        intermediary_url = (f"https://maven.fabricmc.net/net/fabricmc/intermediary/"
                            f"{client_version}/intermediary-{client_version}.jar")
        intermediary_dest = os.path.join(libraries_path, "net", "fabric", "intermediary", client_version,
                                         f"intermediary-{client_version}.jar")
        download_file(intermediary_url, intermediary_dest)

    @staticmethod
    def download_forge_libraries(version_data_path, libraries_path):
        forge_maven_url = "https://maven.minecraftforge.net/"
        download_queue = []

        with open(version_data_path, "r") as file:
            data = json.load(file)

            for library in data["libraries"]:
                # Get download url and path from version data
                if "forge" in library["name"]:
                    continue

                download_url = library["downloads"]["artifact"]["url"]
                path = library["downloads"]["artifact"]["path"]
                if not download_url:
                    # If download_url is None, add minecraft_libraries_url to the header of the url
                    # This method only working when the library is from mojang.
                    # If download_url is not None, using original download url (forge maven)
                    download_url = forge_maven_url + path

                destination = os.path.join(libraries_path, path)

                # Ensure the directories exist before downloading
                os.makedirs(os.path.dirname(destination), exist_ok=True)

                forge_lib_url_and_dest = [
                    (download_url, destination)
                ]
                download_queue.append(forge_lib_url_and_dest)
        multi_thread_download(download_queue, "Forge libraries")

    def install_fabric_loader(self, instance_path):
        def get_support_fabric_loader_list(client_version):
            url = f"https://meta.fabricmc.net/v2/versions/loader/{client_version}"

            # Get the list of all loader versions
            response = requests.get(url)
            if response.status_code != 200:
                print(f"Failed to retrieve data: {response.status_code}")
                return False, None

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
                time.sleep(3)
                return False, None

            return True, loader_versions

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
        if not os.path.exists(instance_info):
            print("Failed to get instance info :( Did you convert it to new format?", color='red')
            time.sleep(4)
            return

        Status, client_version = instance.get_instance_info(instance_info, info_name="client_version")
        game_dir = os.path.join(instance_path, ".minecraft")
        if not os.path.exists(game_dir):
            os.makedirs(game_dir)

        if not Status:
            print("Failed to get instance client version.", color='red')
            return

        # Start install process
        Status, loader_versions = get_support_fabric_loader_list(client_version)
        if not Status:
            return
        Status, loader_version = self.select_loader_version("Fabric Loader", loader_versions, client_version)
        if not Status:
            return
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
        instance.create_custom_config(instance_cfg)

        instance.write_custom_config(instance_cfg, "ModLoaderClass"
                                     , "net.fabricmc.loader.impl.launch.knot.KnotClient")
        instance.write_instance_info("IsVanilla", False, instance_info)
        instance.write_instance_info("Modified", True, instance_info)
        instance.write_instance_info("ModLoaderName", "Fabric", instance_info)
        instance.write_instance_info("ModLoaderVersion", loader_version, instance_info)
        print("Checking duplicates...", color='green')
        libraries_check(instance_libraries)
        print("Install Fabric loader successfully!", color='blue')
        time.sleep(3)

    def fetch_support_forge_versions(self, client_version):
        print("Fetching Forge metadata...", color='lightgreen')

        # Fetch metadata(xml)
        response = requests.get(self.ForgeMetadataURL)
        if response.status_code != 200:
            print(f"Failed to fetch Forge metadata. Status code: {response.status_code}", color='red')
            return False, None
        root = ET.fromstring(response.content)
        versions = root.find("./versioning/versions")
        all_versions = [version.text for version in versions.findall("version")]

        if client_version:
            filtered_versions = [
                v for v in all_versions if v.startswith(client_version)
            ]
            return True, filtered_versions
        return False, None

    def install_forge_loader(self, instance_path):
        # Setting some variable
        global result, full_game_args, full_jvm_args, final_args
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
        instance_custom_config = os.path.join(instance_path, "instance.bakelh.cfg")
        if not os.path.exists(instance_custom_config):
            instance.create_custom_config(instance_custom_config)
        Status, client_version = instance.get_instance_info(instance_info, info_name="client_version")
        game_dir = os.path.join(instance_path, ".minecraft")
        if not os.path.exists(game_dir):
            os.makedirs(game_dir)

        if not Status:
            print("Failed to get instance client version.", color='red')
            return False

        # Fetch support forge version
        Status, forge_versions = self.fetch_support_forge_versions(client_version)
        if not Status:
            print(f"Can't Minecraft version {client_version} support Forge version :(", color='red')
            time.sleep(3)
            return False

        Status, loader_version = self.select_loader_version("Forge", forge_versions, client_version)
        if not Status:
            return

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
            time.sleep(3)
            return False

        print("Preparing to install Forge...", color='green')
        print("Unzipping forge installer...", color='green')
        unzip_dest = os.path.join(Base.launcher_tmp_dir, "forge_installer_unzipped")
        if os.path.exists(unzip_dest):
            shutil.rmtree(unzip_dest)

        extract_zip(ForgeInstallerDest, unzip_dest)

        version_json_path = os.path.join(unzip_dest, "version.json")
        if not os.path.exists(version_json_path):
            print("Could not find version.json. Is it unzip correctly?", color='red')
            time.sleep(3)
            return False

        print("Downloading depends libraries...", color='green')
        self.download_forge_libraries(version_json_path, instance_libraries)

        print("Moving forge library...", color='green')
        forge_client_core_lzma = os.path.join(Base.launcher_tmp_dir, unzip_dest, "data", "client.lzma")
        forge_client_core = os.path.join(instance_libraries, "net", "minecraftforge", "forge", loader_version,
                                         f"forge-{loader_version}-client.jar")
        if not os.path.exists(forge_client_core_lzma):
            print("Could not find client.lzma. ignoring...", color='yellow')
        else:
            with lzma.open(forge_client_core_lzma) as f_in:
                with open(forge_client_core, "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)

        new_path = f"net/minecraftforge/forge/{loader_version}/forge-{loader_version}.jar"
        forge_library_path = os.path.join(Base.launcher_tmp_dir, unzip_dest, "maven", "net", "minecraftforge", "forge",
                                f"{loader_version}", f"forge-{loader_version}.jar")
        final_path = os.path.join(instance_libraries, new_path)
        final_dir = os.path.dirname(final_path)
        if not os.path.exists(final_dir):
            os.makedirs(final_dir)

        try:
            shutil.move(forge_library_path, final_path)
        except FileNotFoundError:
            print("Failed to move forge library. Is it download correctly?", color='red')
            time.sleep(3)
            return False
        except Exception as e:
            print(f"Failed to move forge library. Cause by a unknown error {e}", color='red')
            return False

        print("Confining custom arguments...", color='green')
        with open(version_json_path, "r") as file:
            data = json.load(file)

        loader_main_class = data.get("mainClass", None)
        if not loader_main_class:
            print("Failed to get mod loader class :(", color='red')
            time.sleep(3)
            return False
        else:
            instance.write_custom_config(instance_custom_config, "ModLoaderClass", loader_main_class)

        minecraft_Arguments = data.get("minecraftArguments", None)
        if minecraft_Arguments:
            match = re.search(r'--tweakClass (.*)', minecraft_Arguments)

            if match:
                result = match.group(1)
                final_args = f" --tweakClass {result}"
                print(f"Adding these arguments ( {final_args} ) to custom config...", color='green')
            instance.write_custom_config(instance_custom_config, "ModLoaderGameArgs", final_args)
        else:
            try:
                game_args = data.get('arguments', {}).get('game', None)
                jvm_args = data.get('arguments', {}).get('jvm', None)
                full_game_args = ""
                full_jvm_args = ""
                for argument in game_args:
                    full_game_args += f" {argument}"

                for argument in jvm_args:
                    full_jvm_args += f" {argument}"
                print(f"ModLoaderGameArgs : {full_game_args}")
                print(f"ModLoaderJVMArgs : {full_jvm_args}")
                instance.write_custom_config(instance_custom_config, "ModLoaderGameArgs", full_game_args, write_new_if_not_found=True)
                instance.write_custom_config(instance_custom_config, "ModLoaderJvmArgs", full_jvm_args, write_new_if_not_found=True)
            except KeyError:
                print("Failed to confining custom arguments :(", color='red')
            except Exception as e:
                print(f"Failed to confining custom arguments : {e}", color='red')


        instance.write_instance_info("IsVanilla", False, instance_info)
        instance.write_instance_info("Modified", True, instance_info)
        instance.write_instance_info("ModLoaderName", "Forge", instance_info)
        instance.write_instance_info("ModLoaderVersion", loader_version, instance_info)
        # print("Checking duplicates...", color='green')
        # libraries_check(instance_libraries)
        print("Forge install process finished!", color='green')
        time.sleep(2)

    @staticmethod
    def select_loader_version(loader_name, loader_versions, client_version):
        global selected_version
        while True:
            # Display available versions to the user
            print(f"Available {loader_name} versions for Minecraft version {client_version}:")
            for idx, version in enumerate(loader_versions, start=1):
                print(f"{idx}. {version}")

            # Prompt the user to select a version
            try:
                choice = int(input(f"Select a {loader_name} version (1-{len(loader_versions)}): "))
                if str(choice).lower() == "exit":
                    return True, "EXIT"
                if 1 <= choice <= len(loader_versions):
                    selected_version = loader_versions[choice - 1]
                    return True, selected_version
                else:
                    print("Invalid choice. Please select a valid number.")
            except ValueError:
                print("Invalid input. Please enter a number.")
            continue
        if selected_version == "EXIT":
            return False, None
        else:
            return True, selected_version

    def install_mode_loader(self):
        print("Warning: This feature is under testing. Not sure all method will working fine.", color='red')
        Status, client_version, instance_path = instance_manager.select_instance(
            "Which instance is you want to install mode loader?", client_version=True)

        if not Status:
            print("Failed to get instance path.", color='red')
            return

        while True:
            print("Mode Loader List:", color='blue')
            print("1: Fabric", color='yellow')
            print("2: Forge", color='blue')
            print("Which loader is you want to install?")
            user_input = str(input(":"))

            if user_input == "1":
                self.install_fabric_loader(instance_path)
                return True
            if user_input == "2":
                self.install_forge_loader(instance_path)
                time.sleep(5)
                return True
            elif user_input.upper() == "EXIT":
                return True
            else:
                print("Unknown Options :(", color='red')


mod_installer = ModInstaller()
