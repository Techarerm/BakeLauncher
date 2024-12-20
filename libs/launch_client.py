import os
import tempfile
import subprocess
import time
import multiprocessing
from LauncherBase import Base, print_custom as print

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


def create_new_client_thread_with_output(launch_command, title, PlatFormName):
    FailedToLaunch = False

    if PlatFormName == 'Windows':
        # Create the temp batch file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.bat') as command:
            command.write(f"@echo off\n".encode())
            command.write(f'title {title}\n'.encode())
            command.write(f"{launch_command}\n".encode())
            command.write("del %~f0\n".encode())
            command.write("pause\n".encode())
            final_command = command.name

        try:
            # Launch the process
            print("Creating launch thread...")
            process = subprocess.Popen(
                ['cmd.exe', '/c', 'start', 'cmd.exe', '/k', final_command],
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE
            )
        except Exception as e:
            FailedToLaunch = True
            print(f"Error in Windows process: {e}")

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
        client = multiprocessing.Process(target=launch_process
                                         , args=(launch_command,))
        client.start()
    except Exception as e:
        print(f"Failed to create launch process. Cause: {e}")


def LaunchClient(JVMExecutable, libraries_paths_strings, NativesPath, MainClass,
                 JVMArgs, GameArgs, custom_game_args, instances_id,
                 EnableMultitasking, MultiClientOutput):
    work_instance_dir = os.getcwd()
    # Construct the Minecraft launch command with proper quoting
    minecraft_command = (
        f'{JVMExecutable} {JVMArgs} '
        f'-Djava.library.path="{NativesPath}" -cp "{libraries_paths_strings}" '
        f'{MainClass} {GameArgs} {custom_game_args}'
    )

    # Is for launch using one thread method
    cleaned_jvm_path = JVMExecutable.replace('""', '')
    minecraft_command_one_thread = (
        f'{JVMArgs} '
        f'-Djava.library.path="{NativesPath}" -cp "{libraries_paths_strings}" '
        f'{MainClass} {GameArgs} {custom_game_args}'
    )

    # Debug jvm args
    args = (
        f'{cleaned_jvm_path} {JVMExecutable} {JVMArgs} '
        f'-Djava.library.path="{NativesPath}" -cp "{libraries_paths_strings}" '
        f'{MainClass} {GameArgs} {custom_game_args}'
    )
    # if Base.Debug:
    # print(args)

    green = "\033[32m"
    blue = "\033[34m"
    light_yellow = "\033[93m"
    light_blue = "\033[94m"
    reset = "\033[0m"

    # Set title
    title = f"BakaLauncher: {instances_id}"

    # Create the full launch command with version logging and Minecraft command
    if Base.Platform == 'Windows':
        launch_command = [
            f'echo {light_yellow}BakeLauncher Version: {Base.launcher_version}{reset}',
            f'echo {light_blue}Minecraft Log Output: {reset}',
            'echo ================================================',
            f'{minecraft_command}',
            f'echo {green}Minecraft has stopped running! (Thread terminated){reset}'
        ]
    elif Base.Platform == 'Darwin':
        launch_command = [
            f'echo -ne "\033]0;{title}\007\n"',
            f'cd {work_instance_dir}\n',
            f'clear\n',
            f'printf "{light_yellow}BakeLauncher Version: {Base.launcher_version}{reset}\\n"',
            f'printf "{light_blue}Minecraft Log Output: {reset}\\n"',
            'echo "==============================================="',
            f'{minecraft_command}',
            f'printf "{green}Minecraft has stopped running! (Thread terminated){reset}\\n"',
            f'exit\n'
        ]
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

    # Join the commands with newline characters for the batch file
    launch_command = '\n'.join(launch_command)

    # For unix-like...
    if not Base.Platform == "Windows":
        if os.path.exists("LaunchLoadCommandTemp.sh"):
            os.remove("LaunchLoadCommandTemp.sh")

        with open("LaunchLoadCommandTemp.sh", "w+") as f:
            f.write(launch_command)

    print("Baking Minecraft! :)", color='blue')  # Bring it back :)

    if EnableMultitasking:
        if not Base.DontPrintColor:
            print("Please check the launcher already created a new terminal.", color='purple')
            print("If it didn't create it please check the output and report it to GitHub!", color='green')
        else:
            print("Please check the launcher already created a new terminal.")
            print("If it didn't create it please check the output and report it to GitHub!")
        if Base.LaunchMultiClientWithOutput:
            print("EnableExperimentalMultitasking is Enabled!", color='purple')
            print("Creating mew client thread with log output...", color='green')
            client_process = multiprocessing.Process(
                target=
                create_new_client_thread_with_output,
                args=(launch_command, title, Base.Platform)
            )
            # Start the process
            client_process.start()
        else:
            print("EnableExperimentalMultitasking is Enabled!", color='purple')
            launch_command = f"{JVMExecutable} {minecraft_command_one_thread}"
            create_new_client_thread(launch_command)

    else:
        print("EnableExperimentalMultitasking is Disabled!", color='green')
        print('"Launch Mode: Legacy', color='green')
        if Base.Platform == "Windows":
            local = os.getcwd()
            subprocess.run(f"{JVMExecutable} {minecraft_command_one_thread}")
            print("Minecraft has stopped running! (Thread terminated)", color='green')
            back_to_main_memu = input("Press any key to continue. . .")
        else:
            os.system(minecraft_command)
            print("Minecraft has stopped running! (Thread terminated)", color='green')
            back_to_main_memu = input("Press any key to continue. . .")
