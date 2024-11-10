import os
import requests
import hashlib
import time
from tqdm import tqdm
from LauncherBase import GetPlatformName
from LauncherBase import print_custom as print

# Step 1: Get the Minecraft version data
def get_version_data(version_url):
    response = requests.get(version_url)
    if response.status_code == 200:
        version_data = response.json()
        return version_data
    else:
        raise Exception(f"Failed to fetch version data. Status code: {response.status_code}")

# Step 2: Extract the required Java version
def get_java_version_info(version_data):
    try:
        java_version_info = version_data['javaVersion']
        component = java_version_info['component']
        major_version = java_version_info['majorVersion']
        return component, major_version
    except KeyError:
        raise Exception("Failed to find the javaVersion information in the version data.")

# Step 3: Fetch the Java manifest based on the component and version
def get_java_manifest(java_manifest_url):
    response = requests.get(java_manifest_url)
    if response.status_code == 200:
        manifest_data = response.json()
        return manifest_data
    else:
        raise Exception(f"Failed to fetch Java manifest. Status code: {response.status_code}")

# Step 4: Find the correct manifest URL based on the component and major version
def find_manifest_url(manifest_data, component, major_version):
    PlatformName = GetPlatformName.check_platform_valid_and_return()
    PlatformNameLW = PlatformName.lower()
    if PlatformNameLW == 'windows':
        PlatformNameLW = 'windows-x64'
    elif PlatformNameLW == 'darwin':
        PlatformNameLW = 'mac-os'
    if PlatformNameLW not in manifest_data:
        raise Exception(f"No {PlatformName} platform data found in the manifest.")

    java_versions = manifest_data[PlatformNameLW].get(component, [])
    for version in java_versions:
        if version['version']['name'].startswith(str(major_version)):
            manifest_url = version['manifest']['url']
            return manifest_url
    raise Exception(f"No matching Java manifest found for component {component} and version {major_version}.")

# Step 5: Download the Java manifest
def download_java_manifest(manifest_url):
    response = requests.get(manifest_url)
    if response.status_code == 200:
        manifest_content = response.content
        manifest_file_name = manifest_url.split("/")[-2] + ".json"
        with open(manifest_file_name, "wb") as file:
            file.write(manifest_content)
        print(f"Java manifest downloaded: {manifest_file_name}", color="blue")
    else:
        raise Exception(f"Failed to download manifest. Status code: {response.status_code}")

# Function to verify SHA1 checksum of a file
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

# Function to create directories based on the file path
def create_directories(file_path, destination_folder):
    # Extract directory path and create it if it doesn't exist
    directory = os.path.join(destination_folder, os.path.dirname(file_path))
    if not os.path.exists(directory):
        os.makedirs(directory)

# Function to download a single file with checksum verification
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
        if not verify_checksum(full_file_path, expected_sha1):
            print(f"Checksum mismatch for {file_name}.", color='yellow')
            os.remove(full_file_path)
    else:
        print(f"Failed to download {file_name}. Status code: {response.status_code}")



# Function to download all files with the proper directory structure
def download_java_files(manifest, destination_folder):
    if not os.path.exists(destination_folder):
        os.makedirs(destination_folder)

    files = manifest.get("files", {})
    total_files = len(files)  # Total number of files to download

    description_color = "\033[32m"  # Green text color for description
    reset_color = "\033[39m"  # Reset color back to default

    # Create a progress bar with a custom color
    with tqdm(total=total_files, unit="file", desc="Downloading files") as progress_bar:
        for file_path, file_info in files.items():
            if "downloads" in file_info:
                # Call download_file and update progress if download or verification succeeds
                download_file(file_info, file_path, destination_folder)
                progress_bar.update(1)  # Increment progress bar for each completed file

        # Ensure the progress bar completes at 100%(??? Why it stuck in 92%???)
        progress_bar.n = total_files
        progress_bar.refresh()
def download_jvm(version_data):
    try:
        # Step 2: Extract the Java version information
        component, major_version = get_java_version_info(version_data)
        print(f"Required Java Component: {component}, Major Version: {major_version}", color='green')

        # Step 3: Get the Java manifest URL
        java_manifest_url = 'https://launchermeta.mojang.com/v1/products/java-runtime/2ec0cc96c44e5a76b9c8b7c39df7210883d12871/all.json'
        java_manifest_data = get_java_manifest(java_manifest_url)

        # Step 4: Find the correct manifest URL for the required Java version
        manifest_url = find_manifest_url(java_manifest_data, component, major_version)

        # Step 5: Download the Java manifest
        manifest = requests.get(manifest_url).json()
        JVM_Path = os.path.join("runtimes/" + f'Java_{major_version}')
        if not os.path.exists("runtimes"):
            os.mkdir("runtimes")
        if os.path.exists(f'runtimes' + f'Java_{major_version}'):
            print("Found exits jvm! Do you want to reinstall it? Y/N")
            user_input = input(":")
            if user_input.upper() == "Y":
                os.rmdir(f'runtimes' + f'Java_{major_version}')
                os.mkdir("runtimes/" + f'Java_{major_version}')
                download_java_files(manifest, JVM_Path)
                print("Download JVM finished.", color='blue')
        else:
            download_java_files(manifest, JVM_Path)
            print("Download JVM finished.", color='blue')



        # Fix permissions(for unix like)
        if not GetPlatformName.check_platform_valid_and_return() == "Windows":
            os.system(f"chmod 755 {JVM_Path}/bin/*")


    except Exception as e:
        print(f"Error: {e}")
        return None
