"""
InternalName: LaunchManager
In the file structure: launch_client.py

Just a tool to prepare command for launching clients...
"""
CustomArgs = "--quickPlayMultiplayer 2b2t.org"

import os
import json
import multiprocessing
import subprocess
import tempfile
import shlex
from print_color import print
from __function__ import timer, GetPlatformName, launcher_version
from assets_grabber import read_assets_index_version, get_assets_dir
from jvm_tool import java_version_check, java_search
from Download import get_version_data
from libraries_path import generate_libraries_paths


def SelectMainClass(version_id):
    version_data = get_version_data(version_id)
    main_class = version_data.get("mainClass")
    return main_class


def GetGameArgs(version_id, username, access_token, minecraft_path, assets_dir, assetsIndex, uuid):
    version_data = get_version_data(version_id)  # Fetch version data
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

def create_client_process(launch_command, title):
    PlatFormName = GetPlatformName.check_platform_valid_and_return()
    print("LaunchManager: Please check the launcher already created a new terminal.", color='purple')
    print("LaunchManager: If it didn't create it please check the output and report it to GitHub!", color='green')

    if PlatFormName == 'Windows':
        with tempfile.NamedTemporaryFile(delete=False, suffix='.bat') as command:
            command.write(f"@echo off\n".encode())
            command.write(f'title {title}\n'.encode())
            command.write(f"{launch_command}\n".encode())
            command.write("pause\n".encode())
            command.write("exit\n".encode())
            final_command = command.name
        try:
            process = subprocess.Popen(['cmd.exe', '/c', 'start', 'cmd.exe', '/k', final_command],
                                       shell=True,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,
                                       stdin=subprocess.PIPE)
        except Exception as e:
            print(f"Error in Windows process: {e}")

    elif PlatFormName == 'Linux':
        # Open a new terminal in Linux (gnome-terminal or xterm)
        try:
            subprocess.run(['gnome-terminal', '--', 'bash', '-c', f'{launch_command}; exec bash'])
        except FileNotFoundError:
            # Fallback to xterm if gnome-terminal is not available
            subprocess.run(['xterm', '-hold', '-e', f'{launch_command}'])
    elif PlatFormName == 'Darwin':  # macOS
        try:
            # Join the launch_command_lines into one single command string, ensuring newlines are preserved
            full_command = '; '.join(launch_command)
            # Escape any double quotes inside the command
            escaped_command = full_command.replace('"', '\\"')
            # Build the osascript AppleScript command
            osascript_command = f'tell application "Terminal" to do script "{escaped_command}; exec bash"'
            # Execute the command
            subprocess.run(['osascript', '-e', osascript_command])
        except Exception as e:
            print(f"Error in macOS process: {e}")
    else:
        raise OSError(f"LaunchManager: Unsupported operating system: {PlatFormName}")

def LaunchClient(JVMPath, libraries_paths_strings, NativesPath, MainClass,
                 JVM_Args, JVM_ArgsWindowsSize, JVM_ArgsRAM, GameArgs, custom_game_args, instances_id):
    # Construct the Minecraft launch command with proper quoting
    minecraft_command = (
        f'{JVMPath} {JVM_Args} {JVM_ArgsWindowsSize} {JVM_ArgsRAM} '
        f'-Djava.library.path="{NativesPath}" -cp "{libraries_paths_strings}" '
        f'{MainClass} {GameArgs} {custom_game_args}'
    )

    print("OriginalLaunchCommand:", minecraft_command)
    green = "\033[32m"
    blue = "\033[34m"
    light_yellow = "\033[93m"
    light_blue = "\033[94m"
    reset = "\033[0m"

    # Create the full launch command with version logging and Minecraft command
    launch_command_lines = [
        f'echo {light_yellow}BakeLauncher Version: {launcher_version}{reset}',
        f'echo {light_blue}Minecraft Log Start Here :) {reset}',
        'echo ================================================',
        f'{minecraft_command}',
        f'echo {green}LaunchManager: Minecraft has stopped running! (Thread terminated){reset}'
    ]

    # Join the commands with newline characters for the batch file
    launch_command = '\n'.join(launch_command_lines)

    title = f"BakaLauncher: {instances_id}"

    # Launch a new process using multiprocessing
    client_process = multiprocessing.Process(
        target=create_client_process,
        args=(launch_command, title,)  # Pass the launch_command as an argument
    )

    # Start the process
    client_process.start()

    # Optional: Wait for the process to finish (if needed)
    # client_process.join()


