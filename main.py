import argparse
import importlib.util
import json
import os
import sys
import logging
import threading
import time
from launcher.cli.main_menu import main_menu
from LauncherBase import Base


class BakeLauncher:
    def __init__(self):
        self.start_time = time.time()
        self.boot_args = sys.argv
        self.arguments_parser()
        self.development_mode = False
        self.debug = False
        self.main_interface = main_menu.menuMain
        self.main()

    def arguments_parser(self):
        parser = argparse.ArgumentParser(
            description="BakeLauncher Arguments Parser Info",
        )

        parser.add_argument("-debug", help="Enable debug mode", action="store_true")
        parser.add_argument("-development-mode", help="Enable development mode", action="store_true")

        args = parser.parse_args()

        if args.debug:
            logging.basicConfig(level=logging.DEBUG)
            Base.Debug = True
            self.debug = True

        if args.development_mode:
            Base.DevelopmentMode = True
            self.development_mode = True

        return args

    def modules_loader(self):
        mods_folder = os.path.join(Base.launcher_root_dir, "mods")
        if not os.path.exists(mods_folder):
            return

        folder_list = os.listdir(mods_folder)

        mod_paths_list = []
        for name in folder_list:
            path = os.path.join(mods_folder, name)
            mod_paths_list.append(path)

        for mod_path in mod_paths_list:
            mod_info = os.path.join(mod_path, "mod.info.json")
            if not os.path.exists(mod_info):
                continue

            try:
                with open(mod_info, "r") as f:
                    mod_info = json.load(f)
            except Exception as e:
                print("[Warning] Cannot load mod info from {} ERR: {}".format(mod_info, e))
                continue

            mod_main_name = mod_info.get("modMain", None)
            mod_main_file = mod_info.get("modMainFile", None)
            mod_main_file_path = os.path.join(mod_path, mod_main_file)
            mod_group_id = mod_info.get("groupID", None)
            mod_type = mod_info.get("modType", None)
            blockMain = mod_info.get("blockMain", False)
            require_main_class = mod_info.get("requireMainClass", False)

            if not os.path.exists(mod_main_file_path):
                continue

            if mod_main_name is None:
                continue

            # Define a unique module name based on the file path
            module_name = f"mod_{hash(mod_main_file_path)}"

            # Loading mod
            try:
                spec = importlib.util.spec_from_file_location(module_name, mod_main_file_path)
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module  # Register module in sys.modules
                spec.loader.exec_module(module)
            except Exception as e:
                print("[Warning] Cannot load module {} ERR: {}".format(mod_group_id, e))
                continue

            if not hasattr(module, mod_main_name):
                print(f"[DEBUG] Modules name {mod_group_id} load failed. modMain missing.")
                continue

            mod_function = getattr(module, mod_main_name)
            if not callable(mod_function):
                print(f"[DEBUG] Modules name {mod_group_id} load failed. Not callable.")
                continue

            # Get the function dynamically
            if mod_type == "loadable_modules":
                mod_func = lambda: mod_function(self) if require_main_class else mod_function

                if not blockMain:
                    threading.Thread(target=mod_func).start()
                    print(f"[DEBUG] Modules name {mod_group_id} has been loaded.")
                else:
                    module_thread = threading.Thread(target=mod_func)
                    module_thread.start()
                    module_thread.join()

    def main(self):
        base_status, e = Base.Initialize

        if self.debug:
            spend_time = time.time() - self.start_time
            print(f"[Debug] Loading the launcher took time:{spend_time: 4f}")

        if not base_status:
            print("Init Error :(")
            print(f"ERR CODE: {e}")
            return

        self.arguments_parser()
        if self.development_mode:
            print("[DEBUG] Development mode is enabled. Loading modules...")
            self.modules_loader()

        if self.debug:
            spend_time = time.time() - self.start_time
            print(f"[Debug] Loading the launcher took time:{spend_time: 4f}")

        self.main_interface()


if __name__ == "__main__":
    BakeLauncher()
    print("Launcher terminated.")
    sys.exit(0)
