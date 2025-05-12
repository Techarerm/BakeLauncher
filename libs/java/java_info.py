import json
import os.path
import textwrap

import requests

azul_packages_api = "https://api.azul.com/metadata/v1/zulu/packages"
java_manifest_url = 'https://launchermeta.mojang.com/v1/products/java-runtime/2ec0cc96c44e5a76b9c8b7c39df7210883d12871/all.json'


def get_java_build_download_url_from_azul(platform_name: str, full_arch: str, java_major_version: str):
    full_arch = full_arch.lower()
    platform_name = platform_name.lower()

    arch_map = {
        "arm64": "aarch64",
        "i686": "i686",
        "amd64": "amd64",
        "i386": "i686"
    }

    platform_map = {
        "macos": "macos",
        "darwin": "macos",
        "windows": "windows",
        "linux": "linux"
    }

    real_arch = arch_map.get(full_arch, full_arch)
    platform = platform_map.get(platform_name, platform_name)

    version_type_list = ["jre", "jdk"]

    jre_url = (
        f"/?java_version={java_major_version}&os={platform}&arch={real_arch}&java_package_type=jre&javafx_bundled=true"
        f"&release_status=ga&availability_types=CA&certifications=tck&page=1&page_size=100")

    full_jre_url = azul_packages_api + jre_url

    jdk_url = (f"/?java_version={java_major_version}&os={platform}&arch={real_arch}&java_package_type=jdk"
               f"&javafx_bundled=true"
               f"&release_status=ga&availability_types=CA&certifications=tck&page=1&page_size=100")

    full_jdk_url = azul_packages_api + jdk_url

    version_url_list = [full_jre_url, full_jdk_url]
    for url, ver_type in zip(version_url_list, version_type_list):
        try:
            response = requests.get(url)
            data = response.json()
            java_ver_data = data[0]
            download_url = java_ver_data.get("download_url", None)

            if download_url is not None:
                return True, download_url, ver_type
        except Exception as e:
            return False, None, None


def get_java_version_manifest_data():
    # Get java manifest
    try:
        response = requests.get(java_manifest_url)
        if response.status_code == 200:
            manifest_data = response.json()
            return manifest_data
        else:
            return None
    except Exception as e:
        return None


def get_support_java_version(version_data):
    """
    :param version_data: Special minecraft version data
    :return Status, component, major_version
    """
    try:
        java_version_info = version_data['javaVersion']
        component = java_version_info['component']
        major_version = java_version_info['majorVersion']
        return True, component, major_version
    except KeyError:
        return False, None, None


def get_support_java_version_from_java_version_manifest(platform, full_arch):
    """
    :return SupportList
    """

    platform_map = {
        "darwin": "mac-os",
        "windows": "windows",
        "linux": "linux"
    }

    architecture_map = {
        "amd64": ["x64"],
        "i586": ["x86", "i386"],
        "x86": ["i386", "x86"],
        "arm64": ["arm64"],
        "aarch64": ["arm64"]
    }

    platform_name = platform_map.get(platform.lower(), platform.lower())

    architecture_list = architecture_map.get(full_arch.lower(), full_arch.lower())

    try:
        response = requests.get(java_manifest_url)
    except Exception as e:
        return False, None

    java_manifest_data = response.json()
    java_manifest_data_cleaned = {}
    organized_manifest_data_list = []

    # Get all platform data (except item "gamecore")
    for arch_and_platform, support_java_data in java_manifest_data.items():
        if arch_and_platform == "gamecore":
            continue

        java_manifest_data_cleaned.update({arch_and_platform: support_java_data})

    # Separate platform name and arch from arch_and_platform
    for arch_and_platform, support_java_data in java_manifest_data_cleaned.items():
        if arch_and_platform == "mac-os":
            # For mac os (x86-64)
            java_platform = "mac-os"
            java_arch = "amd64"
        elif "-" in arch_and_platform:
            parts = arch_and_platform.split("-")
            java_platform = '-'.join(parts[:-1])
            java_arch = parts[-1]
        else:
            java_platform = arch_and_platform
            java_arch = "amd64"

        for java_runtime_name, runtime_data in support_java_data.items():
            if not java_runtime_name.startswith("java"):
                if not java_runtime_name.startswith("jre"):
                    continue

            # Skip some empty data
            if len(runtime_data) == 0:
                continue

            # If the platform and architecture are same, append data to list
            if not java_platform.lower() == platform_name:
                continue

            if java_arch.lower() not in architecture_list:
                continue

            # Convert data to dict
            result = {}
            for item in runtime_data:
                result.update(item)
            organized_manifest_data_list.append(result)

    return organized_manifest_data_list


def get_support_java_runtime_version_data(organized_manifest_data_list, major_version):
    """
    Warning: Require organized_manifest_data_list
    """
    java_version_url = None

    for data in organized_manifest_data_list:
        name = data.get("version", {}).get("name", None)
        url = data.get("manifest", {}).get("url", None)
        if name is None:
            continue

        if name.startswith(str(major_version)):
            if url is not None:
                java_version_url = url

    if java_version_url is not None:
        try:
            response = requests.get(java_version_url)
            data = response.json()

            return True, data
        except Exception as e:
            return False, None

    return False, None


def create_java_version_info(java_major_version, java_arch, jvm_runtimes_path):
    java_info_data = textwrap.dedent(f"""\
        # Java Runtime Info
        # This configuration is automatically generated by the BakeLauncher.
        # Configuration stores Java for the launcher (Example: major_version, architecture).
        # Do NOT edit this file or delete it!
        
        JavaMajorVersion = "{java_major_version}"
        Architecture = "{java_arch}"

    """)

    if not os.path.exists(jvm_runtimes_path):
        os.makedirs(jvm_runtimes_path)

    java_info_path = os.path.join(jvm_runtimes_path, "java.version.info")

    if not os.path.exists(java_info_path):
        with open(java_info_path, 'w') as file:
            file.write(java_info_data)


def read_java_info(info_file_path, item):
    with open(info_file_path, "r") as file:
        lines = file.readlines()

    for line in lines:
        line = line.strip()
        if item in line and '=' in line:
            data = line.split('=', 1)[1].strip().strip("")
            return str(data)

    return None