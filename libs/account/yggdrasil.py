"""
The Yggdrasil system has been replaced by msa. If you want to get valid accessToken, please check function msa to get
more information.
"""
import json
import requests

yggdrasil_auth_url = "https://authserver.mojang.com/authenticate"


def get_access_token_yggdrasil(username, password, **kwargs):
    """
    Auth process of the yggdrasil system
    :param username: Minecraft username (maybe email?)
    :param password: Account password

    # Other custom parameters
    :param custom_client_id: Custom client id
    :param custom_auth_server: Replace original server url to custom url
    :param no_ssl_verifying: Disable ssl certificate check when requests data (with custom_auth_server require this)
    :return: Status, uuid
    """
    # parameter stuff
    client_id = kwargs.get("custom_client_id", "00000000402B5328")
    auth_url = kwargs.get("custom_auth_server", yggdrasil_auth_url)

    # For custom auth server
    ssl_verifying = kwargs.get("no_ssl_verifying", True)

    headers = {
        'Content-Type': 'application/json',
    }

    payload = {
        "agent": {
            "name": "Minecraft",
            "version": 1
        },
        "username": username,
        "password": password,
        "clientToken": client_id  # This might be a unique token for your client
    }

    try:
        response = requests.post(auth_url, data=json.dumps(payload), headers=headers, verify=ssl_verifying)

        response_data = response.json()
    except Exception as e:
        return False, None, e

    access_token = response_data.get("accessToken", None)

    if access_token is None:
        return False, None, "AccessTokenNotValid"

    return True, access_token, None
