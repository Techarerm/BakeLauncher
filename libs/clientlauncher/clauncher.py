import os
import subprocess
import time
from datetime import datetime
from libs.lib import LIB_VERSION
import platform
from libs.clientlauncher import legacy
import threading
import queue


class clientInstance(threading.Thread):
    def __init__(self, name, commands, daemon=False):
        super().__init__()
        self.name = name
        self.commands = commands
        self.start_stream_output = threading.Event
        self.client = None
        self.start_date = datetime.now()
        self.output = ""
        self.daemon = daemon

    def start(self):
        try:
            self.client = subprocess.Popen(f"{self.commands}", stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                           text=True)
            print(f"[clientInstance] Java Runtimes PID : {self.client.pid}")
        except Exception as e:
            return False, e

    def is_alive(self):
        return self.client.poll() is None


class clientLauncherDaemon(threading.Thread):
    def __init__(self):
        super().__init__()
        self.fresh_daemon = threading.Thread(target=self.checkClientPool)
        self.refresh_delay = 10

    def checkClientPool(self):
        while True:
            for client_instance in client_launcher.client_pool:
                if not client_instance.is_alive():
                    client_launcher.client_pool.remove(client_instance)
            time.sleep(self.refresh_delay)

    def start(self):
        self.fresh_daemon.start()

    def is_alive(self):
        return self.fresh_daemon.is_alive()

    def cleanup(self):
        for client_instance in client_launcher.client_pool:
            if client_instance.is_alive():
                client_instance.close()


class clientLauncher:
    def __init__(self):
        self.initialized = False
        self.client_pool = []
        self.client_launcher_daemon = clientLauncherDaemon()

    def init(self, info=True, custom_payload=None, start_daemon=True, register_pool=None):
        process_id = os.getpid()
        _locals = locals()
        print("clientLauncher > Initializing...")
        if info:
            print(f"Version Lib-{LIB_VERSION}")
            print(f"Init date: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
            print("")

        if custom_payload is not None:
            print(custom_payload)

        self.client_pool = []

        if start_daemon:
            self.client_launcher_daemon.start()

            if register_pool is not None:
                register_pool.append(self.client_launcher_daemon)

        self.initialized = True

    def createNewClientInstance(self, client_name, command, daemon=False):
        if hasattr(self, client_name):
            return False, "clientNameExists"

        client_instance = clientInstance(client_name, command, daemon=daemon)
        setattr(self, client_name, client_instance)
        self.client_pool.append(client_instance)

        client_instance.daemon = daemon

        return True, client_instance

    def startClientInstance(self, target_client_instance):
        print("clientLauncher > Preparing ClientInstance...")
        if not target_client_instance in self.client_pool:
            return False, "clientInstanceNotExists"

        info = target_client_instance.start()
        if type(info) == tuple:
            if not info[0]:
                print(info[1])
                return False, info[1]

        return True, None

    def start_streaming_output(self, target_client_instance):
        if not target_client_instance in self.client_pool:
            return False, "clientInstanceNotExists"

        target_client_instance.start_stream_output.set()

        return True, None

    def kill_client_process(self, target_client_instance):
        if not target_client_instance in self.client_pool:
            return False, "clientInstanceNotExists"

        try:
            target_client_instance.kill()
            self.client_pool.remove(target_client_instance)
            return True, None
        except Exception as e:
            print("An exception occurred: {}".format(e))
            return False, e

    def refresh_client_pool(self):
        for client_instance in self.client_pool:
            if not client_instance.is_alive():
                print("Died: {}".format(client_instance.name))
            else:
                print("Still alive: {}".format(client_instance.name))

    @staticmethod
    def launch_client_with_terminal_legacy(command):
        print("clientLauncher > Launching...")
        print("[INFO] Launch Data : {}".format(datetime.now().strftime('%d/%m/%Y %H:%M:%S')))
        print("# Using this method clients cannot be seen in the client pool.")
        print("# Also, you can't control this client such as kill it.")
        print("Creating terminal window....")
        if platform.system() == "Darwin":
            Status, code, pid = legacy.create_client_with_terminal_window_darwin(command)
        elif platform.system() == "Windows":
            Status, code, pid = legacy.create_client_with_terminal_window_nt(command)
        elif platform.system() == "Linux":
            Status, code, pid = legacy.create_client_with_terminal_window_linux(command)
        else:
            print("[clientLauncher] Unsupported platform.")
            return

        if Status:
            print("Client process id : {}".format(pid))
        else:
            print("Client stop code : {}".format(code))

    def use_legacy_method(self, command):
        print("clientLauncher > Launching...")
        print("[INFO] Launch Data : {}".format(datetime.now().strftime('%d/%m/%Y %H:%M:%S')))
        print("# Using this method clients cannot be seen in the client pool.")
        print("# Your terminal window will be occupied by the client instance (until it closes)")
        print("Client logs start from here :")
        try:
            subprocess.run(f"{command}")
        except Exception as e:
            print("An exception occurred: {}".format(e))


client_launcher = clientLauncher()
