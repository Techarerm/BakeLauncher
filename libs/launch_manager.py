import os
import shutil
import time
from json import JSONDecodeError
from LauncherBase import Base, print_custom as print
from libs.__assets_grabber import assets_grabber
from libs.__duke_explorer import Duke
from libs.__account_manager import account_manager
from libs.launch.launch_client import launch_client
from libs.__instance_manager import instance_manager
from libs.version.version import *
from libs.version.legacy import legacy_version_support
from libs.libraries.libraries import generate_classpath
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
        append_args = kwargs.get("append_args", False)

        # Get version data
        version_data = get_version_data_from_exist_data(client_version)
        if version_data is None:
            version_data = get_version_data(client_version)

        jvm_args_list = version_data.get("arguments", {}).get("jvm", None)

        if jvm_args_list is None:
            jvm_args_list = []

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
            # Check whether the startup version of macOS requires the parameter "-XstartOnFirstThread" parameter In
            # LWJGL 3.x, macOS requires this args to make lwjgl running on the JVM starts with thread 0) (from wiki.vg)
            if "-XstartOnFirstThread" in jvm_args_list:
                OtherArgs += "-XstartOnFirstThread "

        if append_args:
            OtherArgs += f" {append_args}"

        if without_ram_args:
            return OtherArgs
        else:
            return RAMSize_Args, OtherArgs

    def generate_game_args(self, version_id, username, access_token, game_dir, assets_dir, assetsIndex, uuid, **kwargs):
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

    def launch_game(self, **kwargs):
        global JVMArgs, CustomRAMArgs, JavaPath, LegacyFlag, main_class, append_jvm_args, version_data
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
        InfoStatus, LegacyFlag = instance.get_instance_info(instance_info_path,
                                                            info_name="use_legacy_manifest",
                                                            ignore_not_found=True)

        InfoStatus, minecraft_version = instance.get_instance_info(instance_info_path,
                                                                   info_name="client_version",
                                                                   ignore_not_found=True)

        InfoStatus, real_version = instance.get_instance_info(instance_info_path,
                                                              info_name="real_minecraft_version",
                                                              ignore_not_found=True)

        if not InfoStatus:
            LegacyFlag = True
            print("Warning: You are trying to launch an instance created with a previous version of BakeLauncher.",
                  color='yellow')
            print("Old instances support will be drop soon. ", end='', color='red')
            print("Please go to Extra>Convert Old Instance Structure to convert instance to new structure.",
                  color='red')
            minecraft_version = self.instance_name
            real_version = self.instance_name
        else:
            LegacyFlag = False

        # print version info
        print(f"Version Info : client_version={minecraft_version} real_version={real_version}", color='cyan')

        # Check version.json status
        version_data = get_version_data_from_exist_data(minecraft_version)
        if not version_data:
            print("Version.json not found. Recreating...", color='lightyellow')
            if not Base.InternetConnected:
                print("Internet connection error :( Please connect to internet.", color='red')
                time.sleep(4)
                return "ReCreateVersionJSON>NoInternetConnected"
            orig_version_data = get_version_data(minecraft_version)
            create_version_data(minecraft_version, orig_version_data)
            version_data = get_version_data_from_exist_data(minecraft_version)
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
            print("Could not find support java version in the instance info. Re-try get it from version json.", color='lightyellow')
            major_version = version_data.get("javaVersion", {}).get("majorVersion", None)

        if major_version is not None and major_version != "None":
            JavaPath = Duke.java_version_check(minecraft_version, java_version=major_version)
        else:
            if Base.InternetConnected:
                JavaPath = Duke.java_version_check(minecraft_version)
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
            else:
                access_token = f"[HIDDEN]{access_token}[HIDDEN]"

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
        NativesPath = os.path.join(gameDir, "natives")

        # Get MainClass Name And Set Args(-cp "libraries":client.jar net.minecraft.client.main.Main or
        # net.minecraft.launchwrapper.Launch(old))
        Status, main_class = find_main_class(minecraft_version, custom_version_data=version_data)
        print(f"Using {main_class} as the Main Class.", color='blue')

        # Get assetsIndex and assets_dir
        assetsIndex = assets_grabber.get_assets_index_version(minecraft_version)
        if assetsIndex is None:
            print("Failed to get assets index version :(", color='red')
            time.sleep(3)
            return "FailedToGetAssetsIndexVer"

        assets_dir = assets_grabber.get_assets_dir(minecraft_version, instance_dir)

        """Preparing args"""
        GameArgs = None
        JVMArgs = None
        jvm_ram_args = None
        classpath = None
        InjectJARPath = None
        extra_classpath = ""
        extra_game_args = ""
        extra_jvm_arg = ""

        # Now it available :)
        instance_custom_config = os.path.join(instance_dir, "instance.bakelh.cfg")
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
        classpath_using_version = minecraft_version
        if LegacyFlag:
            client_path = os.path.join(libraries_path, "net", "minecraft", real_version, "client.jar")
            classpath_using_version = real_version
        else:
            client_path = os.path.join(libraries_path, "net", "minecraft", minecraft_version, "client.jar")

        if not os.path.exists(client_path):
            print("Could not find client in the recommended location :(", color='red')

        # Preparing classpath
        if extra_classpath:
            classpath = generate_classpath(classpath_using_version, libraries_path,
                                           extra_classpath=extra_classpath, custom_main_class_path=client_path)
        else:
            classpath = generate_classpath(classpath_using_version, libraries_path, custom_main_class_path=client_path)

        # Preparing jvm args
        if LegacyFlag:
            client_path = os.path.join(libraries_path, "net", "minecraft", real_version, "client.jar")
        else:
            client_path = os.path.join(libraries_path, "net", "minecraft", minecraft_version, "client.jar")

        if JVMArgs is None:
            RAM_Args, OtherArgs = self.generate_jvm_args(minecraft_version)
            JVMArgs = RAM_Args + OtherArgs

        if extra_jvm_arg:
            JVMArgs = JVMArgs + f" {extra_jvm_arg}"

        # Preparing game args
        if GameArgs is None:
            Status, GameArgs = self.generate_game_args(minecraft_version, username, access_token, gameDir, assets_dir,
                                                       assetsIndex, uuid)
            if not Status:
                print("Failed to generate game args :(", color='red')
                time.sleep(3)
                return "GenerateGameArgsFailed"

        if extra_game_args:
            GameArgs = f"{GameArgs} {extra_game_args}"

        # Set instances_id(for multitasking process title)
        instances_id = f"Minecraft {minecraft_version}"

        # Bake Minecraft :)
        if Base.Platform == "Windows":
            launch_client(JVMPath, classpath, NativesPath, main_class, JVMArgs, GameArgs,
                          instances_id, Base.EnableExperimentalMultitasking)
        elif Base.Platform == "Darwin":
            launch_client(JVMPath, classpath, NativesPath, main_class, JVMArgs, GameArgs,
                          instances_id, Base.EnableExperimentalMultitasking)
        elif Base.Platform == "Linux":
            launch_client(JVMPath, classpath, NativesPath, main_class, JVMArgs, GameArgs,
                          instances_id, Base.EnableExperimentalMultitasking)
        else:
            launch_client(JVMPath, classpath, NativesPath, main_class, JVMArgs, GameArgs,
                          instances_id, Base.EnableExperimentalMultitasking)

        os.chdir(Base.launcher_root_dir)
        time.sleep(2)


launch_manager = LauncherManager()
