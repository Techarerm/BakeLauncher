import os
import time

import requests
import hashlib
import shutil
from tqdm import tqdm
from LauncherBase import Base, print_custom as print
from libs.__assets_grabber import assets_grabber_manager


def verify_checksum(file_path, expected_sha1):
    sha1 = hashlib.sha1()
    with open(file_path, "rb") as f:
        while True:
            data = f.read(65536)  # Read in 64KB chunks
            if not data:
                break
            sha1.update(data)
    file_sha1 = sha1.hexdigest()
    return file_sha1 == expected_sha1


def create_directories(file_path, destination_folder):
    # Extract directory path and create it if it doesn't exist
    directory = os.path.join(destination_folder, os.path.dirname(file_path))
    if not os.path.exists(directory):
        os.makedirs(directory)


def download_file(file_info, file_path, destination_folder):
    download_type = "raw"  # You can choose "lzma" if preferred
    file_url = file_info["downloads"][download_type]["url"]
    file_name = os.path.basename(file_path)  # Extract the file name
    full_file_path = os.path.join(destination_folder, file_path)
    expected_sha1 = file_info["downloads"][download_type]["sha1"]

    # Create necessary directories
    create_directories(file_path, destination_folder)

    # Check if the file already exists and verify checksum
    if os.path.exists(full_file_path) and verify_checksum(full_file_path, expected_sha1):
        return

    # Download file
    response = requests.get(file_url)
    if response.status_code == 200:
        with open(full_file_path, "wb") as f:
            f.write(response.content)
        if Base.UsingLegacyDownloadOutput:
            if verify_checksum(full_file_path, expected_sha1):
                print(f"Downloaded and verified {file_name} to {full_file_path}", color='green')
        if not verify_checksum(full_file_path, expected_sha1):
            print(f"Checksum mismatch for {file_name}.", color='yellow')
            os.remove(full_file_path)
    else:
        print(f"Failed to download {file_name}. Status code: {response.status_code}")


def download_java_runtime_files(manifest, install_path):
    if not os.path.exists(install_path):
        return False, "InstallFolderAreNotExist"

    files = manifest.get("files", {})
    total_files = len(files)  # Get total number of files to download(for progress bar)

    # Create a progress bar with a custom color
    if not Base.UsingLegacyDownloadOutput:
        with tqdm(total=total_files, unit="file", desc="Downloading files") as progress_bar:
            for file_path, file_info in files.items():
                if "downloads" in file_info:
                    # Test method
                    download_file(file_info, file_path, install_path)
                    progress_bar.update(1)  # Increment progress bar for each completed file

            # Ensure the progress bar completes at 100%(??? Why it stuck in 92%???)
            progress_bar.n = total_files
            progress_bar.refresh()
    else:
        files = manifest.get("files", {})
        for file_path, file_info in files.items():
            if "downloads" in file_info:
                download_file(file_info, file_path, install_path)

    return True, "DownloadFinished"


def get_java_version_info(version_data):
    try:
        java_version_info = version_data['javaVersion']
        component = java_version_info['component']
        major_version = java_version_info['majorVersion']
        return component, major_version
    except KeyError:
        raise Exception("Failed to find the javaVersion information in the version data.")


def find_selected_java_version_manifest_url(manifest_data, component, major_version):
    if Base.LibrariesPlatform == 'windows':
        JavaPlatformName = 'windows-x64'
    elif Base.LibrariesPlatform == 'darwin':
        JavaPlatformName = 'mac-os'
    else:
        JavaPlatformName = Base.LibrariesPlatform

    if JavaPlatformName not in manifest_data:
        raise Exception(f"No {Base.Platform} platform data found in the manifest.")

    java_versions = manifest_data[JavaPlatformName].get(component, [])
    for version in java_versions:
        if version['version']['name'].startswith(str(major_version)):
            manifest_url = version['manifest']['url']
            return manifest_url
    raise Exception(f"No matching Java manifest found for component {component} and version {major_version}.")


