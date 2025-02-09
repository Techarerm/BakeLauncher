import requests

azul_packages_api = "https://api.azul.com/metadata/v1/zulu/packages"


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

    jre_url = (f"/?java_version={java_major_version}&os={platform}&arch={real_arch}&java_package_type=jre&javafx_bundled=true"
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





