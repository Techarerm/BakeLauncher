import sys
import zipfile
import requests
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from LauncherBase import Base, print_custom as print

VersionManifestURl = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"
LegacyVersionManifestURl = ("https://github.com/Techarerm/BakeLauncher-Library/raw/refs/heads/main/Legacy"
                            "%20Manifest/version_manifest_legacy.json")


def get_version_data(version_id):
    """
    Get version_manifest_v2.json and find requires version of json data
    """

    response = requests.get(VersionManifestURl)
    data = response.json()
    version_list = data['versions']

    version_url = None
    for v in version_list:
        if v['id'] == version_id:
            version_url = v['url']
            break

    if version_url is None:
        response = requests.get(LegacyVersionManifestURl)
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
        print("Failed to get version data :(", color='red')
        return None


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
            print(f"Download successful: {dest_path}", color='lightblue')
        return True  # Indicate success
    except requests.exceptions.RequestException as e:
        print(f"Failed to download {url}: {e}", color='red')
        return False  # Indicate failure


def extract_zip(zip_path, extract_to):
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        print(f"Extracted {zip_path} to {extract_to}")
    except zipfile.BadZipFile as e:
        print(f"Error extracting {zip_path}: {e}", color='red')


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


def write_global_config(item_name, new_item_data):
    found = False
    with open(Base.global_config_path, 'r') as file:
        lines = file.readlines()
        for i in range(len(lines)):
            if item_name in lines[i]:
                # Use the new or existing account ID
                lines[i] = f'{item_name} = "{new_item_data}"\n'
                found = True
    with open(Base.global_config_path, 'w') as file:
        file.writelines(lines)
    if found:
        return True
    else:
        return False

def find_main_class(client_version):
    version_data = get_version_data(client_version)
    main_class = version_data.get("mainClass")
    return main_class