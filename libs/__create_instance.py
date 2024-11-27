import sys

import requests
import os
import zipfile
import time
import datetime
import hashlib
import shutil
from datetime import datetime
from textwrap import dedent
from concurrent.futures import ThreadPoolExecutor, as_completed
from LauncherBase import Base, ClearOutput, print_custom as print
from libs.__assets_grabber import assets_grabber_manager
from libs.__instance_manager import instance_manager
from tqdm import tqdm


def extract_zip(zip_path, extract_to):
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        print(f"Extracted {zip_path} to {extract_to}")
    except zipfile.BadZipFile as e:
        print(f"Error extracting {zip_path}: {e}", color='red')


def download_file(url, dest_path):
    """
    Downloads a file from a URL and saves it to dest_path.
    """
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()

        # Create the directory if it doesn't exist
        dest_dir = os.path.dirname(dest_path)
        if dest_dir:
            os.makedirs(dest_dir, exist_ok=True)

        # Write the file to dest_path
        with open(dest_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        if Base.UsingLegacyDownloadOutput:
            print(f"Download successful: {dest_path}")
        return True  # Indicate success
    except requests.exceptions.RequestException as e:
        print(f"Failed to download {url}: {e}")
        return False  # Indicate failure


def multi_thread_download(nested_urls_and_paths, name, max_workers=5, retries=1):
    """
    Downloads multiple files using multiple threads with retry attempts.
    nested_urls_and_paths should be a nested list where each element is a list containing a tuple of (url, dest_path).
    """
    # Flatten the nested list into a single list of (url, dest_path) tuples
    urls_and_paths = [item for sublist in nested_urls_and_paths for item in sublist]

    # Calculate the total number of files to download (half the length of the list)
    total_files = len(urls_and_paths)

    downloaded_files = []
    failed_files = []
    sys.stderr.flush()
    def download_with_retry(url, dest_path, retry_count):
        """Attempts to download a file with retries."""
        for attempt in range(retry_count + 1):
            success = download_file(url, dest_path)  # Replace with your download logic
            if success:
                return True
            print(f"Retry {attempt + 1} for {url}")
        failed_files.append((url, dest_path))  # Track failed downloads
        return False

    def futures_download(future_to_url, total_files):
        if Base.UsingLegacyDownloadOutput:
            for future in as_completed(future_to_url):
                url, dest_path = future_to_url[future]
                try:
                    success = future.result()
                    if success:
                        downloaded_files.append(dest_path)
                    else:
                        failed_files.append((url, dest_path))  # Track final failure
                except Exception as exc:
                    print(f"Error downloading {url}: {exc}")
                    failed_files.append((url, dest_path))
        else:
            with tqdm(total=total_files, desc=f"Downloading {name}", unit="file", colour='cyan') as pbar_download:
                for future in future_to_url:
                    url, dest_path = future_to_url[future]
                    try:
                        success = future.result()  # Wait for the future to complete
                        if success:
                            downloaded_files.append(dest_path)
                    except Exception as exc:
                        print(f"Error downloading {url}: {exc}")
                    # Update the progress bar correctly
                    pbar_download.update(1)

    # Initial download attempt with a progress bar
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Wrap the futures in tqdm to create a progress bar
        future_to_url = {
            executor.submit(download_with_retry, url, dest_path, retries): (url, dest_path)
            for url, dest_path in urls_and_paths
        }

        futures_download(future_to_url, total_files)

    # Retry failed downloads
    if failed_files:
        print("\nRetrying failed downloads...")
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_url = {
                executor.submit(download_with_retry, url, dest_path, retries): (url, dest_path)
                for url, dest_path in failed_files
            }
            failed_files.clear()  # Clear the list to track final failures

            futures_download(future_to_url, total_files)

    if failed_files:
        print("Files that failed after retries:", failed_files)
    return downloaded_files, failed_files


class Create_Instance:
    def __init__(self):
        self.client_version = None
        self.version_spoof_status = None
        self.legacy_version_type = "classic"
        self.legacy_version = False
        self.SelectedInstanceInstalled = False
        self.VersionManifestURl = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"
        self.LegacyVersionManifestURl = ("https://github.com/Techarerm/BakeLauncher-Library/raw/refs/heads/main/Legacy"
                                         "%20Manifest/version_manifest_legacy.json")
        self.AlphaManifestURl = ("https://github.com/Techarerm/BakeLauncher-Library/raw/refs/heads/main/Legacy"
                                 "%20Manifest/version_manifest_alpha.json")
        self.InfdevManifestURl = ("https://github.com/Techarerm/BakeLauncher-Library/raw/refs/heads/main/Legacy"
                                  "%20Manifest/version_manifest_infdev.json")
        self.IndevManifestURL = ("https://github.com/Techarerm/BakeLauncher-Library/raw/refs/heads/main/Legacy"
                                 "%20Manifest/version_manifest_indev.json")
        self.ClassicManifestURl = ("https://github.com/Techarerm/BakeLauncher-Library/raw/refs/heads/main/Legacy"
                                   "%20Manifest/version_manifest_classic.json")
        self.RubyDungMinecraftManifestURl = ("https://github.com/Techarerm/BakeLauncher-Library/raw/refs/heads/main"
                                             "/Legacy%20Manifest/version_manifest_rd(old_alpha).json")
        self.version_id = None
        self.minecraft_version = ""
        # Working directory
        self.WorkDir = os.getcwd()

    def get_version_url(self, minecraft_version, **kwargs):
        legacy = kwargs.get("legacy", False)
        if legacy:
            response = requests.get(self.LegacyVersionManifestURl)
        else:
            response = requests.get(self.VersionManifestURl)
        manifest = response.json()

        version_info = next((v for v in manifest["versions"] if v["id"] == minecraft_version), None)
        return version_info['url']

    def get_version_data(self, version_id, **kwargs):
        """
        Get version_manifest_v2.json and find requires version of json data
        """
        use_legacy_json = kwargs.get("use_legacy_json", False)

        response = requests.get(self.VersionManifestURl)
        data = response.json()
        version_list = data['versions']

        version_url = None
        for v in version_list:
            if v['id'] == version_id:
                version_url = v['url']
                break

        if version_url is None:
            response = requests.get(self.LegacyVersionManifestURl)
            data = response.json()
            version_list = data['versions']

            version_url = None
            for v in version_list:
                if v['id'] == version_id:
                    version_url = v['url']
                    break

        # If the version_id not in version_list, return None
        if version_url is None:
            print(f"Unable to find same as requires version id: {version_id} in the version_manifest.", color='red')
            print("Failed to get version data. Cause by unknown Minecraft version.", color='red')
            return None

        try:
            # Get version data
            version_response = requests.get(version_url)
            version_data = version_response.json()
            return version_data
        except Exception as e:
            print(f"Error occurred while fetching version data: {e}", color='red')
            print("Failed to get version data. Cause by internet connect error or unknown issues.", color='red')
            return None

    def get_version_list(self, mode, **kwargs):
        # Get version_manifest_v2.json and list all versions (with version_id on the left)
        global rows_all, version_list

        def get_legacy_party(mode):
            # Legacy Part
            legacy_minecraft_response = requests.get(self.LegacyVersionManifestURl)
            """
            alpha_minecraft_response = requests.get(self.AlphaManifestURl)
            infdev_minecraft_response = requests.get(self.InfdevManifestURl)
            indev_manifest_response = requests.get(self.IndevManifestURL)
            classic_minecraft_response = requests.get(self.ClassicManifestURl)
            pre_classic_minecraft_response = requests.get(self.RubyDungMinecraftManifestURl)
            """
            legacy_data = legacy_minecraft_response.json()
            """
            alpha_data = alpha_minecraft_response.json()
            infdev_data = infdev_minecraft_response.json()
            indev_data = indev_manifest_response.json()
            classic_data = classic_minecraft_response.json()
            pre_classic_data = pre_classic_minecraft_response.json()
            """
            legacy_version_list = [version['id'] for version in legacy_data['versions']]
            """
            alpha_version_list = [version['id'] for version in alpha_data['versions']]
            infdev_version_list = [version['id'] for version in infdev_data['versions']]
            indev_version_list = [version['id'] for version in indev_data['versions']]
            classic_version_list = [version['id'] for version in classic_data['versions']]
            pre_classic_version_list = [version['id'] for version in pre_classic_data['versions']]
            """
            format_legacy_version = '\n'.join([f"{index + 1}: {version}"
                                               for index, version in enumerate(legacy_version_list)])
            """
            format_alpha_list = '\n'.join([f"{index + 1}: {version}"
                                           for index, version in enumerate(alpha_version_list)])

            format_infdev_list = '\n'.join([f"{index + 1}: {version}"
                                            for index, version in enumerate(infdev_version_list)])

            format_indev_list = '\n'.join([f"{index + 1}: {version}"
                                           for index, version in enumerate(indev_version_list)])

            format_classic_list = '\n'.join([f"{index + 1}: {version}"
                                             for index, version in enumerate(classic_version_list)])

            format_pre_classic_list = '\n'.join([f"{index + 1}: {version}"
                                                 for index, version in enumerate(pre_classic_version_list)])
            """
            if mode == "format":
                return format_legacy_version
            elif mode == "version_list":
                return legacy_version_list

        legacy_party = kwargs.get('legacy_party', False)
        if legacy_party:
            format_legacy_version = get_legacy_party("format")

            legacy_version_list = get_legacy_party("version_list")

            if mode == "legacy_version_list":
                rows_all = (len(format_legacy_version) + 50) // 40
                version_list = legacy_version_list
            """
            elif mode == "alpha_list":
                rows_all = (len(format_alpha_list) + 50) // 40
                version_list = alpha_version_list
            elif mode == "infdev_list":
                rows_all = (len(format_infdev_list) + 50) // 40
                version_list = infdev_version_list
            elif mode == "indev_list":
                rows_all = (len(format_indev_list) + 50) // 40
                version_list = indev_version_list
            elif mode == "classic_list":
                rows_all = (len(format_classic_list) + 50) // 40
                version_list = classic_version_list
            elif mode == "pre_classic_list":
                rows_all = (len(format_pre_classic_list) + 50) // 40
                version_list = pre_classic_version_list
            """

            # New methods
            print("Available version list:", color='purple')
            for row in range(rows_all):
                line = ""
                for col in range(50):
                    index = col * rows_all + row
                    if index < len(version_list):
                        line += f"{index + 1}: {version_list[index]:<20}\t"
                print(line.strip())  # Print each row after building the line
            print("This list may look really broken :)", color='blue')
            return version_list
        response = requests.get(self.VersionManifestURl)
        data = response.json()

        version_list = data['versions']
        all_available_version = [version['id'] for version in data['versions']]
        release_versions = [version['id'] for version in version_list if version['type'] == 'release']

        # Legacy(list)
        formatted_versions = '\n'.join([f"{index + 1}: {version}"
                                        for index, version in enumerate(release_versions)])

        formatted_versions_all = '\n'.join([f"{index + 1}: {version}"
                                            for index, version in enumerate(all_available_version)])

        # New methods
        rows = (len(release_versions) + 9) // 10  # Round up division to determine rows
        rows_all = (len(all_available_version) + 50) // 40  # Round up division to determine rows
        print("Available version list:", color='purple')
        if mode == "release":
            for row in range(rows):
                line = ""
                for col in range(10):
                    index = col * rows + row
                    if index < len(release_versions):
                        line += f"{index + 1}: {release_versions[index]:<10}\t"
                print(line.strip())  # Print each row after building the line
            return release_versions
        elif mode == "all_version":
            for row in range(rows_all):
                line = ""
                for col in range(50):
                    index = col * rows_all + row
                    if index < len(all_available_version):
                        line += f"{index + 1}: {all_available_version[index]:<20}\t"
                print(line.strip())  # Print each row after building the line
            print("This list may look really broken :)", color='blue')
            return all_available_version
        elif mode == "legacy":
            print(formatted_versions)
            return release_versions
        elif mode == "legacy_all":
            print(formatted_versions_all)
            return all_available_version
        elif mode == "legacy_minecraft":
            print()
        else:
            return all_available_version

    def get_version_type(self, minecraft_version):
        response = requests.get(self.VersionManifestURl)
        legacy_response = requests.get(self.LegacyVersionManifestURl)
        data = response.json()
        legacy_data = legacy_response.json()
        for version in data["versions"]:
            if version["id"] == minecraft_version:
                return version["type"]

        for version in legacy_data["versions"]:
            if version["id"] == minecraft_version:
                return version["type"]

        return None

    @staticmethod
    def instance_list():
        instances_list = os.listdir(Base.launcher_instances_dir)
        row_count = 0
        for name in instances_list:
            if row_count >= Base.MaxInstancesPerRow:
                print("\n", end='')
                row_count = 0
            print(f"{name}", end='')
            print(" | ", end='', color='blue')
            row_count += 1
        print("\n", end='')

    @staticmethod
    def download_natives(libraries, libraries_dir):
        print(f"Platform: {Base.LibrariesPlatform} LibrariesPlatform: {Base.LibrariesPlatform}", tag='Debug',
              color='green')

        # Map platforms to native keys
        native_keys = {
            'windows': 'natives-windows',
            'linux': 'natives-linux',
            'darwin': 'natives-macos',
            'windows-arm64': 'natives-windows-arm64',
            'macos-arm64': 'natives-macos-arm64',
        }
        native_key = native_keys.get(Base.LibrariesPlatform)

        if not native_key:
            print(f"Warning: No native key found for {Base.LibrariesPlatform}", color='yellow')
            return "NativeKeyCheckFailed"

        download_queue = []  # Collect (url, destination) pairs for batch downloading

        def add_to_queue(url, dest):
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            natives_url_and_dest = [
                (url, dest)
            ]
            download_queue.append(natives_url_and_dest)

        found_any_native = False

        for lib in libraries:
            lib_downloads = lib.get('downloads', {})

            # Check platform compatibility via rules
            rules = lib.get('rules')
            if rules:
                allowed = any(
                    rule.get('action') == 'allow' and
                    (not rule.get('os') or rule['os'].get('name') == Base.LibrariesPlatform2ndOld)
                    for rule in rules
                )
                disallowed = any(
                    rule.get('action') == 'disallow' and
                    rule.get('os', {}).get('name') == Base.LibrariesPlatform2ndOld
                    for rule in rules
                )
                if not allowed or disallowed:
                    continue

            # Handle artifact downloads
            artifact = lib_downloads.get('artifact')
            if artifact and native_key in (lib.get('name', '') or artifact.get('path', '')):
                add_to_queue(artifact['url'], os.path.join(libraries_dir, artifact['path']))
                found_any_native = True

            # Handle classifier downloads
            classifiers = lib_downloads.get('classifiers')
            if classifiers and native_key in classifiers:
                classifier_info = classifiers[native_key]
                add_to_queue(classifier_info['url'], os.path.join(libraries_dir, classifier_info['path']))
                found_any_native = True

        # Fallback for macOS to 'natives-osx'
        if not found_any_native and Base.LibrariesPlatform == 'darwin':
            fallback_key = 'natives-osx'
            for lib in libraries:
                classifiers = lib.get('downloads', {}).get('classifiers')
                if classifiers and fallback_key in classifiers:
                    classifier_info = classifiers[fallback_key]
                    add_to_queue(classifier_info['url'], os.path.join(libraries_dir, classifier_info['path']))
                    found_any_native = True
                    break

        # Perform the batch download
        if download_queue:
            multi_thread_download(download_queue, "natives")
        else:
            print(f"No native library found for key: {native_key}", color='yellow')
            return "NativeLibrariesNotFound"

    def download_client(self, version_data, minecraft_version, install_dir):
        version_dir = os.path.join(Base.launcher_instances_dir, install_dir)
        libraries_dir = os.path.join(version_dir, "libraries")
        os.makedirs(libraries_dir, exist_ok=True)

        if not self.legacy_version:
            # Download client.jar
            client_info = version_data['downloads']['client']
            client_url = client_info['url']
        else:
            legacy_url = self.get_version_url(minecraft_version, legacy=True)
            legacy_url = "/".join(legacy_url.split("/")[:-1]) + "/"
            client_url = f"{legacy_url}{minecraft_version}.jar"

        client_dest = os.path.join(version_dir, 'libraries', 'net', 'minecraft', minecraft_version, "client.jar")
        print(f"Downloading client.jar to {client_dest}...", color='green')
        download_file(client_url, client_dest)

    def download_libraries(self, version_data, install_dir):
        """
        Create instances/version_id/folder and download game files
        """
        version_dir = os.path.join(Base.launcher_instances_dir, install_dir)
        libraries_dir = os.path.join(version_dir, "libraries")
        os.makedirs(libraries_dir, exist_ok=True)
        # Download libraries

        # Waiting-Download-List
        download_queue = []

        # Get libraries data from version_data
        libraries = version_data.get('libraries', [])

        # Search support user platform libraries
        for lib in libraries:
            lib_downloads = lib.get('downloads', {})
            artifact = lib_downloads.get('artifact')

            rules = lib.get('rules')
            if rules:
                allowed = False
                for rule in rules:
                    action = rule.get('action')
                    os_info = rule.get('os')
                    if action == 'allow' and (not os_info or os_info.get('name') == Base.Platform):
                        allowed = True
                    elif action == 'disallow' and os_info and os_info.get('name') == Base.Platform:
                        allowed = False
                        break
                if not allowed:
                    continue

            if artifact:
                lib_path = artifact['path']
                lib_url = artifact['url']
                lib_dest = os.path.join(libraries_dir, lib_path)
                os.makedirs(os.path.dirname(lib_dest), exist_ok=True)
                if Base.UsingLegacyDownloadOutput:
                    print(f"Downloading {lib_path} to {lib_dest}...")
                lib_url_and_dest = [
                    (lib_url, lib_dest)
                ]
                download_queue.append(lib_url_and_dest)

        # Download natives(Separated from download is for other functions can easily call it)
        multi_thread_download(download_queue, "libraries")
        print("Downloading natives...", color='green')
        time.sleep(1)
        self.download_natives(libraries, libraries_dir)

    def unzip_natives(self, instance_name):
        global unzip_status

        # Handle platform naming for macOS
        if Base.LibrariesPlatform == 'darwin':
            PlatformName = 'macos'

        instance_dir = os.path.join(Base.launcher_instances_dir, instance_name)
        natives_dir = os.path.join(instance_dir, ".minecraft", "natives")
        if not os.path.exists(natives_dir):
            os.mkdir(natives_dir)

        os.chdir(instance_dir)
        # Find all natives and unzip
        jar_files = []

        for root, dirs, files in os.walk('libraries'):
            for file in files:
                if file.endswith(f"natives-{Base.LibrariesPlatform2nd}.jar"):
                    jar_files.append(os.path.join(root, file))
                elif Base.LibrariesPlatform2nd == 'macos' and file.endswith("natives-osx.jar"):
                    # Fallback to natives-osx.jar if natives-macos.jar is not found
                    jar_files.append(os.path.join(root, file))

        if jar_files:
            unzip_status = True
            for jar_file in jar_files:
                print(f"Found: {jar_file}", color='blue')

                # Create "natives" folder in libraries
                base_dir_name = os.path.basename(os.path.dirname(jar_file))
                natives_dir = os.path.join(os.path.dirname(jar_file), f"natives_{base_dir_name}")
                os.makedirs(natives_dir, exist_ok=True)

                # Extract only files from the JAR to the unique 'natives' directory
                with zipfile.ZipFile(jar_file, 'r') as jar:
                    for member in jar.namelist():
                        if not member.endswith('/'):
                            jar.extract(member, ".minecraft/natives")

        else:
            unzip_status = False
            print("No natives file found.", color='yellow')
        if unzip_status:
            for root, dirs, files in os.walk(natives_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    dest_path = os.path.join(natives_dir, file)

                    if os.path.exists(dest_path):
                        base, ext = os.path.splitext(file)
                        dest_path = os.path.join(natives_dir, f"{base}_copy{ext}")

                    shutil.move(file_path, dest_path)
            print("Unzip Natives successfully!", color='blue')
        else:
            print("Warring: You may get some error you download libraries. Please re-download this version of"
                  " Minecraft again.", color='yellow')
        os.chdir(Base.launcher_root_dir)

    @staticmethod
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

    @staticmethod
    def create_directories(file_path, destination_folder):
        # Extract directory path and create it if it doesn't exist
        directory = os.path.join(destination_folder, os.path.dirname(file_path))
        if not os.path.exists(directory):
            os.makedirs(directory)

    def download_java_file(self, file_info, file_path, destination_folder):
        download_type = "raw"  # You can choose "lzma" if preferred
        file_url = file_info["downloads"][download_type]["url"]
        file_name = os.path.basename(file_path)  # Extract the file name
        full_file_path = os.path.join(destination_folder, file_path)
        expected_sha1 = file_info["downloads"][download_type]["sha1"]

        # Create necessary directories
        self.create_directories(file_path, destination_folder)

        # Check if the file already exists and verify checksum
        if os.path.exists(full_file_path) and self.verify_checksum(full_file_path, expected_sha1):
            return

        # Download file
        response = requests.get(file_url)
        if response.status_code == 200:
            with open(full_file_path, "wb") as f:
                f.write(response.content)
            if Base.UsingLegacyDownloadOutput:
                if self.verify_checksum(full_file_path, expected_sha1):
                    print(f"Downloaded and verified {file_name} to {full_file_path}", color='green')
            if not self.verify_checksum(full_file_path, expected_sha1):
                print(f"Checksum mismatch for {file_name}.", color='yellow')
                os.remove(full_file_path)
        else:
            print(f"Failed to download {file_name}. Status code: {response.status_code}")

    def download_java_runtime_files(self, manifest, install_path):
        if not os.path.exists(install_path):
            return False, "InstallFolderAreNotExist"

        files = manifest.get("files", {})
        total_files = len(files)  # Get total number of files to download(for progress bar)

        # Create a progress bar with a custom color
        if not Base.UsingLegacyDownloadOutput:
            with tqdm(total=total_files, unit="file", desc="Downloading files", colour='cyan') as progress_bar:
                for file_path, file_info in files.items():
                    if "downloads" in file_info:
                        # Test method
                        self.download_java_file(file_info, file_path, install_path)
                        progress_bar.update(1)  # Increment progress bar for each completed file

                # Ensure the progress bar completes at 100%(??? Why it stuck in 92%???)
                progress_bar.n = total_files
                progress_bar.refresh()
        else:
            files = manifest.get("files", {})
            for file_path, file_info in files.items():
                if "downloads" in file_info:
                    self.download_java_file(file_info, file_path, install_path)

        return True, "DownloadFinished"

    @staticmethod
    def get_java_version_info(version_data):
        try:
            java_version_info = version_data['javaVersion']
            component = java_version_info['component']
            major_version = java_version_info['majorVersion']
            return component, major_version
        except KeyError:
            raise Exception("Failed to find the javaVersion information in the version data.")

    @staticmethod
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

    def install_jvm(self, minecraft_version):
        java_manifest_url = 'https://launchermeta.mojang.com/v1/products/java-runtime/2ec0cc96c44e5a76b9c8b7c39df7210883d12871/all.json'

        # Get version data
        selected_version_data = assets_grabber_manager.get_version_data(minecraft_version)

        # Get Java Version Info(from selected version's data)
        component, major_version = self.get_java_version_info(selected_version_data)
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
        selected_java_version_manifest_url = self.find_selected_java_version_manifest_url(manifest_data, component,
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

        if Base.DoNotAskJVMExist and os.path.exists(install_path):
            print("Bypassing reinstall JVM...", color='green', tag='INFO')
            return True, "BypassInstallJVM"

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
        Status, Message = self.download_java_runtime_files(manifest_data, install_path)

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

    @staticmethod
    def mac_os_libraries_bug_fix(instance_name):
        # Patch for some idiot version bug
        if Base.Platform == "Darwin":
            directory = os.path.join(Base.launcher_instances_dir, f"{instance_name}", "libraries", "ca", "weblite",
                                     "1.0.0")
            if not os.path.exists(directory):
                os.makedirs(directory)  # Create intermediate directories if needed
                url = "https://libraries.minecraft.net/ca/weblite/java-objc-bridge/1.0.0/java-objc-bridge-1.0.0.jar"
                try:
                    download_file(url, f"{directory}java-objc-bridge-1.0.0.jar")
                except Exception as e:
                    print(f"An error occurred: {e}")

    def download_games_files(self, version_id, install_dir):
        """
        real_version (if the client type is not legacy, it is the same as client_version).
        If the client is a legacy version, client_version and real_version are not the same(or same? if user using
        rd-132211)

        Why this spoof? Legacy archives place the client in a weird location (version data tag libraries don't have
        the client URL). Additionally, some legacy version libraries have incomplete data. To address this,
        BakeLauncher uses a similar library version as an alternative for these cases.

        Why keep real_version in instance info? When the user launches Minecraft, the launcher manager calls
        a function named "java_version_check" to get the java_version. If the client uses a spoofed version,
        it might crash due to argument bugs. (However, legacy version data's "MinecraftArguments" are complete.)
        """
        # In this function, version id is spoof version(if minecraft version is legacy)
        print("Loading version info...")
        instance_info = os.path.join(install_dir, "instance.bakelh.ini")
        # Get real_version(to download client)
        Status, real_version = instance_manager.get_instance_info(instance_info, info_name='real_minecraft_version')
        version_data = self.get_version_data(version_id)

        # Download game file( libraries, .jar files...)
        print("Downloading client...", color='blue')
        self.download_client(version_data, real_version, install_dir)
        print("Downloading libraries...", color='blue')
        self.download_libraries(version_data, install_dir)
        self.mac_os_libraries_bug_fix(install_dir)
        # Delay time to make old output don't print with new output
        time.sleep(0.5)
        print("The required dependent libraries should have been downloaded :)", color='blue')

        # Download assets(Also it will check this version are use legacy assets or don't use)
        print("Downloading assets...", color='purple')
        assets_grabber_manager.assets_file_grabber(version_id, install_dir)
        os.chdir(self.WorkDir)

        print("Unzipping natives...", color='green')
        self.unzip_natives(install_dir)

        print("Downloading JVM...", color='cyan')
        self.install_jvm(version_id)

        print("When you install a Java version that has never been installed before,"
              " you need to reconfig Java Path!",
              color='blue')
        print("Now all files are download success :)", color='blue')
        print("Exiting....", color='green')

        # Add waiting time(If assets download failed it will print it?)
        time.sleep(1.2)

    def version_spoof(self, require_version):
        global client_version, spoof_enable
        if self.legacy_version:
            real_version = require_version
            print(f" Version Type: {self.legacy_version_type}", color='green', tag='DEBUG')
            if self.legacy_version_type == "alpha":
                client_version = "a1.2.6"
                self.version_spoof_status = True
            elif self.legacy_version_type == "infdev":
                client_version = "inf-20100618"
                self.version_spoof_status = True
            elif self.legacy_version_type == "indev":
                client_version = "inf-20100618"
                self.version_spoof_status = True
            elif self.legacy_version_type == "classic":
                client_version = "c0.30_01c"
                self.version_spoof_status = True
            elif self.legacy_version_type == "pre-classic":
                client_version = "rd-160052"
                self.version_spoof_status = True
            if self.version_spoof_status:
                print(f"Version Spoof Enable | RealVersion: {require_version} Spoof to Version : {client_version}", color='green', tag='DEBUG')
        else:
            client_version = require_version
            real_version = require_version
        return client_version, real_version

    def start_create_instance(self, require_version):
        global instance_path, client_version

        # Check version
        client_version, real_version = self.version_spoof(require_version)
        print(client_version, real_version)
        if not os.path.exists(Base.launcher_instances_dir):
            os.makedirs(Base.launcher_instances_dir)

        instances_dir = os.listdir(Base.launcher_instances_dir)
        if len(instances_dir) == 0:
            print("Installed instance list:", color='green')
            self.instance_list()

        while True:
            # Prompt for instance name
            print("Give a name for this instance (or type 'EXIT' to cancel):", end='', color='blue')
            name = input(":").strip()

            if name.upper() == "EXIT":
                print("Instance creation canceled.", color='yellow')
                return False, "ExitCreateInstance"

            if not name:
                print("Please enter a valid name. Name cannot be empty or spaces only.", color='red')
                continue

            # Generate instance path and get version type
            instance_path = os.path.join(Base.launcher_instances_dir, name)
            version_type = self.get_version_type(real_version)

            # Check if instance already exists
            if os.path.exists(instance_path):
                counter = 2
                new_instance_path = instance_path
                while os.path.exists(new_instance_path):
                    new_instance_path = os.path.join(Base.launcher_instances_dir, f"{name}({counter})")
                    counter += 1

                print(f'Instance name "{name}" already exists.')
                print(f'Do you want to rename it to "{os.path.basename(new_instance_path)}"? (Y/N):', end='',
                      color='yellow')
                user_input = input(":").strip().upper()

                if user_input == "Y":
                    instance_path = new_instance_path
                else:
                    print("Please choose a different name.", color='red')
                    continue

            print(f'Creating instance at "{instance_path}"', color='green')
            if self.legacy_version:
                instance_manager.create_instance_data(
                    instance_name=os.path.basename(instance_path),
                    client_version=client_version,
                    version_type=version_type,
                    is_vanilla=True,
                    modify_status=False,
                    mod_loader_name=None,
                    mod_loader_version=None,
                    real_minecraft_version=real_version,
                    use_legacy_manifest=True
                )
                self.download_games_files(client_version, instance_path)
            else:
                instance_manager.create_instance_data(
                    instance_name=os.path.basename(instance_path),
                    client_version=client_version,
                    version_type=version_type,
                    is_vanilla=True,
                    modify_status=False,
                    mod_loader_name=None,
                    mod_loader_version=None,
                    real_minecraft_version=real_version,
                )
                self.download_games_files(client_version, instance_path)
            return True, "InstanceCreated"

    def reinstall_instances(self):
        # if the instances list is not exist, return Status=False and client_version=ErrorMessage
        print("The instance you want to install must have been converted to the new format!",
              color='red')  # legacy part
        Status, client_version, instance_path = instance_manager.select_instance(
            "Which instance you want to reinstall?", client_version=True)
        if not Status:
            print(f"Failed to get select instance. Cause by error {client_version}", color='red')
            return False

        if Status == "EXIT":
            print("Exiting...", color='green')
            return True

        instance_info = os.path.join(instance_path, "instance.bakelh.ini")
        Status, use_legacy_manifest = instance_manager.get_instance_info(instance_info, info_name="use_legacy_manifest")
        Status, instance_name = instance_manager.get_instance_info(instance_info, info_name="instance_name")
        if use_legacy_manifest:
            self.legacy_version = True
        else:
            self.legacy_version = False

        print(f"Reinstalling instance name {instance_name}...", color='green')
        print(f"Client Version: {client_version} Instance Path: {instance_path}", color='green', tag='DEBUG')
        self.download_games_files(client_version, instance_path)

    def create_instance(self):
        def download_minecraft_with_version_id(list_type=None):
            """
            Allows users to select and download a Minecraft version based on version ID.
            """
            print("Grabbing version list...")
            version_list = self.get_version_list(list_type or "release")

            if not version_list:
                print("No versions found. Please check your connection or version list source.", color='red')
                return

            print("VersionID: MinecraftVersion", "\n", color='purple')
            print("Example: 15: 1.12.2 , 15 is version 1.12's ID", color='green')

            # Handle special list types
            if list_type == "legacy_all":
                print(
                    "Warning: Version list is set to LEGACY_ALL. This may include unsupported versions.",
                    color='yellow')
                print("To reset the list, enter 'legacy_list' or 'list'.", color='green')

            # Additional instructions
            print("Some cool stuff:'")
            print(
                "Type 'list' to print list again. 'legacy_list' for legacy list(support more system than normal list)",
                color='blue')
            print("'legacy_all' for legacy list(but it wll print all available versions. The list will be long)",
                  color='blue')
            print("'list_all' can print all available versions(Not recommended. Poor support for most of system)",
                  color='purple')

            # Get user input
            version_id = input("Please enter the version ID:").strip()

            # Handle special commands
            if version_id.upper() == "EXIT":
                return

            command_mapping = {
                "LIST": "release",
                "LIST_ALL": "all_version",
                "LEGACY_LIST": "legacy",
                "LEGACY_ALL": "legacy_all",
            }

            if version_id.upper() in command_mapping:
                return download_minecraft_with_version_id(list_type=command_mapping[version_id.upper()])

            # Validate version_id as an integer
            try:
                version_id = int(version_id)
            except ValueError:
                print("Invalid version ID. Please enter a numeric value.", color='red')
                return download_minecraft_with_version_id(list_type=list_type)

            # Adjust version_id to match 0-based indexing
            version_id -= 1

            if not (0 <= version_id < len(version_list)):
                print(f"Version ID '{version_id + 1}' is out of range. Please try again.", color='red')
                return download_minecraft_with_version_id(list_type=list_type)

            # Get selected Minecraft version
            minecraft_version = version_list[version_id]

            # Clear screen/output (if ClearOutput is defined)
            if 'ClearOutput' in globals():
                ClearOutput()

            print("Creating instance...", color='green')
            try:
                self.legacy_version = False
                self.start_create_instance(minecraft_version)
            except Exception as e:
                print(f"Failed to create instance. Error: {e}", color='red')
                return

        def download_with_regular_minecraft_version():
            selected_version = False
            version_list = self.get_version_list("normal")
            print("Using regular Minecraft version method...", color='green')
            regular_version_input = str(input("Please enter the Minecraft version:"))
            # Find minecraft_version after get version_id(IMPORTANT:version =/= version_id!)

            if regular_version_input.upper() == "EXIT":
                return

            elif regular_version_input.upper() == "LIST":
                self.get_version_list("all_version")
                download_with_regular_minecraft_version()
                return

            for version in version_list:
                if regular_version_input == version:
                    selected_version = True

            try:
                if selected_version:
                    ClearOutput()
                    print("Creating instance....", color='green')
                    self.start_create_instance(regular_version_input)
                else:
                    # idk this thing would happen or not :)  , just leave it and see what happen....
                    print(f"You type Minecraft version {regular_version_input} are not found :(",
                          color='red')
                    download_with_regular_minecraft_version()

            except ValueError:
                # Back to download_main avoid crash(when user type illegal thing
                print("Oops! Invalid input :( Please enter Minecraft version.")
                download_with_regular_minecraft_version()

        def download_legacy_minecraft():
            while True:
                ClearOutput()
                print("Warning: This method most of data are unofficial(not release from mojang)", color='red')
                print("Legacy list may take over 1 min to generate it.", color='yellow')
                legacy_list = self.get_version_list("legacy_version_list", legacy_party=True)
                print("Please enter you want to download Minecraft version.", color='blue')
                download_version = str(input(":"))
                if download_version.strip().lower() in legacy_list:
                    self.legacy_version_id = download_version
                    self.legacy_version_type = self.get_version_type(download_version)
                    if not self.legacy_version_type == "old_alpha":
                        # except some official version
                        self.legacy_version = True
                    self.start_create_instance(download_version)
                    return True

                if download_version.strip().lower() == "exit":
                    return True

                print(f"You type Minecraft version {download_version} are not found :(",
                      color='red')

        print("Which method you wanna use?", color='green')
        print("1: List all available versions and download", color='green')
        print("2: Type regular Minecraft version and download(include snapshot)", color='blue')
        print("3: Download Legacy Minecraft", color='yellow')
        print("4: Reinstall instance", color='cyan')

        try:
            user_input = str(input(":"))
            if user_input.upper() == "EXIT":
                print("Exiting....", color='green')
                return

            if user_input == "1":
                download_minecraft_with_version_id()
            elif user_input == "2":
                download_with_regular_minecraft_version()
            elif user_input == "3":
                download_legacy_minecraft()
            elif user_input == "4":
                self.reinstall_instances()
            else:
                print("Unknown options :( Please try again.", color='red')
                self.create_instance()
        except ValueError:
            # Back to main avoid crash(when user type illegal thing)
            print("BakeLaunch: Oops! Invalid option :O  Please enter a number.", color='red')

            self.create_instance()


create_instance = Create_Instance()
