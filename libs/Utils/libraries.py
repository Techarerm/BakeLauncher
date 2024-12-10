import os
from LauncherBase import Base, print_custom as print


def libraries_check(libraries_folder):
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

    def find_duplicates(library_versions):
        for lib_name, versions in library_versions.items():
            # Sort versions by semantic versioning (newer versions first)
            versions.sort(key=lambda x: semantic_version_key(x[0]), reverse=True)

            # Check if there are duplicates
            if len(versions) > 1:
                print(f"Found duplicate libraries detected for {lib_name}:", color='red')
                for version, path, file in versions:
                    print(f"  Version: {version}, Path: {path}, File: {file}")

                # Identify the newest version
                newest_version = versions[0]
                print(f"  Keeping: {newest_version[1]}/{newest_version[2]}", color='lightgreen')
                print()

                for version, path, file in versions[1:]:  # Skip the newest version
                    file_to_delete = os.path.join(path, file)
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


def generate_libraries_paths(client_version, libraries_dir):
    jar_paths_string = ""
    client_jar_path = os.path.join(libraries_dir, "net", "minecraft", client_version, "client.jar")

    for root, dirs, files in os.walk(libraries_dir):
        for file in files:
            if file.endswith('.jar') and not file.startswith("client.jar"):
                # Skip adding client.jar to jar_paths_string
                relative_path = os.path.relpath(os.path.join(root, file), start=libraries_dir)
                full_path = os.path.join(".minecraft", "libraries", relative_path)

                # Append the path to the jar_paths_string with the correct separator
                if Base.Platform == "Windows":
                    jar_paths_string += full_path + ";"
                else:
                    jar_paths_string += full_path + ":"

    # Finally, append the client.jar path to the end of the jar paths string if it exists
    if client_jar_path:
        jar_paths_string += client_jar_path

    return jar_paths_string
