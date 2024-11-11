"""
AutoTool

A tool can get Microsoft Refresh Token, Minecraft Account Data(username, uuid), and AccessToken
Some code is from GitHub: https://gist.github.com/dewycube/223d4e9b3cddde932fbbb7cfcfb96759
Modify some functions for automatic refresh token and mult account support...

When you log in your account AutoTool will save all account to AccountData(Also create an id when you want to select use
account.

Example In AccountData:
[
    {
        "id": 1,
        "Username": "BakeLauncherLocalPlayer",
        "UUID": "Unknown",
        "RefreshToken": "None",
        "AccessToken": "Unknown",
        "tag": "LocalTESTPlayerDoNOTUSE"
    },
    {
        "id": 2,
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
import requests
import json
import os
from LauncherBase import ClearOutput, GetPlatformName, timer, initialize_config
from LauncherBase import print_custom as print


class AuthManager:
    def __init__(self):
        self.oauth20_token = "https://login.live.com/oauth20_token.srf"
    def get_microsoft_account_token(self, code):
        """
        Code example M.C559_SN1.2.U.09fd18c9-f260-0000-test-221f3eb387b4
        """
        try:
            # Microsoft token + Microsoft refresh token
            r = requests.post(self.oauth20_token, data={
                "client_id": "00000000402B5328",
                "scope": "service::user.auth.xboxlive.com::MBI_SSL",
                "code": code,
                "redirect_uri": "https://login.live.com/oauth20_desktop.srf",
                "grant_type": "authorization_code"
            })
            r.raise_for_status()
            microsoft_token = r.json()["access_token"]
            microsoft_refresh_token = r.json()["refresh_token"]
            print("Get Microsoft account token and refresh Token successfully!", color='blue')
            return True, microsoft_token, microsoft_refresh_token
        except requests.RequestException:
            print("AuthTool: Failed to get Microsoft token :(", color='red')
            print("AuthTool: Maybe this url are expired. Try to re-login again!", color='red')
            print("AuthTool: If you still can't login please clean your browser token and try again.", color='red')
            return False, 'FailedToGetMicrosoftToken', "FailedToGetRefreshToken"

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
        except requests.RequestException:
            print("AuthTool: Failed to get XBL token.", color='red')
            print("AuthTool: ", color='red')
            return False, "FailedToGetXBLToken"

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
        except requests.RequestException:
            print("AuthTool: Failed to get XSTS token.", color='red')
            print("AuthTool: Maybe this url are expired. Try to re-login again!", color='red')
            print("AuthTool: If stil can't login please clean your browser token and try again.", color='red')
            print("AuthTool: If still can't login....report this issue to GitHUb!.", color='red')
            return False, "FailedToGetXSTSUserHash", "FailedToGetXSTSToken"

    def get_access_token(self, xsts_userhash, xsts_token):
        try:
            # Minecraft token
            r = requests.post("https://api.minecraftservices.com/authentication/login_with_xbox", json={
                "identityToken": f"XBL3.0 x={xsts_userhash};{xsts_token}"
            })
            r.raise_for_status()
            access_token = r.json()["access_token"]
            return True, access_token
        except requests.RequestException:
            print("AuthTool: Failed to get Minecraft token.", color='red')
            print("AuthTool: Maybe this url are expired. Try to re-login again!", color='red')
            return False, "FailedToGetAccessToken"

    def get_account_data(self, minecraft_token):
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
            return True, username, uuid
        except requests.RequestException:
            print("AuthTool: Failed to get Minecraft profile information.", color='red')
            print("AuthTool: Maybe this url are expired. Try to relogin again!", color='red')
            print("AuthTool: If stil can't login please clean your browser token and try again.", color='red')
            print("AuthTool: If still can't login....report this issue to GitHUb!.", color='red')
            return False, "FailedToGetAccountData", ""

    def get_account_id(self, data):
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

    def get_account_data_use_accountid(self, target_id):
        if os.path.exists("data/AccountData.json"):
            with open("data/AccountData.json", 'r') as f:
                try:
                    json_data = json.load(f)
                    # Loop through the data and find the matching ID
                    for entry in json_data:
                        if entry['id'] == int(target_id):
                            # Return the matching entry
                            return True, entry
                    print(f"No account found with ID {target_id}.", color='yellow')
                except json.JSONDecodeError:
                    print("Error reading the JSON file.", color='red')
        else:
            print("JSON file does not exist :(", color='red')
            print("Trying to login your account first!", color='yellow')

        return False, "FailedToGetAccountDataUseAccountID"

    def update_account_data(self, account_id, access_token, username, refresh_token):
        # Fetch account data
        status, selected_account_data = self.get_account_data(account_id)
        if not status:
            return False, f"UpdateAccountData>{selected_account_data}"

        # Load JSON data
        try:
            with open("data/AccountData.json", 'r') as f:
                account_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            return False, f"Error loading AccountData.json: {e}"

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
                print("Token refreshed and saved successfully!")
                return True
            except IOError as e:
                return False, f"Error saving AccountData.json: {e}"

        print(f"No account found with ID {account_id}.", color='yellow')
        return False, "Account not found"

    def set_default_account_id(self, id):
        AccountData = os.path.join("data", "AccountData.json")
        if not os.path.exists(AccountData):
            initialize_config()
        with open("data/config.bakelh.cfg", 'r') as file:
            lines = file.readlines()
            for i in range(len(lines)):
                if 'DefaultAccountID' in lines[i]:
                    # Use the new or existing account ID
                    lines[i] = f'DefaultAccountID = {id}\n'
        with open("data/config.bakelh.cfg", 'w') as file:
            file.writelines(lines)

    def login_process(self):
        print("Please login your account in your web browser.", color='c')
        print("After logging in, please copy the URL and paste it into the launcher.", color='green')
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
            print("AuthTool: Invalid URL. Please try again.", color='red')
            return "CheckURLValidFailed"

        # Start get token process...
        Status, microsoft_token, microsoft_refresh_token = self.get_microsoft_account_token(code)
        if not Status:
            return microsoft_token + microsoft_refresh_token

        Status, xbl_token = self.get_xbl_token(microsoft_token)
        if not Status:
            return xbl_token

        Status, xsts_userhash, xsts_token = self.get_xsts_token(xbl_token)
        if not Status:
            return xsts_userhash + xsts_token

        Status, access_token = self.get_access_token(xsts_userhash, xsts_token)
        if not Status:
            return access_token

        Status, username, uuid = self.get_account_data(access_token)
        if not Status:
            return username


        try:
            # Save the token to AccountData.json
            print("Saving AccountData...", color='green')

            json_data = []

            # Check if the file exists and load existing data
            if os.path.exists("data/AccountData.json"):
                with open("data/AccountData.json", 'r') as f:
                    try:
                        json_data = json.load(f)
                        # Ensure json_data is a list
                        if not isinstance(json_data, list):
                            print("AuthTool: JSON data is not valid! Go to Extra>2: Reset AccountData.json to reset "
                                  "AccountData.json!", color='yellow')
                            timer(4)
                            json_data = []
                    except json.JSONDecodeError:
                        print("AuthTool: Failed to load existing JSON data, resetting to empty list.", color='red')
                        print("AutoTool: Go to Extra>2: Reset AccountData.json to reset "
                              "AccountData.json!", color='yellow')
                        json_data = []

            # Check if the UUID already exists in the AccountData
            existing_entry = next((entry for entry in json_data if entry["UUID"] == uuid), None)

            # Huh...maybe I don't need to modify and use update_account_data...?
            if existing_entry:
                # Update existing entry without changing ID
                existing_entry["RefreshToken"] = microsoft_refresh_token
                existing_entry["AccessToken"] = access_token
                existing_entry["Username"] = username
                print(f"AuthTool: Updated existing account data for UUID: {uuid}", color='yellow')
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
                print(f"AuthTool: Added new account data for UUID: {uuid}", color='green')

            # Write the updated or new data back to the AccountData
            with open("data/AccountData.json", "w") as jsonFile:
                json.dump(json_data, jsonFile, indent=4)

            print("AuthTool: AccountData saved successfully!", color='green')
            print("AuthTool: Want to change launch using account? Y/N:", color='green')
            user_input = input(":")
            if user_input.upper() == "Y":
                print("AuthTool: Change using account...", color='green')
                self.set_default_account_id(new_id)


        except Exception as e:
            print(f"AuthTool: Failed to save account data. Error: {e}", color='red')
            print("AuthTool: Trying to delete file name AccountData.json (in the data folder)!", color='yellow')

        print("Login process finished :)", color='blue')

    def check_account_data_are_valid(self, id):
        try:
            id = int(id)  # Ensure ID is an integer
        except ValueError:
            return False, "ID must be an integer when getting select account data."
        Status, account_data = self.get_account_data_use_accountid(id)

        if not Status:
            # If it failed when getting account data(Status = False), return failed message
            return False, account_data
        try:
            accessToken = account_data["AccessToken"]
            RefreshToken = account_data.get("RefreshToken")
            if RefreshToken is None:
                print(f"AuthTool: Stopping refresh token! Cause by invalid token :(", color='red')
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
            print("AuthTool: Your Minecraft token has expired. Refreshing...", color='yellow')

            # Refresh Microsoft token using the refresh token
            Status, new_microsoft_token, new_refresh_token = self.get_microsoft_account_token(RefreshToken)
            if not Status:
                print("AuthTool: Failed to refresh Microsoft token.", color='red')
                print("AuthTool: Maybe your refresh token are expired! please re-login your account.",
                      color='yellow')
                return False, "CheckAccountDataAreValid>FetchNewMicrosoftTokenFailed"

            # Get a new Minecraft token using the refreshed Microsoft token
            Status, xbl_token = self.get_xbl_token(new_microsoft_token)
            if not Status:
                return False, f"GettingXBLToken>{xbl_token}"

            Status, xsts_userhash, xsts_token = self.get_xsts_token(xbl_token)
            if not Status:
                return False, f"GettingXSTSToken>{xsts_token}"

            Status, access_token = self.get_access_token(xsts_userhash, xsts_token)
            if not Status:
                return False, f"GettingAccessToken>{access_token}"

            Status, username, uuid = self.get_account_data(access_token)
            if not Status:
                return False, f"GettingAccountData>{username}"

            # Update the account data with the new "select" account data
            status, message = self.update_account_data(id, access_token, username, new_refresh_token)
            if not status:
                return False, f"UpdateAccountData>{message}"

            return True, "AccountDataRefreshSuccessfully"

    def login_status(self):
        """
        Check login status.
        Avoid Minecraft crash on auth... However, if the token expires, it will still crash on launch :)
        """
        username = "Player"  # Initialize username to avoid UnboundLocalError
        try:
            with open("data/config.bakelh.cfg", 'r') as file:
                for line in file:
                    if "DefaultAccountID" in line:
                        id = line.split('=')[1].strip()  # Extract the value if found
                        break  # Stop after finding the ID
        except FileNotFoundError:
            initialize_config()
            id = 1

        if os.path.exists('data/AccountData.json'):
            Status, account_data = self.get_account_data_use_accountid(int(id))
            if account_data is None:
                print(
                    "AuthTool: config.bakelh.cfg item DefaultAccountID are not available! Change to use local "
                    "account...",
                    color='yellow')
                id = 1
                Status, account_data = self.get_account_data_use_accountid(int(id))
            username = account_data['Username']  # Set username here
            if account_data['Username'] == "None":
                print("Login Status: Not logged in :(", color='red')
                print("Please log in to your account first!", color='red')
            elif account_data['Username'] == "BakeLauncherLocalPlayer" or account_data['Username'] == "Player":
                print("Warning: You are currently using a local account!", color='red')
                print("Login Status: Not logged in :(", color='red')
                print("Please log in to your account or switch to a different account.", color='red')
            else:
                Status, message = self.check_account_data_are_valid(id)
                if Status:
                    print("Login Status: Already logged in :)", color='green')
                    print("Hi,", username, color="blue")  # Now this should work correctly
                else:
                    print(f"ErrorMessage: {message}")
                    print("Login Status: Expired session :0", color='red')
                    print("Please login your account again!", color='red')
                    print("Hi,", username, color="blue")  # Now this should work correctly
            if "tag" in account_data:
                print(f"Account Tag: {account_data['tag']}", color='green')
        else:
            self.initialize_account_data()
            username = "Player"
            print("Login Status: Not logged in :(", color='red')
            print("Please log in to your account first!", color='red')

    def SelectDefaultAccount(self):
        print("AccountList:")
        with open("data/AccountData.json", "r") as file:
            data = json.load(file)

        # Display available accounts
        for item in data:
            print(f'{item["id"]}: {item["Username"]}')

        # Get user input
        print("AuthTool: Please enter the account ID you want to use.", color='blue')
        print("Type 'exit' to go back to the main menu.")
        user_input = input(":")

        if str(user_input).lower() == "exit":
            print("AuthTool: Exiting...", color='green')
            return

        try:
            user_input = int(user_input)
            found = False
            for item in data:
                if user_input == item["id"]:
                    found = True
                    print("AuthTool: Changing to account...", color='green')

                    # Read the configuration file
                    with open("data/config.bakelh.cfg", 'r') as file:
                        lines = file.readlines()

                    # Update the DefaultAccountID
                    for i in range(len(lines)):
                        if 'DefaultAccountID' in lines[i]:
                            lines[i] = f'DefaultAccountID = {user_input}\n'

                    # Write the updated lines back to the file
                    with open("data/config.bakelh.cfg", 'w') as file:
                        file.writelines(lines)

                    print("AuthTool: Changing default account successfully!", color='blue')
                    time.sleep(1.5)

            if not found:
                print(f"AuthTool: Can't find account with ID {user_input} :(", color='red')
                print("AuthTool: Please check the ID you entered and try again.", color='yellow')
                time.sleep(3)
                self.SelectDefaultAccount()
        except ValueError:
            print("AuthTool: Invalid ID format. Please enter a valid integer.", color='red')
            time.sleep(2)
            self.SelectDefaultAccount()

    def DeleteAccount(self):
        print("AccountList:")
        with open("data/AccountData.json", "r") as file:
            data = json.load(file)

        # Display available accounts
        for item in data:
            print(f'{item["id"]}: {item["Username"]}')

        # Get user input
        print("AuthTool: Please enter the ID of you want to delete account.", color='purple')
        print("Or you can type 'exit' to go back to the main menu.", color='blue')
        user_input = input(":")
        if str(user_input).lower() == "exit":
            print("AuthTool: Exiting...", color='green')
            return

        try:
            user_input = int(user_input)
            found = False
            for item in data:
                if user_input == item["id"]:
                    found = True
                    print("AuthTool: Deleting account...", color='green')

                # Delete user input account
                if user_input == 1:
                    print("AuthTool: You can't delete launcher local account!", color='red')
                    timer(3)
                    return
                data = [entry for entry in data if entry["id"] != user_input]

                with open(f"data/AccountData.json", "w") as file:
                    json.dump(data, file, indent=4)


                timer(3)
            if not found:
                print(f"AuthTool: Can't find account with ID {user_input} :(", color='red')
                print("AuthTool: Please check the ID you entered and try again.", color='yellow')
                timer(3)
                self.SelectDefaultAccount()
            print(f"AuthTool: Deleted account ID {user_input} successfully!", color='blue')
        except ValueError:
            print("AuthTool: Invalid ID format. Please enter a valid integer.", color='red')
            timer(2)
            self.SelectDefaultAccount()

    def initialize_account_data(self):
        if not os.path.exists('data'):
            os.makedirs('data')
        json_data = []

        default_data = {
            "id": 1,
            "Username": 'Player',
            "UUID": "Unknown",
            "RefreshToken": "None",  # When auth_tool notice RefreshToken = None it will stop refresh
            "AccessToken": "null",
            "tag": "TempUser;DemoUser"
        }

        json_data.append(default_data)

        with open("data/AccountData.json", "w") as jsonFile:
            json.dump(json_data, jsonFile, indent=4)

    def AccountManager(self):
        PlatformName = GetPlatformName.check_platform_valid_and_return()
        try:
            print("[AccountManager]", color='blue')
            print('Options:', color='green')
            print("1: Login New Account", color='blue')
            print("2: Select Use Account", color='purple')
            print("3: Delete Account", color='red')
            user_input = int(input(':'))
            if user_input == 1:
                # Login new account
                ClearOutput(PlatformName)
                self.login_process()
            elif user_input == 2:
                # Select launcher default account(Save to config.bakelh.cfg)
                ClearOutput(PlatformName)
                self.SelectDefaultAccount()
            elif user_input == 3:
                # Delete Account
                ClearOutput(PlatformName)
                self.DeleteAccount()

        except ValueError:
            print("AuthTool: Invalid Option :0", color='red')
            self.AccountManager()


account_manager = AuthManager()




