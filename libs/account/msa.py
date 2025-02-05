import requests

def get_microsoft_account_token(code, mode):
    """
    Code example M.C559_SN1.2.U.09fd18c9-f260-0000-test-221f3eb387b4
    """
    global request_data
    oauth20_token = "https://login.live.com/oauth20_token.srf"
    try:
        if mode == "AuthToken":
            # Microsoft token + Microsoft refresh token
            request_data = requests.post(oauth20_token, data={
                "client_id": "00000000402B5328",
                "scope": "service::user.auth.xboxlive.com::MBI_SSL",
                "code": code,
                "redirect_uri": "https://login.live.com/oauth20_desktop.srf",
                "grant_type": "authorization_code"
            })
        elif mode == "RefreshToken":
            request_data = requests.post("https://login.live.com/oauth20_token.srf", data={
                "client_id": "00000000402B5328",
                "scope": "service::user.auth.xboxlive.com::MBI_SSL",
                "refresh_token": code,
                "redirect_uri": "https://login.live.com/oauth20_desktop.srf",
                "grant_type": "refresh_token"
            })
        request_data.raise_for_status()
        microsoft_token = request_data.json()["access_token"]
        microsoft_refresh_token = request_data.json()["refresh_token"]
        return True, microsoft_token, microsoft_refresh_token
    except Exception as e:
        return False, e, None


def get_xbl_token(microsoft_token):
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
        return True, xbl_token
    except Exception as e:
        return False, e


def get_xsts_token(xbl_token):
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
        return True, xsts_userhash, xsts_token
    except Exception as e:
        return False, e, None


def get_access_token(xsts_userhash, xsts_token):
    try:
        # Minecraft token
        r = requests.post("https://api.minecraftservices.com/authentication/login_with_xbox", json={
            "identityToken": f"XBL3.0 x={xsts_userhash};{xsts_token}"
        })
        r.raise_for_status()
        access_token = r.json()["access_token"]
        return True, access_token
    except Exception as e:
        return False, e