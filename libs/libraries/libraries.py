import os
import re
from itertools import cycle
from LauncherBase import Base, print_custom as print
from libs.Utils.utils import download_file, multi_thread_download
from libs.platform.platfrom import *


def libraries_check(libraries_folder, filter_names=None):
    """This function is under testing! Find all available libraries and detect the duplicate version."""
    if filter_names is None:
        filter_names = []

    def semantic_version_key(version):
        """
        Convert a semantic version string to a comparable tuple.
        Handles invalid versions by returning a fallback tuple.
        """
        try:
            return tuple(map(int, version.split('.')))
        except ValueError:
            # Fallback for non-semantic versions (place them last during sorting)
            return tuple()

    def normalize_library_name(file_name):
        """
        Extract the base library name (excluding suffixes like '-client' or '-universal').
        """
        if "-" in file_name:
            return file_name.split("-")[0]
        return file_name

    def should_skip_file(file_name):
        """
        Check if a file should be skipped based on filter_names.
        """
        return any(filter_name in file_name for filter_name in filter_names)

    def find_duplicates(library_versions):
        for lib_name, versions in library_versions.items():
            # Group by normalized file name to ensure distinct library types
            grouped_versions = {}
            for version, path, file in versions:
                base_name = normalize_library_name(file)
                if base_name not in grouped_versions:
                    grouped_versions[base_name] = []
                grouped_versions[base_name].append((version, path, file))

            for base_name, grouped in grouped_versions.items():
                # Sort versions by semantic versioning (newer versions first)
                grouped.sort(key=lambda x: semantic_version_key(x[0]), reverse=True)

                # Check for duplicates
                if len(grouped) > 1:
                    print(f"Found duplicate libraries for {lib_name} ({base_name}):", color='red')
                    for version, path, file in grouped:
                        print(f"  Version: {version}, Path: {path}, File: {file}")

                    # Identify the newest version
                    newest_version = grouped[0]
                    print(f"  Keeping: {newest_version[1]}/{newest_version[2]}", color='lightgreen')
                    print()

                    for version, path, file in grouped[1:]:  # Skip the newest version
                        file_to_delete = os.path.join(path, file)

                        # Check if the file should be skipped
                        if should_skip_file(file):
                            print(f"  Skipping deletion for filtered file: {file_to_delete}", color='yellow')
                            continue

                        print(f"  Deleting duplicate: {file_to_delete}", color='red')
                        try:
                            os.remove(file_to_delete)  # Delete the duplicate file
                            print(f"  Successfully deleted: {file_to_delete}", color='blue')
                        except OSError as e:
                            print(f"  Error deleting {file_to_delete}: {e}", color='red')

                    print()

    library_versions = {}

    # Traverse the libraries folder to find directories containing JAR files
    for root, dirs, files in os.walk(libraries_folder):
        for file in files:
            if file.endswith(".jar") and "natives" not in file:
                # Extract library name and version from the path
                parts = root.split(os.sep)
                if len(parts) >= 2:
                    library_name = parts[-2]
                    version = parts[-1]
                else:
                    library_name = None
                    version = None
                if library_name and version:
                    # Organize by library name and append versions with their paths
                    if library_name not in library_versions:
                        library_versions[library_name] = []
                    library_versions[library_name].append((version, root, file))

    # Check for duplicates
    find_duplicates(library_versions)


