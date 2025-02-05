from LauncherBase import Base


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
