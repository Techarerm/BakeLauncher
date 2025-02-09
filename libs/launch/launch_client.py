import os
import re
import tempfile
import subprocess
import threading
import time
import multiprocessing
from LauncherBase import Base, print_custom as print

if os.name == 'nt':
    from libs.multi.nt import create_terminal

terminals = [
    "gnome-terminal",
    "xterm",
    "konsole",
    "alacritty",
    "termite",
    "xfce4-terminal",
    "lxterminal",
    "deepin-terminal",
    "tilix",
    "st",
    "kitty"
]


def create_new_client_thread_with_output(launch_command, PlatFormName):
    FailedToLaunch = False

    if PlatFormName == 'Windows':
        create_terminal(launch_command, os.getcwd())
    elif PlatFormName == 'Linux':
        try:
            print("Creating launch thread...")
            # Linux don't need subprocess to create new terminal...bruh
            os.system(f"gnome-terminal -- bash -c '{launch_command}; exec bash'")
        except FileNotFoundError:
            for terminal in terminals:
                try:
                    print(f"Trying {terminal}...")
                    if terminal == "xterm" or terminal == "st":
                        # xterm and st need different syntax
                        subprocess.run([terminal, "-hold", "-e", launch_command])
                    else:
                        # All other terminals
                        os.system(f"{terminal} -e bash -c '{launch_command}; exec bash'")
                    break
                except FileNotFoundError:
                    print(f"{terminal} not found, trying next terminal...")
            else:
                FailedToLaunch = True
                print("No suitable recommended terminal found.")

    elif PlatFormName == 'Darwin':  # macOS
        try:
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
            print("Successfully created launch thread!")
        elif PlatFormName == 'Darwin':
            print("Successfully created launch thread!")
            time.sleep(3)
            os.remove(script_path)
        else:
            print("Successfully created launch thread!")
            time.sleep(2)
    else:
        print("LaunchClient: Creating launch thread failed !")
        print("LaunchClient: Cause by unknown system or launch can't find shell :(")


