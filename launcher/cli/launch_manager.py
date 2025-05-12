import shutil
import time
from json import JSONDecodeError
from LauncherBase import print_custom as print
from launcher.cli.__assets_grabber import assets_grabber
from launcher.cli.__duke_explorer import Duke
from launcher.cli.__account_manager import account_manager
from launcher.cli.launch.launch_client import launch_client
from launcher.cli.__instance_manager import instance_manager
from libs.Utils.config import config_loader
from libs.account.account_management import get_current_account_id, get_account_data_use_account_id
from libs.version.version import *
from libs.libraries.libraries import generate_classpath
from libs.instance.instance import instance
from libs.definition.data import *
from libs.clientlauncher.clauncher import client_launcher


class LauncherManager:
    def __init__(self):
        self.real_version = None
        self.minecraft_version = None
        self.instance_name = None
        self.instance_path = None

        self.AutomaticLaunch = False
        self.QuickLaunch = None
        self.QuickInstancesName = None

        self.max_instance_per_row = 20
        self.legacy_method = False
        self.create_log_output_window = True
        self.game_default_screen_height = 720
        self.game_default_screen_width = 1280
        self.jvm_ram_minimum_size = 2048
        self.jvm_ram_max_size = 4096
        self.quick_launch_target_instance_name = None
        self.settings_dict = {
            "INT%MaxInstancesPerRow": "max_instance_per_row",
            "BOOL%LegacyLaunchMethod": "legacy_method",
            "BOOL%LaunchClientWithOutput": "create_log_output_window",
            "INT%DefaultGameScreenHeight": "game_default_screen_height",
            "INT%DefaultGameScreenWidth": "game_default_screen_width",
            "INT%JVMUsageRamSizeMinLimit": "jvm_ram_minimum_size",
            "INT%JVMUsageRamSizeMax": "jvm_ram_max_size",
            "STR%QuickInstanceName": "quick_launch_target_instance_name",
        }

    def load_config(self):
        config_loader(self, self.settings_dict, Base.global_config_path)

    def generate_jvm_args(self, client_version, **kwargs):
        """
        Generate JVM arguments(Only generate require args)
        (About argument "-Djava.library.path=", check launch_client for more information :)
        """
        without_ram_args = kwargs.get("without_ram_args", False)
        append_args = kwargs.get("append_args", False)

        # Get version data
        version_data = get_version_data_from_exist_data(client_version)
        if version_data is None:
            version_data = get_version_data(client_version)

        jvm_args_data = version_data.get("arguments", {}).get("jvm", None)

        # Set Java Virtual Machine use Memory Size
        RAMSize_Args = fr"-Xms{self.jvm_ram_minimum_size}m -Xmx{self.jvm_ram_max_size}m "

        OtherArgs = " "

        # Set this to prevent the windows too small
        Window_Size_Args = (f"-Dorg.lwjgl.opengl.Window.undecorated=false "
                            f"-Dorg.lwjgl.opengl.Display.width={self.game_default_screen_width} "
                            f"-Dorg.lwjgl.opengl.Display.height={self.game_default_screen_height} ")
        OtherArgs += Window_Size_Args

        if Base.Platform == "Windows":
            # JVM_Args_HeapDump(It will save heap dump when Minecraft Encountered OutOfMemoryError? "Only For Windows!")
            OtherArgs += "-XX:HeapDumpPath=MojangTricksIntelDriversForPerformance_javaw.exe_minecraft.exe.heapdump "
        elif Base.Platform == "Darwin":
            # Check whether the startup version of macOS requires the parameter "-XstartOnFirstThread" parameter In
            # LWJGL 3.x, macOS requires this args to make lwjgl running on the JVM starts with thread 0) (from wiki.vg)
            if jvm_args_data is not None:
                for arg in jvm_args_data:
                    if isinstance(arg, dict) and "rules" in arg:
                        for rule in arg["rules"]:
                            if rule.get("action") == "allow" and rule.get("os", {}).get("name") == "osx":
                                if "-XstartOnFirstThread" in arg["value"]:
                                    OtherArgs += f" -XstartOnFirstThread"

        if append_args:
            OtherArgs += f" {append_args}"

        if without_ram_args:
            return OtherArgs
        else:
            return RAMSize_Args, OtherArgs

    @staticmethod
    def generate_game_args(version_id, username, access_token, game_dir, assets_dir, assetsIndex, uuid, **kwargs):
        # parameter stuff
        fetch_version_data_without_using_exist = kwargs.get("fetch_version_data_without_using_exist", False)

        if fetch_version_data_without_using_exist:
            version_data = get_version_data(version_id)
        else:
            version_data = get_version_data_from_exist_data(version_id)
            if version_data is None:
                return False, None

        minecraftArguments = version_data.get("arguments", {}).get("game", None)
        if minecraftArguments is None:
            minecraftArguments = version_data.get("minecraftArguments", None)
            if minecraftArguments is None:
                return False, None

        client_type = version_data.get("type", None)
        user_properties = "{}"
        user_type = "msa"  # Set user type to 'msa'

        if type(minecraftArguments) is list:
            minecraftArguments = ""
            for arg in minecraftArguments:
                minecraftArguments += f" {arg}"

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

        if "AlphaVanillaTweaker" in minecraftArguments or client_type in ["classic", "infdev", "indev", "alpha", "old"
                                                                                                                 "-alpha"]:
            minecraft_args += " --tweakClass net.minecraft.launchwrapper.AlphaVanillaTweaker"

        return True, minecraft_args

    @staticmethod
    def manage_client_instance():
        client_pool = client_launcher.client_pool
        if len(client_launcher.client_pool) == 0:
            print("No such clientInstance in the client pool.", color='red')
            time.sleep(3)
            return

        formatted_clients = '\n'.join([f"{index + 1}: {version}" for index, version in enumerate(client_pool)])
        print(formatted_clients)
        client_id = str(input("Choose a client to streaming output: "))

        try:
            client_id = int(client_id) - 1

            client_instance_info = client_launcher.client_pool[client_id]
            client_instance = client_instance_info[0]
        except ValueError:
            print("Unknown input :/", color='red')
            time.sleep(3)
            return
        except IndexError:
            print("Unknown client id :/", color='red')
            return

        client_instance.stream()

    def prepare_ask_for_instance(self):
        # Loading config
        self.load_config()

        # Check folder "versions" are available in root (To avoid some user forgot to install)
        if not os.path.exists("instances"):
            os.makedirs("instances")

        # Get the instance list from instance manager
        Status, instance_list = instance_manager.instance_list(max_instance_per_row=self.max_instance_per_row)

        if not Status:
            print("No instances are available to launch :(", color='red')
            print("You can use create instance to create a new instance for you :)", color='blue')
            time.sleep(4)

        print("Which instances do you want to launch?")
        self.instance_name = input(":")

        if self.instance_name == "mc":
            self.manage_client_instance()
        else:
            # Ignore some spaces on start or end of the name
            self.instance_name = self.instance_name.strip()
            if str(self.instance_name).upper() == "EXIT":
                return

            # Check user type instances are available
            if self.instance_name not in instance_list:
                print("Can't found instances " + self.instance_name + " of Minecraft :(", color='red')
                print("Please check you type instances version are available on the list.")
                print("If you think game files are corrupted."
                      " Just re-download it(Your world won't be delete when re-download Minecraft).")
                time.sleep(2.2)
                return

            # Set instance path and launch game
            self.instance_path = os.path.join(Base.launcher_instances_dir, self.instance_name)

            self.launch_game()

    def quick_launch(self):
        # Loading config
        self.load_config()

        if self.quick_launch_target_instance_name is None:
            print("Quick launch instance name are undefined :(", color='red')
            time.sleep(2.2)
            return

        Status, instance_list = instance_manager.instance_list()

        if not Status:
            print("No instances are available to launch :( (?)", color='red')
            print("You can use create instance to create a new instance for you :)", color='blue')
            time.sleep(4)

        if self.quick_launch_target_instance_name not in instance_list:
            print(f"QuickLaunch instance name {Base.QuickInstancesName} are not found :(", color='red')
            time.sleep(3)
            return

        # Set instance name and path and then launch game
        self.instance_name = self.quick_launch_target_instance_name
        self.instance_path = os.path.join(Base.launcher_instances_dir, self.quick_launch_target_instance_name)
        self.launch_game()

    def launch_game(self):
        print("Preparing to launch.....", color='c')

        if not Base.InternetConnected:
            print("Warning: Internet is not connected.", color='red')
            print("If the instance is never started in a networked environment."
                  " The launcher may crash when preparing some process.", color='red')

        # Get instance's Minecraft version
        instance_info_path = os.path.join(Base.launcher_instances_dir, self.instance_name, "instance.bakelh.ini")

        InfoStatus, self.minecraft_version = instance.get_instance_info(instance_info_path,
                                                                        info_name="client_version",
                                                                        ignore_not_found=True)

        InfoStatus, self.real_version = instance.get_instance_info(instance_info_path,
                                                                   info_name="real_minecraft_version",
                                                                   ignore_not_found=True)

        # print version info
        print(f"Version Info : client_version={self.minecraft_version} real_version={self.real_version}",
              color='lightyellow')

        # Check version.json status
        version_data = get_version_data_from_exist_data(self.minecraft_version)
        if not version_data:
            print("Version.json not found. Recreating...", color='lightyellow')
            if not Base.InternetConnected:
                print("Internet connection error :( Please connect to internet.", color='red')
                time.sleep(4)
                return "ReCreateVersionJSON>NoInternetConnected"
            orig_version_data = get_version_data(self.minecraft_version)
            create_version_data(self.minecraft_version, orig_version_data)
            version_data = get_version_data_from_exist_data(self.minecraft_version)
            if version_data is None:
                print("Re-create version json failed :(", color='red')
                time.sleep(4)
                return "ReCreateVersionJSONFailed"

        # Get required Java version path
        if os.path.isfile(Base.jvm_setting_path):
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
        if not Status or major_version == "None":
            print("Could not find support java version in the instance info. Re-try get it from version json.",
                  color='lightyellow')
            major_version = version_data.get("javaVersion", {}).get("majorVersion", None)

        if major_version is not None and major_version != "None":
            JavaPath = Duke.java_version_check(self.minecraft_version, java_version=major_version)
        else:
            if Base.InternetConnected:
                JavaPath = Duke.java_version_check(self.minecraft_version)
            else:
                print("Failed to get support java version :( No internet connection.", color='red')
                time.sleep(4)
                return "GetSupportJava>NoInternetConnected"

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
        print(account_manager.account_data_path)
        status, curr_acc_id, e = get_current_account_id(account_manager.account_data_path)
        if not status:
            print(f"Can't find account ID. | {e}", color='red')
            return "AccountIDNotFound"

        AccDataStatus, account_data, e = get_account_data_use_account_id(account_manager.account_data_path, curr_acc_id)
        if not AccDataStatus:
            print(f"Could not get account data. | {e}", color='red')
            return "GetAccountDataFailed"

        try:
            username = account_data['Username']
            access_token = account_data['AccessToken']
            uuid = account_data['UUID']
            if not Base.BypassLoginRequire:
                if username == "Player" or username == "BakeLauncherLocalUser":
                    print("Sorry :( You can't launch game without login in this version.", color='red')
                    time.sleep(3)
                    return "AccountDataInvalid"
            access_token = f"[HIDDEN]{access_token}[HIDDEN]"

        except JSONDecodeError or ValueError:
            print("Failed to launch Minecraft :( Cause by invalid AccountData", color='red')
            return

        # Chdir to gameDir
        gameDir = os.path.join(self.instance_path, INSTANCE_GAME_FOLDER_NAME)
        os.chdir(gameDir)

        old_libraries_path = os.path.join("libraries")
        libraries_path = os.path.join("libraries")
        NativesPath = os.path.join("natives")
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

        # Check natives are available to use
        print("Checking natives...", color='green')
        if not os.path.isdir(NativesPath) or not len(os.listdir(NativesPath)) == 0:
            print("Natives are available! (if it unzip correctly)", color='green')
        else:
            print("Natives are not available or it unzip not correctly :(", color='red')
            print("Please download now you launch instances version(it will recreate it)", color='yellow')
            print("If you still get this error please report this issue to GitHub!", color='green')
            time.sleep(4)
            os.chdir(Base.launcher_root_dir)
            return "NativesAreNotAvailable"

        # Get MainClass Name And Set Args(-cp "libraries":client.jar net.minecraft.client.main.Main or
        # net.minecraft.launchwrapper.Launch(old))
        Status, main_class = find_main_class(self.minecraft_version, custom_version_data=version_data)
        print(f"Using {main_class} as the Main Class.", color='blue')

        # Get assetsIndex and assets_dir
        assetsIndex = assets_grabber.get_assets_index_version(self.minecraft_version)
        if assetsIndex is None:
            print("Failed to get assets index version :(", color='red')
            time.sleep(3)
            return "FailedToGetAssetsIndexVer"

        assets_dir = assets_grabber.get_assets_dir(self.minecraft_version, self.instance_path)

        """Preparing args"""
        GameArgs = None
        JVMArgs = None
        extra_classpath = ""
        extra_game_args = ""
        extra_jvm_arg = ""

        # Now it available :)
        instance_custom_config = os.path.join(self.instance_path, "instance.bakelh.cfg")
        if os.path.exists(instance_custom_config):
            """Processing custom config"""
            print("Found instance config :D", color='blue')
            print('Loading custom config...', color='green')

            args_queue = ["CustomJVMArgs", "CustomGameArgs", "InjectJARPath", "ModLoaderClass", "ModLoaderGameArgs",
                          "ModLoaderJVMArgs"]
            exists_args_data = []

            for arg in args_queue:
                arg_data = instance.read_custom_config(instance_custom_config, arg)

                if not arg_data is None:
                    if len(arg_data) > 0:
                        print(f"Found existing {arg} data : {arg_data}", color='green')
                        exists_args_data.append(arg_data)

                if arg_data is None or len(arg_data) == 0:
                    exists_args_data.append("")

            args_dict = dict(zip(args_queue, exists_args_data))

            custom_jvm_arg = args_dict["CustomJVMArgs"]
            if len(custom_jvm_arg) > 0:
                print("Replace original args to custom arguments...", color='purple')
                JVMArgs = custom_jvm_arg

            custom_game_args = args_dict["CustomGameArgs"]
            if len(custom_game_args) > 0:
                print("Append custom game args to launch-chain...", color='purple')
                extra_game_args += custom_game_args

            InjectJARPath = args_dict["InjectJARPath"]
            if len(InjectJARPath) > 0:
                print("Append inject jar file to classpath...", color='purple')
                extra_classpath = InjectJARPath

            ModLoaderClass = args_dict["ModLoaderClass"]
            if len(ModLoaderClass) > 0:
                print("Replace vanilla mainClass to ModLoaderClass...", color='cyan')
                main_class = ModLoaderClass

            ModLoaderGameArgs = args_dict["ModLoaderGameArgs"]
            if len(ModLoaderGameArgs) > 0:
                print("Append ModLoader game args to launch-chain...", color='cyan')
                extra_game_args += ModLoaderGameArgs

            ModLoaderJVMArgs = args_dict["ModLoaderJVMArgs"]
            if len(ModLoaderJVMArgs) > 0:
                print("Append ModLoader JVMArgs to launch-chain...", color='cyan')
                extra_jvm_arg = ModLoaderJVMArgs

        # Check client jar
        classpath_using_version = self.minecraft_version
        self.client_path = os.path.join(libraries_path, "net", "minecraft", self.minecraft_version, "client.jar")

        if not os.path.exists(self.client_path):
            self.client_path = os.path.join(libraries_path, "net", "minecraft", self.real_version, "client.jar")

        if not os.path.exists(self.client_path):
            # For 0.7.x and pre-0.8
            print("WARNING: Could not find client jar file in the recommended location. Replacing to using legacy...",
                  color='yellow')
            self.client_path = os.path.join(self.instance_path, "client.jar")

        if not os.path.exists(self.client_path):
            print("Could not find client in the recommended location :(", color='red')

        # Preparing classpath
        if extra_classpath:
            classpath = generate_classpath(classpath_using_version, libraries_path,
                                           extra_classpath=extra_classpath, custom_main_class_path=self.client_path)
        else:
            classpath = generate_classpath(classpath_using_version, libraries_path,
                                           custom_main_class_path=self.client_path)

        if JVMArgs is None:
            RAM_Args, OtherArgs = self.generate_jvm_args(self.minecraft_version)
            JVMArgs = RAM_Args + OtherArgs

        if extra_jvm_arg:
            JVMArgs = JVMArgs + f" {extra_jvm_arg}"

        # Preparing game args
        if GameArgs is None:
            Status, GameArgs = self.generate_game_args(self.minecraft_version, username, access_token, gameDir,
                                                       assets_dir,
                                                       assetsIndex, uuid)
            if not Status:
                print("Failed to generate game args :(", color='red')
                time.sleep(3)
                return "GenerateGameArgsFailed"

        if extra_game_args:
            GameArgs = f"{GameArgs} {extra_game_args}"

        # Set instances_id(for multitasking process title)
        instances_id = f"Minecraft {self.minecraft_version}"

        # Bake Minecraft :)
        launch_client(JVMPath, classpath, NativesPath, main_class, JVMArgs, GameArgs,
                      instances_id, self.legacy_method, self.create_log_output_window)

        os.chdir(Base.launcher_root_dir)
        time.sleep(2)


launch_manager = LauncherManager()