def generate_classpath(client_version, libraries_dir, **kwargs):
    """
    Search .jar file in the libraries_dir and combine all paths with classpath_separator
    :param client_version: Minecraft version (Client.jar must in folder *libraries_dir, "net", "minecraft",
     client_version, "client.jar"* If not, you may get some error while game launch
     :param libraries_dir: Directory containing all libraries.
     # extra parameter stuff
     :param kwargs:
     only_return_path_list > return the full library paths list (no client.jar path)
     without_client_jar > return classpath without client jar path
     custom_main_class_path > replace client jar path to custom main class path
     extra_classpath > append extra class paths to classpath
    """
    client_jar_path = None
    jar_paths_string = ""
    libraries_path_list = []
    classpath_separator = ":"

    if Base.Platform == "Windows":
        classpath_separator = ";"

    # parameter stuff
    only_return_path_list = kwargs.get("only_return_path_list", False)
    without_client_jar = kwargs.get("without_client_jar", False)
    custom_main_class_path = kwargs.get("custom_main_class_path", None)
    extra_classpath = kwargs.get("extra_classpath", None)

    # Client jar path
    client_jar_path = os.path.join(libraries_dir, "net", "minecraft", client_version, "client.jar")
    if without_client_jar and custom_main_class_path is not None:
        client_jar_path = custom_main_class_path

    for root, dirs, files in os.walk(libraries_dir):
        for file in files:
            if file.endswith('.jar') and not file.startswith("client.jar"):
                # Skip adding client.jar to jar_paths_string
                relative_path = os.path.relpath(os.path.join(root, file), start=libraries_dir)
                full_path = os.path.join("libraries", relative_path)

                # Append the path to the jar_paths_string with the correct separator
                if Base.Platform == "Windows":
                    jar_paths_string += full_path + classpath_separator
                else:
                    jar_paths_string += full_path + classpath_separator
                libraries_path_list.append(full_path)

    # Finally, append the client.jar path to the end of the jar paths string if it exists
    if not without_client_jar:
        jar_paths_string += client_jar_path
    else:
        jar_paths_string = jar_paths_string.rstrip(classpath_separator)

    if extra_classpath:
        jar_paths_string += classpath_separator + extra_classpath

    if only_return_path_list:
        return libraries_path_list

    return jar_paths_string


def convert_library_name_to_artifact_path(library_path, **kwargs):
    extra_id = None
    classifier = None
    extension = ".jar"
    only_return_artifact_name = kwargs.get("only_return_artifact_name", False)
    try:
        # Remove the square brackets
        library_path = library_path.strip("[]")

        # Split the library path into components
        components = library_path.split(":")
        if len(components) > 3:
            # Handle the components
            group_id = components[0]
            artifact_id = components[1]
            version_and_classifier = components[2]
            if len(components) >= 3:
                extra_id = components[3]
            artifact_version = version_and_classifier
        else:
            group_id = components[0]
            artifact_id = components[1]
            version_and_classifier = components[2]
            artifact_version = version_and_classifier
            if "@" in version_and_classifier:
                artifact_version, extension = version_and_classifier.split("@")
                extension = "." + extension

        if extra_id is not None:
            if "@" in extra_id:
                extension = "-" + extra_id.replace("@", ".")
            else:
                extension = "-" + extra_id + ".jar"

        # Convert group_id to group_path by replacing '.' with the file separator
        group_path = "/".join(group_id.split("."))

        # Construct the file name
        if classifier:
            artifact_file_name = f"{artifact_id}-{artifact_version}{extension}"
        else:
            artifact_file_name = f"{artifact_id}-{artifact_version}{extension}"

        # Construct the full artifact path
        artifact_path = f"{group_path}/{artifact_id}/{artifact_version}/{artifact_file_name}"

        if only_return_artifact_name:
            return True, artifact_id

        return True, artifact_path

    except Exception as e:
        return False, None


