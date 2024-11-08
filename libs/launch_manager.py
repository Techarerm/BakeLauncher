"""
InternalName: LaunchManager
In the file structure: launch_client.py

Just a tool to prepare command for launching clients...
"""

import os
import time
from json import JSONDecodeError
from LauncherBase import print_custom as print
from LauncherBase import timer, GetPlatformName, launcher_version
from libs.assets_grabber import assets_grabber
from libs.jvm_tool import java_version_check, java_search
from libs.__create_instance import game_files_grabber
from libs.auth_tool import get_account_data
from libs.launch_client import LaunchClient


def SelectMainClass(version_id):
    version_data = game_files_grabber.get_version_data(version_id)
    main_class = version_data.get("mainClass")
    return main_class


def macos_jvm_args_support(version_id):
    """
    Check if the version data includes the -XstartOnFirstThread argument for macOS.
    """
    version_data = game_files_grabber.get_version_data(version_id)
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


def generate_libraries_paths(version, libraries_dir):
    global client_jar_path
    jar_paths_string = ""
    client_jar_path = f"libraries/net/minecraft/{version}/client.jar"
    PlatformName = GetPlatformName.check_platform_valid_and_return()

    # Traverse the libraries directory
    print("Generating dependent libraries path for " + version + " of Minecraft...", color="green")
    for root, dirs, files in os.walk(libraries_dir):
        for file in files:
            if file.endswith('.jar') and not file.startswith("client.jar"):
                # Skip adding client.jar to jar_paths_string
                relative_path = os.path.relpath(os.path.join(root, file), start=libraries_dir)
                full_path = os.path.join("libraries", relative_path)

                # Append the path to the jar_paths_string with the correct separator
                if PlatformName == "Windows":
                    jar_paths_string += full_path + ";"
                else:
                    jar_paths_string += full_path + ":"

    # Finally, append the client.jar path to the end of the jar paths string if it exists
    if client_jar_path:
        jar_paths_string += client_jar_path

    return jar_paths_string


def GetGameArgs(version_id, username, access_token, minecraft_path, assets_dir, assetsIndex, uuid):
    version_data = game_files_grabber.get_version_data(version_id)  # Fetch version data
    minecraftArguments = version_data.get("minecraftArguments", "")  # Get the arguments or an empty string
    userCustomArgs = 0
    user_properties = "{}"
    user_type = "msa"  # Set user type to 'msa'
    # Replace placeholders in minecraftArguments with actual values
    minecraft_args = minecraftArguments \
        .replace("${auth_player_name}", username) \
        .replace("${auth_session}", access_token) \
        .replace("${game_directory}", minecraft_path) \
        .replace("${assets_root}", assets_dir) \
        .replace("${version_name}", version_id) \
        .replace("${assets_index_name}", assetsIndex) \
        .replace("${auth_uuid}", uuid) \
        .replace("${auth_access_token}", access_token) \
        .replace("${user_type}", user_type) \
        .replace("${user_properties}", user_properties)  # Replace user_properties if present

    if "--userProperties" in minecraftArguments:
        print("LaunchManage: This version of Minecraft requires --userProperties!", color='green')
        # Properly replace ${user_properties} or add user properties if not present

    # Handle special case where ${auth_player_name} and ${auth_session} are at the beginning
    elif minecraftArguments.startswith("${auth_player_name} ${auth_session}"):
        # Prepend the username and access token as per the special case
        minecraft_args = f"{username} {access_token} --gameDir {minecraft_path} " \
                         f"--assetsDir {assets_dir} --assetIndex {assetsIndex}"

    elif minecraftArguments.endswith("${game_assets}"):
        minecraft_args = f"--username {username} --session {access_token} --version {version_id} --gameDir {minecraft_path} " \
                         f"--assetsDir {assets_dir} --assetIndex {assetsIndex}"

    elif minecraftArguments.startswith("--username") and minecraftArguments.endswith("${auth_access_token}"):
        minecraft_args = f"--username {username} --version {version_id} --gameDir {minecraft_path} " \
                         f"--assetsDir {assets_dir} --assetIndex {assetsIndex} --accessToken {access_token}"

    else:
        minecraft_args = f"--username {username} --version {version_id} --gameDir {minecraft_path} " \
                         f"--assetsDir {assets_dir} --assetIndex {assetsIndex} --uuid {uuid} " \
                         f"--accessToken {access_token} --userType {user_type}"

    return minecraft_args


