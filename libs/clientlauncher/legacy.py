import os
import subprocess
import tempfile

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


def create_client_with_terminal_window_nt(launch_command):
    with tempfile.NamedTemporaryFile(delete=False, suffix='.bat') as command:
        command.write(f"@echo off\n".encode())
        command.write(f"{launch_command}\n".encode())
        command.write("del %~f0\n".encode())
        command.write("pause\n".encode())
        final_command = command.name

    try:
        process = subprocess.Popen(
            ['cmd.exe', '/c', 'start', 'cmd.exe', '/k', final_command],
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE
        )
        return True, None, process.pid
    except Exception as e:
        print(f"Error in Windows process: {e}")
        return False, e, None


def create_client_with_terminal_window_darwin(launch_command):
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

    try:
        process = subprocess.Popen(
            ['osascript', '-e', f'\'{apple_script}\''],
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE
        )
        return True, None, process.pid
    except Exception as e:
        print(f"Error in macOS process: {e}")
        return False, e, None


def create_client_with_terminal_window_linux(launch_command):
    try:
        os.system(f"gnome-terminal -- bash -c '{launch_command}; exec bash'")
        process = subprocess.Popen(["gnome-terminal", "--", "bash", "-c", f"'{launch_command}; exec bash'"])
    except FileNotFoundError:
        for terminal in terminals:
            try:
                if terminal == "xterm" or terminal == "st":
                    # xterm and st need different syntax
                    process = subprocess.Popen([terminal, "-hold", "-e", launch_command])
                else:
                    # All other terminals
                    process = subprocess.Popen([terminal, "-e", "bash", "-c", f"'{launch_command}; exec bash'"])
                return True, None, process.pid
            except FileNotFoundError:
                continue
            except Exception as e:
                return False, e, None
        return False, "No suitable recommended terminal found.", None
