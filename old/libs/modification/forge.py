import json
import os.path
import shutil
from libs.Utils.utils import *
from libs.libraries.libraries import *


class forge_install:
    def __init__(self):
        self.forge_maven_url = "https://maven.minecraftforge.net/"
        self.mojang_maven_url = "https://libraries.minecraft.net/"

    def detect_forge_profile_depends(self, profile_data, **kwargs):
        # Set some variable
        ProcessorsData = []
        MavenNames = []
        url_libraries = []
        return_full_data = kwargs.get("return_full_data", False)

        # Get "data" object from the profile data
        full_data = profile_data.get("data", None)
        if full_data is None:
            return False, None

        if return_full_data:
            return True, full_data

        # Get MCP_VERSION
        MCP_VERSION = full_data.get("MCP_VERSION", {}).get("client", None)
        if MCP_VERSION is None:
            return False, None
        print("MCP_VERSION", MCP_VERSION)

        # Get BINPATCH
        BINPATCH = full_data.get("BINPATCH", {}).get("client", None)
        if BINPATCH is None:
            print("Warning: BINPATCH not found")
            pass

        # Put all dependencies into the waiting list
        for sub_depend, value in full_data.items():
            if "SHA" in sub_depend:
                print(f"{sub_depend} : {value["client"]}")
                continue

            data = value.get("client", None)
            if data is None:
                continue

            # Remove some symbols
            if "[" or "]" in data:
                data = data.replace("[", "").replace("]", "")

            if "'" in data:
                data = data.replace("'", "")
            data = f"{sub_depend}>{data}"
            ProcessorsData.append(data)

        # classifying dependency types (MavenName or other)
        for data in ProcessorsData:
            if ":" in data:
                MavenNames.append(data)

        # Convert all maven names to maven paths
        for name in MavenNames:
            components = name.split(">")
            key, maven_name = components
            print(f"Key : {key} | Name : {maven_name}")
            Status, path = convert_library_name_to_artifact_path(maven_name)
            if Status:
                URL = self.forge_maven_url + path
                url_libraries.append(URL)

    def convert_forge_data_to_real(self, depends_data, full_libraries_path):
        """
        You MUST download finished all required libraries before calling this function.
        If not, you may get error while processors forge.
        Convert all maven paths(inside the data) to the real path
        """
        redo_data = {}
        new_data = {}
        for key, value in depends_data.items():
            client_value = value.get("client", None)
            if client_value is not None:
                redo_data[key] = client_value

        for key, value in redo_data.items():
            Status, path = convert_library_name_to_artifact_path(value)
            if Status:
                print(f"Key : {key} | Old Value : {value} >>> New Value : {path}", color='green')
                full_path = os.path.join(full_libraries_path, path)
                redo_data[key] = full_path
            else:
                print(f"Key : {key} | Old Value : {value} >>> **BYPASS_CONVERT**", color='lightyellow')

        new_data = json.dumps(redo_data, indent=4)
        return new_data

    def get_forge_key_data(self, key_name, profile_data):
        data = profile_data.get("data", None)
        if data is None:
            return None

        return data.get(key_name, {}).get("client", None)

    def detect_forge_processors_depends(self, profile_data):
        processors_data = profile_data.get("processors", None)
        main_processors_class_maven_nams = []
        libraries_names = []

        if not processors_data:
            return False, None

        for data in processors_data:
            sides = data.get("sides", None)
            if sides is not None:
                continue

            # Get class name
            if "jar" in data:
                main_processors_class_maven_nams.append(data["jar"])

            # Get classpath
            if "classpath" in data:
                libraries_names.extend(data["classpath"])

        # Flatten the list of libraries
        return main_processors_class_maven_nams, libraries_names

    def get_forge_processor_depends(self, main_class_name, profile_data):
        global data
        processors_data = profile_data.get("processors", None)
        if processors_data is None:
            return False, None

        selected_processor_data = None

        for data in processors_data:
            class_name = data.get("jar", None)
            if class_name == main_class_name:
                selected_processor_data = data
                break

        # Check if a matching processor was found
        if selected_processor_data is None:
            return False, None

        classpath_list = selected_processor_data.get("classpath", None)
        if classpath_list is None:
            return False, None
        else:
            return True, classpath_list

    def get_forge_all_processors_class_name_and_args(self, profile_data):
        processors_data = profile_data.get("processors", None)
        server_required = profile_data.get("server_required", None)  # ???
        if processors_data is None:
            return False, None

        processors_maven_class_name_list = []
        processors_args_list = []

        for data in processors_data:
            sides = data.get("sides", None)

            if sides is None:
                name = data.get("jar", None)
                args_list = data.get("args", None)

                processors_maven_class_name_list.append(name)
                processors_args_list.append(args_list)

        return processors_maven_class_name_list, processors_args_list

    def download_forge_libraries_modern(self, profile_data, libraries_path):
        libraries = profile_data.get("libraries", {})
        download_queue = []
        for library in libraries:
            url = library.get("downloads", {}).get("artifact", {}).get("url", None)
            if url is None:
                continue
            if len(url) <= 0:
                continue
            path = library.get("downloads", {}).get("artifact", {}).get("path", None)
            if path is None:
                continue
            dest = os.path.join(libraries_path, path)
            library_dir = os.path.dirname(dest)
            os.makedirs(library_dir, exist_ok=True)

            # Download the library
            lib_url_and_dest = [
                (url, dest)
            ]
            download_queue.append(lib_url_and_dest)

        multi_thread_download(download_queue, "Forge libraries")

    def download_forge_libraries_legacy(self, libraries_data, libraries_path):
        global path
        libraries = libraries_data.get("libraries", {})
        download_queue = []
        for library in libraries:
            url = library.get("downloads", {}).get("artifact", {}).get("url", None)
            if url is None or len(url) == 0:
                # Pre-Legacy forge "serverreq": true"
                # server_require = library.get("serverreq", False)
                # client_require = library.get("clientreq", False)
                # if not client_require:
                # if server_require:
                # continue
                # Maven Path example : de.oceanlabs.mcp:mcp_config:1.12.2-20200226.224830@zip
                artifact = library.get("downloads", {}).get("artifact", None)
                maven_path = library.get("name", None)
                # If is legacy forge core file, skip it
                if artifact is not None:
                    continue
                # Convert maven path to the real path
                # de.oceanlabs.mcp:mcp_config:1.12.2-20200226.224830@zip =>
                # de/oceanlabs/mcp/mcp_config/1.12.2-20200226.224830/mcp_config-1.12.2-20200226.224830.zip
                Status, path = convert_library_name_to_artifact_path(maven_path)
                # Stitch into a url
                orig_maven_url = library.get("url", None)
                if orig_maven_url is None:
                    url = self.mojang_maven_url + path
                else:
                    url = self.forge_maven_url + path
            else:
                # For legacy forge (pre-modern)
                path = library.get("downloads", {}).get("artifact", {}).get("path", None)

            dest = os.path.join(libraries_path, path)
            library_dir = os.path.dirname(dest)
            os.makedirs(library_dir, exist_ok=True)
            final_url = url.replace("\\", "/")
            # Download the library
            lib_url_and_dest = [
                (final_url, dest)
            ]
            Status = check_url_status(final_url)
            if Status:
                download_queue.append(lib_url_and_dest)

        multi_thread_download(download_queue, "Forge libraries")

    def convert_maven_name_to_artifact_path_in_the_args(self, arguments, libraries_path):
        new_arguments = []

        for arg in arguments:
            # Detect and process strings in the form of '[ ... ]'
            if arg.startswith("[") and arg.endswith("]"):
                # Convert Maven path to real path
                Status, real_path = convert_library_name_to_artifact_path(arg)
                new_path = os.path.join(libraries_path, real_path)
                new_arguments.append(new_path)
            else:
                # Keep non-Maven path arguments unchanged
                new_arguments.append(arg)

        return new_arguments

    def replace_jvm_args_value_to_real(self, libraries_path, minecraft_version, full_args):
        if os.name == "nt":
            library_separator = ";"
        else:
            library_separator = ":"

        replacements = {
            "${library_directory}": libraries_path,
            "${version_name}": minecraft_version,
            "${classpath_separator}": library_separator,
        }

        # Initialize final_args with the original full_args
        final_args = full_args

        # Apply each replacement progressively
        for placeholder, value in replacements.items():
            final_args = final_args.replace(placeholder, value)

        return final_args

    def move_forge_files(self, unzip_dest, loader_version, instance_libraries, **kwargs):
        custom_forge_like_loader_name = kwargs.get("custom_forge_like_loader_name", None)
        custom_forge_like_loader_maven_name = kwargs.get("custom_forge_like_loader_maven_name", None)

        # For forge-like loader (Or the loader name "neoforge")
        if custom_forge_like_loader_name is not None:
            name = custom_forge_like_loader_name
        else:
            name = "forge"

        if custom_forge_like_loader_maven_name is not None:
            maven_name = custom_forge_like_loader_maven_name
        else:
            maven_name = "minecraftforge"
        # Some recommended path (The path of the forge core file)
        forge_lib_dir = os.path.join(instance_libraries, "net", maven_name, name, loader_version)
        forge_core_dir = os.path.join(instance_libraries, "maven", "net", maven_name, name, loader_version)
        forge_client_dir = os.path.join(instance_libraries, "net", maven_name, name, loader_version)
        os.makedirs(forge_lib_dir, exist_ok=True)
        os.makedirs(forge_core_dir, exist_ok=True)

        # Recommended core files names
        forge_universal_name = f"{name}-{loader_version}-universal.jar"
        forge_core_name = f"{name}-{loader_version}.jar"
        forge_client_name = f"{name}-{loader_version}-client.jar"

        # Move universal jar
        universal_candidates = [
            os.path.join(unzip_dest, forge_universal_name),
            os.path.join(unzip_dest, "maven", "net", maven_name, name, loader_version, forge_universal_name),
            os.path.join(unzip_dest, "libraries", "net", maven_name, name, loader_version, forge_universal_name)
        ]
        for src_path in universal_candidates:
            if os.path.exists(src_path):
                shutil.move(src_path, os.path.join(forge_lib_dir, forge_universal_name))

        # Move core jar
        core_candidates = [
            os.path.join(unzip_dest, forge_core_name),
            os.path.join(unzip_dest, "maven", "net", maven_name, name, loader_version, forge_core_name),
            os.path.join(unzip_dest, "libraries", "net", maven_name, name, loader_version, forge_core_name)
        ]
        for src_path in core_candidates:
            if os.path.exists(src_path):
                shutil.move(src_path, os.path.join(forge_core_dir, forge_core_name))

        # Move client jar
        client_candidates = [
            os.path.join(unzip_dest, forge_client_name),
            os.path.join(unzip_dest, "maven", "net", maven_name, name, loader_version, forge_client_name),
            os.path.join(unzip_dest, "libraries", "net", maven_name, name, loader_version, forge_client_name)
        ]

        for src_path in client_candidates:
            if os.path.exists(src_path):
                shutil.move(src_path, os.path.join(forge_client_dir, forge_client_name))


forge = forge_install()