"""

def download_libraries(version_data, libraries_dir, **kwargs):
    # Download require libraries (from version data)
    library_are_native = False
    # Some parameter stuff
    normal_download = kwargs.get("normal_download", False)
    only_return_library_paths_list = kwargs.get("only_return_library_paths_list", False)
    name = "libraries"
    # Confirm libraries_dir are created
    os.makedirs(libraries_dir, exist_ok=True)

    # Waiting-Download-List
    multi_download_queue = []
    normal_download_url_list = []
    normal_download_path_list = []

    # Get libraries data from version_data
    libraries = version_data.get('libraries', [])

    # Search support user platform libraries
    for lib in libraries:
        lib_downloads = lib.get('downloads', {})
        artifact = lib_downloads.get('artifact')

        rules = lib.get('rules', None)
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
            lib_path = artifact.get('path', None)
            if lib_path is None:
                continue

            lib_url = artifact.get('url', None)
            if lib_url is None:
                continue

            lib_dest = os.path.join(libraries_dir, lib_path)
            os.makedirs(os.path.dirname(lib_dest), exist_ok=True)

            if library_are_native:
                continue

            if normal_download:
                normal_download_url_list.append(lib_url)
                normal_download_path_list.append(lib_dest)
            else:
                lib_url_and_dest = [
                    (lib_url, lib_dest)
                ]
                multi_download_queue.append(lib_url_and_dest)

    if only_return_library_paths_list:
        return normal_download_path_list
    else:
        if normal_download_url_list:
            for url, dest_path in zip(normal_download_url_list, normal_download_path_list):
                download_file(url, dest_path)
        else:
            multi_thread_download(multi_download_queue, name)
"""


def download_libraries(version_data, libraries_dir, **kwargs):
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
    normal_download_url_list = []
    normal_download_path_list = []

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

            lib_dest = os.path.join(libraries_dir, lib_path)
            os.makedirs(os.path.dirname(lib_dest), exist_ok=True)

            if library_are_native and bypass_download_natives:
                continue

            if normal_download:
                normal_download_url_list.append(lib_url)
                normal_download_path_list.append(lib_dest)
            else:
                lib_url_and_dest = [
                    (lib_url, lib_dest)
                ]
                multi_download_queue.append(lib_url_and_dest)

    if normal_download:
        for url, dest_path in zip(normal_download_url_list, normal_download_path_list):
            download_file(url, dest_path)
    else:
        multi_thread_download(multi_download_queue, name)

    if len(multi_download_queue) > 0:
        return True
    else:
        return False