def LaunchManager():
    Main = "LaunchManager"
    root_directory = os.getcwd()
    global CustomGameArgs

    # Check folder "versions" are available in root (To avoid some user forgot to install)
    if not os.path.exists("instances"):
        os.makedirs("instances")

    # Get instances list and check it
    instances_list = os.listdir('instances')
    if len(instances_list) == 0:
        print("LaunchManager: No instances are available to launch :(", color='red')
        print("Try to using DownloadTool to download the Minecraft!", color='yellow')
        timer(4)
        return "NoInstancesAreAvailable"
    else:
        print(f"LaunchManager: Instances list are available :D", color='blue')

    # Ask user want to launch instances...
    print(instances_list, color='blue')
    print("LaunchManager: Which instances is you want to launch instances ?", color='green')
    version_id = input(":")

    # Check user type instances are available
    if version_id not in instances_list:
        print("Can't found instances " + version_id + " of Minecraft :(", color='red')
        print("Please check you type instances version and try again or download it on DownloadTool!", color='yellow')
        timer(3)
        return
    else:
        print("LaunchManager: Preparing to launch.....", color='c')

    # Get required Java version path
    if os.path.isfile('Java_HOME.json'):
        print("LaunchManager: Found exits Java Path config!", color='blue')
    else:
        print("LaunchManager: Can't find exits Java Path config :(", color='red')
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
        print("Please download third version of Minecraft support Java(In DownloadTool)!", color='yellow')
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
        print("LaunchManager: Please reinstall it! (Or download the latest version for your launch instances)",
              color='yellow')
        timer(8)
        return "JavaExecutableAreCorrupted"

    # Get access token and username, uuid to set game args
    print("LaunchManager: Reading account data...", color='green')
    with open('data/AccountData.json', 'r') as file:
        data = json.load(file)
    username = data['AccountName']
    uuid = data['UUID']
    access_token = data['Token']

    # Transfer the current path to launch instances path and set gameDir
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
    print("LaunchManager: Checking natives...", color='green')
    if os.path.isdir(".minecraft/natives"):
        if not len(os.listdir(".minecraft/natives")) == 0:
            print("LaunchManager: Natives are available! (if it unzip correctly)", color='green')
        else:
            timer(8)
            print("LaunchManager: Natives are not available or it unzip not correctly :(", color='red')
            print("LaunchManager: Please download now you launch instances version(it will recreate it)",
                  color='yellow')
            print("LaunchManager: If you still get this error please report this issue to GitHub!", color='green')
            return "NativesAreNotAvailable"
    else:
        timer(8)
        print("LaunchManager: Natives are not available or it unzip not correctly :(", color='red')
        print("LaunchManager: Please download now you launch instances version(it will recreate it)", color='yellow')
        print("LaunchManager: If you still get this error please report this issue to GitHub!", color='green')
        return "NativesAreNotAvailable"

    # Set Natives Path
    NativesPath = ".minecraft/natives"

    # Get librariesPath(Example: /path/LWJGL-1.0.jar:/path/Hopper-1.2.jar:/path/client.jar)
    libraries_paths_strings = generate_libraries_paths(version_id, "libraries")

    # Get MainClass Name And Set Args(-cp "libraries":client.jar net.minecraft.client.main.Main or
    # net.minecraft.launchwrapper.Launch(old))
    main_class = SelectMainClass(version_id)
    print(f"LaunchManager: Using {main_class} as the Main Class.",
          color='blue' if "net.minecraft.client.main.Main" in main_class else 'purple')

    # Get assetsIndex and assets_dir
    assetsIndex = read_assets_index_version(Main, root_directory, version_id)
    assets_dir = get_assets_dir(version_id)

    # Get GameArgs
    GameArgs = GetGameArgs(version_id, username, access_token, gameDir, assets_dir, assetsIndex, uuid)

    # Coming soon :)
    CustomGameArgs = " "

    instances_id = f"Minecraft {version_id}"

    # Bake Minecraft :)
    if PlatformName == "Windows":
        LaunchClient(JVMPath, libraries_paths_strings, NativesPath, main_class, JVM_Args_HeapDump,
                     JVM_Args_WindowsSize, JVM_ArgsRAM, GameArgs,
                     CustomGameArgs, instances_id)
    else:
        JVM_Args_HeapDump = " "
        LaunchClient(JVMPath, libraries_paths_strings, NativesPath, main_class, JVM_Args_HeapDump,
                     JVM_Args_WindowsSize, JVM_ArgsRAM, GameArgs,
                     CustomGameArgs, instances_id)

    os.chdir(root_directory)
    timer(2)
