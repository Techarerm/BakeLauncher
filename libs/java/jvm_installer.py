import os
import hashlib
import requests
from tqdm import tqdm
from LauncherBase import Base, print_custom as print


class class_jvm_installer:

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


jvm_installer = class_jvm_installer()