def download_natives(version_data, libraries_dir, platform_name=Base.Platform, full_arch=Base.FullArch, **kwargs):
    """
    Download natives from version data
    :param version_data: Minecraft version data (JSON)
    :param libraries_dir: libraries folder (The path which library(natives) download to)
    :param unzip_natives_folder: The folder which natives unzip to
    :param platform_name: System (Platform) name (Example: Windows, macOS, Linux)
    :param full_arch: Platform Architecture (Support list: amd64(full support), arm64(not full support),
     i386(not full support. Drop support in the new version)
    """
    # parameter stuff
    only_return_lib_paths = kwargs.get("only_return_lib_paths", False)
    lib_paths = []

    global natives_key_list, native_keys_list

    platform_name = platform_name.lower()
    full_arch = full_arch.lower()

    support_arch_list = ["amd64", "arm64", "i386"]
    if full_arch not in support_arch_list:
        return False, "UnsupportedPlatform"

    # Extract numerical part of architecture (bit-width)
    arch = re.sub(r'\D', "", full_arch)
    if full_arch == "i386":
        arch = "32"

    print(f"Platform : {platform_name} | Architecture : {full_arch} | {arch}Bit", color='green', tag='DEBUG')

    # Map platforms to native keys
    platform_name_dict = {
        'windows': ['windows'],
        'linux': ['linux'],
        'darwin': ["osx"],
    }
    platform_name_list = platform_name_dict.get(platform_name, [])

    print(f"Platform Name < {' '.join(platform_name_list)} >")

    # Mapping native keys based on architecture
    map_keys_amd64 = {
        'windows': ['natives-windows', "natives-windows-64"],
        'linux': ['natives-linux'],
        'darwin': ['natives-macos', "natives-osx"],
        'windows-arm64': ['natives-windows'],
    }

    map_keys_arm64 = {
        'windows': ['natives-windows-arm64'],
        'linux': ['natives-linux-aarch64'],
        'darwin': ['natives-macos-arm64'],
        'windows-arm64': ['natives-windows-arm64'],
    }

    map_keys_i386 = {
        'windows': ['natives-windows-32', "natives-windows-x86"],
        'linux': ['natives-linux-aarch_64'],
        'darwin': ["natives-osx"],  # Unconfirmed
        'windows-arm64': ['natives-windows-arm64'],
    }

    # Assign correct native keys list based on architecture
    if full_arch == "amd64":
        native_keys_list = map_keys_amd64.get(platform_name, [])
    elif full_arch == "arm64":
        native_keys_list = map_keys_arm64.get(platform_name, [])
    elif full_arch == "i386":
        native_keys_list = map_keys_i386.get(platform_name, [])
    else:
        native_keys_list = []

    download_queue = []
    libraries_data = version_data.get('libraries', [])

    # Processing normal natives
    for lib in libraries_data:
        lib_name = lib.get("name", None)
        print(f"Checking lib {lib_name}...")
        lib_downloads = lib.get('downloads', {})

        # Check platform compatibility via rules
        rules = lib.get('rules', [])

        # Process only normal natives (without "classifiers" key)
        classifiers = lib_downloads.get("classifiers", None)
        if rules and classifiers is None:
            allow = rules[0]["action"] if rules and "action" in rules[0] else None
            allow_platform = [rules[0]["os"]["name"]] if rules and "os" in rules[0] and "name" in rules[0]["os"] else []
            disallow_platform = rules[1]["os"]["name"] if len(rules) > 1 and "os" in rules[1] and "name" in rules[1][
                "os"] else []
            artifact = lib_downloads.get('artifact', {})
            lib_path = artifact.get("path", None)
            natives = lib.get("natives", {})
            support_platform_list = list(natives.values())

            allowed_download = False
            for native_key in native_keys_list:
                for plat_name in platform_name_list:
                    if plat_name in disallow_platform:
                        continue

                    if native_key in support_platform_list:
                        allowed_download = True
                        break

                    if plat_name in allow_platform:
                        allowed_download = True
                        break

                    if not plat_name in allow_platform and allow:
                        allowed_download = True

                    if lib_path is not None:
                        if lib_path.endswith(f"{native_key}.jar"):
                            allowed_download = True

                if allowed_download:
                    break

            if allowed_download:
                lib_url = artifact.get("url", None)

                if lib_path is None or lib_url is None:
                    # print(f"Skipping library {lib_name}")
                    continue
                print(f"Library {lib_name} added!", color='lightgreen')
                lib_dest = os.path.join(libraries_dir, lib_path)
                os.makedirs(os.path.dirname(lib_dest), exist_ok=True)
                natives_url_and_dest = [
                    (lib_url, lib_dest)
                ]
                download_queue.append(natives_url_and_dest)
                lib_paths.append(lib_path)

        # Process classifiers if available
        if classifiers:
            for native_key in native_keys_list:
                if native_key in classifiers:
                    print(f"Found match native key in the lib {lib_name}", color='blue')
                    classifier_info = classifiers[native_key]
                    lib_path = classifier_info.get("path")
                    lib_url = classifier_info.get("url")

                    if not lib_path or not lib_url:
                        print(f"Skipping library {lib_name}")
                        continue

                    print(f"Library {lib_name} added!", color='lightgreen')
                    lib_dest = os.path.join(libraries_dir, lib_path)
                    os.makedirs(os.path.dirname(lib_dest), exist_ok=True)
                    natives_url_and_dest = [
                        (lib_url, lib_dest)
                    ]
                    download_queue.append(natives_url_and_dest)
                    lib_paths.append(lib_path)

    if only_return_lib_paths:
        return lib_paths

    multi_thread_download(download_queue, "natives")

    if len(download_queue) > 0:
        return True
    else:
        return False


