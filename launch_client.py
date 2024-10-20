"""
InternalName: LaunchManager
In the file structure: launch_client.py

Just a tool to prepare command for launching clients...
"""

import os
import multiprocessing
import subprocess
import tempfile
import time
from print_color import print
from LauncherBase import timer, GetPlatformName, launcher_version
from assets_grabber import read_assets_index_version, get_assets_dir
from jvm_tool import java_version_check, java_search
from Download import get_version_data
from libraries_path import generate_libraries_paths
from auth_tool import get_account_data

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


def create_new_launch_thread(launch_command, title):
    FailedToLaunch = False
    PlatFormName = GetPlatformName.check_platform_valid_and_return()
    print("LaunchClient: Please check the launcher already created a new terminal.", color='purple')
    print("LaunchClient: If it didn't create it please check the output and report it to GitHub!", color='green')
    if PlatFormName == 'Windows':
        print("LaunchClient: Add command for windows support...", color='green')
        with tempfile.NamedTemporaryFile(delete=False, suffix='.bat') as command:
            command.write(f"@echo off\n".encode())
            command.write(f'title {title}\n'.encode())
            command.write(f"{launch_command}\n".encode())
            command.write("pause\n".encode())
            command.write("exit\n".encode())
            final_command = command.name
        try:
            print("LaunchClient: Creating launch thread...", color='green')
            process = subprocess.Popen(['cmd.exe', '/c', 'start', 'cmd.exe', '/k', final_command],
                                       shell=True,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,
                                       stdin=subprocess.PIPE)
        except Exception as e:
            FailedToLaunch = True
            print(f"Error in Windows process: {e}")

    elif PlatFormName == 'Linux':
        # Open a new terminal in Linux (gnome-terminal or xterm)
        try:
            print("LaunchClient: Creating launch thread...", color='green')
            # Linux don't need subprocess to create new terminal...bruh
            os.system(f"gnome-terminal -- bash -c '{launch_command}; exec bash'")
        except FileNotFoundError:
            # Fallback to xterm if gnome-terminal is not available
            print("LaunchClient: Creating launch thread...", 'green')
            subprocess.run(['xterm', '-hold', '-e', './LaunchLoadCommandTemp.sh'])
            # Linux don't need subprocess to create new terminal...bruh
            # This method is UNTESTED!
            os.system("xterm -hold -e {launch_command}")
    elif PlatFormName == 'Darwin':  # macOS
        now_directory = os.getcwd()
        script = f'''
        tell application "Terminal"
            do script "cd {now_directory} && bash -c './LaunchLoadCommandTemp.sh; read -p \\"Press any key to continue . . .\\"; exit'"
        end tell
        '''

        try:
            """
            print("LaunchClient: Creating launch thread...", 'green')
            os.system("chmod 755 LaunchLoadCommandTemp.sh")
            subprocess.run(['osascript', '-e', script], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            """
            with tempfile.NamedTemporaryFile('w', delete=False, suffix='.sh') as script_file:
                script_file.write(launch_command + '\nexec bash')  # Keep terminal open after execution
                script_path = script_file.name

            os.system(f'chmod +x {script_path}')


            apple_script = f"""
            tell application "Terminal"
                do script "{script_path}"
                activate
            end tell
            """

            os.system(f'osascript -e \'{apple_script}\'')
        except Exception as e:
            FailedToLaunch = True
            print(f"Error in macOS process: {e}")
    else:
        raise OSError(f"LaunchManager: Unsupported operating system: {PlatFormName}")

    if not FailedToLaunch:
        if PlatFormName == 'Windows':
            print("LaunchClient: Successfully created launch thread!", color='blue')
        elif PlatFormName == 'Darwin':
            print("LaunchClient: Successfully created launch thread!", color='blue')
            os.remove(script_path)
        else:
            print("LaunchClient: Successfully created launch thread!", color='blue')
            time.sleep(2)
    else:
        print("LaunchClient: Creating launch thread failed !", 'red')
        print("LaunchClient: Cause by unknown system or launch can't find shell :(", color='red')


