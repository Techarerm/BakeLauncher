import os
import shutil
import time
from json import JSONDecodeError
from LauncherBase import Base, timer, print_custom as print
from libs.__assets_grabber import assets_grabber
from libs.__duke_explorer import Duke
from libs.__account_manager import account_manager
from libs.launch_client import LaunchClient
from libs.__instance_manager import instance_manager
from libs.utils import get_version_data


def SelectMainClass(version_id):
    version_data = get_version_data(version_id)
    main_class = version_data.get("mainClass")
    return main_class


def macos_jvm_args_support(version_id):
    """
    Check if the version data includes the -XstartOnFirstThread argument for macOS.
    """
    version_data = get_version_data(version_id)
    jvm_args_list = version_data.get("arguments", {}).get("jvm", [])

    for jvm_entry in jvm_args_list:
        if isinstance(jvm_entry, dict):  # Only process if it's a dictionary
            rules = jvm_entry.get("rules", [])
            for rule in rules:
                os_data = rule.get("os", {})
                if os_data.get("name") == "osx":  # Check if the OS is macOS
                    value = jvm_entry.get("value", [])
                    if isinstance(value, list) and "-XstartOnFirstThread" in value:
                        return True, "-XstartOnFirstThread"

    return None, " "  # Return None if the argument is not found


def generate_libraries_paths(client_version, libraries_dir):
    jar_paths_string = ""
    client_jar_path = os.path.join(libraries_dir, "net", "minecraft", client_version, "client.jar")

    # Set to track already added ASM versions (version number should be unique)
    added_asm_versions = set()

    # Traverse the libraries directory
    print(f"Generating dependent libraries path for {client_version} of Minecraft...", color="green")
    for root, dirs, files in os.walk(libraries_dir):
        for file in files:
            if file.endswith('.jar') and not file.startswith("client.jar"):
                # Skip adding client.jar to jar_paths_string
                relative_path = os.path.relpath(os.path.join(root, file), start=libraries_dir)
                full_path = os.path.join(".minecraft", "libraries", relative_path)

                # Check if this is an ASM library
                if 'asm' in file:
                    # Extract the version from the file name (assuming version format is in the jar filename)
                    version = file.split('-')[1]
                    if version in added_asm_versions:
                        # Skip this ASM jar if the version is already added
                        print(f"Skipping duplicate ASM library: {file}")
                        continue
                    else:
                        # Mark this version as added
                        added_asm_versions.add(version)

                # Append the path to the jar_paths_string with the correct separator
                if Base.Platform == "Windows":
                    jar_paths_string += full_path + ";"
                else:
                    jar_paths_string += full_path + ":"

    # Finally, append the client.jar path to the end of the jar paths string if it exists
    if client_jar_path:
        jar_paths_string += client_jar_path

    return jar_paths_string


def GetGameArgs(version_id, username, access_token, game_dir, assets_dir, assetsIndex, uuid):
    version_data = get_version_data(version_id)  # Fetch version data
    minecraftArguments = version_data.get("minecraftArguments", "")  # Get the arguments or an empty string
    user_properties = "{}"
    user_type = "msa"  # Set user type to 'msa'
    # Replace placeholders in minecraftArguments with actual values
    minecraft_args = minecraftArguments \
        .replace("${auth_player_name}", username) \
        .replace("${auth_session}", access_token) \
        .replace("${game_directory}", game_dir) \
        .replace("${assets_root}", assets_dir) \
        .replace("${version_name}", version_id) \
        .replace("${assets_index_name}", assetsIndex) \
        .replace("${auth_uuid}", uuid) \
        .replace("${auth_access_token}", access_token) \
        .replace("${user_type}", user_type) \
        .replace("${user_properties}", user_properties)  # Replace user_properties if present

    if "--userProperties" in minecraftArguments:
        print("This version of Minecraft requires --userProperties!", color='green')
        minecraft_args = f"--username {username} --version {version_id} --gameDir {game_dir} " \
                         f"--assetsDir {assets_dir} --assetIndex {assetsIndex} --accessToken {access_token} " \
                         f"--userProperties {user_properties}"

    elif version_data.get("type") == "old-alpha":
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

    if "AlphaVanillaTweaker" in minecraftArguments or version_data.get("type") == "classic":
        minecraft_args += " --tweakClass net.minecraft.launchwrapper.AlphaVanillaTweaker"
    elif "AlphaVanillaTweaker" in minecraftArguments or version_data.get("type") == "infdev":
        minecraft_args += " --tweakClass net.minecraft.launchwrapper.AlphaVanillaTweaker"
    elif "AlphaVanillaTweaker" in minecraftArguments or version_data.get("type") == "indev":
        minecraft_args += " --tweakClass net.minecraft.launchwrapper.AlphaVanillaTweaker"

    return minecraft_args


