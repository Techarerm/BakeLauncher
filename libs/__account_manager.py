"""
AccountManager(Original Name: AuthTool)
This module was added in Pre-Beta 5(Or older version)
A tool can get Microsoft Refresh Token, Minecraft Account Data(username, uuid), and AccessToken
Some code(get token process) is from GitHub: https://gist.github.com/dewycube/223d4e9b3cddde932fbbb7cfcfb96759
Modify some functions for automatic refresh token and multiple accounts support...

When you log in your account, AccountMSC will save your token, account info to AccountData(Also create an account-id
when you want to select use account)


Format Version List:
v1: First Added Version>Beta 0.7.1
v2: Beta 0.8(Dev-JG061024)>Latest

Modern version code released since Beta 0.8(Dev-JG061024)
Commit 0cf3fcc

Credits:
dewycube: Created minecraft_token.py to get access token
Wiki.vg: Documents about auth process

Example In AccountData(v2 Format):
[
    {
        "id": 1,  # Select use account, refresh token, get single account data are all require this
        "Username": "Player",
        "UUID": "Unknown",
        "RefreshToken": "None",
        "AccessToken": "Unknown",
        "tag": "TempUser;DemoUser"
    },
    {
        "id": 2,  # Use get_account_id to get it
        "Username": "TedKai", # Your username
        "UUID": "576477ee9099488798f478d81e6f9fae", # Your Minecraft Account UUID
        "RefreshToken": "Example RefreshToken", # Your Microsoft Account Refresh Token(it use on refresh token)
        "AccessToken": "Example AccessToken" # Your Minecraft Account Token(Or session token. Seems like it will expire
        in one day.
    }
]

"""
import time
import webbrowser
from json import JSONDecodeError
import traceback
import requests
import json
import os
from LauncherBase import Base, ClearOutput, initialize_config, print_custom as print, internal_functions_error_log_dump
from libs.Utils.utils import write_global_config


