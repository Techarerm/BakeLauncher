import argparse
import os
import subprocess
import platform
import datetime

if os.name == 'nt':
    from libs.multi.nt import create_terminal
elif platform.system() == 'Darwin':
    from libs.multi.osx import create_terminal
elif platform.system() == 'Linux':
    from libs.multi.linux import create_terminal
else:
    print("[ERROR] Build Failed. Cause by unsupported platform. ")
    exit(1)

LAUNCH_CLIENT_VER = "0.0.1"

# Arguments
parser = argparse.ArgumentParser(description='LaunchClient')
parser.add_argument('-version', action='store_true', dest="version", help="Print LaunchClient version.")
parser.add_argument("-launch", action="store_true", dest="launch", help="Launch the game.")
parser.add_argument('-jvm_executable_path', dest="jvm_executable_path", type=str,
                    help="The Java Virtual Machine executable path.")
parser.add_argument('-jvm_args', dest="jvm_args", type=str, help="Game JVM arguments.")
parser.add_argument('-classpath', dest="classpath", type=str, help="Games that require library paths.")
parser.add_argument('-mainClass', dest="mainClass", type=str, help="Main class.")
parser.add_argument('-game_args', dest="game_args", type=str, help="Game arguments.")
parser.add_argument("-custom_launch_command", dest="custom_command", type=str,
                    help="Custom command to launch the game.")
parser.add_argument("-hidden_token", dest="hidden_token", type=str, )
parser.add_argument("-workDir", dest="work_dir", type=str, help="Set working directory.")
args = parser.parse_args()


def main():
    print("[LaunchClient]")
    print("VERSION: {}".format(LAUNCH_CLIENT_VER))
    print("PLATFORM: {}".format(platform.system()))
    print("Arguments detected: {}".format(args))
    print("Datetime: {}".format(datetime.datetime.now()))
    print("\n")
    print("[Status]: Preparing command...")

    if args.custom_command:
        print("[Status]: Custom command detected: {}".format(args.custom_command))
        execute_command = args.custom_command
    else:
        if args.jvm_executable_path:
            print("[INFO]: JVM executable path detected: {}".format(args.jvm_executable_path))
        else:
            raise Exception("[ERROR]: JVM executable path not detected")

        if args.jvm_args:
            print("[INFO]: JVM arguments detected: {}".format(args.jvm_args))
        else:
            raise Exception("[ERROR]: JVM arguments not detected")

        if args.classpath:
            print("[INFO]: Classpath detected: {}".format(args.jvm_args))
        else:
            raise Exception("[ERROR]: Class path not detected")

        if args.mainClass:
            print("[INFO]: Main class detected: {}".format(args.mainClass))
        else:
            raise Exception("[ERROR]: Main class not found")

        if args.game_args:
            print("[INFO]: Game arguments detected: {}".format(args.game_args))
        else:
            raise Exception("[ERROR]: Game arguments not detected")

        execute_command = (f"{args.jvm_executable_path} {args.jvm_args} -cp {args.classpath} {args.mainClass}"
                           f" {args.game_args} && sleep 3")
    print("")
    print("[Status]: Launching game...")
    create_terminal(execute_command, args.work_dir)


if __name__ == "__main__":
    if args.work_dir:
        os.chdir(args.work_dir)

    if args.version:
        print(LAUNCH_CLIENT_VER)

    if args.launch:
        main()
else:
    def launch_client_2(full_launch_command, workDir):
        print("[LaunchClient]===>Import Mode")
        print("VERSION: {}".format(LAUNCH_CLIENT_VER))
        print("PLATFORM: {}".format(platform.system()))
        print("Datetime: {}".format(datetime.datetime.now()))
        print("Launch command detected: {}".format(full_launch_command))
        print("")

        print("[Status]: Launching game...")
        create_terminal(full_launch_command, args.work_dir)
