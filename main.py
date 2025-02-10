"""
The main of the BakeLauncher
main.py

Launcher load process:
Init>self.launcher_loader>Init Base>self.main>Start main_memu in new thread>terminated
"""
import multiprocessing
import threading
import time
import traceback
import textwrap
import datetime
import os
from LauncherBase import Base, ClearOutput, BetaWarningMessage, print_custom as print, load_custom_modules
from libs.main_menu import main_menu


class BakeLauncher:
    def __init__(self):
        self.StartStatus = False
        self.Message = None
        self.launcher_loader()

    def load_base(self):
        # Load LauncherBase
        try:
            self.StartStatus, self.Message = Base.Initialize
        except Exception as e:
            ClearOutput()
            tb = traceback.format_exc()  # Full traceback as a string
            function_name = traceback.extract_tb(e.__traceback__)[-1].name
            print(f"BakeLauncher has crashed :( Caused by failed to load Base.", color='lightred')
            print(f"Crash at function name Base.{function_name}()")
            print(f"Error {e}")
            print(f"Detailed traceback:\n{tb}")
            self.generate_crash_log(tb, function_name, e, BaseInitialized=False)

    def launcher_loader(self):
        # Start the launcher process if loading base pass
        while True:
            if not self.StartStatus:
                self.load_base()

            if self.StartStatus:
                try:
                    self.main()
                except Exception as e:
                    # Extract the function name from the traceback
                    ClearOutput()
                    tb = traceback.format_exc()  # Full traceback as a string
                    function_name = traceback.extract_tb(e.__traceback__)[-1].name
                    print(f"BakeLauncher has crashed :( Caused by an error in function '{function_name}': {e}",
                          color='lightred')
                    print(f"Crash at function name {function_name}")
                    print(f"Error {e}")
                    print(f"Detailed traceback:\n{tb}")
                    self.generate_crash_log(tb, function_name, e, BaseInitialized=True)
            else:
                print("Init Error :(", color='red')
                print("If BakeLauncher crashes while loading Base. You can try deleting the invalid profile, this may "
                      "help resolve the issue")

            print("BakeLauncher thread terminated!")
            if Base.LauncherFullResetFlag:
                input("Press any key to reset all thing...")
                self.StartStatus = False
                Base.LauncherFullResetFlag = False
            else:
                EXIT_CODE = str(input("Press any key to continue..."))
                return True

    def main(self):
        # DEBUG for platform check
        print(f"BakeLauncher: Launcher is running on platform : {Base.Platform}", color='lightblue')
        if Base.Debug:
            print(f"Thread Info > PID : {os.getpid()} | Thread : {threading.get_ident()}", color='lightblue')
        ClearOutput()

        # Print BetaWarningMessage
        print(BetaWarningMessage, color='yellow')
        ClearOutput()

        # Dev only
        if Base.AllowModify:
            load_custom_modules()

        # Load main menu
        main_menu_thread = threading.Thread(target=main_menu)
        main_menu_thread.start()

        while True:
            Status = main_menu_thread.is_alive()
            if not Status:
                return
            time.sleep(0.1)


    @staticmethod
    def generate_crash_log(tb, crash_function, e, BaseInitialized):
        crash_log = textwrap.dedent(f"""\
        [BakeLauncher Crash Log]
        
        Launcher Version: {Base.launcher_version}
        Version Type: {Base.launcher_version_type}
        Internal Name: {Base.launcher_internal_version}
        BaseInitialized = {BaseInitialized}
        
        Date: {datetime.datetime.now()}
        Crash at function name: {crash_function}
        Exception:
        {e}
        
        Detailed traceback:
        {tb}        
        """)

        if not os.path.exists("logs"):
            os.mkdir("logs")

        crash_log = "\n".join(line.lstrip() for line in crash_log.splitlines())
        # Format the timestamp to avoid invalid characters
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        log_name = f"crash_{timestamp}.log"
        crash_log_save_path = os.path.join(Base.launcher_root_dir, "logs", log_name)

        with open(crash_log_save_path, "w") as f:
            f.write(crash_log)

        print(f"Crash log has been saved to {crash_log_save_path}")


if __name__ == "__main__":
    # Added multitasking(?) support(for LaunchClient and pyinstaller...)
    multiprocessing.freeze_support()
    BakeLauncher()

