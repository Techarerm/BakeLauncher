import argparse
from print_color import print
from __function__ import GetPlatformName
from __function__ import ClearOutput
from __function__ import timer
from launch_client import launch_wit_args

def argsman():
    ClearOutput(GetPlatformName.check_platform_valid_and_return())
    print("Modify Launch arguments are coming soon :)", color='g' )
    timer(8)


def parse_arguments(platform, custom_args):
    version = librariesCFG = gameDir = assetsDir = assetsIndex = JVMPath = nativespath = MainClass =None
    # Create ArgumentParser for handling custom arguments
    parser = argparse.ArgumentParser(description='"BakeLauncher Custom Arguments Manager"')

    # Add the '-launch' argument (mandatory)
    parser.add_argument('-launch', help="Enable automatic launch client.")

    # Add the optional arguments (they will be required only if -launch is provided)
    parser.add_argument('--version', dest="version", type=str, help="Launch Minecraft version.")
    parser.add_argument('--librariesCFG', dest="librariesCFG", type=str, help="Libraries cfg")
    parser.add_argument('--gameDir', dest="gameDir", type=str, help=".minecraft folder path")
    parser.add_argument('--assetsDir', dest="assetsDir", type=str, help="Assets folder path")
    parser.add_argument('--assetsIndex', dest="assetsIndex", type=str, help="Assets folder path")
    parser.add_argument('--JVMPath', dest="JVMPath", type=str, help="Java runtimes path")
    parser.add_argument('--nativesPath', dest="nativesPath", type=str, help="natives path")
    parser.add_argument('--MainClass', dest="MainClass", type=str, help="MainClass")

    # Parse the initial arguments to check if '-launch' is provided
    args = parser.parse_args(custom_args)

    # If '-launch' is provided, enforce that the other arguments are mandatory
    if args.launch:
        # Ensure that all other arguments are provided
        if not args.version:
            parser.error("--version is required when using -launch")
        if not args.librariesCFG:
            parser.error("--librariesCFG is required when using -launch")
        if not args.gameDir:
            parser.error("--gameDir is required when using -launch")
        if not args.assetsDir:
            parser.error("--assetsDir is required when using -launch")
        if not args.assetsIndex:
            parser.error("--assetsIndex is required when using -launch")
        if not args.nativesPath:
            parser.error("--assetsIndex is required when using -launch")
        if not args.MainClass:
            parser.error("--MainClass is required when using -launch")

    # Assign parsed argument values to variables
    version = args.version
    librariesCFG = args.librariesCFG
    gameDir = args.gameDir
    assetsDir = args.assetsDir
    assetsIndex = args.assetsIndex
    JVMPath = args.JVMPath
    nativespath = args.nativesPath
    MainClass = args.MainClass

    # Return the parsed arguments
    ErrorCheck_Launch = launch_wit_args(platform, version, librariesCFG, gameDir, assetsDir, assetsIndex, JVMPath, nativespath, MainClass)
    if ErrorCheck_Launch == None:
        return
    else:
        print(f"BakeLauncher: Custom arguments launch failed! Cause By {ErrorCheck_Launch}")
    return True