def LaunchManager():
    global CustomGameArgs, CustomJVMArgs, JVM_Args_HeapDump, JVM_Args_WindowsSize, JVM_ArgsRAM, EnableMultitasking, \
        CustomLaunchStatus, account_data, username, access_token, uuid, DemoFlag, ModLoaderClass

    CustomLaunchStatus = ""

    # Check folder "versions" are available in root (To avoid some user forgot to install)
    if not os.path.exists("instances"):
        os.makedirs("instances")

    # Get instances list and check it
    instances_list = os.listdir('instances')
    if len(instances_list) == 0:
        print("No instances are available to launch :(", color='red')
        print("Try to using DownloadTool to download the Minecraft!")
        timer(4)
        return "NoInstancesAreAvailable"

    # Ask user want to launch instances...
    Status, Message = instance_manager.instance_list()
    if not Status:
        return Message
    print("Which instances do you want to launch?")
    instance_name = input(":")

    # Ignore some spaces on start or end of the name
    instance_name = instance_name.strip()
    if str(instance_name).upper() == "EXIT":
        return

    # Check user type instances are available
    if instance_name not in instances_list:
        print("Can't found instances " + instance_name + " of Minecraft :(", color='red')
        print("Please check you type instances version are available on the list.")
        print("If you think game files are corrupted."
              " Just re-download it(Your world won't be delete when re-download Minecraft).")
        time.sleep(2.2)
        return "TypeInstanceAreNotFound"
    else:
        instance_dir = os.path.join(Base.launcher_instances_dir, instance_name)
        print("Preparing to launch.....", color='c')

    # Get instance's Minecraft version
    instance_info_path = os.path.join(Base.launcher_instances_dir, instance_name, "instance.bakelh.ini")
    InfoStatus, use_legacy_manifest = instance_manager.get_instance_info(instance_info_path,
                                                                         info_name="use_legacy_manifest",
                                                                         ignore_not_found=True)
    if use_legacy_manifest:
        InfoStatus, minecraft_version = instance_manager.get_instance_info(instance_info_path,
                                                                           info_name="real_minecraft_version",
                                                                           ignore_not_found=True)
    else:
        InfoStatus, minecraft_version = instance_manager.get_instance_info(instance_info_path,
                                                                           info_name="client_version",
                                                                           ignore_not_found=True)
    if not InfoStatus:
        print("Warning: You are trying to launch a who built with an older version of BakeLauncher.", color='yellow')
        print("Old instances support will be drop soon. ", end='', color='red')
        print("Please go to Extra>Convert Old Instance Structure to convert instance to new structure.", color='red')
        minecraft_version = instance_name

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
    JavaPath = Duke.java_version_check(minecraft_version)

    # Check JavaPath is valid
    if JavaPath is None:
        print("Get JavaPath failed! Cause by None path!", color='red')
        print("Please download third version of Minecraft support Java(In DownloadTool)!")
        timer(5)
        return "FailedToCheckJavaPath"

    if not os.path.exists(JavaPath):
        print("The selected version of Java runtime folder does not exist :(", color='red')
        print("Please reinstall it! (Or download the latest version for your launch instances)", color='yellow')
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
        print("Please reinstall it! (Or download the latest version for your launch instances)", color='yellow')
        timer(2.5)
        return "JavaExecutableAreCorrupted"

    # Get access token and username, uuid to set game args
    print("Reading account data...", color='green')
    with open("data/config.bakelh.cfg", 'r') as file:
        for line in file:
            if "DefaultAccountID" in line:
                id = line.split('=')[1].strip()  # Extract the value if found
                break  # Stop after finding the ID

    try:
        Status, account_data = account_manager.get_account_data_use_accountid(int(id))
        username = account_data['Username']
        uuid = account_data['UUID']
        access_token = account_data['AccessToken']

        if username == "Player" or username == "BakeLauncherLocalUser":
            return "AccountDataInvalid"

    except JSONDecodeError or ValueError:
        print("Failed to launch Minecraft :( Cause by invalid AccountData", color='red')
        return

    # Check EnableMultitasking Support
    EnableMultitasking = False
    try:
        with open("data/config.bakelh.cfg", 'r') as file:
            for line in file:
                if "EnableExperimentalMultitasking" in line:
                    EnableExperimentalMultitasking = line.split('=')[1].strip()  # Extract the value if found
                    if str(EnableExperimentalMultitasking).upper() == "TRUE":
                        EnableMultitasking = True
                    break
    except FileNotFoundError:
        print("No config.bakelh.cfg found :0", color='yellow')

    # Sdt work path to instances
    os.chdir(instance_dir)
    gameDir = ".minecraft"

    # Set Java Virtual Machine use Memory Size
    JVM_ArgsRAM = r"-Xms1024m -Xmx4096m"

    # JVM_Args_HeapDump(It will save heap dump when Minecraft Encountered OutOfMemoryError? "Only For Windows!")
    JVM_Args_HeapDump = r"-XX:HeapDumpPath=MojangTricksIntelDriversForPerformance_javaw.exe_minecraft.exe.heapdump"

    # Set this to prevent the windows too small
    JVM_Args_WindowsSize = (rf"-Dorg.lwjgl.opengl.Window.undecorated=false "
                            rf"-Dorg.lwjgl.opengl.Display.width={Base.DefaultGameScreenWidth} "
                            rf"-Dorg.lwjgl.opengl.Display.height={Base.DefaultGameScreenHeight}")

    # Check natives are available to use
    print("Checking natives...", color='green')
    if os.path.isdir(".minecraft/natives"):
        if not len(os.listdir(".minecraft/natives")) == 0:
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
    NativesPath = ".minecraft/natives"

    # Get librariesPath(Example: /path/LWJGL-1.0.jar:/path/Hopper-1.2.jar:/path/client.jar)
    InjectJARPath = None
    if os.path.exists("libraries"):
        print("Moving libraries folder to .minecraft...")
        shutil.move("libraries", ".minecraft")
    libraries_paths_strings = generate_libraries_paths(minecraft_version, ".minecraft/libraries")
    # Inject jar file to launch chain
    # Get MainClass Name And Set Args(-cp "libraries":client.jar net.minecraft.client.main.Main or
    # net.minecraft.launchwrapper.Launch(old))
    main_class = SelectMainClass(minecraft_version)
    print(f"Using {main_class} as the Main Class.",
          color='blue' if "net.minecraft.client.main.Main" in main_class else 'purple')

    # Get assetsIndex and assets_dir
    assetsIndex = assets_grabber.get_assets_index_version("", minecraft_version)
    assets_dir = assets_grabber.get_assets_dir(minecraft_version)

    # Get GameArgs
    GameArgs = GetGameArgs(minecraft_version, username, access_token, gameDir, assets_dir, assetsIndex, uuid)

    # Now it available :)
    instance_custom_config = os.path.join(instance_dir, "instance.bakelh.cfg")
    if os.path.exists("instance.bakelh.cfg"):
        print("Found instance config :D", color='blue')
        print('Loading custom config...', color='green')

        CustomJVMArgs = instance_manager.read_custom_config(instance_custom_config, "CustomJVMArgs")

        CustomGameArgs = instance_manager.read_custom_config(instance_custom_config, "CustomGameArgs")

        InjectJARPath = instance_manager.read_custom_config(instance_custom_config, "InjectJARPath")

        ModLoaderClass = instance_manager.read_custom_config(instance_custom_config, "ModLoaderClass")

        # Check if CustomJVMArgs(or CustomGameArgs) is None or has a length of 0 (ignoring spaces)
        if CustomJVMArgs is None or len(CustomJVMArgs.strip()) == 0:
            print("CustomJVMArgs is empty or not provided, ignoring...", color='yellow')
            CustomJVMArgs = None
        else:
            # Check point for debug
            CustomLaunchStatus += ";WithCustomJVMArg"
        if CustomGameArgs is None or len(CustomGameArgs.strip()) == 0:
            print("CustomGameArgs is empty or not provided, ignoring...", color='yellow')
            CustomGameArgs = " "  # Replace Custom Args to a spaces(if is empty)
        else:
            # Check point for debug
            CustomLaunchStatus += ";WithCustomGameArg"

        if ModLoaderClass is None or len(ModLoaderClass.strip()) == 0:
            print("ModLoaderClass is empty or not provided, ignoring...", color='yellow')
            ModLoaderClass = None  # Replace Custom Args to a spaces(if is empty)
        else:
            print(ModLoaderClass)
            main_class = ModLoaderClass
    else:
        CustomGameArgs = " "
        CustomJVMArgs = None

    if CustomJVMArgs is not None:
        JVM_Args_WindowsSize = " "
        JVM_ArgsRAM = CustomJVMArgs

    if InjectJARPath is not None:
        libraries_paths_strings += InjectJARPath

    # Set instances_id(for multitasking process title)
    instances_id = f"Minecraft {minecraft_version}"

    # Bake Minecraft :)
    if Base.Platform == "Windows":
        print(f"Mode:(Windows;WithHeapDump;SetWindowSize{CustomLaunchStatus})", color='green', tag='Debug')
        LaunchClient(JVMPath, libraries_paths_strings, NativesPath, main_class, JVM_Args_HeapDump,
                     JVM_Args_WindowsSize, JVM_ArgsRAM, GameArgs,
                     CustomGameArgs, instances_id, EnableMultitasking)
    elif Base.Platform == "Darwin":
        JVM_Args_HeapDump = " "
        # In LWJGL 3.x, macOS requires this args to make lwjgl running on the JVM starts with thread 0) (from wiki.vg)
        CheckRequireXThread, XThreadArgs = macos_jvm_args_support(minecraft_version)
        if CheckRequireXThread:
            print(f"Mode:(Darwin;WithoutHeapDump;SetWindowSize;RequiresXStartFirstThread{CustomLaunchStatus})",
                  color='green', tag='Debug')
            JVM_Args_HeapDump = XThreadArgs
            LaunchClient(JVMPath, libraries_paths_strings, NativesPath, main_class,
                         JVM_Args_HeapDump,
                         JVM_Args_WindowsSize, JVM_ArgsRAM, GameArgs,
                         CustomGameArgs, instances_id, EnableMultitasking)
        else:
            print(f"Mode:(Darwin;WithoutHeapDump;SetWindowSize;WithoutRequiresXStartFirstThread{CustomLaunchStatus})",
                  color='green', tag='Debug')
            LaunchClient(JVMPath, libraries_paths_strings, NativesPath, main_class, JVM_Args_HeapDump,
                         JVM_Args_WindowsSize, JVM_ArgsRAM, GameArgs,
                         CustomGameArgs, instances_id, EnableMultitasking)
    elif Base.Platform == "Linux":
        JVM_Args_HeapDump = " "
        print(f"Mode:(Linux;WithoutHeapDump;SetWindowSize{CustomLaunchStatus})", color='green', tag='Debug')
        LaunchClient(JVMPath, libraries_paths_strings, NativesPath, main_class, JVM_Args_HeapDump,
                     JVM_Args_WindowsSize, JVM_ArgsRAM, GameArgs,
                     CustomGameArgs, instances_id, EnableMultitasking)
    else:
        JVM_Args_HeapDump = " "
        print(f"Mode:(UnknownOS;WithoutHeapDump;SetWindowSize{CustomLaunchStatus})", color='green', tag='Debug')
        LaunchClient(JVMPath, libraries_paths_strings, NativesPath, main_class, JVM_Args_HeapDump,
                     JVM_Args_WindowsSize, JVM_ArgsRAM, GameArgs,
                     CustomGameArgs, instances_id, EnableMultitasking)

    os.chdir(Base.launcher_root_dir)
    time.sleep(2)
