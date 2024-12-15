import os
import time
from libs.instance.instance import instance
from LauncherBase import Base, print_color as print


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
        This method will be deleted in the next update.
        """

        def convert_process(instance_name, client_version, version_type):
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

            convert_process(self.name, self.CLIENT_VERSION, version_type)

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
                    version_type = instance.get_instance_type(instance_name)
                    convert_process(instance_name, instance_name, version_type)
            except Exception as e:
                print(f"Error Message {e}", color='red')


instance_manager = InstanceManager()
