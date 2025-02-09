from LauncherBase import Base, print_custom as print


def get_special_platform_name(platform_name_type):
    # Get the special platform name for some method
    LibrariesPlatform = Base.Platform.lower()
    if Base.Platform == "Darwin":
        LibrariesPlatform2nd = "macos"
        LibrariesPlatform2ndOld = "osx"
    else:
        LibrariesPlatform2nd = LibrariesPlatform
        LibrariesPlatform2ndOld = LibrariesPlatform

    if platform_name_type.lower() == "librariesplatform":
        return LibrariesPlatform
    elif platform_name_type.lower() == "librariesplatform2nd":
        return LibrariesPlatform2nd
    elif platform_name_type.lower() == "librariesplatform2ndOld":
        return LibrariesPlatform2ndOld
    else:
        return LibrariesPlatform, LibrariesPlatform2nd, LibrariesPlatform2ndOld


def macos_natives_rosetta_support():
    print("Arm64 macOS detected!", color='lightgreen')
    print("Older version of Minecraft are not supported arm64 macOS running.", end="", color='cyan')
    print("You can install Rosetta to make it works on your mac. (Not sure all version are supported)",
          color='cyan')
    print("If you want install minecraft version are over (or same) 1.19, you may don't need to install this.")
    print("Do you already have Rosetta installed on your Mac ? Y/N", color='blue')
    user_input = str(input(":"))
    if user_input.lower() == "y":
        print("Using recommended setting...")
        return True
    else:
        print("Replace lib_name_2 to real...")
        return False

def arm64_jvm_support(platform_name, java_major_version):
    print("All Java runtimes build are from azul.", color='purple')
    print("Checking support...", color='green')

