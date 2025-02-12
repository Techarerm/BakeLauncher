import importlib.util
import os.path
import shutil
import sys
import time
import importlib
from libs.instance.instance import instance
from libs.version.version import *
from libs.libraries.libraries import *
from libs.__assets_grabber import assets_grabber
from libs.Utils.utils import *

all_funs = ["function", "create_a_custom_instance", "test_hook_mod"]


def download_libraries_test(version_data, libraries_dir, **kwargs):
    """
    Download require libraries (from version data)
    """
    library_are_native = False
    # Some parameter stuff
    normal_download = kwargs.get("normal_download", False)
    bypass_download_natives = kwargs.get("bypass_download_natives", False)
    name = "libraries"
    # Confirm libraries_dir are created
    os.makedirs(libraries_dir, exist_ok=True)

    # Waiting-Download-List
    multi_download_queue = []
    download_url_list = []
    download_path_list = []
    checksum_list = []

    # Get libraries data from version_data
    libraries = version_data.get('libraries', [])

    # Search support user platform libraries
    for lib in libraries:
        lib_downloads = lib.get('downloads', {})
        artifact = lib_downloads.get('artifact')

        rules = lib.get('rules', None)
        if rules:
            # Bypass download native
            continue

        if artifact:
            lib_path = artifact.get('path', None)
            if lib_path is None:
                continue

            lib_url = artifact.get('url', None)
            if lib_url is None:
                continue

            sha = artifact.get('sha1', None)
            checksum_list.append(sha)

            lib_dest = os.path.join(libraries_dir, lib_path)
            os.makedirs(os.path.dirname(lib_dest), exist_ok=True)

            if library_are_native and bypass_download_natives:
                continue

            download_url_list.append(lib_url)
            download_path_list.append(lib_dest)

    if normal_download:
        for url, dest_path in zip(download_url_list, download_path_list):
            download_file(url, dest_path)
    else:
        multithread_download(download_url_list, download_path_list, "libraries",
                             with_verify_checksum=True, file_hash_list=checksum_list,
                             download_with_progress_bar=True)

    if len(multi_download_queue) > 0:
        return True
    else:
        return False


def function():
    version_data = get_version_data("1.21.4")
    libraries_dir = os.path.join(Base.launcher_tmp_dir, "libraries")

    if os.path.exists(libraries_dir):
        shutil.rmtree(libraries_dir)

    download_libraries_test(version_data, libraries_dir)

    exit_code = input("Press any key to exit playground...")


def create_a_custom_instance():
    global libraries_folder_path
    print("***CUSTOM INSTANCE***", color='lightgreen')
    instance_name = str(input("Name of instance: "))
    print("If you want to create minecraft version can't find in the version manifest, "
          "just type a version which launch method is similar version.", color='purple')
    client_version = str(input("Version of client (must can be found in the version manifest) : "))
    main_class = str(input("Main class (can be custom) : "))
    support_java_version = str(input("Support java version (example: 8 or 17) : "))
    version_type = str(input("Version type (can be custom) : "))
    assets_version = str(input("Assets version (must can be download from the mojang server) :"))
    real_minecraft_version = input("Real minecraft version (can be custom) : ")

    print("Creating folder..", color='lightgreen')
    instance_dir = os.path.join(Base.launcher_instances_dir, instance_name)
    game_folder = os.path.join(instance_dir, ".minecraft")

    if os.path.exists(instance_dir):
        print("Instance folder already exists. Canceling create instance...", color='red')
        time.sleep(4)
        return

    os.makedirs(instance_dir)

    instance.create_instance_info(
        instance_name=instance_name,
        client_version=client_version,
        version_type=version_type,
        is_vanilla=True,
        modify_status=False,
        mod_loader_name=None,
        mod_loader_version=None,
        real_minecraft_version=real_minecraft_version,
        use_legacy_manifest=True,
        java_major_version=support_java_version,
        main_class=main_class
    )
    client_jar_dest = os.path.join(instance_dir, ".minecraft", "libraries", "net", "minecraft", real_minecraft_version)
    os.makedirs(client_jar_dest, exist_ok=True)

    print("Instance info created successfully!", color='lightblue')
    print("***IMPORT FILE***", color='orange')
    print("Client core file. (The mainClass file)")
    client_jar_path = str(input("Client.jar file path:"))
    if not os.path.exists(client_jar_path):
        print("File not found. Canceling create instance...", color='red')
        time.sleep(3)
        return

    print("Want to import libraries folder into the game folder?", color='green')
    user_input = str(input("Y/N: "))
    libraries_dest = os.path.join(game_folder, "libraries")
    if user_input.upper() == "Y":
        libraries_folder_path = str(input("Libraries folder path : "))
        if not os.path.exists(libraries_folder_path):
            print("Folder not found. Canceling create instance...", color='red')
            time.sleep(3)
            return
        else:
            shutil.move(libraries_folder_path, libraries_dest)
    else:
        print("Downloading libraries using spoof version...")
        version_data = get_version_data(client_version)

        if version_data is None:
            print("Could not get version data. Canceling create instance...", color='red')
            time.sleep(3)

        download_libraries(version_data, libraries_dest)
        download_natives(version_data, libraries_dest)

    print("Downloading assets...", color='cyan')
    assets_grabber.assets_file_grabber(client_version, instance_dir)

    print("Custom instance created!", color='blue')
    time.sleep(3)


def test_hook_mod():
    """
    Add modify support for launcher?

    """
    print("***MOD HOOKER***", color='purple')
    print("# This function is for testing launcher modify support.", color='green')
    print("Warning: Launcher doesn't check if mods are harmful :X", color='lightyellow')
    print("So...have fun :)", color='lightblue')
    mod_folder = str(input("Mod folder path : "))

    mod_info = os.path.join(mod_folder, "mod.info.json")
    if not os.path.exists(mod_info):
        print("Mod info file not found. Canceling hook...", color='red')
        time.sleep(3)
        return

    try:
        with open(mod_info, "r") as f:
            mod_info = json.load(f)
    except Exception as e:
        print("Read mod info failed. Canceling hook...", color='red')
        time.sleep(3)
        return

    mod_main_name = mod_info.get("modMain", None)
    mod_main_file = mod_info.get("modMainFile", None)
    mod_main_file_path = os.path.join(mod_folder, mod_main_file)

    if not os.path.exists(mod_main_file_path):
        print("Mod main file not found. Canceling hook...", color='red')
        time.sleep(3)
        return

    if mod_main_name is None:
        print("Mod main not found. Canceling hook...", color='red')
        time.sleep(3)
        return

    # Load the module dynamically
    module_name = "mod_module"
    spec = importlib.util.spec_from_file_location(module_name, mod_main_file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # Define a unique module name based on file path
    module_name = f"mod_{hash(mod_main_file_path)}"

    # If the module is already loaded, reload it
    if module_name in sys.modules:
        print(f"Reloading module: {module_name}")
        module = importlib.reload(sys.modules[module_name])
    else:
        print(f"Importing module: {module_name}")
        spec = importlib.util.spec_from_file_location(module_name, mod_main_file_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module  # Register module in sys.modules
        spec.loader.exec_module(module)

    # Get the function dynamically
    if hasattr(module, mod_main_name):
        mod_function = getattr(module, mod_main_name)
        if callable(mod_function):
            print(f"Successfully loaded {mod_main_name} from {mod_main_file}")
            mod_function()  # Call the function
        else:
            print(f"{mod_main_name} is not callable.")
    else:
        print(f"Function {mod_main_name} not found in {mod_main_file}.")

    exit_code = input("Press any key to exit playground...")
