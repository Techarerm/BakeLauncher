import os
import shutil
import time
import unicodedata
from json import JSONDecodeError
from LauncherBase import Base, print_custom as print
from libs.__assets_grabber import assets_grabber
from libs.__duke_explorer import Duke
from libs.__account_manager import account_manager
from libs.launch_client import LaunchClient
from libs.__instance_manager import instance_manager
from libs.Utils.utils import get_version_data, find_main_class
from libs.Utils.libraries import generate_libraries_paths
from libs.instance.instance import instance


class LauncherManager:
    def __init__(self):
        self.instance_name = None

    def generate_jvm_args(self, client_version, **kwargs):
        """
        Generate JVM arguments(Only generate require args)
        (About argument "-Djava.library.path=", check launch_client for more information :)
        """
        without_ram_args = kwargs.get("without_ram_args", False)

        # Grabbing args list(Added saved arguments process)
        if os.path.exists("launch.data"):
            with open("launch.data", "r") as data:
                jvm_args_list = next((line.split('=')[1].strip() for line in data if "JVMArgsList" in line), None)
        else:
            jvm_args_list = None

        if not jvm_args_list:
            version_data = get_version_data(client_version)
            jvm_args_list = version_data.get("arguments", {}).get("jvm", [])
            found = False

            if os.path.exists("launch.data"):
                with open("launch.data", "r") as data:
                    lines = data.readlines()

                with open("launch.data", "w") as data:
                    for line in lines:
                        if "JVMArgsList" in line:
                            data.write(f"JVMArgsList={jvm_args_list}\n")
                            found = True
                        else:
                            data.write(line)

                    if not found:
                        data.write(f"JVMArgsList={jvm_args_list}\n")
            else:
                with open("launch.data", "w") as data:
                    data.write(f"JVMArgsList={jvm_args_list}\n")

        # Set Java Virtual Machine use Memory Size
        RAMSize_Args = fr"-Xms{Base.JVMUsageRamSizeMinLimit}m -Xmx{Base.JVMUsageRamSizeMax}m "

        OtherArgs = " "

        # Set this to prevent the windows too small
        Window_Size_Args = (f"-Dorg.lwjgl.opengl.Window.undecorated=false "
                            f"-Dorg.lwjgl.opengl.Display.width={Base.DefaultGameScreenWidth} "
                            f"-Dorg.lwjgl.opengl.Display.height={Base.DefaultGameScreenHeight} ")
        OtherArgs += Window_Size_Args

        if Base.Platform == "Windows":
            # JVM_Args_HeapDump(It will save heap dump when Minecraft Encountered OutOfMemoryError? "Only For Windows!")
            OtherArgs += "-XX:HeapDumpPath=MojangTricksIntelDriversForPerformance_javaw.exe_minecraft.exe.heapdump "
        elif Base.Platform == "Darwin":
            # Check whether the startup version of macOS requires the parameter "-XstartOnFirstThread" parameter
            # In LWJGL 3.x, macOS requires this args to make lwjgl running on the JVM starts with thread 0) (from wiki.vg)
            for jvm_entry in jvm_args_list:
                if not isinstance(jvm_entry, dict):  # Only process if it's a dictionary
                    continue
                rules = jvm_entry.get("rules", [])
                for rule in rules:
                    os_data = rule.get("os", {})
                    if not os_data.get("name") == "osx":  # Check if the OS is macOS
                        continue
                    value = jvm_entry.get("value", [])
                    if isinstance(value, list) and "-XstartOnFirstThread" in value:
                        OtherArgs += "-XstartOnFirstThread "

        if without_ram_args:
            return OtherArgs
        else:
            return RAMSize_Args, OtherArgs

    def generate_game_args(self, version_id, username, access_token, game_dir, assets_dir, assetsIndex, uuid, instance_path):
        global minecraftArguments, client_type
        # Fetch version data and arguments
        if not os.path.exists("launch.data"):
            version_data = get_version_data(version_id)
            minecraftArguments = version_data.get("minecraftArguments", "")
            with open("launch.data", "w") as data:
                data.write(f"minecraftArguments={minecraftArguments}")
        else:
            with open("launch.data", "r") as data:
                for line in data:
                    if "minecraftArguments" in line:
                        minecraftArguments = line.split('=')[1].strip()
                        break

        # Get client type
        instance_info = os.path.join(instance_path, "instance.bakelh.ini")
        if os.path.exists(instance_info):
            Status, version_type = instance.get_instance_info(instance_info, info_name="type")
            client_type = version_type if version_type not in {None, "None"} else "default"
        else:
            version_data = get_version_data(version_id)
            client_type = version_data.get("type", "default")

        user_properties = "{}"
        user_type = "msa"  # Set user type to 'msa'

        if "--userProperties" in minecraftArguments:
            minecraft_args = f"--username {username} --version {version_id} --gameDir {game_dir} " \
                             f"--assetsDir {assets_dir} --assetIndex {assetsIndex} --accessToken {access_token} " \
                             f"--userProperties {user_properties}"

        elif client_type == "old-alpha":
            minecraft_args = f"{username} {access_token} --gameDir {game_dir} --assetsDir {assets_dir}"

        # Handle special case where ${auth_player_name} and ${auth_session} are at the beginning
        elif minecraftArguments.startswith("${auth_player_name} ${auth_session}"):
            # Prepend the username and access token as per the special case
            minecraft_args = f"{username} {access_token} --gameDir {game_dir} " \
                             f"--assetsDir {assets_dir} --assetIndex {assetsIndex}"

        elif minecraftArguments.endswith("${game_assets}"):
            minecraft_args = f"--username {username} --session {access_token} --version {version_id} --gameDir {game_dir} " \
                             f"--assetsDir {assets_dir} --assetIndex {assetsIndex}"

        elif minecraftArguments.startswith("--username") and minecraftArguments.endswith("${auth_access_token}"):
            minecraft_args = f"--username {username} --version {version_id} --gameDir {game_dir} " \
                             f"--assetsDir {assets_dir} --assetIndex {assetsIndex} --accessToken {access_token}"

        else:
            minecraft_args = f"--username {username} --version {version_id} --gameDir {game_dir} " \
                             f"--assetsDir {assets_dir} --assetIndex {assetsIndex} --uuid {uuid} " \
                             f"--accessToken {access_token} --userType {user_type}"

        if "AlphaVanillaTweaker" in minecraftArguments or client_type in ["classic", "infdev", "indev", "alpha"]:
            minecraft_args += " --tweakClass net.minecraft.launchwrapper.AlphaVanillaTweaker"

        return minecraft_args

    def launch_game(self, **kwargs):
        global JVMArgs, CustomRAMArgs, JavaPath, LegacyFlag, main_class
        QuickLaunch = kwargs.get("QuickLaunch", False)

        # Check folder "versions" are available in root (To avoid some user forgot to install)
        if not os.path.exists("instances"):
            os.makedirs("instances")

        # Get instances list and check it
        instances_list = os.listdir('instances')

        if not QuickLaunch:
            if len(instances_list) == 0:
                print("No instances are available to launch :(", color='red')
                print("You can use create instance to create a new instance for you :)", color='blue')
                time.sleep(4)
                return "NoInstancesAreAvailable"

            # Ask user want to launch instances...
            Status, Message = instance_manager.instance_list()
            if not Status:
                return Message
            print("Which instances do you want to launch?")
            self.instance_name = input(":")

            # Ignore some spaces on start or end of the name
            self.instance_name = self.instance_name.strip()
            if str(self.instance_name).upper() == "EXIT":
                return
        else:
            self.instance_name = Base.QuickInstancesName

        # Check user type instances are available
        if self.instance_name not in instances_list:
            print("Can't found instances " + self.instance_name + " of Minecraft :(", color='red')
            print("Please check you type instances version are available on the list.")
            print("If you think game files are corrupted."
                  " Just re-download it(Your world won't be delete when re-download Minecraft).")
            time.sleep(2.2)
            return "TypeInstanceAreNotFound"
        else:
            instance_dir = os.path.join(Base.launcher_instances_dir, self.instance_name)
            print("Preparing to launch.....", color='c')

        if not Base.InternetConnected:
            print("Warning: Internet is not connected.", color='red')
            print("If the instance is never started in a networked environment."
                  " The launcher may crash when preparing some process.", color='red')

        # Get instance's Minecraft version
        instance_info_path = os.path.join(Base.launcher_instances_dir, self.instance_name, "instance.bakelh.ini")
        InfoStatus, use_legacy_manifest = instance.get_instance_info(instance_info_path,
                                                                     info_name="use_legacy_manifest",
                                                                     ignore_not_found=True)

        if use_legacy_manifest:
            InfoStatus, minecraft_version = instance.get_instance_info(instance_info_path,
                                                                       info_name="real_minecraft_version",
                                                                       ignore_not_found=True)
        else:
            InfoStatus, minecraft_version = instance.get_instance_info(instance_info_path,
                                                                       info_name="client_version",
                                                                       ignore_not_found=True)
        if not InfoStatus:
            LegacyFlag = True
            print("Warning: You are trying to launch a who built with an older version of BakeLauncher.",
                  color='yellow')
            print("Old instances support will be drop soon. ", end='', color='red')
            print("Please go to Extra>Convert Old Instance Structure to convert instance to new structure.",
                  color='red')
            minecraft_version = self.instance_name
        else:
            LegacyFlag = False
        # Get required Java version path
        if os.path.isfile('data/Java_HOME.json'):
            print("Found exist Java Path config!", color='blue')
        else:
            print("Can't find exist Java Path config :(", color='red')
            print("Want create it now ? Y/N", color='green')
            user_input = input(":")
            if user_input.upper() == "Y":
                print("Calling duke...")
                os.chdir(Base.launcher_root_dir)
                Duke.duke_finder()
            else:
                return "JVMConfigAreNotFound"

        print("Getting JVM Path...", color='c')
        Status, major_version = instance.get_instance_info(instance_info_path, info_name="support_java_version")
        if not LegacyFlag:
            if major_version is None or not major_version == "None":
                JavaPath = Duke.java_version_check(minecraft_version, java_version=major_version)
            else:
                if Base.InternetConnected:
                    JavaPath = Duke.java_version_check(minecraft_version)
                else:
                    print("Failed to get support java version :( No internet connection.", color='red')
        else:
            JavaPath = Duke.java_version_check(minecraft_version)

        # Check JavaPath is valid
        if JavaPath is None:
            print("Get JavaPath failed! Cause by None path!", color='red')
            print("Try 4: Extra>7: Search Java Runtimes(Duke) to create JavaConfig.", color='green')
            print("If you still get the error when launching Minecraft. Go to '3: Create Instance>4: Reinstall "
                  "instance' to reinstall it.", color='indigo')
            time.sleep(4)
            return "FailedToCheckJavaPath"

        if not os.path.exists(JavaPath):
            print("The selected version of Java runtime folder does not exist :(", color='red')
            print("Go to '3: Create Instance>4: Reinstall instance' to reinstall it.", color='yellow')
            time.sleep(2.5)
            return "JavaRuntimePathDoesNotExist"
        # After get JVMPath(bin), Get PlatformName and set the actual required Java Virtual Machine Path
        if Base.Platform == 'Windows':
            java_executable = "java.exe"
        else:
            java_executable = "java"

        # Full path to the Java executable
        java_executable_path = os.path.join(JavaPath, java_executable)

        # Check if Java executable exists
        if os.path.isfile(java_executable_path):
            JVMPath = f'"{java_executable_path}"'  # Enclose in quotes for proper execution
        else:
            print("Error: Your Java executable is corrupted :(", color='red')
            print("Go to '3: Create Instance>4: Reinstall instance' to reinstall it.", color='yellow')
            time.sleep(2.5)
            return "JavaExecutableAreCorrupted"

        # Get access token and username, uuid to set game args
        print("Reading account data...", color='green')
        AccountIDStatus, account_id = account_manager.get_default_account_id()
        if not AccountIDStatus:
            print("Can't find account ID!", color='red')
            return "AccountIDNotFound"
        AccDataStatus, account_data = account_manager.get_account_data_use_account_id(account_id)
        if not AccDataStatus:
            print("Could not get account data!", color='red')
            return "GetAccountDataFailed"

        try:
            username = account_data['Username']
            access_token = account_data['AccessToken']
            uuid = account_data['UUID']
            if username == "Player" or username == "BakeLauncherLocalUser":
                print("Sorry :( You can't launch game without login in this version.", color='red')
                time.sleep(3)
                return "AccountDataInvalid"

        except JSONDecodeError or ValueError:
            print("Failed to launch Minecraft :( Cause by invalid AccountData", color='red')
            return

        # Sdt work path to instances gameDir
        gameDir = os.path.join(instance_dir, ".minecraft")
        old_libraries_path = os.path.join(instance_dir, "libraries")
        libraries_path = os.path.join(gameDir, "libraries")
        # Move libraries folder to .minecraft folder
        if not os.path.exists(libraries_path):
            if os.path.exists(old_libraries_path):
                shutil.move(old_libraries_path, gameDir)
            else:
                print("Library folder not found :( Please reinstall the instance.", color='red')
                time.sleep(3)
                return "LibrariesNotFound"

        if not os.path.exists(gameDir):
            print("Failed to launch Minecraft :( Cause by instance file are corrupted.", color='red')
            print("Please go to '3: Create Instance>4: Reinstall instance' to reinstall it.", color='yellow')
            time.sleep(2.5)
            return "GameDirDoesNotExist"
        else:
            os.chdir(gameDir)

        # Check natives are available to use
        print("Checking natives...", color='green')
        if os.path.isdir("natives"):
            if not len(os.listdir("natives")) == 0:
                print("Natives are available! (if it unzip correctly)", color='green')
            else:
                print("Natives are not available or it unzip not correctly :(", color='red')
                print("Please download now you launch instances version(it will recreate it)",
                      color='yellow')
                print("If you still get this error please report this issue to GitHub!", color='green')
                time.sleep(4)
                os.chdir(Base.launcher_root_dir)
                return "NativesAreNotAvailable"
        else:
            print("Natives are not available or it unzip not correctly :(", color='red')
            print("Please download now you launch instances version(it will recreate it)", color='yellow')
            print("If you still get this error please report this issue to GitHub!", color='green')
            time.sleep(4)
            os.chdir(Base.launcher_root_dir)
            return "NativesAreNotAvailable"

        # Set Natives Path
        NativesPath = "natives"

        # Get librariesPath(Example: /path/LWJGL-1.0.jar:/path/Hopper-1.2.jar:/path/client.jar)
        InjectJARPath = None
        legacy_client_path = os.path.join(instance_dir, "client.jar")
        if os.path.exists(legacy_client_path):
            print("Failed to launch Minecraft :( Did you convert it to new format?", color='red')
            time.sleep(3)
            return "ClientNotFound"
        libraries_paths_strings = generate_libraries_paths(minecraft_version, "libraries")
        # Inject jar file to launch chain
        # Get MainClass Name And Set Args(-cp "libraries":client.jar net.minecraft.client.main.Main or
        # net.minecraft.launchwrapper.Launch(old))
        if not LegacyFlag:
            Status, main_class = instance.get_instance_info(instance_info_path, info_name="main_class")
            if main_class is None or main_class == "None":
                main_class = find_main_class(minecraft_version)
        else:
            main_class = find_main_class(minecraft_version)

        print(f"Using {main_class} as the Main Class." ,color='blue')

        # Get assetsIndex and assets_dir
        assetsIndex = assets_grabber.get_assets_index_version(minecraft_version)
        if assetsIndex is None:
            print("Failed to get assets index version :(", color='red')
            time.sleep(3)
            return "FailedToGetAssetsIndexVer"

        assets_dir = assets_grabber.get_assets_dir(minecraft_version)

        # Get GameArgs
        GameArgs = self.generate_game_args(minecraft_version, username, access_token, gameDir, assets_dir, assetsIndex,
                                           uuid, instance_dir)

        # Now it available :)
        instance_custom_config = os.path.join(instance_dir, "instance.bakelh.cfg")
        if os.path.exists(instance_custom_config):
            print("Found instance config :D", color='blue')
            print('Loading custom config...', color='green')

            CustomJVMArgs = instance.read_custom_config(instance_custom_config, "CustomJVMArgs")

            CustomGameArgs = instance.read_custom_config(instance_custom_config, "CustomGameArgs")

            InjectJARPath = instance.read_custom_config(instance_custom_config, "InjectJARPath")

            ModLoaderClass = instance.read_custom_config(instance_custom_config, "ModLoaderClass")

            # Check if CustomJVMArgs(or CustomGameArgs) is None or has a length of 0 (ignoring spaces)
            if CustomJVMArgs is None or len(CustomJVMArgs.strip()) == 0:
                # print("CustomJVMArgs is empty or not provided, ignoring...", color='yellow')
                CustomJVMArgs = None

            if CustomGameArgs is None or len(CustomGameArgs.strip()) == 0:
                # print("CustomGameArgs is empty or not provided, ignoring...", color='yellow')
                CustomGameArgs = " "  # Replace Custom Args to a spaces(if is empty)

            if ModLoaderClass is None or len(ModLoaderClass.strip()) == 0:
                # print("ModLoaderClass is empty or not provided, ignoring...", color='yellow')
                ModLoaderClass = None  # Replace Custom Args to a spaces(if is empty)
            else:
                print(f"Found exist Mod Loader class: {ModLoaderClass}", color='indigo')
                print("Replacing Main Class to Mod Loader Class...", color='green')
                main_class = ModLoaderClass

        else:
            CustomGameArgs = " "
            CustomJVMArgs = None

        if InjectJARPath is not None:
            libraries_paths_strings += InjectJARPath

        # Config JVM Args
        RAM_Args, OtherArgs = self.generate_jvm_args(minecraft_version)
        if CustomJVMArgs is None:
            FinalArgs = RAM_Args + OtherArgs
        else:
            FinalArgs = CustomJVMArgs

        # Set instances_id(for multitasking process title)
        instances_id = f"Minecraft {minecraft_version}"

        # Bake Minecraft :)
        if Base.Platform == "Windows":
            LaunchClient(JVMPath, libraries_paths_strings, NativesPath, main_class, FinalArgs, GameArgs,
                         CustomGameArgs, instances_id, Base.EnableExperimentalMultitasking,
                         Base.LaunchMultiClientWithOutput)
        elif Base.Platform == "Darwin":
            LaunchClient(JVMPath, libraries_paths_strings, NativesPath, main_class,
                         FinalArgs, GameArgs,
                         CustomGameArgs, instances_id, Base.EnableExperimentalMultitasking,
                         Base.LaunchMultiClientWithOutput)
        elif Base.Platform == "Linux":
            LaunchClient(JVMPath, libraries_paths_strings, NativesPath, main_class, FinalArgs, GameArgs,
                         CustomGameArgs, instances_id, Base.EnableExperimentalMultitasking,
                         Base.LaunchMultiClientWithOutput)
        else:
            LaunchClient(JVMPath, libraries_paths_strings, NativesPath, main_class, FinalArgs, GameArgs,
                         CustomGameArgs, instances_id, Base.EnableExperimentalMultitasking,
                         Base.LaunchMultiClientWithOutput)

        os.chdir(Base.launcher_root_dir)
        time.sleep(2)


launch_manager = LauncherManager()
