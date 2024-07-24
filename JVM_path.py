"""
Warring:I only add Java 21 support(for 1.20.5 up to 1.21)
"""


import os
import subprocess


def get_java_home():
    """Find system java path...(Is not all)"""
    return os.getenv('JAVA_HOME')


def find_jvm_paths():
    """
    Finds potential JVM installation paths.(Only for Windows)
    """
    paths = []
    # Check common installation directories
    common_paths = [
        "C:\\Program Files\\Java",
        "C:\\Program Files (x86)\\Java"
    ]

    for path in common_paths:
        if os.path.exists(path):
            for root, dirs, files in os.walk(path):
                for dir_name in dirs:
                    if "jdk" in dir_name or "jre" in dir_name:
                        paths.append(os.path.join(root, dir_name))
            break
    return paths


def get_jvm_version(java_bin):
    """Gets the version of the JVM."""
    try:
        print(f"Checking JVM version for: {java_bin}")
        version_output = subprocess.check_output([java_bin, "-version"], stderr=subprocess.STDOUT,
                                                 universal_newlines=True)
        for line in version_output.split('\n'):
            if "version" in line:
                version = line.split('"')[1]
                return version
    except subprocess.CalledProcessError as e:
        print(f"Error checking version for {java_bin}: {e}")
    except FileNotFoundError as e:
        print(f"Java executable not found: {java_bin}")
    return None


def main():
    java_home = get_java_home()
    if java_home:
        java_bin = os.path.join(java_home, "bin", "java")
        if os.path.isfile(java_bin):
            version = get_jvm_version(java_bin)
            if version and int(version.split('.')[0]) > 21:
                print(f"JVM found in JAVA_HOME with version {version}: {java_home}")
                return

    jvm_paths = find_jvm_paths()
    for path in jvm_paths:
        java_bin = os.path.join(path, "bin", "java")
        if os.path.isfile(java_bin):
            version = get_jvm_version(java_bin)
            if version and int(version.split('.')[0]) > 21:
                print(f"JVM found with version {version}: {path}")
                return

    print("No JVM found with version greater than 21.")


if __name__ == "__main__":
    main()