"""
def download_natives(version_data, libraries_dir, **kwargs):
    # darwin macos osx
    global ib_platform_name, lib_name_2, lib_name_old, native_key

    #
    only_return_native_paths_list = kwargs.get("only_return_native_paths_list", False)
    natives_path_list = []

    lib_platform_name, lib_name_2, lib_name_old = get_special_platform_name("ALL")
    print(f"Platform: {Base.Platform} LibrariesPlatform: {lib_platform_name}", tag='Debug',
          color='green')

    # Map platforms to native keys
    native_keys = {
        'windows': 'natives-windows',
        'linux': 'natives-linux',
        'darwin': 'natives-macos',
        'windows-arm64': 'natives-windows-arm64',
        'macos-arm64': 'natives-macos-arm64',
    }

    if Base.FullArch.lower() == "arm64":
        if Base.Platform == "Windows":
            native_key = f"{lib_name_2}-arm64"
        elif Base.Platform == "Darwin":
            print("Arm64 macOS detected!", color='lightgreen')
            print("Older version of Minecraft are not supported arm64 macOS running.", end="", color='cyan')
            print("You can install Rosetta to make it works on your mac. (Not sure all version are supported)",
                  color='cyan')
            print("If you want install minecraft version are over (or same) 1.19, you may don't need to install this.")
            print("Do you already have Rosetta installed on your Mac ? Y/N", color='blue')
            user_input = str(input(":"))
            if user_input.lower() == "y":
                print("Using recommended setting...")
            else:
                print("Replace lib_name_2 to real...")
                native_key = f"{lib_name_2}-arm64"
    else:
        native_key = native_keys.get(lib_platform_name)

    if not native_key:
        print(f"Warning: No native key found for {lib_platform_name}", color='yellow')
        return "NativeKeyCheckFailed"

    download_queue = []
    natives_dest_list = []  # For unzip natives

    def add_to_queue(url, dest, og_path):
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        natives_url_and_dest = [
            (url, dest)
        ]
        download_queue.append(natives_url_and_dest)
        natives_dest_list.append(dest)
        natives_path_list.append(og_path)

    found_any_native = False

    libraries_data = version_data.get('libraries', {})

    for lib in libraries_data:
        lib_downloads = lib.get('downloads', {})

        # Check platform compatibility via rules
        rules = lib.get('rules')
        if rules:
            allowed = any(
                rule.get('action') == 'allow' and
                (not rule.get('os') or rule['os'].get('name') == lib_name_old)
                for rule in rules
            )
            disallowed = any(
                rule.get('action') == 'disallow' and
                rule.get('os', {}).get('name') == lib_name_old
                for rule in rules
            )
            if not allowed or disallowed:
                continue

        # Handle artifact downloads
        artifact = lib_downloads.get('artifact')
        if artifact and native_key in (lib.get('name', '') or artifact.get('path', '')):
            add_to_queue(artifact['url'], os.path.join(libraries_dir, artifact['path']), artifact['path'])
            found_any_native = True

        # Handle classifier downloads
        classifiers = lib_downloads.get('classifiers')
        if classifiers and native_key in classifiers:
            classifier_info = classifiers[native_key]
            add_to_queue(classifier_info['url'], os.path.join(libraries_dir, classifier_info['path']),
                         classifier_info['path'])
            found_any_native = True

    # Fallback for macOS to 'natives-osx'
    if not found_any_native and lib_platform_name == 'darwin':
        fallback_key = 'natives-osx'
        for lib in libraries_data:
            classifiers = lib.get('downloads', {}).get('classifiers')
            if classifiers and fallback_key in classifiers:
                classifier_info = classifiers[fallback_key]
                add_to_queue(classifier_info['url'], os.path.join(libraries_dir, classifier_info['path']),
                             classifier_info['path'])
                found_any_native = True
                break

    # Perform the batch download
    if only_return_native_paths_list:
        return natives_path_list
    else:
        if download_queue:
            multi_thread_download(download_queue, "natives")
            return True, None
        else:
            print(f"No native library found for key: {native_key}", color='yellow')
            return True, "NativeLibrariesNotFound"
"""
