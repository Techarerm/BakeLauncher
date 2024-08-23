import os
import json
import path_tool
from path_tool import path_client


def get_lwjgl_version(minecraft_version):
    """
    Determine the LWJGL version based on the Minecraft version.
    """
    version_tuple = tuple(map(int, minecraft_version.split(".")))

    if version_tuple < (1, 7, 3):
        return "LWJGL 2.6.x"
    elif (1, 7, 3) <= version_tuple <= (1, 8, 9):
        return "LWJGL 2.8.x"
    elif (1, 9) <= version_tuple <= (1, 12, 2):  # Include 1.12.2
        return "LWJGL 2.9.4"
    elif version_tuple == (1, 13):
        return "LWJGL 3.1.6"
    elif (1, 14) <= version_tuple <= (1, 18):
        return "LWJGL 3.2.2"
    elif version_tuple >= (1, 19):
        return "LWJGL 3.3.3"
    else:
        raise ValueError("Unsupported Minecraft version")



def java_version_check(version):
    print("Trying to check this version of Minecraft requirement Java version....")
    version_tuple = tuple(map(int, version.split(".")))

    with open("Java_HOME.json", "r") as file:
        data = json.load(file)

    if version_tuple > (1, 16):
        print("Up to Java-17")
        if version_tuple >= (1, 21):
            Java_path = data.get("Java_21")
        else:
            Java_path = data.get("Java_17")
    else:
        Java_path = data.get("Java_8")

    return Java_path


def launch():
    local = os.getcwd()
    Version_list = os.listdir('versions')
    print(Version_list)
    print("Which one is you wanna launch version ? :)")
    version_id = input(":")
    try:
        lwjgl_version = get_lwjgl_version(version_id)
        print(f"Using {lwjgl_version} for Minecraft version {version_id}.")
    except ValueError as e:
        print(e)
        return  # Exit if the version is unsupported

    # Determine natives_library based on LWJGL version
    if lwjgl_version == "LWJGL 2.6.x":
        natives_library = local + "\\LWJGL\\2.6.x\\1.0(6d0e9e5bfb61b441b31cff10aeb801ab64345a7d)"
    elif lwjgl_version == "LWJGL 2.8.x":
        natives_library = local + "\\LWJGL\\2.8.x\\1.8.9(455edb6b1454a7f3243f37b5f240f69e1b0ce4fa)"
    elif lwjgl_version == "LWJGL 2.9.4":
        natives_library = local + "\\LWJGL\\2.9.4\\1.12(91d80911a67c3f95b232483aa2646ad7663a2976)"
    elif lwjgl_version == "LWJGL 3.1.6":
        natives_library = local + "\\LWJGL\\3.1.6\\362f886f0e087997ece5e8b064ff34886b378668"
    elif lwjgl_version == "LWJGL 3.2.2":
        natives_library = local + "\\LWJGL\\3.2.2\\1.14(476a2617ce0938d8559f61d5a7505fad49424892)"
    elif lwjgl_version == "LWJGL 3.3.3":
        natives_library = local + "\\LWJGL\\3.3.3\\44685878b69bb36a6fb05390c06c8b0243d34f57"
    else:
        print("Error: LWJGL version not recognized.")
        return  # Exit if the LWJGL version is not recognized

    path_client(version_id)
    print("Launching...")
    print("Getting JVM path...")

    assertdir = None  # Initialize assertdir
    assetIndex = "Legacy"  # Default value for assetIndex

    if os.path.isfile('Java_HOME.json'):
        Java_path = java_version_check(version_id)
        Java_path = f'"{Java_path + "\\java.exe"}"'
        os.chdir(r'versions/' + version_id)
        minecraft_path = f".minecraft"
        jvm_args1 = r"-XX:HeapDumpPath=MojangTricksIntelDriversForPerformance_javaw.exe_minecraft.exe.heapdump "
        jvm_argsRAM = r" -Xms512m -Xmx4096m"
        jvm_args2 = "-Djava.library.path={}".format(natives_library)

        with open('libraries_path.cfg', 'r', encoding='utf-8') as file:
            libraries = file.read()

        # Check if the version is higher than 1.5.2 to determine RunClass
        version_tuple = tuple(map(int, version_id.split(".")))
        if version_tuple > (1, 5, 2):
            RunClass = " -cp {} net.minecraft.client.main.Main ".format(libraries)
        else:
            RunClass = " -cp {} net.minecraft.launchwrapper.Launch ".format(libraries)

        # Determine assertdir and assetIndex based on version
        assets_dir = os.path.join(local, ".minecraft", "assets")
        if version_tuple <= (1, 6, 1):
            assertdir = ".minecraft/assets"
            assetIndex = "Legacy"
        else:
            if os.path.exists(".minecraft/assets/indexes/" + version_id +".json"):
                assertdir = ".minecraft/assets"
                assetIndex = version_id
            else:
                assertdir = ".minecraft/assets"
                assetIndex = "17"
        print("Reading account data....")
        os.chdir(local)
        with open('data\\AccountData.json', 'r') as file:
            data = json.load(file)
        username = data['AccountName']
        uuid = data['UUID']
        access_token = data['Token']
        os.chdir(r'versions/' + version_id)

        minecraft_args = "--username {} --version {} --gameDir {} --assetsDir {} --assetIndex {} --uuid {} --accessToken {}".format(
            username, version_id, minecraft_path, assertdir, assetIndex, uuid, access_token)

        RunCommand = Java_path + " " + jvm_args1 + jvm_argsRAM + " " + jvm_args2 + RunClass + minecraft_args
        print(RunCommand)
        print("Baking Minecraft! :)")
        os.system(RunCommand)
        os.chdir(local)
    else:
        print("You didn't configure your Java path!")
        print("Please go back to the main menu and select 5: Config Java!")
