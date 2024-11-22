"""
Main
(BakeLauncher Main)
CheckArch(Call LauncherBase)>GetPlatformName>Load Main_Memu>Ended
"""
import multiprocessing
from LauncherBase import Base, ClearOutput, BetaWarningMessage, print_custom as print
from libs.main_memu import main_memu


class BakeLauncher:
    """
    Main(Just main :D )
    Check platform and arch support > check args > main_memu or parse_arguments > terminated
    """
    def __init__(self):

        # Load LauncherBase
        StartStatus, Message = Base.Initialize()

        # Start launcher process if loading base pass
        if StartStatus:
            self.main()
        else:
            print(f"Can't init BakeLauncher. Cause by {Message}")

        print("BakeLauncher thread terminated!")
        input("Press any key to continue...")

    def main(self):
        # DEBUG for platform check
        print(f"BakeLauncher: Launcher is running on platform: {Base.Platform}", color='blue')
        ClearOutput()

        # Print BetaWarningMessage
        print(BetaWarningMessage, color='yellow')
        ClearOutput()

        # Load main menu
        main_memu()


if __name__ == "__main__":
    # Added multitasking(?) support(for LaunchClient and pyinstaller...)
    multiprocessing.freeze_support()
    BakeLauncher()
