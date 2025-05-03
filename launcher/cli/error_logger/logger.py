import os
from datetime import datetime
from LauncherBase import Base


class Logger:
    def __init__(self):
        self.logs = ""
        self.start_date = datetime.now()

    def append(self, function_name, log_type, message):
        self.logs += f"[{function_name}] [{log_type}] : {message}\n"

    def clear(self):
        self.logs = ""

    def show_info(self):
        print("Logger Info :")
        for line in self.logs.split("\n"):
            print(line)

    def dump_logs(self):
        print("Dumping logs....")

        name = f"logs-{datetime.now().strftime('%Y_%m_%d_%H_%M_%S')}"

        file_path = os.path.join(Base.launcher_root_dir, "logs", name)

        with open(file_path, "w") as f:
            f.write(self.logs)