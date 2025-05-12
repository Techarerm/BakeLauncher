import subprocess
import sys
import time
from datetime import datetime

a = False


class progress_the_bar:
    def __init__(self):
        self.count = 0
        self.title_text = 'Progress...'
        self.progress_symbol = "*"
        self.symbol_quantity = 0

    def init(self, count, **kwargs):
        self.count = count
        self.title_text = kwargs.get('text', self.title_text)
        self.progress_symbol = kwargs.get('progress_symbol', self.progress_symbol)
        self.symbol_quantity = 0

    def add(self):
        text = ""
        self.symbol_quantity += 1
        spaces = self.count - self.symbol_quantity
        for n in range(0, self.symbol_quantity):
            text += self.progress_symbol

        for space in range(0, spaces):
            text += " "

        sys.stdout.write(f'\r {self.title_text} [{text}]')
        time.sleep(0.01)


def progress_bar(wait_time):
    progress_symbol = "*"
    for i in range(wait_time + 1):
        text = ""
        spaces = wait_time - i
        for n in range(0, i):
            text += progress_symbol

        for space in range(0, spaces):
            text += " "

        sys.stdout.write(f'\r Progress... [{text}]')
        time.sleep(0.01)

def client_view():
    print("Client Log Viewer")
    while True:
        sys.stdout.write(f"Logs : \n {logs}")
        sys.stdout.write(f"\rDate : {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print("")
        time.sleep(0.1)


def test_playground_java(java_bin, jar_file):
    try:
        process = subprocess.Popen([java_bin, jar_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        while True:
            line = process.stdout.readline()
            if not line:
                break
            print(line.decode().strip())  # Stream output

        process.wait()
    except Exception as e:
        raise e


class clientLauncher:
    def __init__(self):
        self.logs = ""
        self.process = None

    def init_clientLauncher(self):
        print("ClientLauncher")
        print("Preparing for launch...")
        self.logs += "ClientLauncher\n"
        self.logs += "Version 0.1\n"
        self.logs += f"Create Date: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n"

    def launch_client(self, full_launch_command):
        self.process = subprocess.Popen(full_launch_command,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE,
                                        text=True, bufsize=1,
                                        universal_newlines=True)

    def start_streaming_output(self):
        for line in self.process.stdout:
            sys.stdout.write("{line}\n".format(line=line))
            sys.stdout.flush()
            self.logs += f"{line}\n"

        self.process.stdout.close()
        self.process.wait()

    def kill_client_process(self):
        try:
            self.process.kill()
        except Exception as e:
            print("An exception occurred: {}".format(e))

    def save_streaming_output(self, output_file_path):
        with open(output_file_path, 'w') as output_file:
            output_file.write(self.logs)



"""
pg = progress_the_bar()

pg.init(100)
for i in range(100):
    pg.add()
    time.sleep(0.1)
"""

import subprocess
import sys
import time

class ScrollingOutput:
    def __init__(self, command, max_lines=5):
        self.command = command
        self.output_lines = []
        self.max_lines = max_lines

    def run(self):
        process = subprocess.Popen(self.command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1, universal_newlines=True)

        for line in process.stdout:
            line = line.rstrip()  # Remove trailing newlines
            if line:
                self.output_lines.append(line)
                if len(self.output_lines) > self.max_lines:
                    self.output_lines.pop(0)  # Remove the oldest line

                # Move cursor up and clear previous lines
                sys.stdout.write("\033[F" * self.max_lines)  # Move cursor up by max_lines
                sys.stdout.write("\033[J")  # Clear screen from cursor down

                # Print the updated output buffer
                for out_line in self.output_lines:
                    print(out_line)

                  # Force update in terminal

        process.stdout.close()
        process.wait()



print(getattr(sys, "frozen", False))