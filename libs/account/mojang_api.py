import base64
import json

import requests


def get_account_uuid(username):
    """
    Get minecraft account uuid using username (without using accessToken)
    :param username: Minecraft username
    :return: Status, uuid

    PLEASE READ THIS MESSAGE IF YOU WANT TO USE THIS METHOD TO GET UUID
    This endpoint is currently very unreliable as of January 15, 2025 (frequent, random 403 errors) due to a
    misconfiguration by Mojang. (From minecraft wiki)
    https://bugs.mojang.com/browse/WEB-7591?focusedId=1375404&page=com.atlassian.jira.plugin.system.issuetabpanels%3Acomment-tabpanel#comment-1375404
    """

    url = f"https://api.mojang.com/users/profiles/minecraft/{username}"

    try:
        response = requests.get(url)
        data = response.json()

        uuid = data.get("id", None)
    except Exception as e:
        return False, None

    if uuid is None:
        return False, None

    return True, uuid


def get_account_ign_using_uuid(uuid):
    """
    Get Minecraft account "in game name"
    :param uuid: Minecraft account uuid
    :return: Status, username
    """

    url = f"https://api.minecraftservices.com/minecraft/profile/lookup/{uuid}"

    try:
        response = requests.get(url)
        data = response.json()
    except Exception as e:
        return False, None

    username = data.get("name", None)

    if username is None:
        return False, None

    return True, username


def check_account_uuid_are_valid(uuid):
    """
    Check Minecraft account uuid status (if not found return False)
    :param uuid: Minecraft account uuid
    :return: Status
    """

    url = f"https://api.minecraftservices.com/minecraft/profile/lookup/{uuid}"

    try:
        response = requests.get(url)
        data = response.json()
    except Exception as e:
        return False

    username = data.get("errorMessage", None)

    if username is None:
        return True

    return False


def get_account_textures_data(uuid):
    """
    Get Minecraft account texture data (properties>value) (json data)
    :param uuid: Minecraft account uuid
    :return: Status, textures_data
    """
    global account_textures_json
    url = f"https://sessionserver.mojang.com/session/minecraft/profile/{uuid}"

    try:
        response = requests.get(url)
        data = response.json()
    except Exception as e:
        return False, None

    # Base64 data
    account_texture_info = data.get("properties", {}).get("value", None)

    if account_texture_info is None:
        return False, None

    try:
        account_texture_decode = base64.b64decode(data)
        final_data = account_texture_decode.decode('utf-8')

        account_textures_json = json.loads(final_data)
    except Exception as e:
        return False, None

    if len(account_textures_json) == 0:
        return False, None

    return True, account_textures_json


def get_account_skin_url(uuid):
    """
    Get Minecraft account skin url
    :param uuid: Minecraft account uuid
    :return: Status, skin_url
    """

    Status, account_textures_json = get_account_textures_data(uuid)

    if not Status:
        return False, None

    skin_url = account_textures_json.get("textures", {}).get('SKIN', {}).get("url", None)

    if skin_url is None:
        return False, None

    return True, skin_url


def get_account_cape_url(uuid):
    """
    Get Minecraft account cape url
    :param uuid: Minecraft account uuid
    :return: Status, cape_url
    """

    Status, account_textures_json = get_account_textures_data(uuid)

    if not Status:
        return False, None

    cape_url = account_textures_json.get("textures", {}).get('CAPE', {}).get("url", None)

    if cape_url is None:
        return False, None

    return True, cape_url


def get_account_username_and_uuid(accessToken):
    """
    Get Minecraft account data
    :param uuid: Minecraft account uuid
    :return: Status, username, uuid, ErrorMessage
    """
    try:
        # Minecraft username and UUID
        r = requests.get("https://api.minecraftservices.com/minecraft/profile", headers={
            "Authorization": f"Bearer {accessToken}"
        })
        r.raise_for_status()
        username = r.json()["name"]
        uuid = r.json()["id"]
        return True, username, uuid, None
    except Exception as e:
        return False, None, None, e


def change_account_skin(accessToken, type, url):
    """
    Change Minecraft account skin using exists skin url (get from upload_account_skin)
    Get Minecraft account data
    :param accessToken: Minecraft accessToken
    :param type: Skin type (classic or slim)
    :param url: Skin texture url (using upload_account_skin to get it)
    :return: Status, ErrorMessage
    """
    try:
        payload = {
            "variant": type,
            "url": url
        }

        # Minecraft username and UUID
        r = requests.post("https://api.minecraftservices.com/minecraft/profile/skins", headers={
            "Authorization": f"Bearer {accessToken}"}, json=payload)

        if r.ok:
            return True, None

        return False, r.json().get("errorMessage", "UnknownErr")
    except Exception as e:
        return False, e


def upload_account_skin(accessToken, type, file_path):
    """
    Upload minecraft skin to mojang server
    :param accessToken: Minecraft accessToken
    :param type: Skin type (classic or slim)
    :param file_path: Skin file path
    :return: Status, skin_url, ErrorMessage
    """
    try:
        url = 'https://api.minecraftservices.com/minecraft/profile/skins'

        headers = {
            'Authorization': f'Bearer {accessToken}'
        }

        files = {
            'file': open(file_path, 'rb'),
            'variant': (None, type)
        }
        print(files)

        response = requests.post(url, headers=headers, files=files)
        data = response.json()
        skin_url = data.get('skins')[0].get("url")

        if skin_url is None:
            return False, None, "GetURLFailed"

        return True, skin_url, None

    except Exception as e:
        return False, None, e


