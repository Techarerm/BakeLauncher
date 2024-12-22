import os
import shutil
import time
import traceback
from libs.instance.instance import instance
from LauncherBase import Base, print_color as print, internal_functions_error_log_dump
from libs.Utils.utils import find_main_class, get_version_data
from libs.__duke_explorer import Duke


class InstanceManager:
    def __init__(self):
        self.real_minecraft_version = None
        self.use_legacy_manifest = None
        self.name = None
        self.SelectedInstanceInstalled = None
        self.InstallVersion = False
        self.VersionManifestURl = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"
        self.fabric_installer_version_list = "https://meta.fabricmc.net/v2/versions/installer"

        # Instance Info
        self.INSTANCE_NAME = None
        self.CLIENT_VERSION = None
        self.VERSION_TYPE = None
        self.LAUNCHER_VERSION = None
        self.INSTANCE_FORMAT = None
        self.CREATE_DATE = None
        self.CONVERT_FROM_LEGACY = False

        # Instance Structure
        self.game_folder = ".minecraft"
        self.assets_folder = ".minecraft/assets"

        # Modify Info
        self.ISVanilla = False
        self.Modified = False
        self.ModLoaderName = False
        self.ModLoaderVersion = False

        # Config
        self.EnableConfig = True
        self.CFGPath = "instance.bakelh.cfg"

        self.RenameSuccessful = False
        self.instance_path = None

    @staticmethod
    def instance_list(**kwargs):
        only_print_legacy = kwargs.get('only_print_legacy', False)
        only_return_list = kwargs.get('only_return_list', False)
        without_drop_no_instance_error = kwargs.get('without_drop_no_instance_available_error', False)
        only_return_legacy_list = kwargs.get('only_return_legacy_list', False)
        if not os.path.exists(Base.launcher_instances_dir):
            return False, "NoInstancesAreAvailable"
        else:
            instances_list_original = os.listdir(Base.launcher_instances_dir)
            if len(instances_list_original) == 0:
                return False, "NoInstancesAreAvailable"

        if not instances_list_original:
            if not without_drop_no_instance_error:
                print("No instances are available.", color='red')
                print("Go to step 3: Create Instance. After it's installed, you can try this method again!",
                      color='yellow')
                return False, "NoInstancesAreAvailable"
            else:
                print("[You are looking to the null space]", color='darkwhite')
                return True, "NoInstancesAreAvailable"

        instances_list_legacy = []
        instances_list_new = []

        # Classify instances as legacy or new
        for instance in instances_list_original:
            instance_info_path = os.path.join(Base.launcher_instances_dir, instance, "instance.bakelh.ini")
            if os.path.exists(instance_info_path):
                instances_list_new.append(instance)
            else:
                instances_list_legacy.append(instance)

        # Filter results based on parameters
        if only_print_legacy:
            instances_list = instances_list_legacy
        else:
            instances_list = instances_list_legacy + instances_list_new

        if only_return_list:
            return True, instances_list

        if only_return_legacy_list:
            return True, instances_list_legacy

        # Display the instances in rows
        row_count = 0
        max_per_row = getattr(Base, "MaxInstancesPerRow", 20)  # Default to 5 if not defined

        if max_per_row <= 0:  # Handle invalid configurations
            max_per_row = 5

        if not len(instances_list) == 0:
            for name in instances_list:
                if row_count >= max_per_row:
                    print("\n", end='')  # New line after max instances per row
                    row_count = 0
                print(f"{name}", end='')
                print(" | ", end='', color='blue')
                row_count += 1
            print("")
        else:
            if without_drop_no_instance_error:
                print("[You are looking to the null space]", color='darkwhite')
                return True, "NoInstancesAreAvailable"
            else:
                return False, "NoInstancesAreAvailable"
        return True, instances_list

    def select_instance(self, Message, **kwargs):
        """
        Return Status(True, False), Instance_Client_Version(if it found client_version in kwargs), Instance_Path
        """
        client_version = kwargs.get('client_version', False)
        only_print_legacy = kwargs.get('only_print_legacy', False)
        # If Status return True, Message will be instance_list
        if only_print_legacy:
            Status, instance_list = self.instance_list(only_print_legacy=True)
        else:
            Status, instance_list = self.instance_list()

        if not Status:
            print(f"Failed to get instance list. Cause by error {instance_list}", color='red')
            return False, Message, None

        while True:
            print(f"{Message}", color='blue')
            instance_name = str(input(":"))
            if instance_name.upper() == "EXIT":
                return "EXIT", None, None
            instance_path = os.path.join(Base.launcher_instances_dir, instance_name)
            instance_info = os.path.join(Base.launcher_instances_dir, instance_name, "instance.bakelh.ini")
            if instance_name in instance_list:
                if not client_version:
                    return True, instance_path, "NoUsage"

                Status, client_version = instance.get_instance_info(instance_info, info_name='client_version',
                                                                    ignore_not_found=True)

                # For old structure instances
                if not Status:
                    # Old structure instances(legacy part)
                    return True, instance_name, instance_path
                else:
                    # New structure instances
                    return True, client_version, instance_path
            else:
                print(f"Type instance name {instance_name} are not found :(", color='red')

    def load_custom_config(self, custom_config_path, item, item_name):
        # Check if the config file exists; create if not
        if not os.path.exists(custom_config_path):
            instance.create_custom_config(custom_config_path)

        # Read and process the config file
        found = False
        with open(custom_config_path, 'r') as config_file:
            for line in config_file:
                if line.startswith(item + "="):
                    value = line.split('=', 1)[1].strip()
                    if value:
                        print(f"Found existing {item_name}:\n {value}")
                        found = True
                        break  # Exit loop once the item is found

    def legacy_instances_convert(self, **kwargs):
        """
        This function will be deleted in the next update.
        """

        def convert_process(instance_name, client_version, version_type, java_major_version, main_class):
            # Convert instance to new structure
            print("Converting to new structure...", color='green')
            instance.create_instance_info(
                instance_name=instance_name,
                client_version=client_version,
                version_type=version_type,
                is_vanilla=True,
                modify_status=False,
                mod_loader_name=None,
                mod_loader_version=None,
                convert_by_legacy=True,
                java_major_version=java_major_version,
                main_class=main_class
            )
            print("Conversion completed successfully :)", color='blue')

        automatic_convert = kwargs.get('automatic_convert', False)

        if not automatic_convert:
            instances_list = os.listdir(Base.launcher_instances_dir)

            # Selecting an instance
            Status, self.CLIENT_VERSION, instance_path_old = self.select_instance(
                "Select an instance to convert to the new structure.",
                client_version=True,
                only_print_legacy=True,
            )

            if not Status:
                print("Failed to convert instance to new structure :( Caused by invalid instance return.")
                return "FailedToConvertInstance"

            if Status == "EXIT":
                print("Exiting...", color='green')
                return

            version_type = instance.get_instance_type(self.CLIENT_VERSION)

            # Asking for renaming
            print("Do you want to rename it? Y/N: ", end="")
            user_input = input().strip().upper()

            if user_input == "Y":
                while True:  # Loop until valid name is provided
                    print(f"Enter new name for this instance ({self.CLIENT_VERSION}): ", color='green')
                    self.name = input(":").strip()

                    if self.name in instances_list:
                        print(f"An instance with the name '{self.name}' already exists!")
                        continue

                    try:
                        # Attempt renaming
                        os.rename(
                            os.path.join(Base.launcher_instances_dir, self.CLIENT_VERSION),
                            os.path.join(Base.launcher_instances_dir, self.name),
                        )
                        self.instance_path = os.path.join(Base.launcher_instances_dir, self.name)
                        break  # Exit loop on success
                    except Exception as e:
                        print(f"Failed to rename instance. Error: {e}", color='red')
                        print("Ensure the name is valid and not restricted by your system.", color='red')
            else:
                print("Bypassed rename process.", color='green')
                self.instance_path = instance_path_old
                self.name = self.CLIENT_VERSION
            print(f"Convert instance name {self.name}...", color='green')
            instance_path = os.path.join(Base.launcher_instances_dir, self.name)
            legacy_libraries_path = os.path.join(instance_path, "libraries")
            legacy_client_path = os.path.join(instance_path, "client.jar")
            game_folder = os.path.join(instance_path, ".minecraft")
            new_client_path = os.path.join(game_folder, "libraries", "net", "minecraft", self.name)
            if os.path.exists(legacy_libraries_path):
                print("Found legacy libraries. Moving to new folder...", color='green')
                shutil.move(legacy_libraries_path, game_folder)

            if os.path.exists(legacy_client_path):
                target_dir = os.path.dirname(new_client_path)
                os.makedirs(target_dir, exist_ok=True)
                print("Found legacy client. Moving to new folder...", color='green')
                try:
                    # Move the file
                    shutil.move(legacy_client_path, new_client_path)
                    print(f"Moved client.jar to {new_client_path}", color='green')
                except Exception as e:
                    print(f"Failed to move client.jar. Error: {e}", color='red')

            version_data = get_version_data(self.CLIENT_VERSION)
            component, major_version = Duke.get_java_version_info(version_data)
            main_class = find_main_class(self.name)
            convert_process(self.name, self.CLIENT_VERSION, version_type, major_version, main_class)

        else:
            print("This method does not support renaming instances!", color='red')
            print(f"Searching legacy instances in dir {Base.launcher_instances_dir}...")
            try:
                Status, instances_list_legacy = self.instance_list(only_return_legacy_list=True)
                if len(instances_list_legacy) == 0:
                    print("No instances legacy found :(", color='red')
                    time.sleep(2)
                    return

                if not Status:
                    print(
                        f"Failed to convert all instances to new structure :( Caused by error {instances_list_legacy}",
                        color='red')
                    return "FailedToConvertInstance"
                for instance_name in instances_list_legacy:
                    print(f"Convert instance name {instance_name}...", color='green')
                    instance_path = os.path.join(Base.launcher_instances_dir, instance_name)
                    legacy_libraries_path = os.path.join(instance_path, "libraries")
                    legacy_client_path = os.path.join(instance_path, "client.jar")
                    game_folder = os.path.join(instance_path, ".minecraft")
                    new_client_path = os.path.join(game_folder, "libraries", "net", "minecraft", instance_name)
                    if os.path.exists(legacy_libraries_path):
                        print("Found legacy libraries. Moving to new folder...", color='green')
                        shutil.move(legacy_libraries_path, game_folder)

                    if os.path.exists(legacy_client_path):
                        os.makedirs(new_client_path, exist_ok=True)
                        print("Found legacy client. Moving to new folder...", color='green')
                        try:
                            # Move the file
                            shutil.move(legacy_client_path, new_client_path)
                            print(f"Moved client.jar to {new_client_path}", color='green')
                        except Exception as e:
                            print(f"Failed to move client.jar. Error: {e}", color='red')

                    version_type = instance.get_instance_type(instance_name)
                    version_data = get_version_data(instance_name)
                    component, major_version = Duke.get_java_version_info(version_data)
                    main_class = find_main_class(instance_name)
                    convert_process(instance_name, instance_name, version_type, major_version, main_class)
            except Exception as e:
                print(f"Error Message {e}", color='red')

    def print_instance_info(self):
        Status, client_version, instance_path = self.select_instance("Choose an instance to print info :"
                                                                     , client_version=True)
        if not Status:
            return

        instance_info = os.path.join(instance_path, "instance.bakelh.ini")
        if not os.path.exists(instance_info):
            print("Could not get instance info. Are you using legacy instance?", color='red')
            time.sleep(4)
            return

        Status, instance_name = instance.get_instance_info(instance_info, info_name="instance_name")
        if not Status:
            print("Failed to get instance name :(", color='red')

        Status, support_java_version = instance.get_instance_info(instance_info, info_name="support_java_version")
        if not Status:
            print("Failed to get support java version :(", color='red')

        Status, version_type = instance.get_instance_info(instance_info, info_name="type")
        if not Status:
            print("Failed to get version type :(", color='red')

        Status, created_by_launcher_version = instance.get_instance_info(instance_info, info_name="launcher_version")
        if not Status:
            print("Failed to get launcher version :(", color='red')

        Status, instance_format = instance.get_instance_info(instance_info, info_name="instance_format")
        if not Status:
            print("Failed to get instance format :(", color='red')

        Status, create_date = instance.get_instance_info(instance_info, info_name="create_date")
        if not Status:
            print("Failed to get create date :(", color='red')

        Status, create_date = instance.get_instance_info(instance_info, info_name="convert_by_legacy")
        if not Status:
            print("Failed to get convert by legacy status :(", color='red')

        Status, real_minecraft_version = instance.get_instance_info(instance_info, info_name="real_minecraft_version")
        if not Status:
            print("Failed to get real minecraft version :(", color='red')

        Status, use_legacy_manifest = instance.get_instance_info(instance_info, info_name="use_legacy_manifest")
        if not Status:
            print("Failed to get use legacy manifest status :(", color='red')

        Status, game_folder = instance.get_instance_info(instance_info, info_name="game_folder")
        if not Status:
            print("Failed to get game folder :(", color='red')

        Status, assets_folder = instance.get_instance_info(instance_info, info_name="assets_folder")
        if not Status:
            print("Failed to get assets folder :(", color='red')

        Status, IsVanilla = instance.get_instance_info(instance_info, info_name="IsVanilla")
        if not Status:
            print("Failed to get IsVanila status :(", color='red')

        Status, Modified = instance.get_instance_info(instance_info, info_name="Modified")
        if not Status:
            print("Failed to get modified status :(", color='red')

        Status, ModLoaderName = instance.get_instance_info(instance_info, info_name="ModLoaderName")
        if not Status:
            print("Failed to get ModLoaderName :(", color='red')

        Status, ModLoaderVersion = instance.get_instance_info(instance_info, info_name="ModLoaderVersion")
        if not Status:
            print("Failed to get ModLoaderVersion :(", color='red')

        Status, EnableConfig = instance.get_instance_info(instance_info, info_name="EnableConfig")
        if not Status:
            print("Failed to get EnableConfig status :(", color='red')

        Status, CFGPath = instance.get_instance_info(instance_info, info_name="CFGPath")
        if not Status:
            print("Failed to get CFGPath :(", color='red')

        print("Instance Info")
        print(f"Instance Name : {instance_name}", color='green')
        print(f"Minecraft Version : {client_version}")
        print(f"Support Java Version : {support_java_version}")
        print(f"Version Type : {version_type}")
        print(f"Created By Launcher Version : {created_by_launcher_version}")
        print(f"Create Date : {create_date}")
        print(f"Convert By Legacy? : {use_legacy_manifest}")
        print(f"Real Minecraft Version : {real_minecraft_version}", color='red')
        print(f"Use Legacy Manifest : {use_legacy_manifest}", color='indigo')
        print(f"")
        print(f"# Instance Structure")
        print(f"Game Folder : {game_folder}", color='lightyellow')
        print(f"Assets Folder : {assets_folder}", color='lightmagenta')
        print("")
        print("# Modify Info")
        print(f"IsVanilla : {IsVanilla}", color='green')
        if not IsVanilla:
            print(f"Modified: {Modified}", color='purple')
            print(f"ModLoaderName: {ModLoaderName}", color='purple')
            print(f"ModLoaderVersion: {ModLoaderVersion}", color='purple')
        print("")
        print("# Config Info")
        print(f"EnableConfig: {EnableConfig}")
        print(f"CFGPath : {CFGPath}")
        print("Press enter to exit...", color='green')
        input("")

    def uninstall_instance(self):
        # Get instance path
        Status, client_version, instance_path = self.select_instance(
            "Which instance is you want to uninstall?", client_version=True)

        if not Status or instance_path is None:
            return

        # Get instance info
        instance_info = os.path.join(instance_path, "instance.bakelh.ini")
        Status, instance_name = instance.get_instance_info(instance_info, info_name="instance_name")
        Status, use_legacy_manifest = instance.get_instance_info(instance_info, info_name="use_legacy_manifest")

        if use_legacy_manifest:
            Status, minecraft_version = instance.get_instance_info(instance_info, info_name="real_minecraft_version")
        else:
            Status, minecraft_version = instance.get_instance_info(instance_info, info_name="client_version")

        print(f"Uninstall Instance Name : {instance_name}", color='red')
        print(f"Minecraft Version : {minecraft_version}", color='green')
        user_input = str(input("Are you sure you want to uninstall it? (y/n) "))
        user_input = user_input.strip().lower()
        if user_input == "y":
            try:
                print("Uninstalling...", color='green')
                shutil.rmtree(instance_path)
                print("Instance uninstalled successfully!", color='blue')
                time.sleep(2)
            except Exception as e:
                print(f"Failed to uninstall the instance :( Cause by error {e}", color='red')
                time.sleep(5)
        return

    def rename_instance(self):
        # Select instance
        Status, client_version, instance_path = self.select_instance(
            "Choose an instance to print info:", client_version=True
        )
        if not Status:
            return

        # Get instance info
        instance_info = os.path.join(instance_path, "instance.bakelh.ini")
        Status, instance_name = instance.get_instance_info(instance_info, info_name="instance_name")
        if not Status:
            print("Could not find instance_name in the instance info :(", color='red')
            time.sleep(3)
            return

        # Prompt for new name
        while True:
            print("Give a new name for this instance (or type 'EXIT' to cancel):", end=' ', color='blue')
            new_name = input(":").strip()

            if new_name.upper() == "EXIT":
                print("Instance rename canceled.", color='yellow')
                return

            if not new_name:
                print("Please enter a valid name. Name cannot be empty or spaces only.", color='red')
                continue

            # Generate new instance path
            renamed_instance_path = os.path.join(Base.launcher_instances_dir, new_name)

            # Handle duplicate names
            if os.path.exists(renamed_instance_path):
                counter = 2
                while os.path.exists(renamed_instance_path):
                    renamed_instance_path = os.path.join(Base.launcher_instances_dir, f"{new_name}({counter})")
                    counter += 1

                print(f'Instance name "{new_name}" already exists.')
                print(f'Do you want to rename it to "{os.path.basename(renamed_instance_path)}"? (Y/N):', end=' ',
                      color='yellow')
                user_input = input(":").strip().upper()

                if user_input == "Y":
                    new_name = os.path.basename(renamed_instance_path)
                else:
                    print("Please choose a different name.", color='red')
                    continue
            break

        # Perform the renaming
        print("Starting rename process...", color='green')
        try:
            new_instance_path = os.path.join(Base.launcher_instances_dir, new_name)
            os.rename(instance_path, new_instance_path)  # Use paths, not names
            instance.write_instance_info("instance_name", new_name, instance_info)
        except Exception as e:
            print(f"Failed to rename instance :( Cause by error {e}")
            time.sleep(3)
        else:
            print("Rename process finished!", color='blue')
            time.sleep(1.5)

    def launcher_instance_status(self):
        print("Launcher Instance Status")
        print(f"Launcher Version : {Base.launcher_version}")
        print(f"Format : {Base.launcher_data_format}", color='lightgreen')
        print(f"Instances Dir : {Base.launcher_instances_dir}")

        # Get instance list length
        Status, instance_list = self.instance_list(only_return_list=True)
        if not Status:
            print("Failed to get instance list :(", color='red')
            time.sleep(2)
            return

        Status, legacy_instance_list = self.instance_list(only_return_legacy_list=True)
        if not Status:
            print("Failed to get legacy instance list :(", color='red')
            time.sleep(2)
            return

        # Get instance length
        full_instance_length = len(instance_list)
        legacy_instance_length = len(legacy_instance_list)
        new_instance_length = full_instance_length - legacy_instance_length

        print("Available Instance Length : ", new_instance_length, color='green')
        print("Legacy Format Instance Length : ", legacy_instance_length, color='yellow')
        print("Modern Instance Length : ", new_instance_length, color='blue')
        if legacy_instance_length > 0:
            print("=========================================================================================")
            print("Warning: You have legacy format instances in your instances list.", color='yellow')
            print("Legacy instance support is about to be removed in new version.", color='red')
            print("If you still want to play them in the future. Go to '5: Extra > 5: Convert Old Instance Structure'"
                  " to convert it to new format.", color='yellow')
            print("Use '5: Extra > 6: Auto-Convert Old Instance Structure' can automatically convert"
                  " all legacy instance :)", color='blue')

        print("")
        print("Press enter to exit...", color='green')
        input("")
        return

    def ManagerMemu(self):
        try:
            print("[Instance Manager]", color='orange')
            print("1: Print Instance Info")
            print("2: Uninstall Instance")
            print("3: Rename Instance")
            print("4: Launcher Instance Status")

            user_input = str(input(":"))
            user_input = user_input.strip()

            if user_input == "1":
                self.print_instance_info()
            elif user_input == "2":
                self.uninstall_instance()
            elif user_input == "3":
                self.rename_instance()
            elif user_input == "4":
                self.launcher_instance_status()
            elif user_input == "exit":
                return
            else:
                print(f"Unknown option {user_input} :(", color='red')
                time.sleep(2)
                self.ManagerMemu()

            return

        except Exception as e:
            if Exception is ValueError:
                # Back to main avoid crash(when user type illegal thing)
                print("BakeLaunch: Oops! Invalid option :O  Please enter a number.", color='red')
                self.ManagerMemu()
                time.sleep(1.5)
            else:
                print(f"Instance Manager got a error when calling a internal functions. Error: {e}", color='red')
                function_name = traceback.extract_tb(e.__traceback__)[-1].name
                detailed_traceback = traceback.format_exc()
                internal_functions_error_log_dump(e, "Instance Manager", function_name, detailed_traceback)
                time.sleep(5)


instance_manager = InstanceManager()
