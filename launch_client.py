import os
import sys
import subprocess
import Auth_tool
from Auth_tool import login
import json
"""
from JVM_path import get_java_home
from JVM_path import find_jvm_paths
from JVM_path import get_jvm_version
from JVM_path import main
"""


def launch():
    """
    Warring:If your systemd default Java version are not 21,you may got crash when Minecraft launch....
    """
    print("Launching...")
    print("Getting JVM path...")
    minecraft_path = r"data\.minecraft"
    normal_library = r"data\.minecraft\bin\44685878b69bb36a6fb05390c06c8b0243d34f57"
    assertdir = r"data\.minecraft\assets"
    jvm_args1 = r"-XX:HeapDumpPath=MojangTricksIntelDriversForPerformance_javaw.exe_minecraft.exe.heapdump "
    jvm_argsRAM = r" -Xms512m -Xmx4096m"
    jvm_args2 = "-Djava.library.path={}".format(normal_library)
    '''
    Huh:)...Yep...Is hardcoded path....
    IS JUST FOR TEST I WILL DELETE IT IN FUTURE
    '''
    libraries = (r"data\.minecraft\libraries\net\sf\jopt-simple\jopt-simple\5.0.4\jopt-simple-5.0.4.jar;data\.minecraft\libraries\com\mojang\logging\1.2.7\logging-1.2.7.jar;data\.minecraft\libraries\com\google\guava\guava\32.1.2-jre\guava-32.1.2-jre.jar"
                 r";data\.minecraft\libraries\com\mojang\brigadier\1.2.9\brigadier-1.2.9.jar;data\.minecraft\libraries\com\mojang\brigadier\1.2.9\brigadier-1.2.9.jar"
                 r";data\.minecraft\libraries\io\netty\netty-buffer\4.1.97.Final\netty-buffer-4.1.97.Final.jar;data\.minecraft\libraries\io\netty\netty-codec\4.1.97.Final\netty-codec-4.1.97.Final.jar"
                 r";data\.minecraft\libraries\io\netty\netty-common\4.1.97.Final\netty-common-4.1.97.Final.jar;data\.minecraft\libraries\io\netty\netty-resolver\4.1.97.Final\netty-resolver-4.1.97.Final.jar"
                 r";data\.minecraft\libraries\io\netty\netty-transport\4.1.97.Final\netty-transport-4.1.97.Final.jar;data\.minecraft\libraries\io\netty\netty-handler\4.1.97.Final\netty-handler-4.1.97.Final.jar"
                 r";data\.minecraft\libraries\io\netty\netty-transport-classes-epoll\4.1.97.Final\netty-transport-classes-epoll-4.1.97.Final.jar;data\.minecraft\libraries\io\netty\netty-transport-native-unix-common\4.1.97.Final\netty-transport-native-unix-common-4.1.97.Final.jar"
                 r";data\.minecraft\libraries\com\mojang\datafixerupper\8.0.16\datafixerupper-8.0.16.jar;data\.minecraft\libraries\com\google\code\gson\gson\2.10.1\gson-2.10.1.jar;data\.minecraft\libraries\org\apache\commons\commons-lang3\3.14.0\commons-lang3-3.14.0.jar"
                 r";data\.minecraft\libraries\it\unimi\dsi\fastutil\8.5.12\fastutil-8.5.12.jar;data\.minecraft\libraries\org\apache\commons\commons-lang3\3.14.0\commons-lang3-3.14.0.jar;data\.minecraft\libraries\net\java\dev\jna\jna-platform\5.14.0\jna-platform-5.14.0.jar"
                 r";data\.minecraft\libraries\org\joml\joml\1.10.5\joml-1.10.5.jar;data\.minecraft\libraries\com\mojang\authlib\6.0.54\authlib-6.0.54.jar;data\.minecraft\libraries\net\java\dev\jna\jna\5.14.0\jna-5.14.0.jar;data\.minecraft\libraries\org\lwjgl\lwjgl\3.3.3\lwjgl-3.3.3.jar"
                 r";data\.minecraft\libraries\org\lwjgl\lwjgl-glfw\3.3.3\lwjgl-glfw-3.3.3.jar;data\.minecraft\libraries\org\apache\logging\log4j\log4j-core\2.22.1\log4j-core-2.22.1.jar;data\.minecraft\libraries\org\apache\commons\commons-compress\1.26.0\commons-compress-1.26.0.jar"
                 r";data\.minecraft\libraries\org\apache\commons\commons-lang3\3.14.0\commons-lang3-3.14.0.jar;data\.minecraft\libraries\commons-io\commons-io\2.15.1\commons-io-2.15.1.jar;data\.minecraft\libraries\com\google\guava\failureaccess\1.0.1\failureaccess-1.0.1.jar"
                 r";data\.minecraft\libraries\org\lwjgl\lwjgl-opengl\3.3.3\lwjgl-opengl-3.3.3.jar;data\.minecraft\libraries\org\lwjgl\lwjgl-openal\3.3.3\lwjgl-openal-3.3.3.jar;data\.minecraft\libraries\com\ibm\icu\icu4j\73.2\icu4j-73.2.jar"
                 r";data\.minecraft\libraries\org\apache\logging\log4j\log4j-api\2.22.1\log4j-api-2.22.1.jar;data\.minecraft\libraries\com\mojang\text2speech\1.17.9\text2speech-1.17.9.jar;data\.minecraft\libraries\org\lwjgl\lwjgl-stb\3.3.3\lwjgl-stb-3.3.3.jar"
                 r";data\.minecraft\libraries\org\lwjgl\lwjgl-tinyfd\3.3.3\lwjgl-tinyfd-3.3.3.jar;data\.minecraft\libraries\com\github\oshi\oshi-core\6.4.10\oshi-core-6.4.10.jar;data\.minecraft\libraries\org\apache\logging\log4j\log4j-slf4j2-impl\2.22.1\log4j-slf4j2-impl-2.22.1.jar"
                 r";data\.minecraft\libraries\org\apache\logging\log4j\log4j-slf4j2-impl\2.22.1\log4j-slf4j2-impl-2.22.1.jar;data\.minecraft\libraries\com\mojang\patchy\2.2.10\patchy-2.2.10.jar;data\.minecraft\libraries\com\mojang\javabridge\1.2.24\javabridge-1.2.24.jar;data\.minecraft\libraries\commons-codec\commons-codec\1.16.0\commons-codec-1.16.0.jar"
                 r";data\.minecraft\libraries\org\apache\logging\log4j\log4j-slf4j18-impl\2.17.0\log4j-slf4j18-impl-2.17.0.jar;data\.minecraft\libraries\commons-logging\commons-logging\1.2\commons-logging-1.2.jar"
                 r";data\.minecraft\libraries\it\unimi\dsi\fastutil\8.5.12\fastutil-8.5.12.jar;data\.minecraft\libraries\net\java\dev\jna\jna\5.14.0\jna-5.14.0.jar;data\.minecraft\libraries\org\apache\httpcomponents\httpcore\4.4.16\httpcore-4.4.16.jar"
                 r";data\.minecraft\libraries\org\apache\httpcomponents\httpclient\4.5.13\httpclient-4.5.13.jar;data\.minecraft\libraries\org\jcraft\jorbis\0.0.17\jorbis-0.0.17.jar;data\.minecraft\libraries\org\joml\joml\1.10.5\joml-1.10.5.jar"
                 r";data\.minecraft\libraries\org\lz4\lz4-java\1.8.0\lz4-java-1.8.0.jar;data\.minecraft\libraries\org\slf4j\slf4j-api\2.0.9\slf4j-api-2.0.9.jar;data\.minecraft\libraries\org\ow2\asm\asm\9.6\asm-9.6.jar"
                 r";data\.minecraft\libraries\org\ow2\asm\asm-analysis\9.6\asm-analysis-9.6.jar;data\.minecraft\libraries\org\ow2\asm\asm-commons\9.6\asm-commons-9.6.jar;data\.minecraft\libraries\org\ow2\asm\asm-tree\9.6\asm-tree-9.6.jar;.minecraft\libraries\org\ow2\asm\asm-util\9.6\asm-util-9.6.jar"
                 r";data\.minecraft\libraries\com\mojang\blocklist\1.0.10\blocklist-1.0.10.jar;data\client.jar")

    RunClass = " -cp {} net.minecraft.client.main.Main ".format(libraries)
    print("Reading account data....")
    with open('data\\AccountData.json', 'r') as file:
        data = json.load(file)
    username = data['AccountName']
    uuid = data['UUID']
    access_token = data['Token']
    minecraft_args = "--username {} --version 1.21 --gameDir {} --assetsDir {} --assetIndex 17 --uuid {} --accessToken {}".format(username, minecraft_path, assertdir, uuid, access_token)
    RunCommand = "java " + jvm_args1 + jvm_argsRAM + " " + jvm_args2 + RunClass + minecraft_args
    print("Baking Minecraft! :)")
    os.system(RunCommand)




