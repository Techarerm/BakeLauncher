import platform

INSTANCE_GAME_FOLDER_NAME = ".minecraft" if not platform.platform() == "Darwin" else "minecraft"