def launch_process(launch_command):
    try:
        subprocess.Popen(
            launch_command,
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    except Exception as e:
        print(f"Failed to launch process. Cause: {e}")


def create_new_client_thread(launch_command):
    try:
        client_thread = threading.Thread(args=(launch_command,), target=launch_process)
        client_thread.start()
    except Exception as e:
        print(f"Failed to create launch process. Cause: {e}")


def prepare_command(JVMExecutable, libraries_paths_strings, NativesPath, MainClass,
                    JVMArgs, GameArgs):
    global real_game_args
    print("LaunchInfo", color='lightyellow')
    print("JVMExecutable: \n   ", JVMExecutable, "\n", color='lightgreen')
    print("JVM Arguments: \n   ", JVMArgs, "\n", color='blue')
    print("NativesPath: \n   ", NativesPath, "\n", color='lightgreen')
    print("Classpath: \n  ", libraries_paths_strings, "\n", color='lightgreen')
    print("MainClass: \n   ", MainClass, "\n", color='lightgreen')

    # Replace access token
    if "[HIDDEN]" in GameArgs:
        real_game_args = GameArgs.replace("[HIDDEN]", "")
        GameArgs = re.sub(r'\[HIDDEN\].*?\[HIDDEN\]', '${AccessToken}', GameArgs)
        print("GameArgs: \n   ", GameArgs, color='lightgreen')

    minecraft_command = (
        f'{JVMExecutable} {JVMArgs} '
        f'-Djava.library.path="{NativesPath}" -cp "{libraries_paths_strings}" '
        f'{MainClass} {real_game_args}'
    )

    minecraft_command_one_thread = (
        f'{JVMArgs}'
        f'-Djava.library.path="{NativesPath}" -cp "{libraries_paths_strings}" '
        f'{MainClass} {real_game_args}'
    )

    return minecraft_command, minecraft_command_one_thread


def launch_client(JVMExecutable, libraries_paths_strings, NativesPath, MainClass,
                  JVMArgs, GameArgs, instances_id,
                  EnableMultitasking):
    work_instance_dir = os.getcwd()
    minecraft_command, minecraft_command_one_thread = prepare_command(JVMExecutable, libraries_paths_strings,
                                                                      NativesPath, MainClass, JVMArgs, GameArgs)
    green = "\033[32m"
    light_yellow = "\033[93m"
    light_blue = "\033[94m"
    reset = "\033[0m"

    # Set title
    title = f"BakaLauncher: {instances_id}"

    # Create the full launch command with version logging and Minecraft command
    if Base.Platform == 'Windows':
        launch_command = " & ".join([
            f'title {title}',
            f'echo {light_yellow}BakeLauncher Version: {Base.launcher_version}{reset}',
            f'echo {light_blue}Minecraft Log Output: {reset}',
            f'echo ================================================',
            f'{minecraft_command}',
            f'echo {green}Minecraft has stopped running! (Thread terminated){reset}',
            'pause'
        ])
    elif Base.Platform == 'Darwin':
        launch_command = "; ".join([
            f'echo -n -e "\033]0;{title}\007"',
            f'cd "{work_instance_dir}"',
            'clear',
            f'printf "{light_yellow}BakeLauncher Version: {Base.launcher_version}{reset}\\n"',
            f'printf "{light_blue}Minecraft Log Output: {reset}\\n"',
            'echo "==============================================="',
            minecraft_command,
            f'printf "{green}Minecraft has stopped running! (Thread terminated){reset}\\n"',
            'exit'
        ])
    elif Base.Platform == "Linux":
        launch_command = [
            f'echo -ne "\033]0;{title}\007"',
            f'echo -e {light_yellow}"BakeLauncher Version: {Base.launcher_version}"{reset}',
            f'echo -e {light_blue}"Minecraft Log Output: "{reset}',
            'echo "==============================================="',
            f'{minecraft_command}',
            f'echo -e {green}"Minecraft has stopped running! (Thread terminated)"{reset}]\n'
        ]
    else:
        launch_command = [
            f'echo -e "BakeLauncher Version: {Base.launcher_version}"',
            f'echo -e "Minecraft Log Output: "',
            'echo "==============================================="',
            f'{minecraft_command}',
            f'echo -e "Minecraft has stopped running! (Thread terminated)"\n'
        ]

    print("Baking Minecraft! :)", color='blue')  # Bring it back :)
    if EnableMultitasking:
        if not Base.DontPrintColor:
            if Base.LaunchMultiClientWithOutput:
                print("Please check the launcher already created a new terminal and Minecraft is running",
                      color='lightyellow')
            else:
                print("Please check if Minecraft is running.", color="lightyellow")
            print("If you can't find it, report the platform operation and launcher output to GitHub!",
                  color='lightyellow')
        else:
            print("Please check the launcher already created a new terminal.")
            print("If you can't find it, report the platform operation and launcher output to GitHub!")
        if Base.LaunchMultiClientWithOutput:
            print("EnableExperimentalMultitasking is Enabled!", color='purple')
            print("Creating mew client thread with log output...", color='green')
            client_process = multiprocessing.Process(
                target=
                create_new_client_thread_with_output,
                args=(launch_command, Base.Platform)
            )
            # Start the process
            client_process.start()
        else:
            print("EnableExperimentalMultitasking is Enabled!", color='purple')
            launch_command = f"{JVMExecutable} {minecraft_command_one_thread}"
            create_new_client_thread(launch_command)

    else:
        print("EnableExperimentalMultitasking is Disabled!", color='green')
        print('Launch Mode: Legacy', color='green')
        if Base.Platform == "Windows":
            subprocess.run(f"{JVMExecutable} {minecraft_command_one_thread}")
            print("Minecraft has stopped running! (Thread terminated)", color='green')
            EXIT = input("Press any key to continue. . .")
        else:
            os.system(minecraft_command)
            print("Minecraft has stopped running! (Thread terminated)", color='green')
            EXIT = input("Press any key to continue. . .")