def install_jvm(minecraft_version):
    java_manifest_url = 'https://launchermeta.mojang.com/v1/products/java-runtime/2ec0cc96c44e5a76b9c8b7c39df7210883d12871/all.json'

    # Get version data
    selected_version_data = assets_grabber_manager.get_version_data(minecraft_version)

    # Get Java Version Info(from selected version's data)
    component, major_version = get_java_version_info(selected_version_data)
    print(f"Required Java Component: {component}, Major Version: {major_version}", color='green', tag='DEBUG')

    # Get java manifest
    try:
        response = requests.get(java_manifest_url)
        if response.status_code == 200:
            manifest_data = response.json()
        else:
            print(f"Failed to fetch Java manifest. Status code: {response.status_code}")
            return "FailedToFetchJavaManifest"
    except Exception as e:
        print(f"Error when fetch Java Manifest: {e}")
        return f"FailedToFetchJavaManifest[{e}]"

    # gEt "selected java version manifest_url"
    selected_java_version_manifest_url = find_selected_java_version_manifest_url(manifest_data, component,
                                                                                 major_version)

    try:
        # Get manifest data
        manifest_data = requests.get(selected_java_version_manifest_url).json()
    except Exception as e:
        print(f"Error when fetch selected Java manifest data: {e}", color='red')
        return "FailedToFetchJavaManifestData"

    # Change work dir back to launcher root(avoid some path error) and get install dir
    os.chdir(Base.launcher_root_dir)
    install_path = os.path.join("runtimes", f"Java_{major_version}")

    # Check install dir status
    if Base.OverwriteJVMIfExist:
        print("OverwriteJVMIfExist has been enabled.", color='blue', tag='INFO')
        if os.path.exists(install_path):
            shutil.rmtree(install_path)

    if os.path.exists(install_path):
        print("Warning: A same version of Java runtime has been installed.", color='yellow')
        print("Do you want to reinstall it? Y/N")
        user_input = str(input(":"))
        if not user_input.upper() == "Y":
            print("Bypass installing Java runtime...", color='green')
            return True, "BypassInstallJVM"
        else:
            # Install, uninstall ???
            print("Uninstall Java runtime...", color='green')
            shutil.rmtree(install_path, ignore_errors=True)
            print("Uninstall Java runtime finished!", color='blue')
            os.makedirs(install_path)
            time.sleep(0.5)
    else:
        os.makedirs(install_path)
    Status, Message = download_java_runtime_files(manifest_data, install_path)

    if Status:
        print(f"Successfully installed Java runtime.", color='blue')
    else:
        print(f"Failed to install Java runtime :( Cause by {Message}", color='red')
        return False, "DownloadJavaRuntime>InstallJVMFailed"

    if not Base.Platform == "Windows":
        print("Do you want to fix permissions for the Java runtime?", color='blue', tag='PROMPT')
        print(
            "Sometimes you may get 'Permission denied' errors when launching Minecraft. "
            "This method can help fix these issues. :)",
            color='green'
        )
        print("The launcher may require your password to repair permissions.", color='purple', tag='INFO')
        print("Linux systems often need this fix to ensure the Java runtime works properly.", color='green')

        user_input = input("Proceed with fixing permissions? (Y/N): ").strip().upper()

        if user_input == "Y":
            try:
                # Execute chmod command
                command = f"chmod -R +x {install_path}/*"
                command2 = f"chmod -R +x {install_path}/bin/*"
                os.system(command)
                os.system(command2)
                print("Permissions fixed successfully.", color='green', tag='SUCCESS')
            except Exception as e:
                print(f"Error when fixing permissions: {e}", color='red', tag='ERROR')
                return False, "FailedToFixPermissions"
        else:
            print("Permission fix skipped by user.", color='yellow', tag='INFO')
            Message = "PermissionFixBypassed"

    if not len(Message) == 0:
        return True, f"InstallJVMFinished[{Message}]"
    else:
        return True, "InstallJVMFinished"
