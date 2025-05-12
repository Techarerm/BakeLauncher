import subprocess
import sys
import threading
from datetime import datetime
import keyboard


class universal(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def launch_client(self, full_launch_command):
        self.process = subprocess.Popen(full_launch_command,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE,
                                        text=True, bufsize=1,
                                        universal_newlines=True)




universal = universal()


"""
class clientLauncher:
    def __init__(self):
        super().__init__()
        self.client_thread = None
        self.stop_log_thread_event = threading.Event()

    def start(self, launch_command):
        thread = self.create_client_thread(launch_command)
        return thread

    @staticmethod
    def create_client_process(command):
        subprocess.Popen(command,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE,
                         text=True, bufsize=1,
                         universal_newlines=True)

    def create_client_thread(self, jvm_launch_command):
        self.client_thread = threading.Thread(target=self.create_client_process, args=(jvm_launch_command,))
        self.client_thread.start()
        return self.client_thread

    @staticmethod
    def start_log_output(thread, logs):
        if thread.is_alive():
            while True:
                for line in thread.stdout:
                    sys.stdout.write("{line}".format(line=line))
                    sys.stdout.flush()
                    logs += f"{line}\n"

                thread.process.stdout.close()
                thread.process.wait()
"""