def launch_wit_args(platform, version_id, librariesCFG, gameDir, assetsDir, assetsIndex, jvm_path, nativespath,
                    main_class, ):
    Main = "LaunchManager"
    local = os.getcwd()

    # I "will" choose a free time to refactor this code....
    print(f"Launch with args has been deleted since {launcher_version}", color='green')
    timer(8)


def LaunchManager():
    Main = "LaunchManager"
    root_directory = os.getcwd()
    global CustomGameArgs, CustomJVMArgs, JVM_Args_HeapDump, JVM_Args_WindowsSize, JVM_ArgsRAM, EnableMultitasking, \
        CustomLaunchStatus, account_data, username, access_token, uuid, DemoFlag

    CustomLaunchStatus = ""

    # Check folder "versions" are available in root (To avoid some user forgot to install)
    if not os.path.exists("instances"):
        os.makedirs("instances")

    # Get instances list and check it
    instances_list = os.listdir('instances')
    if len(instances_list) == 0:
        print("LaunchManager: No instances are available to launch :(", color='red')
        print("Try to using DownloadTool to download the Minecraft!")
        timer(4)
        return "NoInstancesAreAvailable"

    # Ask user want to launch instances...
    print(" | ".join(map(str, instances_list)))
    print("LaunchManager: Which instances is you want to launch instances ?")
    version_id = input(":")

    # Check user type instances are available
    if version_id not in instances_list:
        print("Can't found instances " + version_id + " of Minecraft :(", color='red')
        print("Please check you type instances version and try again or download it on DownloadTool!")
        timer(3)
        return
    else:
        print("Preparing to launch.....", color='c')

    # Get required Java version path
    if os.path.isfile('Java_HOME.json'):
        print("Found exist Java Path config!", color='blue')
    else:
        print("LaunchManager: Can't find exist Java Path config :(", color='red')
        print("Want create it now ? Y/N", color='green')
        user_input = input(":")
        if user_input.upper() == "Y":
            print("LaunchManager: Calling java_search..")
            os.chdir(root_directory)
            java_search()

    print("LaunchManager: Getting JVM Path...", color='c')
    JavaPath = java_version_check(Main, version_id)

    # Check JavaPath is valid
    if JavaPath is None:
        print("LaunchManager:Get JavaPath failed! Cause by None path!", color='red')
        print("Please download third version of Minecraft support Java(In DownloadTool)!")
        timer(5)
        return "FailedToCheckJavaPath"

    # After get JVMPath(bin), Get PlatformName and set the actual required Java Virtual Machine Path
    PlatformName = GetPlatformName.check_platform_valid_and_return()
    if PlatformName == 'Windows':
        java_executable = "java.exe"
    else:
        java_executable = "java"

    # Full path to the Java executable
    java_executable_path = os.path.join(JavaPath, java_executable)
    # Check if Java executable exists
    if os.path.isfile(java_executable_path):
        JVMPath = f'"{java_executable_path}"'  # Enclose in quotes for proper execution
    else:
        print("LaunchManager: Your Java executable is corrupted :(", color='red')
        print("LaunchManager: Please reinstall it! (Or download the latest version for your launch instances)")
        timer(5)
        return "JavaExecutableAreCorrupted"

    # Get access token and username, uuid to set game args
    print("Reading account data...", color='green')
    with open("data/config.bakelh.cfg", 'r') as file:
        for line in file:
            if "DefaultAccountID" in line:
                id = line.split('=')[1].strip()  # Extract the value if found
                break  # Stop after finding the ID

    try:
        account_data = get_account_data(int(id))
        username = account_data['Username']
        uuid = account_data['UUID']
        access_token = account_data['AccessToken']

        if username == "Player" or username == "BakeLauncherLocalUser":
            print("Warning: You are currently using a temporary user profile. "
                  "This means you can only play Minecraft in demo mode :)", color='yellow')
            return_check = input("If you understand this, press 'Y' to continue launching: ")
            if not return_check.upper() == "Y":
                return
            else:
                DemoFlag = True
        else:
            DemoFlag = False

    except JSONDecodeError or ValueError:
        print("LaunchManager: Failed to launch Minecraft :( Cause by invalid AccountData", color='red')
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
        print("LaunchManager: No config.bakelh.cfg found :0", color='yellow')

    # Sdt work path to instances
    os.chdir(r'instances/' + version_id)
    gameDir = ".minecraft"

    # Set Java Virtual Machine use Memory Size
    JVM_ArgsRAM = r"-Xms1024m -Xmx4096m"

    # JVM_Args_HeapDump(It will save heap dump when Minecraft Encountered OutOfMemoryError? "Only For Windows!")
    JVM_Args_HeapDump = r"-XX:HeapDumpPath=MojangTricksIntelDriversForPerformance_javaw.exe_minecraft.exe.heapdump"

    # Set this to prevent the windows too small
    JVM_Args_WindowsSize = (r"-Dorg.lwjgl.opengl.Window.undecorated=false -Dorg.lwjgl.opengl.Display.width=1280 "
                            r"-Dorg.lwjgl.opengl.Display.height=720")

    # Check natives are available to use
    print("Checking natives...", color='green')
    if os.path.isdir(".minecraft/natives"):
        if not len(os.listdir(".minecraft/natives")) == 0:
            print("Natives are available! (if it unzip correctly)", color='green')
        else:
            timer(8)
            print("LaunchManager: Natives are not available or it unzip not correctly :(", color='red')
            print("Please download now you launch instances version(it will recreate it)",
                  color='yellow')
            print("If you still get this error please report this issue to GitHub!", color='green')
            return "NativesAreNotAvailable"
    else:
        timer(8)
        print("LaunchManager: Natives are not available or it unzip not correctly :(", color='red')
        print("Please download now you launch instances version(it will recreate it)", color='yellow')
        print("If you still get this error please report this issue to GitHub!", color='green')
        return "NativesAreNotAvailable"

    # Set Natives Path
    NativesPath = ".minecraft/natives"

    # Get librariesPath(Example: /path/LWJGL-1.0.jar:/path/Hopper-1.2.jar:/path/client.jar)
    libraries_paths_strings = generate_libraries_paths(version_id, "libraries")

    # Get MainClass Name And Set Args(-cp "libraries":client.jar net.minecraft.client.main.Main or
    # net.minecraft.launchwrapper.Launch(old))
    main_class = SelectMainClass(version_id)
    print(f"Using {main_class} as the Main Class.",
          color='blue' if "net.minecraft.client.main.Main" in main_class else 'purple')

    # Get assetsIndex and assets_dir
    assetsIndex = assets_grabber.get_assets_index_version("", version_id)
    assets_dir = assets_grabber.get_assets_dir("", version_id)

    # Get GameArgs
    GameArgs = GetGameArgs(version_id, username, access_token, gameDir, assets_dir, assetsIndex, uuid)

    # Now it available :)
    if os.path.exists("instance.bakelh.cfg"):
        print("Found instance config :D", color='blue')
        print('Loading custom config...', color='green')

        with open("instance.bakelh.cfg", 'r') as file:
            for line in file:
                # Check for CustomGameArgs
                if "CustomGameArgs" in line:
                    # Extract everything after '=' and strip leading/trailing whitespace
                    CustomGameArgs = line.split('=', 1)[1].strip()  # Use maxsplit to capture the whole value
                    print(f"Added custom game args to launch chain: '{CustomGameArgs}'", color='blue')
                    continue

                # Check for CustomJVMArgs
                if "CustomJVMArgs" in line:
                    # Extract everything after '=' and strip leading/trailing whitespace
                    CustomJVMArgs = line.split('=', 1)[1].strip()  # Use maxsplit to capture the whole value
                    print(f"Added custom args to launch chain: '{CustomJVMArgs}'",
                          color='blue')
                    continue

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
    else:
        CustomGameArgs = " "
        CustomJVMArgs = None

    if not CustomJVMArgs == None:
        JVM_Args_WindowsSize = " "
        JVM_ArgsRAM = CustomJVMArgs

    if DemoFlag:
        if "-demo" not in CustomGameArgs:
            CustomGameArgs += " -demo"
        if "DemoUser" not in CustomLaunchStatus:
            CustomLaunchStatus += ";DemoUser"


    # Set instances_id(for multitasking process title)
    instances_id = f"Minecraft {version_id}"

    # Bake Minecraft :)
    if PlatformName == "Windows":
        print(f"Mode:(Windows;WithHeapDump;SetWindowSize{CustomLaunchStatus})", color='green', tag='Debug')
        print(GameArgs)
        LaunchClient(JVMPath, libraries_paths_strings, NativesPath, main_class, JVM_Args_HeapDump,
                     JVM_Args_WindowsSize, JVM_ArgsRAM, GameArgs,
                     CustomGameArgs, instances_id, EnableMultitasking)
    elif PlatformName == "Darwin":
        JVM_Args_HeapDump = " "
        # In LWJGL 3.x, macOS requires this args to make lwjgl running on the JVM starts with thread 0) (from wiki.vg)
        CheckRequireXThread, XThreadArgs = macos_jvm_args_support(version_id)
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
    elif PlatformName == "Linux":
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

    os.chdir(root_directory)
    time.sleep(2)
