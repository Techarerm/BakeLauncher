"""
https://learn.microsoft.com/zh-tw/windows/win32/api/processthreadsapi/nf-processthreadsapi-createprocessa
"""
import os
import win32process
import win32con
import win32security


def create_terminal(launch_command, workDir):
    # Set up the necessary security attributes (can be None if not required)
    sa = win32security.SECURITY_ATTRIBUTES()
    sa.bInheritHandle = 1

    # Launch command (Using cmd as the recommended setting)
    command = "cmd /c " + launch_command

    # Create the client process
    startupinfo = win32process.STARTUPINFO()
    startupinfo.dwFlags = win32con.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = win32con.SW_SHOWNORMAL

    if workDir is None:
        workDir = os.getcwd()

    process_info = win32process.CreateProcess(
        None,  # ApplicationName
        command,  # Command line (cmd.exe)
        None,  # Process attributes
        None,  # Thread attributes
        0,  # Inherit handles
        win32con.CREATE_NEW_CONSOLE,  # Create a new console
        None,  # Environment variables
        workDir,  # Set workDir
        startupinfo  # Startup information
    )

    # Process information contains the PID and other details (optional to use)
    print(f"Client Process ID: {process_info[2]}")
