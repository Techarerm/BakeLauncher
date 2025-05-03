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
import os
from LauncherBase import Base, initialize_config, print_custom as print, internal_functions_error_log_dump
from launcher.cli.display_util.util import clear
from libs.account.auth_process import get_access_token_msa
from libs.account.msa import *
from libs.account.mojang_api import *
from libs.account.auth_management import *
from launcher.cli import main_menu


class AuthManager:
    def __init__(self):
        self.RefreshTokenFlag = False
        self.grant_type = None
        self.request_data = None
        self.account_data_path = Base.account_data_path

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
                    return False, None
                except json.JSONDecodeError:
                    return False, None
        else:
            return False, "AccountDataDoesNotExist"

    def update_account_data(self, account_id, access_token, username, refresh_token):
        # Fetch account data
        status, selected_account_data, e = get_account_data_use_account_id(self.account_data_path, account_id)
        if not status:
            return False, f"Update account data failed: {e} | The specified account ID's data does not exist."

        # Load JSON data
        status, AccountData, e = read_account_data(self.account_data_path)

        if not status:
            return False, f"Update account data failed: {e} | Get main AccountData data failed."

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
                    break
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
            "https://login.live.com/oauth20_authorize.srf?client_id=00000000402B5328&redirect_uri=https://login.live"
            ".com/oauth20_desktop.srf&response_type=code&scope=service::user.auth.xboxlive.com::MBI_SSL"
        )

        blank_page_url = input("URL:")
        if blank_page_url.lower() == "exit":
            print("Back to main menu...")
            return True

        try:
            code = blank_page_url.split("code=")[1].split("&")[0]
        except IndexError:
            print("Invalid URL. Please try again.", color='lightred')
            return False

        Status, microsoft_token, microsoft_refresh_token, Err = get_microsoft_account_token(code, "AuthToken")
        if not Status:
            print(f"Failed to get microsoft account token :( Cause by error {Err}", color='red')
            time.sleep(3)
            return f"GetMSAccountTokenFailed>ERR:{Err}"

        status, accessToken, e = get_access_token_msa(microsoft_token)
        if not status:
            print(f"Failed to refresh access token. | {e}", color='red')
            return False

        status, username, uuid, e = get_account_username_and_uuid(accessToken)
        if not status:
            print(f"Failed to get Minecraft profile information. Cause by error {e}", color='red')
            time.sleep(3)
            return False
        else:
            print("Minecraft Username:", username, color='lightblue')
            print("Minecraft UUID:", uuid, color='lightblue')

            # Save the token to AccountData.json
            login_process_status = False
            print("Saving AccountData...", color='lightgreen')

            acc_exists_status, acc_id, e = check_target_account_exists_using_uuid(self.account_data_path, uuid)
            if not acc_exists_status:
                status, e, acc_id = write_new_account_to_account_data(self.account_data_path, username, uuid
                                                                      , microsoft_refresh_token, accessToken, "msa")
                if status:
                    print(f"Added new account to AccountData | UUID: {uuid}", color='lightgreen')
                    login_process_status = True
                else:
                    print(f"Failed to add new account to AccountData | ERR: {e}", color='red')
            else:
                print("AccountData already exists. | Updating new data...", color='lightgreen')
                status, e = update_specified_account_data(self.account_data_path, id, username, microsoft_refresh_token,
                                                          accessToken)
                if status:
                    print(f"Updated account data | UUID: {uuid}", color='lightgreen')
                    login_process_status = True
                else:
                    print(f"Failed to update new data. | ERR: {e}", color='red')

            if login_process_status:
                print("AccountData saved successfully!", color='lightblue')
                print("Want to change launch using account? Y/N:", color='lightgreen')
                user_input = input(":")
                if user_input.upper() == "Y":
                    print("Change using account...", color='lightgreen')
                    Status = self.set_default_account_id(acc_id)
                    if not Status:
                        print("Failed to change DefaultAccountID. Is your config file corrupted?", color='red')
                        time.sleep(3)
                print("Login process finished.", color='blue')
            else:
                print("Login process cancelled.", color='red')
                time.sleep(3)


    def check_account_data_are_valid(self, id):
        try:
            id = int(id)  # Ensure ID is an integer
        except ValueError:
            print(f"Wrong type account ID. | Type : {type(id)}", color='red')
            return False
        Status, account_data, e = get_account_data_use_account_id(self.account_data_path, id)

        if not Status:
            # If it failed when getting account data(Status = False), return failed message
            return False
        try:
            accessToken = account_data.get("AccessToken", None)
            RefreshToken = account_data.get("RefreshToken", None)
            if RefreshToken is None:
                print(f"Stopping refresh token! Cause by invalid token :(", color='lightred')
                return False
        except KeyError:
            return False

        account_status = check_access_token_are_valid(accessToken)
        if not account_status:
            print("Your Minecraft token has expired. Refreshing...", color='lightyellow')

            # Refresh Microsoft token using the refresh token
            Status, new_microsoft_token, new_refresh_token, Err = get_microsoft_account_token(RefreshToken,
                                                                                              "RefreshToken")
            if not Status:
                print(f"Failed to refresh Microsoft token. Cause by error {Err}", color='red')
                print("Maybe your refresh token are expired! please re-login your account.", color='yellow')
                Base.RefreshTokenFailedFlag = True
                time.sleep(5)
                return False, f"FailedToRefreshToken>Err:{Err}"

            status, accessToken, e = get_access_token_msa(new_refresh_token, refresh_code=True)
            if not status:
                print(f"Failed to refresh access token. | {e}", color='red')
                return False, f"FailedToRefreshToken>Err:{Err}"

            status, username, uuid, e = get_account_username_and_uuid(accessToken)
            if not status:
                print(f"Failed to get Minecraft profile information. Cause by error {e}", color='red')
                return False, f"FailedToRefreshToken>Err:{Err}"

            # Update the account data with the new "select" account data
            status, e = update_specified_account_data(self.account_data_path, id, username, new_refresh_token,
                                                      accessToken)
            if not status:
                print(f"Failed to update new ac account data :( | {e}", color='red')
                time.sleep(3)
                return False, e

            # Set flag after refresh token finished
            main_menu.main_menu.ResetMainMenu = True
            print("Refresh token process finished!", color='lightblue')
            return True, "AccountDataRefreshSuccessfully"
        return True

    def login_status(self):
        """
        Check login status.
        """
        global id, account_data, message, Status

        # Get DefaultAccountID From account data
        Status, account_id = self.get_default_account_id()
        if not Status:
            # Overwrite broken config file if DefaultAccountID not found
            print("DefaultAccountID are not found. Is your config corrupted?", color='lightyellow')
            print("Using exist launcher account...", tag='INFO')
            self.set_default_account_id(1)
            time.sleep(2)
            main_menu.main_menu.ResetMainMenu = True
            return

        if os.path.exists(self.account_data_path):
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
                    main_menu.main_menu.ResetMainMenu = True
                    return
                else:
                    # Reset Main Menu
                    main_menu.main_menu.ResetMainMenu = True
                    return
            if account_data is None:
                print(f"Can't find id '{account_id}' in the account data ! Change to use local account...",
                      color='yellow')

                # Set DefaultAccountID to local account
                Status = self.set_default_account_id(1)
                if not Status:
                    print("Failed to change DefaultAccountID. Is your config file corrupted?", color='red')
                    time.sleep(3)

                # Reset main memu to clean warning message
                Base.MainMenuResetFlag = True
                time.sleep(3)
                return
            username = account_data['Username']  # Set username here
            if account_data['Username'] == "None":
                print("Login Status: Not logged in :(", color='lightred')
                print("Please log in to your account first!", color='lightred')
            elif not Base.BypassLoginRequire and account_data['Username'] == "Player":
                print("Warning: You are currently using a local account!", color='lightred')
                # print("Please log in to your account or switch to a different account.", color='lightred')
                print("Login Status: Not logged in :(", color='lightred')
            else:
                # Bypass login status check(print
                if not Base.BypassLoginStatusCheck:
                    # Set by check_account_data_are_valid(If refresh token failed. Set it to True)
                    # Refresh main_menu(Used to prevent errors message from remaining on the main menu)
                    # When main_memu is reloaded, it stops refreshing tokens until the initiator is completely reset.
                    if not Base.RefreshTokenFailedFlag:
                        # Check internet connect(If not bypass it and print "login status: Unknown")
                        if Base.BypassLoginRequire:
                            Status = False
                        else:
                            if Base.InternetConnected:
                                Status = self.check_account_data_are_valid(account_id)
                            else:
                                # Network not connected
                                Status = False
                        # Continue the above code(If RefreshTokenFailedFlag = True, set MainMenuResetFlag to True
                        # and return. Then main_memu will be reset. When calling login_status, stop refresh process
                        # and print "Login Status: Expired session :0" Because Base.RefreshTokenFailedFlag is True)
                        if Base.RefreshTokenFailedFlag:
                            main_menu.main_menu.ResetMainMenu = True
                            return
                    else:
                        Status = False
                else:
                    Status = True
                # When MainMenuResetFlag = True(After refreshing the token it will be set to True) stop print login
                # message(until main_menu set MainMenuResetFlag = False)
                # Used only if the refresh token succeeds or Base.RefreshTokenFailedFlag = True
                if main_menu.main_menu.ResetMainMenu:
                    return

                if Status:
                    # Print this message when the access token has not expired or Base.BypassLoginStatusCheck = True
                    print("Login Status: Already logged in :)", color='lightgreen')
                    print("Hi,", username, color="lightblue")
                else:
                    if Base.BypassLoginRequire:
                        print("Login Status: Already logged in (?)", color='lightgreen')
                        print("Hi,", username, color="lightblue")
                    else:
                        # No internet connection
                        if not Base.InternetConnected:
                            print("Login Status: Unknown", color='yellow')
                            print("Hi,", username, color="lightblue")
                        else:
                            # Print this message when refresh token failed.
                            print("Login Status: Expired session :0", color='lightred')
                            print("Please login your account again!", color='lightred')
                            print("Hi,", username, color="lightblue")
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
        Status = self.set_default_account_id("2")
        if not Status:
            return False, "ChangeDefaultAccountIDFailed"

        # Write the updated or new data back to the AccountData
        print("Writing new account data...", color='lightgreen')
        try:
            with open("data/AccountData.json", "w") as file:
                json.dump(new_account_data, file, indent=4)
        except Exception as e:
            return False, f"WriteNewAccountData>Error: {e}"
        print("Update new format successfully!", color='blue')
        time.sleep(3)
        return True, None

    def clean_account_config(self):
        print("Cleaning AccountData...", color='green')
        Status = self.initialize_account_data()

        if not Status:
            print("Cleaning AccountData failed :(", color='red')
        else:
            print("AccountData cleaned successfully!", color='green')

        time.sleep(2)

        return

    def AccountManager(self):
        try:
            print("[AccountManager]", color='lightblue')
            print('Options:', color='green')
            if Base.InternetConnected:
                print("1: Login New Account", color='lightblue')
            else:
                print("1: Login New Account", color='darkgray')
            print("2: Select Use Account", color='purple')
            print("3: Delete Account", color='red')
            print("4: Clear AccountData", color='lightred')
            print("5: Exit", color='green')
            user_input = str(input(':'))
            if user_input == "1":
                # Login new account
                clear()
                if Base.InternetConnected:
                    self.login_process()
                else:
                    print("No Internet Connection :(", color="red")
                    time.sleep(4)
                    return
            elif user_input == "2":
                # Select launcher default account(Save to config.bakelh.cfg)
                clear()
                self.SelectDefaultAccount()
            elif user_input == "3":
                # Delete Account
                clear()
                self.DeleteAccount()
            elif user_input == "4":
                self.initialize_account_data()
            elif user_input == "5":
                return
            else:
                print(f"Unknown options {user_input} :/", color='red')
                time.sleep(2)
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
