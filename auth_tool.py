import webbrowser
import requests
import json
import print_color
from print_color import print

def login():
    global logged
    global username
    global access_token
    
    print("[AutoTool]", color='cyan')
    print("AuthTool: You must manually use a web browser to login to your account!!!", color='red')
    print("AuthTool: Remember to paste the URL after you login :)", color='green')
    print("AuthTool: Press enter to jump into login...", color='purple')
    print("Or you can type 'Exit' to go back to the main menu :)", color='cyan')
    
    webbrowser.open(
        "https://login.live.com/oauth20_authorize.srf?client_id=00000000402B5328&redirect_uri=https://login.live.com/oauth20_desktop.srf&response_type=code&scope=service::user.auth.xboxlive.com::MBI_SSL"
    )
    
    blank_page_url = input("URL:")
    if blank_page_url.lower() == "exit":
        print("Back to main menu...")
        return
    
    try:
        code = blank_page_url.split("code=")[1].split("&")[0]
    except IndexError:
        print("AuthTool: Invalid URL. Please try again.", color='red')
        return

    try:
        # Microsoft token + Microsoft refresh token
        r = requests.post("https://login.live.com/oauth20_token.srf", data={
            "client_id": "00000000402B5328",
            "scope": "service::user.auth.xboxlive.com::MBI_SSL",
            "code": code,
            "redirect_uri": "https://login.live.com/oauth20_desktop.srf",
            "grant_type": "authorization_code"
        })
        r.raise_for_status()
        microsoft_token = r.json()["access_token"]
        microsoft_refresh_token = r.json()["refresh_token"]
        print("AuthTool: Microsoft Refresh Token:", microsoft_refresh_token, color='blue')
    except requests.RequestException:
        print("AuthTool: Failed to get Microsoft token :(", color='red')
        print("AuthTool: Maybe this url are expired. Try to relogin again!", color='red')
        print("AuthTool: If stil can't login please clean your browser token and try again.", color='red')
        print("AuthTool: If still can't login....report this issue to GitHUb!.", color='red')
        return

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
    except requests.RequestException:
        print("AuthTool: Failed to get XBL token.", color='red')
        print("AuthTool: ", color='red')
        return

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
    except requests.RequestException:
        print("AuthTool: Failed to get XSTS token.", color='red')
        print("AuthTool: Maybe this url are expired. Try to relogin again!", color='red')
        print("AuthTool: If stil can't login please clean your browser token and try again.", color='red')
        print("AuthTool: If still can't login....report this issue to GitHUb!.", color='red')
        return

    try:
        # Minecraft token
        r = requests.post("https://api.minecraftservices.com/authentication/login_with_xbox", json={
            "identityToken": f"XBL3.0 x={xsts_userhash};{xsts_token}"
        })
        r.raise_for_status()
        minecraft_token = r.json()["access_token"]
        print("AuthTool: Minecraft Token:", minecraft_token, color='blue')
    except requests.RequestException:
        print("AuthTool: Failed to get Minecraft token.", color='red')
        print("AuthTool: Maybe this url are expired. Try to relogin again!", color='red')
        print("AuthTool: If stil can't login please clean your browser token and try again.", color='red')
        print("AuthTool: If still can't login....report this issue to GitHUb!.", color='red')
        return


    try:
        # Minecraft username and UUID
        r = requests.get("https://api.minecraftservices.com/minecraft/profile", headers={
            "Authorization": f"Bearer {minecraft_token}"
        })
        r.raise_for_status()
        username = r.json()["name"]
        uuid = r.json()["id"]
        print("AuthTool: Minecraft Username:", username, color='blue')
        print("AuthTool: Minecraft UUID:", uuid, color='blue')
    except requests.RequestException:
        print("AuthTool: Failed to get Minecraft profile information.", color='red')
        print("AuthTool: Maybe this url are expired. Try to relogin again!", color='red')
        print("AuthTool: If stil can't login please clean your browser token and try again.", color='red')
        print("AuthTool: If still can't login....report this issue to GitHUb!.", color='red')
        return


    try:
        # Save the token to AccountData.json
        print("AuthTool: Saving AccountData...", color='green')
        data = {
            "AccountName": username,
            "UUID": uuid,
            "Token": minecraft_token
        }
        with open("data\\AccountData.json", "w") as jsonFile:
            json.dump(data, jsonFile)
        print("AuthTool: AccountData saved successfully!", color='green')
    except Exception as e:
        print(f"AuthTool: Failed to save account data. Error: {e}", color='red')
        print("AuthTool: Trying delete file name AccountData.json(Is in the data folder)!", color='yellow')
    print("Login process finished :)", color='blue')
