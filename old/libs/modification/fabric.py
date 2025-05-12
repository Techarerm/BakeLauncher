import os
import shutil
import requests
from libs.Utils.utils import download_file, multi_thread_download
from LauncherBase import Base
from launcher.cli.Data import print_custom as print


class fabric_install():
    def __init__(self):
        self.fabric_maven = f"https://maven.fabricmc.net"

    def get_fabric_version_data(self, loader_version, client_version):
        if not loader_version or not client_version:
            return None

        fabric_version_url = f"https://meta.fabricmc.net/v2/versions/loader/{client_version}/{loader_version}"

        r = requests.get(fabric_version_url)
        if not r.ok:
            return None
        else:
            version_data = r.json()

        if "launcherMeta" in version_data:
            return version_data

        return None

    def download_loader(self, loader_version, libraries_path):
        # Check loader version valid
        if not loader_version:
            return False

        loader_path = f"/net/fabricmc/fabric-loader/{loader_version}/fabric-loader-{loader_version}.jar"
        loader_url = self.fabric_maven + loader_path
        loader_dest = libraries_path + loader_path

        download_file(loader_url, loader_dest)
        if not os.path.exists(loader_dest):
            return False

        return True

    def download_intermediary(self, client_version, libraries_path):
        if not client_version:
            return False

        intermediary_path = f"/net/fabricmc/intermediary/{client_version}/intermediary-{client_version}.jar"
        intermediary_url = self.fabric_maven + intermediary_path
        intermediary_dest = libraries_path + intermediary_path
        download_file(intermediary_url, intermediary_dest)

        if not os.path.exists(intermediary_dest):
            return False

        return True

    @staticmethod
    def download_libraries(libraries_data, libraries_path):
        download_queue = []

        for lib in libraries_data:
            group_id, artifact_id, version = lib["name"].split(":")

            # Create directory structure (use '/' for URL paths)
            group_path = group_id.replace(".", "/")  # Convert groupId to folder structure using "/"
            library_path = os.path.join(libraries_path, group_path, artifact_id, version)

            # Ensure the target folder exists
            os.makedirs(library_path, exist_ok=True)

            # Construct the download URL using the corrected path
            url = f"https://maven.fabricmc.net/{group_path}/{artifact_id}/{version}/{artifact_id}-{version}.jar"

            # Full path where the JAR will be saved
            destination = os.path.join(library_path, f"{artifact_id}-{version}.jar")

            # Download the library
            fabric_lib_url_and_dest = [
                (url, destination)
            ]
            download_queue.append(fabric_lib_url_and_dest)
        multi_thread_download(download_queue, "Fabric libraries")

    def get_support_fabric_loader_list(self, client_version, **kwargs):
        full_list = kwargs.get("full_list", False)
        only_stable = kwargs.get("only_stable", False)
        if not client_version:
            return False, None

        fabric_support_version_url = f"https://meta.fabricmc.net/v2/versions/loader/{client_version}"

        # Get the list of all loader versions
        response = requests.get(fabric_support_version_url)
        if response.status_code != 200:
            return False, None

        loader_data = response.json()
        loader_versions = []

        # Only return the stable version
        if only_stable:
            for loader in loader_data:
                if loader["loader"]["stable"]:
                    return True, loader["loader"]["version"]
            return False, None

        if full_list:
            # Collect the available Fabric loader versions
            for loader in loader_data:
                loader_versions.append(loader["loader"]["version"])
        else:
            # Collect only 20 versions in the list
            version_length = 0
            for loader in loader_data:
                if version_length < 20:
                    loader_versions.append(loader["loader"]["version"])
                else:
                    break
                version_length += 1

        if not loader_versions:
            return False, None

        return True, loader_versions


fabric = fabric_install()
