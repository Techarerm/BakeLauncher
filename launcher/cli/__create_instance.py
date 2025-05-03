import os.path
import time
import shutil
import zipfile
import traceback
from launcher.cli.__duke_explorer import Duke
from libs.instance.instance import instance
from libs.java.java_info import *
from libs.java.jvm_installer import jvm_installer
from launcher.cli.__instance_manager import instance_manager
from launcher.cli.__assets_grabber import assets_grabber
from launcher.cli.modification.mod_installer import mod_installer
from libs.Utils.utils import download_file
from libs.version.version import *
from LauncherBase import print_custom as print, internal_functions_error_log_dump
from launcher.cli.display_util.util import clear
from libs.libraries.libraries import download_libraries, download_natives
from libs.definition.data import *


class Create_Instance:
    def __init__(self):
        self.fabric_loader_version = None
        self.fabric_loader_dest = None
        self.client_version = ""
        self.libraries_path = ""
        self.version_spoof_status = None
        self.legacy_version_type = "classic"
        self.legacy_version = False
        self.SelectedInstanceInstalled = False
        self.require_jvm_version_installed = False
        self.MaxTextInOneItem = 10
        self.MaxVersionPerLine = 4
        self.VersionManifestURl = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"
        self.LegacyVersionManifestURl = ("https://github.com/Techarerm/BakeLauncher-Library/raw/refs/heads/main/Legacy"
                                         "%20Manifest/version_manifest_legacy.json")
        self.AlphaManifestURl = ("https://github.com/Techarerm/BakeLauncher-Library/raw/refs/heads/main/Legacy"
                                 "%20Manifest/version_manifest_alpha.json")
        self.InfdevManifestURl = ("https://github.com/Techarerm/BakeLauncher-Library/raw/refs/heads/main/Legacy"
                                  "%20Manifest/version_manifest_infdev.json")
        self.IndevManifestURL = ("https://github.com/Techarerm/BakeLauncher-Library/raw/refs/heads/main/Legacy"
                                 "%20Manifest/version_manifest_indev.json")
        self.ClassicManifestURl = ("https://github.com/Techarerm/BakeLauncher-Library/raw/refs/heads/main/Legacy"
                                   "%20Manifest/version_manifest_classic.json")
        self.RubyDungMinecraftManifestURl = ("https://github.com/Techarerm/BakeLauncher-Library/raw/refs/heads/main"
                                             "/Legacy%20Manifest/version_manifest_rd(old_alpha).json")
        self.version_id = None
        self.minecraft_version = ""
        # Working directory
        self.WorkDir = os.getcwd()

    def print_format_version_list(self, mode, **kwargs):
        """
        :param mode: legacy or modern
        :param kwargs: only_print_release_version (only print release version)
        """

        # parameter stuff
        only_print_release_version = kwargs.get('only_release_version', False)

        # Get the full version list
        release_versions = get_minecraft_version_list(only_return_release=True)
        full_version = get_minecraft_version_list()

        versions_list = release_versions if only_print_release_version else full_version

        # Legacy list (Example: 1: {Version})
        formatted_versions = '\n'.join([f"{index + 1}: {version}" for index, version in enumerate(versions_list)])

        # Modern list
        rows = (len(versions_list) + 9) // self.MaxVersionPerLine  # Round up division to determine rows

        print("Available version list:", color='purple')
        if mode == "legacy":
            print(formatted_versions)
        else:
            for row in range(rows):
                line = ""
                for col in range(12):
                    index = col * rows + row
                    if index < len(versions_list):
                        line += f"{index + 1}: {versions_list[index]:<{self.MaxTextInOneItem}}\t"
                print(line.strip())

        return versions_list


    @staticmethod
    def download_client(version_data, minecraft_version, install_dir, **kwargs):
        version_dir = os.path.join(Base.launcher_instances_dir, install_dir)
        libraries_dir = os.path.join(version_dir, INSTANCE_GAME_FOLDER_NAME, "libraries")
        os.makedirs(libraries_dir, exist_ok=True)

        # testing
        custom_client_url = kwargs.get('custom_client_url', None)
        if custom_client_url is not None:
            client_url = custom_client_url
        else:
            # Download client.jar
            client_info = version_data['downloads']['client']
            client_url = client_info['url']

        custom_dest = kwargs.get("custom_dest", None)

        if custom_dest is not None:
            client_dest = os.path.join(custom_dest, "client.jar")
        else:
            client_dest = os.path.join(version_dir, INSTANCE_GAME_FOLDER_NAME, 'libraries', 'net',
                                       'minecraft', minecraft_version,
                                       "client.jar")

        print(f"Downloading client.jar to {client_dest}...")
        download_file(client_url, client_dest)

        if os.path.exists(client_dest):
            return True
        else:
            return False

    def unzip_natives(self, instance_name):
        global unzip_status, PlatformName

        lib_platform_name = Base.Platform.lower()
        full_arch = Base.FullArch.lower()

        # Map platforms to native keys
        platform_name_dict = {
            'windows': ['windows'],
            'linux': ['linux'],
            'darwin': ["osx"],
        }
        platform_name_list = platform_name_dict.get(lib_platform_name, [])

        print(f"Platform Name < {' '.join(platform_name_list)} >")

        # Mapping native keys based on architecture
        map_keys_amd64 = {
            'windows': ['natives-windows', "natives-windows-64"],
            'linux': ['natives-linux'],
            'darwin': ['natives-macos', "natives-osx"],
            'windows-arm64': ['natives-windows'],
        }

        map_keys_arm64 = {
            'windows': ['natives-windows-arm64'],
            'linux': ['natives-linux-aarch64'],
            'darwin': ['natives-macos-arm64'],
            'windows-arm64': ['natives-windows-arm64'],
        }

        map_keys_i386 = {
            'windows': ['natives-windows-32', "natives-windows-x86"],
            'linux': ['natives-linux-aarch_64'],
            'darwin': ["natives-osx"],  # Unconfirmed
            'windows-arm64': ['natives-windows-arm64'],
        }

        # Handle platform naming for macOS
        if lib_platform_name == 'darwin':
            PlatformName = 'macos'

        # Assign correct native keys list based on architecture
        if full_arch == "amd64":
            native_keys_list = map_keys_amd64.get(lib_platform_name, [])
        elif full_arch == "arm64":
            native_keys_list = map_keys_arm64.get(lib_platform_name, [])
        elif full_arch == "i386":
            native_keys_list = map_keys_i386.get(lib_platform_name, [])
        else:
            native_keys_list = []
        instance_dir = os.path.join(Base.launcher_instances_dir, instance_name)
        instance_natives_dir = os.path.join(instance_dir, INSTANCE_GAME_FOLDER_NAME, "natives")
        instance_libraries_dir = os.path.join(instance_dir, INSTANCE_GAME_FOLDER_NAME, "libraries")
        if not os.path.exists(instance_natives_dir):
            os.mkdir(instance_natives_dir)

        os.chdir(instance_dir)
        # Find all natives and unzip
        jar_files = []

        for root, dirs, files in os.walk(instance_libraries_dir):
            for file in files:
                for native_key in native_keys_list:
                    if file.endswith(f"{native_key}.jar"):
                        jar_files.append(os.path.join(root, file))

        if jar_files:
            unzip_status = True
            for jar_file in jar_files:
                print(f"Found: {jar_file}", color='blue')

                # Create "natives" folder in libraries
                base_dir_name = os.path.basename(os.path.dirname(jar_file))
                natives_dir = os.path.join(os.path.dirname(jar_file), f"natives_{base_dir_name}")
                os.makedirs(natives_dir, exist_ok=True)

                # Extract only files from the JAR to the unique 'natives' directory
                with zipfile.ZipFile(jar_file, 'r') as jar:
                    for member in jar.namelist():
                        if not member.endswith('/'):
                            jar.extract(member, f"{INSTANCE_GAME_FOLDER_NAME}/natives")

        else:
            unzip_status = False
            print("No natives file found.", color='yellow')

        if unzip_status:
            # Move all file to natives_dir
            for root, dirs, files in os.walk(instance_natives_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    dest_path = os.path.join(instance_natives_dir, file)

                    shutil.move(file_path, dest_path)

            # After moving all files, optionally remove now-empty subdirectories
            for root, dirs, files in os.walk(instance_natives_dir, topdown=False):
                for d in dirs:
                    dir_path = os.path.join(root, d)
                    if not os.listdir(dir_path):  # If the directory is empty
                        os.rmdir(dir_path)
            print("Unzip Natives successfully!", color='blue')
        else:
            print("Warring: You may get some error you download libraries. Please re-download this version of"
                  " Minecraft again.", color='yellow')
        os.chdir(Base.launcher_root_dir)

    def install_jvm(self, version_data):
        # Change work dir back to launcher root(avoid some path error) and get install dir
        os.chdir(Base.launcher_root_dir)

        # Flag
        support_java_version_not_found_in_official_data = False
        require_jvm_version_installed = False

        # Get Java version info (from selected version's data)
        get_java_version, component, major_version = get_support_java_version(version_data)
        if get_java_version:
            print(f"Required Java Component: {component}, Major Version: {major_version}", color='green', tag='DEBUG')
        else:
            print("Could not get support Java version :( Is the manifest server down?")

        # Get organized_manifest_data (include filtered data, Java support platform are same as user's pc)
        manifest_data_list = get_support_java_version_from_java_version_manifest(Base.Platform, Base.FullArch)

        url_status, data = get_support_java_runtime_version_data(manifest_data_list, major_version)
        if url_status:
            support_java_version_not_found_in_official_data = True
            print("Found available Java runtime in the official manifest!", color='blue')
        else:
            print("No available Java runtime in the official manifest :(", color='red')

        install_path = os.path.join(Base.launcher_root_dir, "runtimes", f"Java_{major_version}")
        java_version_info_path = os.path.join(install_path, "java.version.info")

        if not os.path.exists(java_version_info_path) and os.path.exists(install_path):
            print("Found legacy runtime! Uninstalling...", color='yellow')
            try:
                shutil.rmtree(install_path)
            except Exception as e:
                print(f"Error when uninstalling runtime :D Err:{e}", color='red')

        Status = False
        if support_java_version_not_found_in_official_data:
            # Check install dir status
            if Base.OverwriteJVMIfExist:
                print("OverwriteJVMIfExist has been enabled.", color='blue', tag='INFO')
                if os.path.exists(install_path):
                    shutil.rmtree(install_path)

            if Base.DoNotAskJVMExist and os.path.exists(install_path):
                print("Bypassing reinstall JVM...", color='green', tag='INFO')
                return True, "BypassInstallJVM"

            if os.path.exists(install_path):
                require_jvm_version_installed = True
                print("Warning: A same version of Java runtime has been installed.", color='yellow')
                print("Do you want to reinstall it? Y/N")
                user_input = str(input(":"))
                if not user_input.upper() == "Y":
                    print("Bypass installing Java runtime...", color='green')
                    return True, "BypassInstallJVM"
                else:
                    # Install, uninstall ???
                    print("Uninstall Java runtime...", color='green')
                    shutil.rmtree(install_path, ignore_errors=True)
                    print("Uninstall Java runtime finished!", color='blue')
                    os.makedirs(install_path)
                    time.sleep(0.5)
            else:
                os.makedirs(install_path)
            Status, Message = jvm_installer.download_java_runtime_files(data, install_path)
        else:
            print("Could not find support runtimes from the official resource :(", color='red')
            print("Some platform are not in the official support list. If your platform are not support, ", end='')
            print("launcher will use Java runtimes built by azul.")
            print("Do you want to install Java runtimes from azul ?")
            user_input = str(input(":"))
            if user_input.upper() == "Y":
                install_path = os.path.join(Base.launcher_root_dir, "runtimes", "azul", f"Java_{major_version}")
                Status, Message = jvm_installer.install_azul_build_version_jvm(major_version, install_path)
            else:
                shutil.rmtree(install_path)
                Message = "Unsupported Platform"
                return

        if Status:
            create_java_version_info(major_version, Base.FullArch, install_path)
            print(f"Successfully installed Java runtime.", color='blue')
        else:
            print(f"Failed to install Java runtime :( Cause by {Message}", color='red')
            return False, f"DownloadJavaRuntime>Err{Message}"

        if not Base.Platform == "Windows":
            print("Do you want to fix permissions for the Java runtime?", color='blue', tag='PROMPT')
            print("Sometimes you may get 'Permission denied' errors when launching Minecraft. "
                  "This method can help fix these issues. :)",
                  color='green'
                  )
            print("The launcher may require our password to repair permissions.", color='purple', tag='INFO')
            print("Linux systems often need this fix to ensure the Java runtime works properly.", color='green')

            user_input = input("Proceed with fixing permissions? (Y/N): ").strip().upper()

            if user_input == "Y":
                try:
                    for dir_path, _, filenames in os.walk(install_path):
                        for filename in filenames:
                            file_path = os.path.join(dir_path, filename)

                            if not os.access(file_path, os.X_OK):
                                os.system(f"chmod +x {file_path}")
                    print("Permissions fixed successfully.", color='green', tag='SUCCESS')
                except Exception as e:
                    print(f"Error when fixing permissions: {e}", color='red', tag='ERROR')
                    return False, "FailedToFixPermissions"
            else:
                print("Permission fix skipped by user.", color='yellow', tag='INFO')

        if not self.require_jvm_version_installed:
            print("Do you want to create JVMConfig?", color='blue')
            print("This config is require when launching Minecraft (Find Usage JVM Path).", color='green')
            user_input = input("Y/N : ")
            if user_input.upper() == "Y":
                Duke.duke_finder()

        return True, "InstallJVMFinished"

    def download_game_files(self, version_id, install_dir, **kwargs):
        # Parameter stuff
        without_download_client = kwargs.get("without_download_client", False)

        game_folder = os.path.join(install_dir, INSTANCE_GAME_FOLDER_NAME)
        libraries_dir = os.path.join(install_dir, INSTANCE_GAME_FOLDER_NAME, "libraries")
        os.makedirs(game_folder, exist_ok=True)
        os.makedirs(libraries_dir, exist_ok=True)

        # Get ver data
        print("Loading version info...")
        version_data = get_version_data(version_id)

        if version_data is None:
            return False, "Get version data failed."

        # Download client.jar
        if not without_download_client:
            print("Downloading client...", color='lightblue')
            client_download_statsu = self.download_client(version_data, version_id, install_dir)
            if not client_download_statsu:
                return False, "Download client failed."

        # Download libraries
        print("Downloading libraries...", color='lightblue')
        lib_download_status = download_libraries(version_data, libraries_dir, **kwargs)
        if not lib_download_status:
            return False, "Download libraries failed."

        # Download natives
        natives_download_status = download_natives(version_data, libraries_dir)
        if not natives_download_status:
            return False, "Download natives failed. Platform unsupported."

        # Delay time to make old output don't print with new output
        time.sleep(0.5)
        print("The required dependent libraries should have been downloaded :)", color='blue')

        # Download the assets (Also it will check this version are use legacy assets or don't use)
        print("Downloading assets...", color='purple')
        assets_grabber.assets_file_grabber(version_id, install_dir)
        os.chdir(self.WorkDir)

        print("Unzipping natives...", color='green')
        self.unzip_natives(install_dir)

        print("Downloading JVM...", color='cyan')
        self.install_jvm(version_data)

        print("When you install a Java version that has never been installed before,"
              " you need to reconfig Java Path!",
              color='blue')
        print("Now all files are download success :)", color='blue')
        print("Exiting....", color='green')

        # Add waiting time (If the assets' download failed, it will print it?)
        time.sleep(1.2)
        return True, None

    def download_legacy_game(self, real_version, spoof_version, install_dir):
        # Getting custom client url and download client
        print("Getting client url..")
        legacy_url = get_minecraft_version_url(real_version, custom_version_manifest_url=self.LegacyVersionManifestURl)
        # Check legacy url valid
        if legacy_url is None:
            print("Could not get version url.", color='red', tag='ERROR')
            return False, "Get version url failed"

        legacy_url = "/".join(legacy_url.split("/")[:-1]) + "/"
        client_url = f"{legacy_url}{real_version}.jar"
        legacy_version_data = get_version_data(real_version, custom_version_manifest_url=self.LegacyVersionManifestURl)
        if legacy_version_data is None:
            # Retry using the official source
            legacy_version_data = get_version_data(real_version)

        # Check url status
        if legacy_version_data is None:
            print("Version url are unavailable :( Is the server down?", color='red')
            time.sleep(3)
            return False, "Version url unavailable"

        # Download client
        Status = self.download_client(legacy_version_data, real_version, install_dir, custom_client_url=client_url)
        if not Status:
            return False, "Downloading client failed :("

        print("Downloading spoof version files...", color='blue')
        Status, e = self.download_game_files(spoof_version, install_dir, without_download_client=True)
        if not Status:
            return False, f"Download spoof version game files failed. ERR:{e}"

        return True, "Spoof version game files downloaded"

    def version_spoof(self, require_version):
        global client_version, spoof_enable
        """
        real_version (if the client type is not legacy, it is the same as client_version).
        If the client is a legacy version, client_version and real_version are not the same(or same? if user using
        rd-132211)

        Why this spoof? Legacy archives place the client in a weird location (version data tag libraries don't have
        the client URL). Additionally, some legacy version libraries have incomplete data. To address this,
        BakeLauncher uses a similar library version as an alternative for these cases.

        Why keep real_version in instance info? When the user launches Minecraft, the launcher manager calls
        a function named "java_version_check" to get the java_version. If the client uses a spoofed version,
        it might crash due to argument bugs. (However, legacy version data's "MinecraftArguments" are complete.)
        """
        if self.legacy_version:
            real_version = require_version
            print(f" Version Type: {self.legacy_version_type}", color='green', tag='DEBUG')
            if self.legacy_version_type == "alpha":
                client_version = "a1.2.6"
                self.version_spoof_status = True
            elif self.legacy_version_type == "infdev":
                client_version = "inf-20100618"
                self.version_spoof_status = True
            elif self.legacy_version_type == "indev":
                client_version = "inf-20100618"
                self.version_spoof_status = True
            elif self.legacy_version_type == "classic":
                client_version = "c0.30_01c"
                self.version_spoof_status = True
            elif self.legacy_version_type == "pre-classic":
                client_version = "rd-160052"
                self.version_spoof_status = True
            else:
                # official version
                client_version = self.legacy_version
                self.version_spoof_status = False
            if self.version_spoof_status:
                print(f"Version Spoof Enable | RealVersion: {require_version} Spoof to Version : {client_version}",
                      color='green', tag='DEBUG')
        else:
            client_version = require_version
            real_version = require_version
        return client_version, real_version

    def rollback_install_instance(self, instance_path):
        print("Rollback installing...", color='green')

        if not os.path.exists(instance_path):
            return False, "Specified instance are not found"

        try:
            shutil.rmtree(instance_path)
        except Exception as e:
            return False, e

        return True, None

    def start_create_instance(self, require_version):
        # Check version
        client_version, real_version = self.version_spoof(require_version)
        if not os.path.exists(Base.launcher_instances_dir):
            os.makedirs(Base.launcher_instances_dir)

        instances_dir = os.listdir(Base.launcher_instances_dir)
        if len(instances_dir) == 0:
            print("Installed instance list:", color='green')
            instance_manager.instance_list(without_drop_no_instance_available_error=True)

        while True:
            # Prompt for instance name
            print("Give a name for this instance (or type 'EXIT' to cancel):", end='', color='lightblue')
            name = input(":").strip()

            if name.upper() == "EXIT":
                print("Instance creation canceled.", color='yellow')
                return False, "ExitCreateInstance"

            if not name:
                print("Please enter a valid name. Name cannot be empty or spaces only.", color='red')
                continue

            # Set the instance path
            instance_path = os.path.join(Base.launcher_instances_dir, name)

            # Save version.json
            version_data = get_version_data(client_version)
            create_version_data(client_version, version_data)

            # Get version info
            version_type = get_minecraft_version_type(real_version)
            Status, main_class = find_main_class(real_version, custom_version_data=version_data)
            component, major_version = Duke.get_java_version_info(get_version_data(client_version))

            # Check if instance already exists
            if os.path.exists(instance_path):
                counter = 2
                new_instance_path = instance_path
                while os.path.exists(new_instance_path):
                    new_instance_path = os.path.join(Base.launcher_instances_dir, f"{name}({counter})")
                    counter += 1

                print(f'Instance name "{name}" already exists.')
                print(f'Do you want to rename it to "{os.path.basename(new_instance_path)}"? (Y/N):', end='',
                      color='yellow')
                user_input = input(":").strip().upper()

                if user_input == "Y":
                    instance_path = new_instance_path
                else:
                    print("Please choose a different name.", color='red')
                    continue

            print(f'Creating instance at {instance_path}', color='lightgreen')

            game_folder = os.path.join(instance_path, INSTANCE_GAME_FOLDER_NAME)
            os.makedirs(game_folder, exist_ok=True)

            instance.create_instance_info(
                instance_name=os.path.basename(instance_path),
                client_version=client_version,
                version_type=version_type,
                is_vanilla=True,
                modify_status=False,
                mod_loader_name=None,
                mod_loader_version=None,
                real_minecraft_version=real_version,
                java_major_version=major_version,
                main_class=main_class
            )
            Status, error = self.download_game_files(client_version, instance_path)
            if not Status:
                print(f"Error while downloading game files : {error}", color='red')
                time.sleep(5)
            else:
                return True, "InstanceCreated"

    def reinstall_instances(self):
        # if the instances list does not exist, return Status=False and client_version=ErrorMessage
        print("The instance you want to install must have been converted to the new format!",
              color='red')  # legacy part
        Status, client_version, instance_path = instance_manager.select_instance(
            "Which instance you want to reinstall?", client_version=True)
        if not Status:
            print(f"Failed to get select instance. Cause by error {client_version}", color='red')
            return False

        if Status == "EXIT":
            print("Exiting...", color='green')
            return True

        instance_info = os.path.join(instance_path, "instance.bakelh.ini")
        if not os.path.exists(instance_path):
            print("Could not reinstall instance :( Did you convert it to new format?", color='red')
            time.sleep(4)
            return

        Status, instance_name = instance.get_instance_info(instance_info, info_name="instance_name")
        version_data = get_version_data(client_version)
        if version_data is None:
            print("Failed to get version data. Cause by source is unavailable :(", color='red')
            time.sleep(5)
            return True

        # Avoid macOS hide game folder
        game_folder = os.path.join(instance_path, INSTANCE_GAME_FOLDER_NAME)
        os.makedirs(game_folder, exist_ok=True)

        print(f"Reinstalling instance name {instance_name}...", color='green')
        print(f"Client Version: {client_version} Instance Dir: {instance_path}", color='green', tag='DEBUG')
        self.download_game_files(client_version, instance_path)

    def create_instance(self):
        def download_minecraft_with_version_id(list_type=None, only_release_version=True, ):
            """
            Allows users to select and download a Minecraft version based on version ID.
            """
            print("Grabbing version list...")
            if list_type is not None:
                if list_type != "release" and list_type != "legacy":
                    only_release_version = False

            mode = "modern"
            if list_type == "legacy" or list_type == "legacy_all":
                mode = "legacy"
            print(mode)
            version_list = self.print_format_version_list(mode, only_release_version=only_release_version)

            if not version_list:
                print("No versions found. Please check your connection or version list source.", color='red')
                return

            print("VersionID: MinecraftVersion", "\n", color='purple')
            print("Example: 15: 1.12.2 , 15 is version 1.12's ID", color='green')

            # Handle special list types
            if list_type == "legacy_all":
                print(
                    "Warning: Version list is set to LEGACY_ALL. This may include unsupported versions.",
                    color='yellow')
                print("To reset the list, enter 'legacy_list' or 'list'.", color='green')

            # Additional instructions
            print("Some cool stuff:'")
            print(
                "Type 'list' to print list again. 'legacy_list' for legacy list(support more system than normal list)",
                color='blue')
            print("'legacy_all' for legacy list(but it wll print all available versions. The list will be long)",
                  color='blue')
            print("'list_all' can print all available versions(Not recommended. Poor support for most of system)",
                  color='purple')

            # Get user input
            version_id = input("Please enter the version ID:").strip()

            # Handle special commands
            if version_id.upper() == "EXIT":
                return

            command_mapping = {
                "LIST": "release",
                "LIST_ALL": "all_version",
                "LEGACY_LIST": "legacy",
                "LEGACY_ALL": "legacy_all",
            }

            if version_id.upper() in command_mapping:
                return download_minecraft_with_version_id(list_type=command_mapping[version_id.upper()])

            # Validate version_id as an integer
            try:
                version_id = int(version_id)
            except ValueError:
                print("Invalid version ID. Please enter a numeric value.", color='red')
                return download_minecraft_with_version_id(list_type=list_type)

            # Adjust version_id to match 0-based indexing
            version_id -= 1

            if not (0 <= version_id < len(version_list)):
                print(f"Version ID '{version_id + 1}' is out of range. Please try again.", color='red')
                return download_minecraft_with_version_id(list_type=list_type)

            # Get selected Minecraft version
            minecraft_version = version_list[version_id]

            # Clear screen/output (if clear is defined)
            if 'clear' in globals():
                clear()

            print("Creating instance...", color='green')
            try:
                self.start_create_instance(minecraft_version)
            except Exception as e:
                print(f"Failed to create instance. Error: {e}", color='red')
                time.sleep(5)
                return

        def download_with_regular_minecraft_version():
            selected_version = False
            version_list = get_minecraft_version_list()
            print("Using regular Minecraft version method...", color='green')
            regular_version_input = str(input("Please enter the Minecraft version:"))
            # Find minecraft_version after get version_id(IMPORTANT:version =/= version_id!)

            if regular_version_input.upper() == "EXIT":
                return

            elif regular_version_input.upper() == "LIST":
                self.print_format_version_list("modern")
                download_with_regular_minecraft_version()
                return

            for version in version_list:
                if regular_version_input == version:
                    selected_version = True

            try:
                if selected_version:
                    clear()
                    print("Creating instance....", color='green')
                    self.start_create_instance(regular_version_input)
                else:
                    # idk this thing would happen or not :)  , just leave it and see what happen....
                    print(f"You type Minecraft version {regular_version_input} are not found :(",
                          color='red')
                    download_with_regular_minecraft_version()

            except ValueError:
                # Back to download_main avoid crash(when user type illegal thing
                print("Oops! Invalid input :( Please enter Minecraft version.")
                download_with_regular_minecraft_version()

        if Base.InternetConnected:
            print("Which method you wanna use?", color='green')
            print("1: List all available versions and download", color='green')
            print("2: Type regular Minecraft version and download(include snapshot)", color='blue')
            print("3: Download Legacy Minecraft (Disabled)", color='gray')
            print("4: Reinstall instance", color='cyan')
            print("5: Install Mod Loder(Exp)", color='purple')
            user_input = str(input(":"))
            if user_input.upper() == "EXIT":
                print("Exiting....", color='green')
                return

            if user_input == "1":
                download_minecraft_with_version_id()
            elif user_input == "2":
                download_with_regular_minecraft_version()
            elif user_input == "4":
                self.reinstall_instances()
            elif user_input == "5":
                mod_installer.install_mode_loader()
            else:
                print("Unknown options :( Please try again.", color='red')
                self.create_instance()
            try:
                print("")
            except Exception as e:
                if Exception is ValueError:
                    print("Oops! Invalid option :O  Please enter a number.", color='red')
                    self.create_instance()
                    time.sleep(1.5)
                else:
                    # Dump error log if crash while downloading game files or other process
                    print(f"Create Instance got a error when calling a internal functions. Error: {e}", color='red')
                    function_name = traceback.extract_tb(e.__traceback__)[-1].name
                    detailed_traceback = traceback.format_exc()
                    internal_functions_error_log_dump(e, "Create Instance", function_name, detailed_traceback)
                    time.sleep(5)
        else:
            print("No Internet Connection :/", color='red')
            time.sleep(4)
            return


create_instance = Create_Instance()
