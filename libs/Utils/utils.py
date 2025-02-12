import sys
import zipfile
import requests
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from LauncherBase import Base, print_custom as print
from libs.Utils.crypto import verify_checksum, verify_checksum_v2

VersionManifestURl = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"
LegacyVersionManifestURl = ("https://github.com/Techarerm/BakeLauncher-Library/raw/refs/heads/main/Legacy"
                            "%20Manifest/version_manifest_legacy.json")


def download_file(url, dest_path, **kwargs):
    """
    Downloads a file from a URL and saves it to dest_path.
    """
    # parameter stuff
    with_verify = kwargs.get('with_verify', True)
    sha1 = kwargs.get('sha1', None)
    no_output = kwargs.get('no_output', False)
    chunk_size = kwargs.get('custom_chunk_size', 8192)

    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()

        # Create the directory if it doesn't exist
        dest_dir = os.path.dirname(dest_path)
        if dest_dir:
            os.makedirs(dest_dir, exist_ok=True)

        # Write the file to dest_path
        with open(dest_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=chunk_size):
                file.write(chunk)

        if with_verify:
            if sha1 is not None:
                Status = verify_checksum(dest_path, sha1)
                if not Status:
                    return False

        if not no_output:
            print(f"Download successful: {dest_path}", color='lightgreen')

        return True
    except requests.exceptions.RequestException as e:
        if not no_output:
            print(f"Failed to download {url}: {e}", color='red')
        return False


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
    no_output = True

    if Base.UsingLegacyDownloadOutput:
        no_output = False

    def download_with_retry(url, dest_path, retry_count):
        """Attempts to download a file with retries."""
        for attempt in range(retry_count + 1):
            success = download_file(url, dest_path, no_output=no_output)  # Replace with your download logic
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
        print("Files that failed after retries:", failed_files, color='red')
    return downloaded_files, failed_files


def multithread_download(download_url_list, file_dest_list, progress_name, max_workers=8, **kwargs):
    support_crypto_type = ["sha1", "md5", "sha256"]
    total_files = len(download_url_list)
    download_task = {}
    failed_files = []

    # parameters

    with_verify_checksum = kwargs.get("with_verify_checksum", False)
    file_hash_list = kwargs.get("file_hash_list", [])
    download_with_progress_bar = kwargs.get("download_with_progress_bar", False)
    no_output = kwargs.get("no_output", download_with_progress_bar)
    crypto_type = kwargs.get("crypto_type", "sha1")

    if crypto_type not in support_crypto_type:
        return False, f"Unsupported crypto type {crypto_type}."

    if with_verify_checksum:
        if not len(file_hash_list) > 0:
            return False, "file_hash_list not found."
    else:
        for i in range(0, len(download_url_list)):
            file_hash_list.append(None)

    def download_file_with_failure_return(url, file_dest_path):
        down_status = download_file(url, file_dest_path, no_output=no_output)
        return down_status

    def download_file_with_failure_return_and_verify(url, file_dest, hash):
        down_status = download_file(url, file_dest, no_output=no_output)
        if not down_status:
            return False

        status = verify_checksum_v2(file_dest, hash, crypto_type)
        if not status:
            if not no_output:
                print(f"Warning: File {file_dest} checksum mismatch. Deleting...")
            try:
                os.remove(file_dest)
            except Exception as e:
                print(f"Error deleting file: {e}")
            return False

        return True

    # Start first download attempt
    with ThreadPoolExecutor(max_workers=max_workers) as executor:

        pbar_download = tqdm(total=total_files, desc=f"Downloading {progress_name}",
                             unit="file") if download_with_progress_bar else None

        for file_url, file_dest, file_hash in zip(download_url_list, file_dest_list, file_hash_list):
            if with_verify_checksum:
                future = executor.submit(download_file_with_failure_return_and_verify, file_url, file_dest, file_hash)
            else:
                future = executor.submit(download_file_with_failure_return, file_url, file_dest)
            download_task[future] = (file_url, file_dest, file_hash)

        for future in as_completed(download_task):
            url, dest_path, _ = download_task[future]
            download_status = future.result()
            if not download_status:
                failed_files.append((url, dest_path))

            if pbar_download:
                pbar_download.update(1)

        if pbar_download:
            pbar_download.close()

    # Retry failed downloads
    if failed_files:
        retry_failed_files = []
        with ThreadPoolExecutor(max_workers=max_workers) as retry_executor:
            pbar_retry = tqdm(total=len(failed_files), desc=f"Re-Downloading {progress_name}",
                              unit="file") if download_with_progress_bar else None
            retry_download_task = {}

            for url, dst_path in failed_files:
                future = retry_executor.submit(download_file_with_failure_return, url, dst_path
                                               , no_output=download_with_progress_bar)
                retry_download_task[future] = (url, dst_path)

            for future in as_completed(retry_download_task):
                url, dest_path = retry_download_task[future]
                download_status = future.result()
                if not download_status:
                    retry_failed_files.append(url)

                if pbar_retry:
                    pbar_retry.update(1)

            if pbar_retry:
                pbar_retry.close()

        if retry_failed_files:
            for url in retry_failed_files:
                print(f"Failed to download file. URL: {url}")

    return True


def find_jar_file_main_class(jar_file_path):
    manifest_path = 'META-INF/MANIFEST.MF'
    try:
        with zipfile.ZipFile(jar_file_path, 'r') as jar:
            if manifest_path in jar.namelist():
                manifest = jar.read(manifest_path).decode('utf-8')
                for line in manifest.splitlines():
                    if line.startswith('Main-Class:'):
                        # Return the class name specified in the Main-Class entry
                        return line.split(':')[1].strip()
    except Exception as e:
        return None


def check_url_status(url):
    try:
        # Send a HEAD request to save bandwidth
        response = requests.head(url, allow_redirects=True, timeout=5)
        if response.status_code == 200:
            return True
        elif response.status_code == 404:
            return False
        else:
            return False
    except Exception as e:
        return False
