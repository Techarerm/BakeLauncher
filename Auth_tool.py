"""
Authentication Tool
Original:https://gist.github.com/dewycube/223d4e9b3cddde932fbbb7cfcfb96759
This is how you get a minecraft token using a microsoft account (like the launcher does).
The minecraft token is used to join servers, change username, skin, cape, ...
License: do whatever you want.
"""
import webbrowser
import requests
import json

def login():
    global logged
    global username
    global access_token
    print("You must manually use a web browser to login your account!!!")
    print("[Authentication tool]")
    print("Rememver to paste url after you login :)")
    print("Press enter to jump into login...")
    webbrowser.open(
        "https://login.live.com/oauth20_authorize.srf?client_id=00000000402B5328&redirect_uri=https://login.live.com/oauth20_desktop.srf&response_type=code&scope=service::user.auth.xboxlive.com::MBI_SSL")
    blank_page_url = input("URL:")
    code = blank_page_url.split("code=")[1].split("&")[0]

    # microsoft token + microsoft refresh token
    r = requests.post("https://login.live.com/oauth20_token.srf", data={
        "client_id": "00000000402B5328",  # minecraft launcher
        "scope": "service::user.auth.xboxlive.com::MBI_SSL",
        "code": code,
        "redirect_uri": "https://login.live.com/oauth20_desktop.srf",
        "grant_type": "authorization_code"
    })
    microsoft_token = r.json()["access_token"]
    microsoft_refresh_token = r.json()["refresh_token"]
    print("\nMicrosoft Refresh Token:", microsoft_refresh_token)

    # xbl token
    r = requests.post("https://user.auth.xboxlive.com/user/authenticate", json={
        "Properties": {
            "AuthMethod": "RPS",
            "SiteName": "user.auth.xboxlive.com",
            "RpsTicket": microsoft_token
        },
        "RelyingParty": "http://auth.xboxlive.com",
        "TokenType": "JWT"
    })
    xbl_token = r.json()["Token"]

    # xsts token
    r = requests.post("https://xsts.auth.xboxlive.com/xsts/authorize", json={
        "Properties": {
            "SandboxId": "RETAIL",
            "UserTokens": [xbl_token]
        },
        "RelyingParty": "rp://api.minecraftservices.com/",
        "TokenType": "JWT"
    })
    xsts_userhash = r.json()["DisplayClaims"]["xui"][0]["uhs"]
    xsts_token = r.json()["Token"]

    # minecraft token
    r = requests.post("https://api.minecraftservices.com/authentication/login_with_xbox", json={
        "identityToken": f"XBL3.0 x={xsts_userhash};{xsts_token}"
    })
    minecraft_token = r.json()["access_token"]
    print("\nMinecraft Token:", minecraft_token)

    # minecraft username and uuid
    r = requests.get("https://api.minecraftservices.com/minecraft/profile", headers={
        "Authorization": f"Bearer {minecraft_token}"
    })
    username = r.json()["name"]
    uuid = r.json()["id"]
    print("\nMinecraft Username:", username)
    print("\nMinecraft UUID:", uuid)

    # The minecraft token expires after 24 hours, so you need to use the microsoft refresh token to
    # generate a new microsoft token and use it in the requests above to get a new minecraft token.
    # The microsoft token also expires after 24 hours, so there is no point in storing it. The only
    # tokens worthy of being stored are: minecraft token (expires after 24 hours) and microsoft refresh
    # token (expires after 90 days if unused or at any time if revoked).

    # Do this when the minecraft token expires:
    # Generate a new microsoft token using the microsoft refresh token
    r = requests.post("https://login.live.com/oauth20_token.srf", data={
        "scope": "service::user.auth.xboxlive.com::MBI_SSL",
        "client_id": "00000000402B5328",
        "grant_type": "refresh_token",
        "refresh_token": microsoft_refresh_token
    })
    microsoft_token = r.json()["access_token"]
    print("Login process finish :)")
    print("Saving...")
    jsonFile = open("data\\AccountData.json" , "w")
    data = {}
    data["AccountName"] = username
    data["UUID"] = uuid
    data["Token"] = minecraft_token
    json.dump(data, jsonFile)