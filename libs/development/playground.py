import json
import ast
import os.path
import shutil
import time
from LauncherBase import Base, print_custom as print
from libs.account.mojang_api import *
from libs.__account_manager import account_manager
from libs.instance.instance import instance
from libs.version.version import get_version_data
from libs.libraries.libraries import download_libraries, download_natives
from libs.__assets_grabber import assets_grabber

all_funs = ["function", "create_a_custom_instance"]

def function():
    print("Reading account data...")
    AccountIDStatus, account_id = account_manager.get_default_account_id()
    if not AccountIDStatus:
        return "AccountIDNotFound"
    AccDataStatus, account_data = account_manager.get_account_data_use_account_id(account_id)
    if not AccDataStatus:
        return "GetAccountDataFailed"

    username = account_data['Username']
    access_token = account_data['AccessToken']
    uuid = account_data['UUID']

    path = "C:/Users/techa/Downloads/20c412d50462805e.png"

    Status, url, err = upload_account_skin(access_token, "classic", path)
    print(Status, url, err)
    print(change_account_skin(access_token, "classic", url))

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




