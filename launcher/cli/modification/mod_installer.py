import ast
import json
import shutil
import subprocess
from json import JSONDecodeError
import requests
import xml.etree.ElementTree as ET
import time
from launcher.cli.__instance_manager import instance_manager
from libs.Utils.utils import extract_zip, find_jar_file_main_class
from libs.libraries.libraries import *
from libs.instance.instance import instance
from launcher.cli.modification.fabric import fabric
from launcher.cli.modification.forge import forge
from libs.definition.data import *


class ModInstaller:
    def __init__(self):
        self.loader_version = "None"
        self.client_version = "None"
        self.libraries_path = "None"
        self.ForgeMetadataURL = "https://maven.minecraftforge.net/net/minecraftforge/forge/maven-metadata.xml"

    def install_fabric_loader(self, instance_path):
        # Setting some variable
        instance_cfg = os.path.join(instance_path, "instance.bakelh.cfg")
        instance.create_custom_config(instance_cfg)

        instance_libraries = os.path.join(instance_path, INSTANCE_GAME_FOLDER_NAME, "libraries")
        if not os.path.exists(instance_libraries):
            print("Error while checking instance. Libraries folder not found.")
            time.sleep(3)
            return False

        instance_info = os.path.join(instance_path, "instance.bakelh.ini")
        if not os.path.exists(instance_info):
            print("Failed to get instance info :( Did you convert it to new format?", color='red')
            time.sleep(4)
            return

        # Get client_version from instance info
        Status, client_version = instance.get_instance_info(instance_info, info_name="client_version")
        game_dir = os.path.join(instance_path, INSTANCE_GAME_FOLDER_NAME)
        if not os.path.exists(game_dir):
            os.makedirs(game_dir)

        if not Status:
            print("Failed to get instance client version.", color='red')
            time.sleep(3)
            return

        # Start install process
        Status, loader_versions = fabric.get_support_fabric_loader_list(client_version)
        if not Status:
            print(loader_versions)
            return

        Status, loader_version = self.select_loader_version("Fabric Loader", loader_versions, client_version)
        if not Status:
            return

        loader_version_data = fabric.get_fabric_version_data(loader_version, client_version)
        if not loader_version_data:
            print("Failed to get loader version.", color='red')
            time.sleep(3)
            return False

        libraries_data = loader_version_data["launcherMeta"]["libraries"]["common"]
        print("Downloading Fabric loader...", color='green')
        Status = fabric.download_loader(loader_version, instance_libraries)
        if not Status:
            print("Failed to download fabric loader :(", color='red')
            time.sleep(3)
            return False

        print("Downloading intermediary...", color='green')
        Status = fabric.download_intermediary(client_version, instance_libraries)
        if not Status:
            print("Failed to download intermediary :(", color='red')
            time.sleep(3)
            return False

        fabric.download_libraries(libraries_data, instance_libraries)

        print("Confining Fabric setting...", color='green')
        main_class = loader_version_data["launcherMeta"]["mainClass"]["client"]
        instance.write_custom_config(instance_cfg, "ModLoaderClass", main_class)
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

    def install_legacy_forge(self, install_profile, forge_installer_dest, libraries_path, instance_cfg, loader_version):
        global arguments
        version_json_status = True
        print("Checking installer type...", color='lightgreen', tag="DEBUG")
        version_json_path = os.path.join(forge_installer_dest, "version.json")
        if os.path.exists(version_json_path):
            print("Type : Legacy", color='green', tag="DEBUG")
        else:
            version_json_status = False
            print("Version data not found. Get libraries data from install profile instead.", color='yellow')
            print("Type : Pre-Legacy", color='green', tag="DEBUG")

        # Get version data
        if version_json_status:
            with open(version_json_path, "r") as f:
                forge_version_data = json.load(f)
        else:
            forge_version_data = install_profile.get("versionInfo", [])
            if len(forge_version_data) == 0:
                print("Could not find versionInfo. Unsupported forge profile", color='red', tag="DEBUG")
                time.sleep(3)
                return False, None

        libraries = {}
        print("Getting dependencies...", color='blue')
        install_profile_libraries = install_profile.get("libraries", [])
        version_libraries = forge_version_data.get("libraries", [])
        libraries['libraries'] = libraries.get('libraries', []) + install_profile_libraries + version_libraries
        forge.download_forge_libraries_legacy(libraries, libraries_path)

        # Get main class and arguments
        main_class = forge_version_data.get("mainClass", None)
        orig_arguments = forge_version_data.get("minecraftArguments", None)
        match = re.search(r'--tweakClass\s+(\S+)', orig_arguments)

        if match:
            arguments = match.group(0)

        if main_class is not None:
            print(f"mainClass : {main_class}", color='purple')
            instance.write_custom_config(instance_cfg, "ModLoaderClass", main_class)

        if arguments is not None:
            print(f"minecraftArguments : {arguments}", color='blue')
            instance.write_custom_config(instance_cfg, "ModLoaderGameArgs", arguments)

        print("Moving forge core file...",color='cyan')
        forge.move_forge_files(forge_installer_dest, loader_version, libraries_path)
        filter_list = ["client", "mappings", "slim", "forge", "extra", "asm"]
        print("Checking libraries duplication")
        libraries_check(libraries_path, filter_list)
        print("Install forge finished!", color='lightgreen')
        time.sleep(3)
        return True

    def install_forge_loader(self, instance_path):
        # Setting some variable
        global full_mc_slim_path, full_mc_extra_path, full_mc_srg_path, game_args, jvm_args, resolved_args
        instance_libraries = os.path.join(instance_path, INSTANCE_GAME_FOLDER_NAME, "libraries")
        instance_info = os.path.join(instance_path, "instance.bakelh.ini")
        instance_custom_config = os.path.join(instance_path, "instance.bakelh.cfg")
        game_dir = os.path.join(instance_path, INSTANCE_GAME_FOLDER_NAME)
        if not os.path.exists(game_dir):
            os.makedirs(game_dir)

        if not os.path.exists(instance_libraries):
            print("Failed to get instance info. Did you convert it to new format?", color='red')
            time.sleep(3)
            return False

        if not os.path.exists(instance_custom_config):
            instance.create_custom_config(instance_custom_config)

        # Get minecraft client version
        Status, client_version = instance.get_instance_info(instance_info, info_name="client_version")
        if not Status:
            print("Failed to get instance client version.", color='red')
            time.sleep(3)
            return False

        # Fetch version support forge versions
        Status, forge_versions = self.fetch_support_forge_versions(client_version)
        if not Status:
            print(f"Can't Minecraft version {client_version} support Forge version :(", color='red')
            time.sleep(3)
            return False

        Status, loader_version = self.select_loader_version("Forge", forge_versions, client_version)
        if not Status:
            return

        # Download installer
        print("Downloading forge installer...", color='green')
        forge_installer_url = (f"https://maven.minecraftforge.net/net/minecraftforge/forge/"
                               f"{loader_version}/forge-{loader_version}-installer.jar")

        installer_dest = os.path.join(Base.launcher_tmp_dir, "forge-installer.jar")

        # Clear tmp file
        if os.path.exists(installer_dest):
            os.remove(installer_dest)

        download_file(forge_installer_url, installer_dest)

        if not os.path.exists(installer_dest):
            print("Failed to download forge installer :(", color='red')
            time.sleep(3)
            return False

        print("Preparing to install Forge...", color='green')
        print("Unzipping forge installer...", color='green')
        unzip_dest = os.path.join(Base.launcher_tmp_dir, "forge_installer_unzipped")
        libraries_dest = os.path.join(unzip_dest, "libraries")
        if os.path.exists(unzip_dest):
            shutil.rmtree(unzip_dest)

        if os.path.exists(libraries_dest):
            shutil.rmtree(libraries_dest)

        os.makedirs(libraries_dest, exist_ok=True)

        extract_zip(installer_dest, unzip_dest)

        install_profile_path = os.path.join(unzip_dest, "install_profile.json")
        if not os.path.exists(install_profile_path):
            print("Could not find install_profile. Is it unzip correctly?", color='red')
            time.sleep(3)
            return False

        print("Loading install profile...")
        try:
            with open(install_profile_path, "r") as f:
                install_profile_data = json.load(f)
        except JSONDecodeError as e:
            print("Loading install profile failed.", color='red')
            time.sleep(3)
            return False

        # Check the installer type
        try:
            processors_data = install_profile_data["processors"]
            if len(processors_data) <= 0:
                processors_data = install_profile_data["BAKEBAKE"]
        except KeyError:
            #  print("This version of forge installer is not supported :(", color='red')
            #  print("Just wait 0.5 month...the update will coming...I think :)", color='blue')
            Status = self.install_legacy_forge(install_profile_data, unzip_dest, instance_libraries,
                                               instance_custom_config, loader_version)
            return Status

        version_json_path = os.path.join(unzip_dest, "version.json")
        if os.path.exists(version_json_path):
            with open(version_json_path, "r") as f:
                version_json = json.load(f)
        else:
            print("Failed to get forge version data. Version.json is missing!", color='red')
            time.sleep(3)

        # Check BINPATCH
        binpatch_path = os.path.join(unzip_dest, "data", "client.lzma")
        if not os.path.exists(binpatch_path):
            print("BINPATCH not found :(", color='red')
            time.sleep(3)
            return False

        # Detect forge profile
        print("Checking install profile....", color='green')
        forge.detect_forge_profile_depends(install_profile_data)

        # Get processor class (no usage) and dependencies libraries
        processors_maven_class_list_no_usage, libraries = forge.detect_forge_processors_depends(install_profile_data)

        # Get processor class and corresponding args
        processors_maven_class_list, processors_args_list = forge.get_forge_all_processors_class_name_and_args(
            install_profile_data)

        # Prepare processor_class url and path
        download_queue = []
        for name in processors_maven_class_list:
            Status, processor_class_path = convert_library_name_to_artifact_path(name)
            url = forge.forge_maven_url + processor_class_path
            dest = os.path.join(libraries_dest, processor_class_path)
            lib_url_and_dest = [
                (url, dest)
            ]
            download_queue.append(lib_url_and_dest)

        # Prepare dependencies libraries url and path
        for library in libraries:
            Status, library_path = convert_library_name_to_artifact_path(library)
            url = forge.forge_maven_url + library_path
            dest = os.path.join(libraries_dest, library_path)
            lib_url_and_dest = [
                (url, dest)
            ]
            download_queue.append(lib_url_and_dest)

        # Download requires file and libraries
        time.sleep(2)

        # For installer process
        print("Downloading processors dependencies...", color='lightgreen')
        multi_thread_download(download_queue, "Processors libraries")
        forge.download_forge_libraries_modern(install_profile_data, libraries_dest)
        # For forge core launch
        print("Downloading forge dependencies...", color='cyan')
        forge.download_forge_libraries_modern(version_json, instance_libraries)
        forge.download_forge_libraries_modern(install_profile_data, instance_libraries)

        # Get processors class requires libraries and some info
        libraries_path_string_list = []
        processors_main_class_list = []
        for processor_class, processor_args in zip(processors_maven_class_list, processors_args_list):
            libraries_path_string = ""  # Reset for each processor_class
            Status, libraries = forge.get_forge_processor_depends(processor_class, install_profile_data)
            Status, processor_class_path = convert_library_name_to_artifact_path(processor_class)
            processor_class_path = os.path.join(libraries_dest, processor_class_path)

            # Process libraries for this processor_class
            for library in libraries:
                Status, library_path = convert_library_name_to_artifact_path(library)
                full_path = os.path.join(libraries_dest, library_path)
                libraries_path_string += full_path + ";"

            # Add the processor's class path to libraries_path_string
            libraries_path_string += processor_class_path

            # Remove trailing semicolon
            if libraries_path_string.endswith(";"):
                libraries_path_string = libraries_path_string[:-1]

            # Save processor information (without placeholder replacement)
            libraries_path_string_list.append(libraries_path_string)
            if os.path.exists(processor_class_path):
                print(f"Exists: {processor_class_path}", color='lightgreen')
            else:
                print(f"Not found: {processor_class_path}", color='red')

            processors_main_class_list.append(find_jar_file_main_class(processor_class_path))
            print(f"Processor Name : {processor_class}", color='lightblue')
            if libraries is not None:
                print("Dependencies :", color='cyan')
                for library in libraries:
                    print(library)

            if processor_args is not None:
                print("Arguments:", processor_args, color='lightred')

        print("Preparing files...", color='green')

        # Client.jar
        client_jar_path = os.path.join(instance_libraries, "net", "minecraft", client_version, "client.jar")
        if not os.path.exists(client_jar_path):
            print("Client not found :( Please reinstall your instance.", color='red')
            time.sleep(3)
            return False

        # Getting placeholders (replace data require this)
        Status, depends_data = forge.detect_forge_profile_depends(install_profile_data, return_full_data=True)
        placeholders_data = forge.convert_forge_data_to_real(depends_data, libraries_dest)
        # Convert it to type dict
        placeholders = ast.literal_eval(placeholders_data)

        # Append the client path into the placeholders
        MINECRAFT_JAR = {'MINECRAFT_JAR': client_jar_path}
        placeholders.update(MINECRAFT_JAR)

        # Append side type into the placeholders
        side = {'SIDE': "client"}
        placeholders.update(side)

        # Update client lzma path
        try:
            placeholders.update(BINPATCH=binpatch_path)
        except KeyError:
            pass

        # Generate process install command (Replace data into the arguments
        processors_command_list = []
        processors_info = []
        for main_class, libraries_path_string, args in zip(processors_main_class_list, libraries_path_string_list,
                                                           processors_args_list):
            # Replace placeholders in arguments
            try:
                resolved_args = [
                    arg.format(**placeholders) if isinstance(arg, str) else arg
                    for arg in args
                ]
            except KeyError as e:
                print("Unable to resolve arguments :(", color='red')
                print("Unsupported version error.", color='red')
                print(e)
                time.sleep(3)
                return False

            # Resolve maven paths in arguments
            final_args = forge.convert_maven_name_to_artifact_path_in_the_args(
                resolved_args, libraries_dest
            )

            # Prepare the full command for this processor
            full_args = " ".join(final_args)
            command = f'java -Xmx4G -cp "{libraries_path_string}" {main_class} {full_args}'
            processors_command_list.append(command)

        for command in processors_command_list:
            print(command)

        print("Processing Forge Install...", color='prple')
        for processor_name, command in zip(processors_main_class_list, processors_command_list):
            print(f"Processing {processor_name}...", color='lightyellow')
            try:
                # print(command)
                subprocess.run(command, shell=True, check=True)
            except Exception as e:
                print("Error while processing ", e, color='red')

        """
        forge.move_forge_files(unzip_dest, loader_version, instance_libraries)
        forge_client_maven_path = forge.get_forge_key_data("PATCHED", install_profile_data)
        F, forge_client_path = convert_library_name_to_artifact_path(forge_client_maven_path)
        full_forge_client_path = os.path.join(instance_libraries, forge_client_path)

        # forge_client_hash = forge.get_forge_key_data("PATCHED_SHA", install_profile_data)
        if not os.path.exists(full_forge_client_path):
            print("Client file does not exist.", color='red')
            print("Install forge failed!", color='red')
            time.sleep(3)
            return False

        game_main_class = version_json.get("mainClass", None)
        if game_main_class is None:
            print("Failed to get main class.")
        else:
            instance.write_custom_config(instance_custom_config, "ModLoaderClass", game_main_class)

        if version_json.get("arguments", None):
            arguments_dict = version_json.get("arguments")
            game_args = arguments_dict.get("game", None)
            jvm_args = arguments_dict.get("jvm", None)

        final_game_args = ""
        final_jvm_args = ""
        if game_args is not None:
            for arg in game_args:
                final_game_args += arg + " "

        if jvm_args is not None:
            for orig_arg in jvm_args:
                arg = forge.replace_jvm_args_value_to_real(instance_libraries, client_version, orig_arg)
                final_jvm_args += arg + " "

        if final_game_args != "":
            instance.write_custom_config(instance_custom_config, "ModLoaderGameArgs", final_game_args)

        if final_jvm_args != "":
            instance.write_custom_config(instance_custom_config, "ModLoaderJVMArgs", final_jvm_args)

        # Check libraries
        # forge.detecting_requires_library_and_delete_no_usage(instance_libraries, client_version, version_json)

        filter_list = ["client", "mappings", "slim", "forge", "extra", "srg"]
        libraries_check(instance_libraries, filter_list)
        print("Forge install process finished!", color='blue')
        time.sleep(2)
        """

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
                choice = input(f"Select a {loader_name} version (1-{len(loader_versions)}): ")
                if str(choice).lower() == "exit":
                    return True, None

                if 1 <= int(choice) <= len(loader_versions):
                    selected_version = loader_versions[int(choice) - 1]
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

        if Status == "EXIT":
            return

        while True:
            print("Mode Loader List:", color='blue')
            print("1: Fabric", color='yellow')
            print("2: Forge (Not Recommended)", color='red')
            print("# The Minecraft version since 1.13~1.14.4 and 1.17~latest install forge are not supported.", color='red')
            print("Which loader is you want to install?")
            user_input = str(input(":"))

            if user_input == "1":
                self.install_fabric_loader(instance_path)
                return True
            if user_input == "2":
                self.install_forge_loader(instance_path)
                return True
            if user_input.upper() == "EXIT":
                return True
            else:
                print("Unknown Options :(", color='red')


mod_installer = ModInstaller()
