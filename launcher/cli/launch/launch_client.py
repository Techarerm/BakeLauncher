import os
import re
import subprocess
import threading
import multiprocessing
from LauncherBase import Base
from launcher.cli.display_util.util import print_color as print
from libs.clientlauncher.clauncher import client_launcher


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
                  JVMArgs, GameArgs, instances_id, legacy_method, launch_client_with_terminal):
    work_instance_dir = os.getcwd()
    minecraft_command, minecraft_command_one_thread = prepare_command(JVMExecutable, libraries_paths_strings,
                                                                      NativesPath, MainClass, JVMArgs, GameArgs)
    green = "\033[32m"
    light_yellow = "\033[93m"
    light_blue = "\033[94m"
    reset = "\033[0m"

    # Set title
    title = f"BakaLauncher: {instances_id}"
    print(minecraft_command)
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
    if not client_launcher.initialized:
        client_launcher.init(register_pool=Base.DaemonPool)

    if launch_client_with_terminal:
        print("Creating mew client thread with log output...", color='green')
        client_launcher.launch_client_with_terminal_legacy(launch_command)
    elif not legacy_method:
        if Base.Platform == "Windows":
            launch_command = f"{JVMExecutable} {minecraft_command_one_thread}"
        Status, client = client_launcher.createNewClientInstance(title, launch_command, daemon=True)
        if Status:
            client_launcher.startClientInstance(client)
    else:
        if Base.Platform == "Windows":
            launch_command = f"{JVMExecutable} {minecraft_command_one_thread}"
        if Base.Platform == "Windows":
            client_launcher.use_legacy_method(launch_command)
        else:
            client_launcher.use_legacy_method(launch_command)
