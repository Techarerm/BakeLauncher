import requests

minecraft_launcher_client_id = "00000000402B5328"


def get_microsoft_account_token(code, mode):
    """
    Get microsoft account token using oauth20_token (code)
    Code example M.C559_SN1.2.U.09fd18c9-f260-0000-test-221f3eb387b4
    :param code: oauth20_token code
    :param mode: oauth20_token code type (AuthToken or RefreshToken)
    :return: Status, microsoft_token, microsoft_refresh_token, ErrorMessage
    """
    request_data = {}
    oauth20_token = "https://login.live.com/oauth20_token.srf"
    try:
        if mode == "AuthToken":
            # Microsoft token + Microsoft refresh token
            request_data = requests.post(oauth20_token, data={
                "client_id": minecraft_launcher_client_id,
                "scope": "service::user.auth.xboxlive.com::MBI_SSL",
                "code": code,
                "redirect_uri": "https://login.live.com/oauth20_desktop.srf",
                "grant_type": "authorization_code"
            })
        elif mode == "RefreshToken":
            request_data = requests.post("https://login.live.com/oauth20_token.srf", data={
                "client_id": minecraft_launcher_client_id,
                "scope": "service::user.auth.xboxlive.com::MBI_SSL",
                "refresh_token": code,
                "redirect_uri": "https://login.live.com/oauth20_desktop.srf",
                "grant_type": "refresh_token"
            })
        else:
            return False, None, None, "TokenTypeUndefined"
        request_data.raise_for_status()
        microsoft_token = request_data.json()["access_token"]
        microsoft_refresh_token = request_data.json()["refresh_token"]
        return True, microsoft_token, microsoft_refresh_token, None
    except Exception as e:
        return False, None, None, e


def get_xbl_token(microsoft_token):
    """
    Get xbl token (Auth from Xbox live server)
    :param microsoft_token: A valid Microsoft access token
    :return: Status, xbl_token, ErrorMessage
    """
    try:
        # XBL token
        r = requests.post("https://user.auth.xboxlive.com/user/authenticate", json={
            "Properties": {
                "AuthMethod": "RPS",
                "SiteName": "user.auth.xboxlive.com",
                "RpsTicket": microsoft_token
            },
            "RelyingParty": "http://auth.xboxlive.com",
            "TokenType": "JWT"
        })
        r.raise_for_status()
        xbl_token = r.json()["Token"]
        return True, xbl_token, None
    except Exception as e:
        return False, None, e


def get_xsts_token(xbl_token):
    """
    Get xsts token
    :param xbl_token: A valid Xbox live token (Can get using function get_xbl_token)
    :return: Status, xsts_userhash, xsts_token, ErrorMessage
    """
    try:
        # XSTS token
        r = requests.post("https://xsts.auth.xboxlive.com/xsts/authorize", json={
            "Properties": {
                "SandboxId": "RETAIL",
                "UserTokens": [xbl_token]
            },
            "RelyingParty": "rp://api.minecraftservices.com/",
            "TokenType": "JWT"
        })
        r.raise_for_status()
        xsts_userhash = r.json()["DisplayClaims"]["xui"][0]["uhs"]
        xsts_token = r.json()["Token"]
        return True, xsts_userhash, xsts_token, None
    except Exception as e:
        return False, None, None, e


def get_access_token(xsts_userhash, xsts_token):
    """
    Get access token
    :param xsts_userhash: A valid xsts_userhash (Can get using function get_xsts_token)
    :param xsts_token: A valid xsts_token (Get function same as above param)
    :return: Status, access_token, ErrorMessage
    """
    try:
        # Minecraft token
        r = requests.post("https://api.minecraftservices.com/authentication/login_with_xbox", json={
            "identityToken": f"XBL3.0 x={xsts_userhash};{xsts_token}"
        })
        r.raise_for_status()
        access_token = r.json()["access_token"]
        return True, access_token, None
    except Exception as e:
        return False, None, e