def LaunchClient(JVMPath, libraries_paths_strings, NativesPath, MainClass,
                 JVM_Args, JVM_ArgsWindowsSize, JVM_ArgsRAM, GameArgs, custom_game_args, instances_id, EnableMultitasking):

    WorkPath = os.getcwd()
    # Construct the Minecraft launch command with proper quoting
    minecraft_command = (
        f'{JVMPath} {JVM_Args} {JVM_ArgsWindowsSize} {JVM_ArgsRAM} '
        f'-Djava.library.path="{NativesPath}" -cp "{libraries_paths_strings}" '
        f'{MainClass} {GameArgs} {custom_game_args}'
    )

    # Is for launch using one thread method
    cleaned_jvm_path = JVMPath.replace(" ", "")
    minecraft_command_one_thread = (
        f'{cleaned_jvm_path} {JVM_Args} {JVM_ArgsWindowsSize} {JVM_ArgsRAM} '
        f'-Djava.library.path="{NativesPath}" -cp "{libraries_paths_strings}" '
        f'{MainClass} {GameArgs} {custom_game_args}'
    )

    green = "\033[32m"
    blue = "\033[34m"
    light_yellow = "\033[93m"
    light_blue = "\033[94m"
    reset = "\033[0m"

    # Set title
    title = f"BakaLauncher: {instances_id}"

    # Create the full launch command with version logging and Minecraft command
    if GetPlatformName.check_platform_valid_and_return() == 'Windows':
        launch_command = [
            f'echo {light_yellow}BakeLauncher Version: {launcher_version}{reset}',
            f'echo {light_blue}Minecraft Log Start Here :) {reset}',
            'echo ================================================',
            f'{minecraft_command}',
            f'echo {green}LaunchManager: Minecraft has stopped running! (Thread terminated){reset}'
        ]
    elif GetPlatformName.check_platform_valid_and_return() == 'Darwin':
        # THANKS　Apple making this process become complicated...
        launch_command = [
            f'echo -ne "\033]0;{title}\007\n"',
            f'cd {WorkPath}\n',
            f'clear\n',
            f'printf "{light_yellow}BakeLauncher Version: {launcher_version}{reset}\\n"',
            f'printf "{light_blue}Minecraft Log Start Here :) {reset}\\n"',
            'echo "==============================================="',
            f'{minecraft_command}',
            f'printf "{green}LaunchManager: Minecraft has stopped running! (Thread terminated){reset}\\n"',
            f'exit\n'
        ]
    else:
        launch_command = [
            f'echo -ne "\033]0;{title}\007"',
            f'echo -e {light_yellow}"BakeLauncher Version: {launcher_version}"{reset}',
            f'echo -e {light_blue}"Minecraft Log Start Here :)"{reset}',
            'echo "==============================================="',
            f'{minecraft_command}',
            f'echo -e {green}"LaunchManager: Minecraft has stopped running! (Thread terminated)"{reset}'
        ]

    # Join the commands with newline characters for the batch file
    launch_command = '\n'.join(launch_command)

    # For unix-like...
    if not GetPlatformName.check_platform_valid_and_return() == "Windows":
        if os.path.exists("LaunchLoadCommandTemp.sh"):
            os.remove("LaunchLoadCommandTemp.sh")

        with open("LaunchLoadCommandTemp.sh", "w+") as f:
            f.write(launch_command)


    if EnableMultitasking == True:
        # Launch a new process using multiprocessing
        print("LaunchClient: EnableExperimentalMultitasking is Enabled :)", color='purple')
        client_process = multiprocessing.Process(
            target=create_new_launch_thread,
            args=(launch_command, title,)  # Pass the launch_command as an argument
        )

        # Start the process
        client_process.start()
    else:
        print("LaunchClient: EnableExperimentalMultitasking is Disabled!", color='green')
        print('"BakeLauncher One Thread Launch Mode"', color='green')
        if GetPlatformName.check_platform_valid_and_return() == "Windows":
            subprocess.run(minecraft_command_one_thread, shell=True)
            print("LaunchManager: Minecraft has stopped running! (Thread terminated)", color='green')
            back_to_main_memu = input("Press any key to continue. . .")
        else:
            subprocess.run(minecraft_command, shell=True)
            print("LaunchManager: Minecraft has stopped running! (Thread terminated)", color='green')
            back_to_main_memu = input("Press any key to continue. . .")


