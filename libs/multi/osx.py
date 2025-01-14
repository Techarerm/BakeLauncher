# -*- coding: utf-8 -*-
import os
from AppKit import NSWorkspace
from Foundation import NSAppleScript


def create_terminal(launch_command, workDir):
    if workDir is None:
        workDir = os.getcwd()

    full_script = f'''
    tell application "Terminal"
        do script ""
        set win to front window
        set position of win to {{0, 0}}
        set bounds of win to {{0, 0, 800, 600}}
        do script "{launch_command}" in win
    end tell
    '''

    script = NSAppleScript.alloc().initWithSource_(full_script)

    result, e_message = script.executeAndReturnError_(None)
    if result:
        pid = result.stringValue()
        print(f"Client Process ID: {pid}")
    else:
        print(f"An error occurred {e_message}")



