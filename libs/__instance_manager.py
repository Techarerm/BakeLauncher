import json
import os
import time
from LauncherBase import Base, print_color as print
import requests
from datetime import datetime
import textwrap


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

    def get_instance_type(self, minecraft_version):
        response = requests.get(self.VersionManifestURl)
        data = response.json()

        # Search for the specific version
        version_info = next((v for v in data['versions'] if v['id'] == minecraft_version), None)

        # Display the type if found
        if version_info:
            return version_info['type']
        else:
            return None

    @staticmethod
    def create_custom_config(config_file_path):
        print("Creating custom config...", color='green')
        default_data = textwrap.dedent("""\
        [BakeLauncher Instance Custom Config]
        
        ModLoaderClass =
        CustomJVMArgs = 
        MemoryJVMArgs = 
        CustomGameArgs = 
        InjectJARFile = 
        InjectJARPath = 

        """)
        with open(config_file_path, 'w') as config_file:
            config_file.write(default_data)

    @staticmethod
    def read_custom_config(config_file_path, item):
        with open(config_file_path, "r") as file:  # Open the file in read mode
            lines = file.readlines()  # Read all lines into a list

        for line in lines:
            line = line.strip()  # Strip leading/trailing whitespace and newline characters
            # Check if the item is in the line and the line contains '=' (key-value pair)
            if item in line and '=' in line:
                # Split the line at '=' and get the value part, then strip any extra spaces
                data = line.split('=')[1].strip()  # Strip again in case there are spaces around the value
                return data  # Return the cleaned data

        return None  # Return None if the item is not found

    @staticmethod
    def write_custom_config(custom_config_path, item, data):
        global custom_item
        item = str(item)
        if item.lower() == "jvmargs":
            custom_item = "CustomJVMArgs"
        elif item.lower() == "gameargs":
            custom_item = "CustomGameArgs"
        elif item.lower() == "injectjarpath":
            custom_item = "InjectJARPath"
        elif item.lower() == "modloderclass":
            custom_item = "ModLoaderClass"
        elif item.lower() == "memoryjvmargs":
            custom_item = "MemoryJVMArgs"

        with open(custom_config_path, 'r') as file:
            lines = file.readlines()
            for i in range(len(lines)):
                if custom_item in lines[i]:
                    # Use the new or existing account ID
                    lines[i] = f'{custom_item} = {data}\n'
                    found = True
        with open(custom_config_path, 'w') as file:
            file.writelines(lines)
        if found:
            return True
        else:
            return False

    @staticmethod
    def write_instance_info(item_name, new_data, instance_info_path):
        if not os.path.exists(instance_info_path):
            return False

        found = False
        try:
            with open(instance_info_path, 'r') as file:
                lines = file.readlines()

            # Look for the item_name in the lines and update its value
            for i in range(len(lines)):
                if item_name in lines[i]:
                    if isinstance(new_data, bool):
                        lines[i] = f'{item_name} = {str(new_data).lower()}\n'
                    else:
                        lines[i] = f'{item_name} = "{new_data}"\n'
                    found = True
                    break  # Exit the loop once we've made the change

            # Write info file
            if found:
                with open(instance_info_path, 'w') as file:
                    file.writelines(lines)

        except (IOError, OSError) as e:  # Handle general file errors
            print(f"Error: {e}")
            return False

        return found

    def create_instance_info(self, instance_name, client_version, version_type, is_vanilla, modify_status,
                             mod_loader_name, mod_loader_version, **kwargs):

        # Setting some path and create date
        selected_instance_dir = os.path.join(Base.launcher_instances_dir, instance_name)
        selected_instance_ini = os.path.join(selected_instance_dir, "instance.bakelh.ini")
        create_date = datetime.now()
        print("Instance Info Path: ", selected_instance_ini, color='green', tag='DEBUG')
        print("Instance Dir: ", selected_instance_dir, color='green', tag='DEBUG')

        # Check selected_instance_dir status
        if not os.path.exists(selected_instance_dir):
            os.makedirs(selected_instance_dir)
        else:
            self.SelectedInstanceInstalled = True

        # Get kwargs

        # If user using method name "Convert Old Instance Structure" to upgrade instance to new structure, set it to
        # True
        convert_by_legacy = kwargs.get('convert_by_legacy', False)

        # If create instance info version is legacy_version Minecraft,
        use_legacy_manifest = kwargs.get('use_legacy_manifest', False)

        # "REAL" version(a reason for not using client_version to get Minecraft version is Legacy Minecraft instance
        # info client_version is spoof version(check create_instance>version_spoof)
        real_minecraft_version = kwargs.get('real_minecraft_version', client_version)

        # Get java major version
        java_major_version = kwargs.get('java_major_version', None)

        # Avoid to overwrite old data
        if os.path.exists(selected_instance_ini):
            print("Could not create new instance info. Cause by instance info already exists.", tag_color='red',
                  tag='Warning')
            return True

        instance_info = textwrap.dedent(f"""\
            # BakeLauncher Instance Info
            # This configuration stores instance data for the launcher (e.g., instance_name, client_version).
            # Do NOT edit this file or delete it!

            # Instance Info
            instance_name = "{instance_name}"
            client_version = "{client_version}"
            support_java_version = "{java_major_version}"
            type = "{version_type}"
            launcher_version = "{Base.launcher_internal_version}"
            instance_format = "{Base.launcher_data_format}"
            create_date = "{create_date}"
            convert_by_legacy = {convert_by_legacy}
            # If your real_minecraft_version is not same as client_version. Maybe you are using a unofficial source Minecraft
            real_minecraft_version = "{real_minecraft_version}"
            use_legacy_manifest = {use_legacy_manifest}

            # Instance Structure
            game_folder = ".minecraft"  # Path to the main game folder
            assets_folder = ".minecraft/assets"  # Path to the assets folder

            # Modify Info
            IsVanilla = {is_vanilla}
            Modified = {modify_status}
            ModLoaderName = {mod_loader_name}
            ModLoaderVersion = {mod_loader_version}

            # Config
            EnableConfig = True
            CFGPath = "instance.bakelh.cfg"
        """)

        with open(selected_instance_ini, "w+") as ini_file:
            ini_file.write(instance_info)

    def load_custom_config(self, custom_config_path, item, item_name):
        # Check if the config file exists; create if not
        if not os.path.exists(custom_config_path):
            self.create_custom_config(custom_config_path)

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

    def get_instance_info(self, instance_info_path, **kwargs):
        """
        Args list:
        instance_info_path: Path to the instance info file.
        info_name: Get selected instance information data(not found return False and None)
        # If info_name is not found return True, {All available data}...
        ignore_not_found: Legacy stuff(don't print instance info file not found error)
        """

        info_name = kwargs.get('info_name', None)
        ignore_not_found = kwargs.get('ignore_not_found')

        #
        if not os.path.exists(instance_info_path):
            if not ignore_not_found:
                print("Failed to get instance info. Cause by instance info file not found.")
                print("Maybe you are using a instance who create by old version BakeLauncher.")
                print("Please go to Extra>Convert Old Instance Structure")
                time.sleep(3)
            return False, None

        try:
            with open(instance_info_path, 'r') as file:
                for line in file:
                    # Strip whitespace and ignore comment lines
                    line = line.strip()
                    if line.startswith("instance_name"):
                        # Extract the value after the equals sign
                        key, value = line.split("=", 1)
                        self.INSTANCE_NAME = value.strip().strip('"').strip("'")

                    if line.startswith("client_version"):
                        # Extract the value after the equals sign
                        key, value = line.split("=", 1)
                        self.CLIENT_VERSION = value.strip().strip('"').strip("'")

                    if line.startswith("type"):
                        # Extract the value after the equals sign
                        key, value = line.split("=", 1)
                        self.VERSION_TYPE = value.strip().strip('"').strip("'")

                    if line.startswith("launcher_version"):
                        # Extract the value after the equals sign
                        key, value = line.split("=", 1)
                        self.LAUNCHER_VERSION = value.strip().strip('"').strip("'")

                    if line.startswith("instance_format"):
                        # Extract the value after the equals sign
                        key, value = line.split("=", 1)
                        self.INSTANCE_FORMAT = value.strip().strip('"').strip("'")

                    if line.startswith("create_date"):
                        # Extract the value after the equals sign
                        key, value = line.split("=", 1)
                        self.CREATE_DATE = value.strip().strip('"').strip("'")

                    if line.startswith("real_minecraft_version"):
                        # Extract the value after the equals sign
                        key, value = line.split("=", 1)
                        self.real_minecraft_version = value.strip().strip('"').strip("'")
                        self.real_minecraft_version = self.real_minecraft_version.strip("'").strip("'")

                    if line.startswith("use_legacy_manifest"):
                        # Extract the value after the equals sign
                        self.use_legacy_manifest = line.split('=')[1].strip().upper() == "TRUE"

                    if line.startswith("IsVanilla"):
                        # Extract the value after the equals sign
                        self.use_legacy_manifest = line.split('=')[1].strip().upper() == "TRUE"

                    if line.startswith("Modified"):
                        # Extract the value after the equals sign
                        self.use_legacy_manifest = line.split('=')[1].strip().upper() == "TRUE"

                    if line.startswith("ModLoaderName"):
                        # Extract the value after the equals sign
                        key, value = line.split("=", 1)
                        self.CREATE_DATE = value.strip().strip('"').strip("'")

                    if line.startswith("ModLoaderVersion"):
                        # Extract the value after the equals sign
                        key, value = line.split("=", 1)
                        self.CREATE_DATE = value.strip().strip('"').strip("'")

        except Exception as e:
            print(f"Error reading file: {e}")
            print("Maybe you are using a instance who create by old version BakeLauncher.")
            print("Please go to Extra>Convert Old Instance Structure to convert instance to new structure.")
            time.sleep(3)
            return False, None

        info_list = [self.INSTANCE_NAME, self.CLIENT_VERSION, self.VERSION_TYPE, self.LAUNCHER_VERSION,
                     self.INSTANCE_FORMAT, self.CREATE_DATE]

        if info_name is None:
            for info in info_list:
                if info is None:
                    print(f"Warning: info name {info} is None", color='yellow')
        else:
            if info_name == "instance_name":
                return True, self.INSTANCE_NAME
            elif info_name == "client_version":
                return True, self.CLIENT_VERSION
            elif info_name == "type":
                return True, self.VERSION_TYPE
            elif info_name == "launcher_version":
                return True, self.LAUNCHER_VERSION
            elif info_name == "instance_format":
                return True, self.INSTANCE_FORMAT
            elif info_name == "create_date":
                return True, self.CREATE_DATE
            elif info_name == "use_legacy_manifest":
                return True, self.use_legacy_manifest
            elif info_name == "real_minecraft_version":
                return True, self.real_minecraft_version
            else:
                return False, "UnknownArgs"

        return (True, self.INSTANCE_NAME, self.CLIENT_VERSION, self.VERSION_TYPE, self.LAUNCHER_VERSION,
                self.INSTANCE_FORMAT, self.CREATE_DATE)

    @staticmethod
    def instance_list(**kwargs):
        only_print_legacy = kwargs.get('only_print_legacy', False)
        only_return_list = kwargs.get('only_return_list', False)
        only_return_legacy_list = kwargs.get('only_return_legacy_list', False)
        instances_list_original = os.listdir(Base.launcher_instances_dir)

        if not instances_list_original:
            print("No instances are available.", color='red')
            print("Go to step 3: Create Instance. After it's installed, you can try this method again!", color='yellow')
            return False, "NoInstancesAreAvailable"

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

        for name in instances_list:
            if row_count >= max_per_row:
                print("\n", end='')  # New line after max instances per row
                row_count = 0
            print(f"{name}", end='')
            print(" | ", end='', color='blue')
            row_count += 1
        print("")
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

                Status, client_version = self.get_instance_info(instance_info, info_name='client_version',
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

    def legacy_instances_convert(self, **kwargs):
        """
        This method will be deleted in the next update.
        """

        def convert_process(instance_name, client_version, version_type):
            # Convert instance to new structure
            print("Converting to new structure...", color='green')
            instance_manager.create_instance_info(
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

            version_type = self.get_instance_type(self.CLIENT_VERSION)

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
                    version_type = self.get_instance_type(instance_name)
                    convert_process(instance_name, instance_name, version_type)
            except Exception as e:
                print(f"Error Message {e}", color='red')

instance_manager = InstanceManager()
