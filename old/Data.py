import os
import sys
import threading
from LauncherBase import Base
from modules.print_colorx.print_color import print as print_color


class DataBase:
    def __init__(self):
        # Flag and list(Set by launcher)
        self.EndLoadFlag = False  # If the loading process failed (such as platform check failure), set to true.
        self.MainMenuResetFlag = False  # Set to true by check_account_data_are_valid or other functions
        self.InternetConnected = False
        self.StartUsingErrorLog = False
        self.RefreshTokenFailedFlag = False
        self.LauncherFullResetFlag = False
        self.UnknownPlatform = False
        self.DontLoadMainMemu = False
        # Global stuff
        self.Debug = False
        self.DontPrintColor = False  # Stop print colorful text
        self.DisableClearOutput = False  # Debug
        self.DefaultAccountID = None
        self.LauncherWorkDir = None  # Setting from the global config file
        self.NoPrintConfigInfo = False
        self.NoInternetConnectionCheck = False
        self.PingServerIP = None
        self.BypassLoginStatusCheck = False
        # main_menu stuff
        self.NoList = False  # Make main_menu not print the list
        self.AutomaticOpenOption = False  # Start the selected option when load main_menu (from global config)
        self.AutoOpenOptionName = None  # Select option
        self.LauncherTitleColor = 'lightblue'
        # LaunchManager stuff
        self.AutomaticLaunch = False
        self.QuickLaunch = None
        self.QuickInstancesName = None
        self.MaxInstancesPerRow = 20
        self.EnableExperimentalMultitasking = False
        self.LaunchMultiClientWithOutput = True
        self.DefaultGameScreenHeight = 720
        self.DefaultGameScreenWidth = 1280
        self.JVMUsageRamSizeMinLimit = 2048
        self.JVMUsageRamSizeMax = 4096
        # Duke
        self.PrioUseOfSpecifiedJVM = True  # When launching game, priority use specified JVM path (CustomJVMInstallPath)
        self.CustomJVMInstallPath = None  # Custom runtimes
        self.SearchJVMInCustomPath = False  # When searching available JVM, append it to the search list.
        # (Type = Custom-Installed)
        # Create Instance stuff
        self.OverwriteJVMIfExist = False  # Overwrite JVM runtimes without asking user
        # (If minecraft_version require jvm_version available in the 'runtimes' folder)
        self.DoNotAskJVMExist = False  # If the version requires an installed version of runtimes,
        # skip asking the user to reinstall it
        self.UsingLegacyDownloadOutput = False  # Legacy download output is good.
        self.MaxVersionPerLine = 5  # Check config to get more information!
        self.setting_dict = {
            "BOOL%Debug": self.Debug,
            "BOOL%DisableClearOutput": self.DisableClearOutput,
            "BOOL%DontPrintColor": self.DontPrintColor,
            "BOOL%NoList": self.NoList,
            "BOOL%AutomaticOpenOption": self.AutomaticOpenOption,
            "BOOL%QuickLaunch": self.QuickLaunch,
            "BOOL%PrioUseOfSpecifiedJVM ": self.PrioUseOfSpecifiedJVM,
            "BOOL%SearchJVMInCustomPath": self.SearchJVMInCustomPath,
            "BOOL%DoNotAskJVMExist": self.DoNotAskJVMExist,
            "BOOL%OverwriteJVMIfExist": self.OverwriteJVMIfExist,
            "BOOL%UsingLegacyDownloadOutput": self.UsingLegacyDownloadOutput,
            "BOOL%NoInternetConnectionCheck": self.NoInternetConnectionCheck,
            "BOOL%BypassLoginStatusCheck": self.BypassLoginStatusCheck,
            "BOOL%EnableExperimentalMultitasking": self.EnableExperimentalMultitasking,
            "BOOL%LaunchMultiClientWithOutput": self.LaunchMultiClientWithOutput,
            "BOOL%AutomaticLaunch": self.AutomaticLaunch,
            "INT%DefaultAccountID": self.DefaultAccountID,
            "STR%AutoOpenOptionName": self.AutoOpenOptionName,
            "STR%LauncherTitleColor": self.LauncherTitleColor,
            "STR%CustomJVMInstallPath": self.CustomJVMInstallPath,
            "STR%LauncherWorkDir": self.LauncherWorkDir,
            "STR%PingServerIP": self.PingServerIP,
            "INT%MaxInstancesPerRow": self.MaxInstancesPerRow,
            "INT%MaxVersionPerLine": self.MaxVersionPerLine,
            "STR%QuickInstancesName": self.QuickInstancesName,
            "INT%DefaultGameScreenWidth": self.DefaultGameScreenWidth,
            "INT%DefaultGameScreenHeight": self.DefaultGameScreenHeight,
            "INT%JVMUsageRamSizeMinLimit": self.JVMUsageRamSizeMinLimit,
            "INT%JVMUsageRamSizeMax": self.JVMUsageRamSizeMax
        }
        # Dev stuff
        self.AllowModify = False
        self.AllowUnsafeImport = False
        self.AllowLoadCustomModules = False
        self.CustomModulesPathList = []
        self.BypassLoginRequire = False
        self.PrintThreadInfo = False
        self.DevelopmentMode = True
        if self.DevelopmentMode:
            self.AllowModify = True
            self.AllowUnsafeImport = True
            self.AllowLoadCustomModules = True
            self.CustomModulesPathList = []
            self.BypassLoginRequire = False
            self.PrintThreadInfo = False
        else:
            self.AllowModify = False


DB = DataBase()


def ClearOutput():
    if not DB.DisableClearOutput:
        if Base.Platform == "Windows":
            os.system("cls")
        elif Base.Platform == "Darwin":
            os.system("clear")
        elif Base.Platform == "Linux":
            os.system("clear")
    else:
        return


"""
def print_custom(*args, **kwargs):
    thread_id = None
    if Base.PrintThreadInfo:
        thread_id = threading.get_ident()

    if not Base.DontPrintColor:
        color = kwargs.pop('color', None)  # Remove color from kwargs if it exists
        if not Base.PrintThreadInfo:
            print_color(*args, color=color, **kwargs)  # Pass remaining args and color
        else:
            print_color(f"[{thread_id}] ", *args, color=color, **kwargs)
    else:
        if not Base.PrintThreadInfo:
            print(*args)
        else:
            print(f"[{thread_id}] ", *args)
"""

def print_custom(*args, **kwargs):
    thread_id = None

    if not DB.DontPrintColor:
        color = kwargs.pop('color', None)  # Remove color from kwargs if it exists
        print_color(*args, color=color, **kwargs)

    else:
        print(*args)