class AuthManager:
    def __init__(self):
        self.RefreshTokenFlag = False
        self.grant_type = None
        self.request_data = None
        self.oauth20_token = "https://login.live.com/oauth20_token.srf"

    def get_microsoft_account_token(self, code, mode):
        """
        Code example M.C559_SN1.2.U.09fd18c9-f260-0000-test-221f3eb387b4
        """
        try:
            if mode == "AuthToken":
                # Microsoft token + Microsoft refresh token
                self.request_data = requests.post(self.oauth20_token, data={
                    "client_id": "00000000402B5328",
                    "scope": "service::user.auth.xboxlive.com::MBI_SSL",
                    "code": code,
                    "redirect_uri": "https://login.live.com/oauth20_desktop.srf",
                    "grant_type": "authorization_code"
                })
            elif mode == "RefreshToken":
                self.request_data = requests.post("https://login.live.com/oauth20_token.srf", data={
                    "client_id": "00000000402B5328",
                    "scope": "service::user.auth.xboxlive.com::MBI_SSL",
                    "refresh_token": code,
                    "redirect_uri": "https://login.live.com/oauth20_desktop.srf",
                    "grant_type": "refresh_token"
                })
            self.request_data.raise_for_status()
            microsoft_token = self.request_data.json()["access_token"]
            microsoft_refresh_token = self.request_data.json()["refresh_token"]
            return True, microsoft_token, microsoft_refresh_token
        except Exception as e:
            return False, e, None

    def get_xbl_token(self, microsoft_token):
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

    def get_xsts_token(self, xbl_token):
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

    def get_access_token(self, xsts_userhash, xsts_token):
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

    def get_account_data(self, minecraft_token):
        try:
            # Minecraft username and UUID
            r = requests.get("https://api.minecraftservices.com/minecraft/profile", headers={
                "Authorization": f"Bearer {minecraft_token}"
            })
            r.raise_for_status()
            username = r.json()["name"]
            uuid = r.json()["id"]
            return True, username, uuid
        except Exception as e:
            return False, e, None

    @staticmethod
    def get_account_id(data):
        """
        The ID(AccountID) is for BakeLauncher can simply to get account without required uuid or username
        "Data is from AccountData.json"
        """
        # Get all id inside the AccountData
        ids = [entry['id'] for entry in data]
        new_id = 1
        while new_id in ids:
            # If id 1 is in data, new_id + 1 until can't find same one.
            new_id += 1
        return new_id

    @staticmethod
    def get_account_data_use_account_id(target_id):
        if os.path.exists("data/AccountData.json"):
            with open("data/AccountData.json", 'r') as f:
                try:
                    json_data = json.load(f)
                    # Loop through the data and find the matching ID
                    for entry in json_data:
                        if entry['id'] == int(target_id):
                            # Return the matching entry
                            return True, entry
                    return False, f"NoAccountFoundWithID>{target_id}"
                except json.JSONDecodeError:
                    return False, "JSONDecodeError"
        else:
            return False, "AccountDataDoesNotExist"

    def update_account_data(self, account_id, access_token, username, refresh_token):
        # Fetch account data
        status, selected_account_data = self.get_account_data_use_account_id(account_id)
        if not status:
            return False, f"UpdateAccountData>GetAccountDataUseAccountID>{selected_account_data}"

        # Load JSON data
        try:
            with open("data/AccountData.json", 'r') as f:
                account_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            return False, f"LoadingAccountData>Error:{e}"

        # Update "select" account data
        account_found = False
        for account in account_data:
            if account['id'] == account_id:  # Fixed: Using account_id
                account['Username'] = username  # Update if username changed
                account["AccessToken"] = access_token
                account["RefreshToken"] = refresh_token
                account_found = True
                break

        # Write back to the AccountData if account was found and updated
        if account_found:
            try:
                with open("data/AccountData.json", "w") as jsonFile:
                    json.dump(account_data, jsonFile, indent=4)
                return True, None
            except IOError as e:
                return False, f"SavingAccountData>Error: {e}"

        return False, f"NoAccountFoundWithID{account_id}"

    @staticmethod
    def set_default_account_id(account_id):
        if not os.path.exists(Base.global_config_path):
            initialize_config()
        with open(Base.global_config_path, 'r') as file:
            lines = file.readlines()
            for i in range(len(lines)):
                if 'DefaultAccountID' in lines[i]:
                    # Use the new or existing account ID
                    lines[i] = f'DefaultAccountID = {account_id}\n'
                    found = True
        with open(Base.global_config_path, 'w') as file:
            file.writelines(lines)
        if found:
            return True
        else:
            return False

    @staticmethod
    def get_default_account_id():
        found = False
        if not os.path.exists(Base.global_config_path):
            initialize_config()
        with open(Base.global_config_path, 'r') as file:
            for line in file:
                if "DefaultAccountID" in line:
                    id = line.split('=')[1].strip().strip().strip('"').strip("'")
                    try:
                        id = int(id)
                        found = True
                    except ValueError:
                        print("Failed to get DefaultAccountID. Config file is invalid.", color='lightred')
                        found = False
                    break
        if found:
            return True, id
        else:
            print("Warning: DefaultAccountID are not in config!", color='lightyellow')
            return False, None

    def login_process(self):
        print("Please login your account in your web browser.", color='c')
        print("After logging in, please copy the URL and paste it into the launcher.", color='lightgreen')
        print("Or you can type 'Exit' to go back to the main menu.", color='cyan')

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
            print("Invalid URL. Please try again.", color='lightred')
            return "CheckURLValidFailed"

        # Start get token process...
        Status, microsoft_token, microsoft_refresh_token = self.get_microsoft_account_token(code, "AuthToken")
        if not Status:
            print(f"Failed to get microsoft account token :( Cause by error {microsoft_token}", color='red')
            time.sleep(3)
            return microsoft_token + microsoft_refresh_token

        Status, xbl_token = self.get_xbl_token(microsoft_token)
        if not Status:
            print(f"Failed to get XBL token :( Cause by error {xbl_token}", color='red')
            time.sleep(3)
            return xbl_token

        Status, xsts_userhash, xsts_token = self.get_xsts_token(xbl_token)
        if not Status:
            print(f"Failed to get XBL token :( Cause by error {xsts_userhash}", color='red')
            time.sleep(3)
            return xsts_userhash + xsts_token

        Status, access_token = self.get_access_token(xsts_userhash, xsts_token)
        if not Status:
            print(f"Failed to get access token :( Cause by error {access_token}", color='red')
            time.sleep(3)
            return access_token

        Status, username, uuid = self.get_account_data(access_token)
        if not Status:
            print(f"Failed to get Minecraft profile information. Cause by error {username}", color='red')
            time.sleep(3)
            return username
        else:
            print("Minecraft Username:", username, color='lightblue')
            print("Minecraft UUID:", uuid, color='lightblue')

        try:
            # Save the token to AccountData.json
            print("Saving AccountData...", color='lightgreen')

            json_data = []

            # Check if the file exists and load existing data
            if os.path.exists("data/AccountData.json"):
                with open("data/AccountData.json", 'r') as f:
                    try:
                        json_data = json.load(f)
                        # Ensure json_data is a list
                        if not isinstance(json_data, list):
                            print("JSON data is not valid! Go to Extra>2: Reset AccountData.json to reset "
                                  "AccountData.json!", color='lightyellow')
                            time.sleep(4)
                            json_data = []
                    except json.JSONDecodeError:
                        print("Failed to load existing JSON data, resetting to empty list.", color='red')
                        print("Go to Extra>2: Reset AccountData.json to reset "
                              "AccountData.json!", color='lightyellow')
                        json_data = []

            # Check if the UUID already exists in the AccountData
            existing_entry = next((entry for entry in json_data if entry["UUID"] == uuid), None)

            # Huh...maybe I don't need to modify and use update_account_data...?
            if existing_entry:
                # Update existing entry without changing ID
                existing_entry["RefreshToken"] = microsoft_refresh_token
                existing_entry["AccessToken"] = access_token
                existing_entry["Username"] = username
                print(f"Updated existing account data for UUID: {uuid}", color='lightyellow')
                new_id = existing_entry["id"]  # Use the existing ID
            else:
                # Get a new ID for new accounts
                new_id = self.get_account_id(json_data)
                data = {
                    "id": new_id,
                    "Username": username,
                    "UUID": uuid,
                    "RefreshToken": microsoft_refresh_token,
                    "AccessToken": access_token
                }

                # Append new data to old json data(or new?)
                json_data.append(data)
                print(f"Added new account data for UUID: {uuid}", color='lightgreen')

            # Write the updated or new data back to the AccountData
            with open("data/AccountData.json", "w") as jsonFile:
                json.dump(json_data, jsonFile, indent=4)

            print("AccountData saved successfully!", color='lightblue')
            print("Want to change launch using account? Y/N:", color='lightgreen')
            user_input = input(":")
            if user_input.upper() == "Y":
                print("Change using account...", color='lightgreen')
                Status = self.set_default_account_id(new_id)
                if not Status:
                    print("Failed to change DefaultAccountID. Is your config file corrupted?", color='red')
                    time.sleep(3)
                else:
                    Base.RefreshTokenFailedFlag = False

        except Exception as e:
            print(f"Failed to save account data. Error: {e}", color='lightred')
            print("Trying to delete file name AccountData.json (in the data folder)!", color='lightyellow')

        print("Login process finished :)", color='blue')

    def check_account_data_are_valid(self, id):
        try:
            id = int(id)  # Ensure ID is an integer
        except ValueError:
            return False, "ID must be an integer when getting select account data."
        Status, account_data = self.get_account_data_use_account_id(id)

        if not Status:
            # If it failed when getting account data(Status = False), return failed message
            return False, account_data
        try:
            accessToken = account_data["AccessToken"]
            RefreshToken = account_data.get("RefreshToken")
            if RefreshToken is None:
                print(f"Stopping refresh token! Cause by invalid token :(", color='lightred')
                return
        except KeyError:
            return False, "CheckMinecraftToken>GetAccountDataFailed", ""

        try:
            with open("data/AccountData.json", 'r') as f:
                json_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            return False, f"Error loading AccountData.json: {e}"

        try:
            # Check if the current Minecraft token is valid
            r = requests.get("https://api.minecraftservices.com/minecraft/profile", headers={
                "Authorization": f"Bearer {accessToken}"
            }, timeout=18)
            r.raise_for_status()
            username = r.json()["name"]
            uuid = r.json()["id"]
            return True, "AccountDataAreValid"

        except requests.RequestException:
            print("Your Minecraft token has expired. Refreshing...", color='lightyellow')

            # Refresh Microsoft token using the refresh token
            Status, new_microsoft_token, new_refresh_token = self.get_microsoft_account_token(RefreshToken,
                                                                                              "RefreshToken")
            if not Status:
                print(f"Failed to refresh Microsoft token. Cause by error {new_microsoft_token}", color='red')
                print("Maybe your refresh token are expired! please re-login your account.",
                      color='yellow')
                Base.RefreshTokenFailedFlag = True
                time.sleep(5)
                return False, "FailedToRefreshToken"

            # Get a new Minecraft token using the refreshed Microsoft token
            self.RefreshTokenFlag = True
            Status, xbl_token = self.get_xbl_token(new_microsoft_token)
            if not Status:
                print(f"Failed to get XBL token :( Cause by error {xbl_token}", color='red')
                time.sleep(3)
                return False, f"GettingXBLToken>{xbl_token}"

            Status, xsts_userhash, xsts_token = self.get_xsts_token(xbl_token)
            if not Status:
                print(f"Failed to get XBL token :( Cause by error {xsts_userhash}", color='red')
                time.sleep(3)
                return False, f"GettingXSTSToken>{xsts_userhash}"

            Status, access_token = self.get_access_token(xsts_userhash, xsts_token)
            if not Status:
                print(f"Failed to get Minecraft token :( Cause by error {access_token}", color='red')
                time.sleep(3)
                return False, f"GettingAccessToken>{access_token}"

            Status, username, uuid = self.get_account_data(access_token)
            if not Status:
                print(f"Failed to get Minecraft profile information :( Cause by error {username}", color='red')
                time.sleep(3)
                return False, f"GettingAccountData>{username}"

            # Update the account data with the new "select" account data
            Status, message = self.update_account_data(id, access_token, username, new_refresh_token)
            if not Status:
                print(f"Failed to update new ac account data :( Cause by error {message}", color='red')
                time.sleep(3)
                return False, f"UpdateAccountData>{message}"

            # Set flag after refresh token finished
            Base.MainMenuResetFlag = True
            self.RefreshTokenFlag = False
            print("Refresh token process finished!", color='lightblue')
            return True, "AccountDataRefreshSuccessfully"

    def login_status(self):
        """
        Check login status.
        """
        global id, account_data, message

        # Get DefaultAccountID From account data
        Status, account_id = self.get_default_account_id()
        if not Status:
            # Overwrite broken config file if DefaultAccountID not found
            print("DefaultAccountID are not found. Is your config corrupted?", color='lightyellow')
            print("Using exist launcher account...", tag='INFO')
            write_global_config("DefaultAccountID", "1")
            time.sleep(2)
            Base.MainMenuResetFlag = True
            account_id = 1

        if os.path.exists('data/AccountData.json'):
            try:
                Status, account_data = self.get_account_data_use_account_id(account_id)
            except Exception as e:
                print(f"Failed to get selected account data. Cause by error {e}", color='red')
                print("Are you update launcher version from old version(old<0.8)?", color='yellow')
                print("In Beta 0.9, you can convert your AccountData to the new format :)", color='lightblue')
                print("Convert to new format? Y/N")
                user_input = str(input(":"))
                if user_input.upper() == "Y":
                    Status, e = self.convert_legacy_account_data()
                    if not Status:
                        print(f"Failed to convert legacy account data to new format :( Cause by error {e}", color='red')
                else:
                    Status = False

                if not Status:
                    # If user don't want to convert account data to new format, reset account data and reload main menu
                    self.initialize_account_data()
                    Status = self.set_default_account_id(1)
                    if not Status:
                        print("Failed to change DefaultAccountID. Is your config file corrupted?", color='red')
                        time.sleep(3)

                # Reset Main Menu
                Base.MainMenuResetFlag = True
                return
            if account_data is None:
                print(
                    f"Can't find id '{account_id}' in the account data ! Change to use local "
                    "account...",
                    color='yellow')
                account_id = 1
                Status, account_data = self.get_account_data_use_account_id(account_id)
            username = account_data['Username']  # Set username here
            if account_data['Username'] == "None":
                print("Login Status: Not logged in :(", color='lightred')
                print("Please log in to your account first!", color='lightred')
            elif account_data['Username'] == "BakeLauncherLocalPlayer" or account_data['Username'] == "Player":
                print("Warning: You are currently using a local account!", color='lightred')
                # print("Please log in to your account or switch to a different account.", color='lightred')
                print("Login Status: Not logged in :(", color='lightred')
            else:
                # Bypass check
                if not Base.BypassLoginStatusCheck:
                    if not Base.RefreshTokenFailedFlag:
                        if Base.InternetConnected:
                            Status, message = self.check_account_data_are_valid(account_id)
                        else:
                            Status = False
                        if Base.RefreshTokenFailedFlag:
                            Base.MainnResetFlag = True
                            return
                        else:
                            Base.RefreshTokenFailedFlag = False
                    else:
                        Status = False
                else:
                    Status = True
                # When MainMenuResetFlag = True(After refreshing the token it will be set to True) stop print login
                # message(until main_menu set MainMenuResetFlag = False)
                if Base.MainMenuResetFlag:
                    return

                if Status:
                    print("Login Status: Already logged in :)", color='lightgreen')
                    print("Hi,", username, color="lightblue")  # Now this should work correctly
                else:
                    if not Base.InternetConnected:
                        print("Login Status: Unknown", color='yellow')
                        print("Hi,", username, color="lightblue")
                    else:
                        # Base.ErrorMessageList.append(message)
                        print("Login Status: Expired session :0", color='lightred')
                        print("Please login your account again!", color='lightred')
                        print("Hi,", username, color="lightblue")  # Now this should work correctly
            if "tag" in account_data:
                print(f"Account Tag: {account_data['tag']}", color='lightgreen')
        else:
            self.initialize_account_data()
            print("Login Status: Not logged in :(", color='lightred')
            print("Please log in to your account first!", color='lightred')
            print("Hi, Baker", color='yellow')

    def SelectDefaultAccount(self):
        print("AccountList:")
        with open("data/AccountData.json", "r") as file:
            data = json.load(file)

        # Display available accounts
        for item in data:
            print(f'{item["id"]}: {item["Username"]}')

        # Get user input
        print("Please enter the account ID you want to use.", color='lightblue')
        print("Type 'exit' to go back to the main menu.")
        user_input = input(":")

        if str(user_input).lower() == "exit":
            print("Exiting...", color='green')
            return

        try:
            user_input = int(user_input)
            found = False
            for item in data:
                if user_input == item["id"]:
                    found = True
                    print("Changing to account...", color='lightgreen')

                    self.set_default_account_id(user_input)

                    print("Changing default account successfully!", color='lightblue')
                    Base.RefreshTokenFailedFlag = False
                    time.sleep(1.5)

            if not found:
                print(f"ACan't find account with ID {user_input} :(", color='lightred')
                print("Please check the ID you entered and try again.", color='lightyellow')
                time.sleep(3)
                self.SelectDefaultAccount()
        except ValueError:
            print("Invalid ID format. Please enter a valid integer.", color='lightred')
            time.sleep(2)
            self.SelectDefaultAccount()

    @staticmethod
    def read_account_data():
        if not os.path.exists(Base.account_data_path):
            return False, "AccountDataNotFound"

        try:
            with open(Base.account_data_path, "r") as file:
                data = json.load(file)
        except JSONDecodeError:
            return False, "ReadAccountDataFailed>ERROR_CODE=JSONDecodeError"

        return True, data

    def get_account_list(self):
        AccountIDList = []
        AccountNameList = []
        if not os.path.exists(Base.account_data_path):
            return False, "AccountDataNotFound", None

        try:
            with open(Base.account_data_path, "r") as file:
                data = json.load(file)
        except JSONDecodeError:
            return False, "ReadAccountDataFailed>Error_Code=JSONDecodeError", None

        try:
            for item in data:
                AccountIDList.append(item["id"])
                AccountNameList.append(item["Username"])
        except TypeError:
            return False, "ReadAccountDataFailed>Error_Code=TypeError", None

        return True, AccountIDList, AccountNameList

    @staticmethod
    def write_account_data(new_data):
        """
        :param new_data: New AccountData
        """
        if not os.path.exists(Base.account_data_path):
            return False, "AccountDataNotFound"

        try:
            with open(Base.account_data_path, "w") as file:
                json.dump(new_data, file)
        except JSONDecodeError:
            return False, "ReadAccountDataFailed>ERROR_CODE=JSONDecodeError"

        return True, True

    def delete_select_account_data(self, account_id):
        """
        :param account_id: Want delete account's id(int)

        """
        global found_same_id
        if not os.path.exists(Base.global_config_path):
            self.initialize_account_data()

        if not os.path.exists(Base.account_data_path):
            return False,

        ReadStatus, AccData = self.read_account_data()

        if not ReadStatus:
            return False, f"DeleteAccountData>ReadAccountDataFailed>{AccData}"

        for item in AccData:
            found_same_id = False
            if account_id == item["id"]:
                found_same_id = True
                data = [entry for entry in AccData if entry["id"] != account_id]

                # Reassign IDs sequentially
                for index, account in enumerate(data):
                    account["id"] = index + 1

                # Write new data
                self.write_account_data(data)
                break

        if not found_same_id:
            return False, f"NoSameIDAccountFound"
        else:
            return True, ":)"

    def DeleteAccount(self):
        Status, AccountIDList, AccountNameList = self.get_account_list()
        if not Status:
            print(f"Failed to get account list :( Cause by error {AccountIDList}")
            time.sleep(3)
            return

        while True:
            print("AccountList:")
            for account_id, account_name in zip(AccountIDList, AccountNameList):
                print(f"{account_id}: {account_name}", color='blue')

            # Get user input
            print("Please enter the ID of the account you want to delete.")
            print("Or you can type 'exit' to go back to the menu.")
            user_input = input(": ")
            if str(user_input).lower() == "exit":
                print("Exiting...")
                return True

            # Validate user input as integer
            try:
                user_input = int(user_input)
            except ValueError:
                print("Invalid ID format. Please enter a valid integer.")
                time.sleep(2)

            print(f"Deleting account data with id {user_input}...", color='indigo')

            Status, e = self.delete_select_account_data(user_input)
            if not Status:
                print("Failed to delete account data :(", color='red')
                print("Please check you enter account id is in the list and try again.", color='yellow')
                print(f"{e}")
                time.sleep(3)
                return
            else:
                print("Account data deleted successfully!", color='green')

            Status, now_id = self.get_default_account_id()
            if not Status:
                print("Failed to get Default Account ID :( Is your config file corrupted?", color='red')
                time.sleep(3)
                return True
            now_id = int(now_id)
            new_id = now_id
            if now_id is not None:
                if not now_id == 1:
                    if now_id > user_input:
                        new_id -= 1
                        Status = self.set_default_account_id(new_id)
                        if not Status:
                            print("Failed to change DefaultAccountID. Is your config file corrupted?", color='red')
                            time.sleep(3)
            else:
                print("Found Account ID are not valid. :( Is your config file corrupted?", color='red')
                time.sleep(3)
                return True

            return True

    @staticmethod
    def initialize_account_data():
        if not os.path.exists('data'):
            os.makedirs('data')
        json_data = []

        default_data = {
            "id": 1,
            "Username": 'Player',
            "UUID": "Unknown",
            "RefreshToken": "None",  # When check_account_data_are_valid notice RefreshToken = None it will stop refresh
            "AccessToken": "null",
            "tag": "TempUser;DemoUser"
        }

        json_data.append(default_data)

        with open("data/AccountData.json", "w") as jsonFile:
            json.dump(json_data, jsonFile, indent=4)

    def convert_legacy_account_data(self):
        if not os.path.exists("data/AccountData.json"):
            time.sleep(3)
            return False, "AccountDataNotFound"

        try:
            with open("data/AccountData.json", "r") as account_data:
                data = json.load(account_data)
        except Exception as e:
            return False, e

        try:
            print("Checking AccountData format...", color='green')
            TryGetLegacyAccountName = data["AccountName"]
            if TryGetLegacyAccountName == "None" or TryGetLegacyAccountName is None:
                # print(". Bypassing convert process...", color='yellow')
                return False, "AccountDataAreInvalid"
            print("AccountData are valid! Starting convert process...", color='lightblue')
        except ValueError:
            print("Check AccountData format version failed. Are you using the modern format of AccountData?",
                  color='red')
            time.sleep(3)
            return False, "CouldNotCheckAccountDataFormatVersion"

        username = data["AccountName"]
        uuid = data["UUID"]
        access_token = data["Token"]

        try:
            refresh_token = data["RefreshToken"]
            if refresh_token is None or refresh_token == "None":
                # In 0.7.1, launcher added RefreshToken to AccountData(old version not support)
                refresh_token = None
        except ValueError:
            refresh_token = None

        print("Backup old AccountData...", color='green')

        # Delete old backup file
        try:
            if os.path.exists("data/AccountData.json.bak"):
                os.remove("data/AccountData.json.bak")
        except Exception as e:
            return Exception, f"DeleteAccountData>Error: {e}"

        try:
            os.rename("data/AccountData.json", "data/AccountData.json.bak")
        except PermissionError:
            return False, "PermissionError"

        self.initialize_account_data()

        try:
            with open("data/AccountData.json", "r") as acc_data:
                new_account_data = json.load(acc_data)
        except Exception as e:
            return False, f"LoadingNewAccountData>Error: {e}"

        new_id = self.get_account_id(new_account_data)

        new_data = {
            "id": new_id,
            "Username": username,
            "UUID": uuid,
            "RefreshToken": refresh_token,
            "AccessToken": access_token
        }

        # Append new data to old json data(or new?)
        new_account_data.append(new_data)
        print("Changing default account id...", color='green')
        Status = self.set_default_account_id(2)
        if not Status:
            return False, "ChangeDefaultAccountIDFailed"

        # Write the updated or new data back to the AccountData
        try:
            with open("data/AccountData.json", "w") as file:
                json.dump(new_account_data, file, indent=4)
        except Exception as e:
            return False, f"WriteNewAccountData>Error: {e}"

        return True

    def AccountManager(self):
        try:
            print("[AccountManager]", color='lightblue')
            print('Options:', color='green')
            print("1: Login New Account", color='lightblue')
            print("2: Select Use Account", color='purple')
            print("3: Delete Account", color='red')
            print("4: Exit", color='green')
            user_input = str(input(':'))
            if user_input == "1":
                # Login new account
                ClearOutput()
                self.login_process()
            elif user_input == "2":
                # Select launcher default account(Save to config.bakelh.cfg)
                ClearOutput()
                self.SelectDefaultAccount()
            elif user_input == "3":
                # Delete Account
                ClearOutput()
                self.DeleteAccount()
            elif user_input == "4":
                return
        except Exception as e:
            if Exception is ValueError:
                print("Unknown input :O", color='red')
                time.sleep(1.5)
            else:
                print(f"AccountManager got a error when calling a internal functions. Error: {e}", color='red')
                function_name = traceback.extract_tb(e.__traceback__)[-1].name
                detailed_traceback = traceback.format_exc()
                internal_functions_error_log_dump(e, "AccountManager", function_name, detailed_traceback)
                time.sleep(5)

account_manager = AuthManager()