def LaunchManager():
    Main = "LaunchManager"
    root_directory = os.getcwd()
    global CustomGameArgs, CustomJVMArgs, JVM_Args_HeapDump, JVM_Args_WindowsSize, JVM_ArgsRAM, EnableMultitasking

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
        print("LaunchManager: Found exist Java Path config!", color='blue')
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
    with open("data/config.bakelh.cfg", 'r') as file:
        for line in file:
            if "DefaultAccountID" in line:
                id = line.split('=')[1].strip()  # Extract the value if found
                break  # Stop after finding the ID

    account_data = get_account_data(int(id))

    username = account_data['Username']
    uuid = account_data['UUID']
    access_token = account_data['AccessToken']

    if username == "Unknown":
        print("LaunchManager: Warring! You are not logged ! Client will crash when you trying to launch it!!!", color='red')
    # Transfer the current path to launch instances path and set gameDir

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
        print("LaunchClient: No config.bakelh.cfg found :0", color='yellow')

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

    # Now it available :)
    if os.path.exists("instance.bakelh.cfg"):
        print("LaunchManager: Found instance config :D", color='blue')
        print('LauncherManager: Trying to add custom config to launch chain...', color='green')

        with open("instance.bakelh.cfg", 'r') as file:
            for line in file:
                # Check for CustomGameArgs
                if "CustomGameArgs" in line:
                    # Extract everything after '=' and strip leading/trailing whitespace
                    CustomGameArgs = line.split('=', 1)[1].strip()  # Use maxsplit to capture the whole value
                    print(f"LaunchManager: Added custom game args to launch chain: '{CustomGameArgs}'", color='blue')
                    continue  # Continue to look for other args

                # Check for CustomJVMArgs
                if "CustomJVMArgs" in line:
                    # Extract everything after '=' and strip leading/trailing whitespace
                    CustomJVMArgs = line.split('=', 1)[1].strip()  # Use maxsplit to capture the whole value
                    print(f"LaunchManager: Replaced the default jvm_args to custom args: '{CustomJVMArgs}'",
                          color='blue')
                    continue  # Continue to look for other args

        # Check if CustomJVMArgs is None or has a length of 0 (ignoring spaces)
        if CustomJVMArgs is None or len(CustomJVMArgs.strip()) == 0:
            print("LaunchManager: CustomJVMArgs is empty or not provided, ignoring...", color='yellow')
            CustomJVMArgs = None  # Or handle as needed

        if CustomGameArgs is None or len(CustomGameArgs.strip()) == 0:
            print("LaunchManager: CustomGameArgs is empty or not provided, ignoring...", color='yellow')
            CustomGameArgs = " "  # Or handle as needed
    else:
        CustomGameArgs = " "
        CustomJVMArgs = None

    if not CustomJVMArgs == None:
        JVM_Args_WindowsSize = " "
        JVM_ArgsRAM = CustomJVMArgs

    instances_id = f"Minecraft {version_id}"
    # Bake Minecraft :)
    if PlatformName == "Windows":
        print("LaunchMode:(Windows;WithHeapDump;SetWindowSize)", color='blue')
        LaunchClient(JVMPath, libraries_paths_strings, NativesPath, main_class, JVM_Args_HeapDump,
                     JVM_Args_WindowsSize, JVM_ArgsRAM, GameArgs,
                     CustomGameArgs, instances_id, EnableMultitasking)
    elif PlatformName == "Darwin":
        JVM_Args_HeapDump = " "
        CheckRequireXThread, XThreadArgs = macos_jvm_args_support(version_id)
        print(f"Debug: {CheckRequireXThread}")
        if CheckRequireXThread:
            print("LaunchMode:(Darwin;WithoutHeapDump;SetWindowSize;RequireXStartFirstThread)", color='blue')
            JVM_Args_HeapDump = XThreadArgs
            LaunchClient(JVMPath, libraries_paths_strings, NativesPath, main_class,
                         JVM_Args_HeapDump,
                         JVM_Args_WindowsSize, JVM_ArgsRAM, GameArgs,
                         CustomGameArgs, instances_id, EnableMultitasking)
        else:
            print("LaunchMode:(Darwin;WithoutHeapDump;SetWindowSize;WithoutRequireXStartFirstThread)", color='blue')
            LaunchClient(JVMPath, libraries_paths_strings, NativesPath, main_class, JVM_Args_HeapDump,
                         JVM_Args_WindowsSize, JVM_ArgsRAM, GameArgs,
                         CustomGameArgs, instances_id, EnableMultitasking)
    elif PlatformName == "Linux":
        JVM_Args_HeapDump = " "
        print("LaunchMode:(Linux;WithoutHeapDump;SetWindowSize;WithoutRequireXStartFirstThread)", color='blue')
        LaunchClient(JVMPath, libraries_paths_strings, NativesPath, main_class, JVM_Args_HeapDump,
                     JVM_Args_WindowsSize, JVM_ArgsRAM, GameArgs,
                     CustomGameArgs, instances_id, EnableMultitasking)
    else:
        JVM_Args_HeapDump = " "
        print("LaunchMode:(UnknownOS;WithoutHeapDump;SetWindowSize;WithoutRequireXStartFirstThread)", color='blue')
        LaunchClient(JVMPath, libraries_paths_strings, NativesPath, main_class, JVM_Args_HeapDump,
                     JVM_Args_WindowsSize, JVM_ArgsRAM, GameArgs,
                     CustomGameArgs, instances_id, EnableMultitasking)

    os.chdir(root_directory)
    time.sleep(2)