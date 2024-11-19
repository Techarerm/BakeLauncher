import requests
import os
import zipfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from LauncherBase import Base, ClearOutput, print_custom as print
from libs.__assets_grabber import assets_grabber_manager
from libs.download_jvm import install_jvm
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
            with tqdm(total=len(failed_files), desc=f"Downloading {name}", unit="file") as progress_bar:
                for future in future_to_url:
                    url, dest_path = future_to_url[future]
                    try:
                        success = future.result()
                        if success:
                            downloaded_files.append(dest_path)
                    except Exception as exc:
                        print(f"Error downloading {url}: {exc}")
                    # Update the progress bar after each file retry
                    progress_bar.n = total_files
                    progress_bar.update(1)

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
        self.VersionManifestURl = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"
        self.version_id = None
        self.minecraft_version = ""

        # Working directory
        self.WorkDir = os.getcwd()

    def get_version_data(self, version_id):
        """
        Get version_manifest_v2.json and find requires version of json data
        """
        response = requests.get(self.VersionManifestURl)
        data = response.json()
        version_list = data['versions']

        # Find the URL for the given version_id
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

    def get_version_list(self, mode):
        # Get version_manifest_v2.json and list all versions (with version_id on the left)
        response = requests.get(self.VersionManifestURl)
        data = response.json()
        version_list = data['versions']

        all_available_version = [version['id'] for version in data['versions']]
        release_versions = [version['id'] for version in version_list if version['type'] == 'release']

        # Legacy
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
        else:
            return all_available_version

    def download_natives(self, libraries, libraries_dir):
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

    def download_libraries(self, version_data, version_id):
        """
        Create instances/version_id/folder and download game files
        """
        version_dir = os.path.join("instances", version_id)
        libraries_dir = os.path.join(version_dir, "libraries")
        os.makedirs(libraries_dir, exist_ok=True)

        # Download client.jar
        client_info = version_data['downloads']['client']
        client_url = client_info['url']
        client_dest = os.path.join(version_dir, 'libraries', 'net', 'minecraft', version_id, "client.jar")
        print(f"Downloading client.jar to {client_dest}...")
        download_file(client_url, client_dest)

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
        time.sleep(0.5)
        self.download_natives(libraries, libraries_dir)

    def unzip_natives(self, version):
        global unzip_status

        # Handle platform naming for macOS
        if Base.LibrariesPlatform == 'darwin':
            PlatformName = 'macos'

        if not os.path.exists(f"instances/{version}/.minecraft/natives"):
            os.mkdir(f"instances/{version}/.minecraft/natives")

        os.chdir(f"instances/{version}")
        # Find all natives and unzip
        print("Unzipping Natives...", color='green')
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
            print("Unzip Natives successfully!", color='blue')
        else:
            print("Warring: You may get some error you download libraries. Please re-download this version of"
                  " Minecraft again.", color='yellow')
        os.chdir(self.WorkDir)

    @staticmethod
    def mac_os_libraries_bug_fix(minecraft_version):
        # Patch for some idiot version bug
        if Base.Platform == "Darwin":
            directory = f"instances/{minecraft_version}/libraries/ca/weblite/1.0.0"
            if not os.path.exists(directory):
                os.makedirs(directory)  # Create intermediate directories if needed
                url = "https://libraries.minecraft.net/ca/weblite/java-objc-bridge/1.0.0/java-objc-bridge-1.0.0.jar"
                try:
                    download_file(url, f"{directory}java-objc-bridge-1.0.0.jar")
                except Exception as e:
                    print(f"An error occurred: {e}")

    def download_games_files(self, version_id):
        print("Loading version info...")
        version_data = self.get_version_data(version_id)
        # Download game file( libraries, .jar files...., and natives)
        print("Downloading libraries...", color='blue')
        self.download_libraries(version_data, version_id)
        self.mac_os_libraries_bug_fix(version_id)
        print("The required dependent libraries should have been downloaded :)", color='blue')

        # Download assets(Also it will check this version are use legacy assets or don't use)
        print("Downloading assets...", color='purple')
        assets_grabber_manager.assets_file_grabber(version_id)
        os.chdir(self.WorkDir)

        print("Unzipping natives...", color='green')
        self.unzip_natives(version_id)

        print("Downloading JVM...", color='cyan')
        install_jvm(version_id)

        print("When you install a Java version that has never been installed before,"
              " you need to reconfig Java Path!",
              color='blue')
        print("Now all files are download success :)", color='blue')
        print("Exiting....", color='green')

        # Add waiting time(If assets download failed it will print it?)
        time.sleep(1.2)

    def create_instance(self):
        def download_minecraft_with_version_id(**kwargs):
            global list_type
            if not kwargs:
                print("Grabbing version list...")
                version_list = self.get_version_list("release")
                print("VersionID: MinecraftVersion", "\n", color='purple')
                print("Example: 15: 1.12.2 , 15 is version 1.12's ID", color='green')
                list_type = ""
            else:
                list_type = kwargs.get('list_type', None)  # Default to None if 'list_type' is not provided
                print("Grabbing version list...")
                version_list = self.get_version_list(list_type)
                print("VersionID: MinecraftVersion", "\n", color='purple')
                print("Example: 15: 1.12.2 , 15 is version 1.12's ID", color='green')

            if list_type == "legacy_all":
                print(
                    "Warning: Version list has been set to LEGACY_ALL. That mean launcher will search version_id in LEGACY_ALL.",
                    color='yellow')
                print("To reset the list back to original. You can enter 'legacy_list' or just 'list' to back.",
                      color='green')
            print("Some cool stuff:'")
            print(
                "Type 'list' to print list again. 'legacy_list' for legacy list(support more system than normal list)",
                color='blue')
            print("'legacy_all' for legacy list(but it wll print all available versions. The list will be long)",
                  color='blue')
            print("'list_all' can print all available versions(Not recommended. Poor support for most of system)",
                  color='purple')
            version_id = str(input("Please enter the version ID:"))

            if version_id.upper() == "EXIT":
                return

            if version_id.upper() == "LIST":
                download_minecraft_with_version_id(NO_LIST=True, list_type="release")
                return

            if version_id.upper() == "LIST_ALL":
                print(
                    "Warning: Version list has been set to 'LIST_ALL'. That mean launcher will search version_id in 'LIST_ALL'.",
                    color='yellow')
                print("To reset the list back to original. You can enter 'legacy_list' or just 'list' to back.",
                      color='green')
                download_minecraft_with_version_id(NO_LIST=True, list_type="all_version")
                return

            if version_id.upper() == "LEGACY_LIST":
                download_minecraft_with_version_id(NO_LIST=True, list_type='legacy')
                return

            if version_id.upper() == "LEGACY_ALL":
                print(
                    "Warning: Version list has been set to LEGACY_ALL. That mean launcher will search version_id in LEGACY_ALL.",
                    color='yellow')
                print("To reset the list back to original. You can enter 'legacy_list' or just 'list' to back.",
                      color='green')
                download_minecraft_with_version_id(NO_LIST=True, list_type='legacy_all')
                return

            try:
                version_id = int(version_id)
            except ValueError:
                print('Failed to get version ID :(', color='red')

            if isinstance(version_id, int):
                version_id = int(version_id)
            else:
                print("You are NOT typing a valid versionID!", color='red')
                print("VersionID: MinecraftVersion", "\n")
                print(
                    "Please type VersionID not MinecraftVersion or back memu and using '2:Type Minecraft version' "
                    "method !")
                print("Example: 15: 1.12.2 , 15 is version 1.12's ID", color='green')
                time.sleep(2)
                download_minecraft_with_version_id()

            version_id -= 1
            if 0 <= version_id < len(version_list):
                # Check user type version_id are available
                minecraft_version = version_list[version_id]
                self.download_games_files(minecraft_version)
                return
            else:
                print(f"You type version id '{version_id}' are not found :(", color='red')
                time.sleep(1.2)
                download_minecraft_with_version_id()

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
                    self.download_games_files(regular_version_input)
                else:
                    # idk this thing would happen or not :)  , just leave it and see what happen....
                    print(f"You type Minecraft version {regular_version_input} are not found :(",
                          color='red')
                    download_with_regular_minecraft_version()

            except ValueError:
                # Back to download_main avoid crash(when user type illegal thing
                print("Oops! Invalid input :( Please enter Minecraft version.")
                download_with_regular_minecraft_version()

        print("Which method you wanna use?", color='green')
        print("1:List all available versions and download 2:Type regular Minecraft version and download(include "
              "snapshot)")

        try:
            user_input = str(input(":"))
            if user_input.upper() == "EXIT":
                print("Exiting....", color='green')
                return

            if user_input == "1":
                download_minecraft_with_version_id()
            elif user_input == "2":
                download_with_regular_minecraft_version()
            else:
                print("Unknown options :( Please try again.", color='red')
                self.create_instance()
        except ValueError:
            # Back to main avoid crash(when user type illegal thing)
            print("BakeLaunch: Oops! Invalid option :O  Please enter a number.", color='red')

            self.create_instance()


create_instance = Create_Instance()
