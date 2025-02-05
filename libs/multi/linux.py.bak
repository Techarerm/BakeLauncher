import os
import shutil
import subprocess

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


def find_internal_terminal(terminal_list):
    for terminal in terminal_list:
        if shutil.which(terminal):
            return terminal
    return None


def create_terminal(launch_command, workDir):
    if workDir is None:
        workDir = os.getcwd()

    recommended_terminal = find_internal_terminal(terminals)

    if not recommended_terminal:
        print("Unsupported Linux build.")
        return

    try:
        os.system(f"gnome-terminal -- bash -c '{launch_command}; exec bash'")
    except FileNotFoundError:
        for terminal in terminals:
            try:
                print(f"Trying {terminal}...")
                if terminal == "xterm" or terminal == "st":
                    subprocess.run([terminal, "-hold", "-e", launch_command])
                else:
                    os.system(f"{terminal} -e bash -c '{launch_command}; exec bash'")
                break
            except FileNotFoundError:
                print(f"{terminal} not found, trying next terminal...")
        else:
            print("No suitable recommended terminal found.")