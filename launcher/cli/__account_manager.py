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
import traceback
from LauncherBase import Base, initialize_config, print_custom as print, internal_functions_error_log_dump
from launcher.cli.display_util.util import clear
from libs.account.auth_process import get_account_token_msa
from libs.account.msa import *
from libs.account.mojang_api import *
from libs.account.account_management import *
from launcher.cli import main_menu


class AuthManager:
    def __init__(self):
        self.RefreshTokenFlag = False
        self.SuspendAccountInfo = False
        self.grant_type = None
        self.request_data = None
        self.account_data_path = Base.account_data_path
        self.skip_login_check = False

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
                    acc_id = line.split('=')[1].strip().strip().strip('"').strip("'")
                    try:
                        acc_id = int(acc_id)
                        found = True
                    except ValueError:
                        print("Failed to get DefaultAccountID. Config file is invalid.", color='lightred')
                        found = False
                    break
        if found:
            return True, acc_id
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

        status, access_token, new_refresh_token, e = get_account_token_msa(code)

        if not status:
            print(f"Failed to get accessToken. | {e}.", color='lightred')
            return False

        status, username, uuid, e = get_account_username_and_uuid(access_token)
        if not status:
            print(f"Failed to get Minecraft profile information. | {e}", color='red')
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
                status, acc_id, e = write_new_account_to_account_data(self.account_data_path, username, uuid
                                                                      ,new_refresh_token, access_token,
                                                                      "msa")
                if status:
                    print(f"Added new account to AccountData | UUID: {uuid}", color='lightgreen')
                    login_process_status = True
                else:
                    print(f"Failed to add new account to AccountData | ERR: {e}", color='red')
            else:
                print("AccountData already exists. | Updating new data...", color='lightgreen')
                status, e = update_specified_account_data(self.account_data_path, acc_id, username,
                                                          new_refresh_token, access_token, tag="")
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
                    status, e = set_current_account_id(self.account_data_path, acc_id)
                    if not status:
                        print(f"Failed to change DefaultAccountID :( | ERR: {e}", color='red')
                        time.sleep(2)
                print("Login process finished.", color='blue')
            else:
                print("Login process cancelled.", color='red')
                time.sleep(3)

    def login_status(self):
        """
        Print login status.
        """

        if self.SuspendAccountInfo:
            return

        def suspend_account_info_process():
            time.sleep(4)
            self.SuspendAccountInfo = True
            main_menu.main_menu.ResetMainMenu = True

        # Skip print account info if fist time creates AccountData (front mode)
        if not os.path.exists(self.account_data_path):
            create_account_data(self.account_data_path)
            return

        # Check AccountData version (Legacy Support Part)
        status, version, e = check_account_data_version(self.account_data_path)

        if not status:
            print("Checking AccountData version failed. | AccountInfo suspend.", color='lightyellow')
            suspend_account_info_process()
            return

        if version != "v3":
            print(self.account_data_path)
            status, e = convert_legacy_format_account_data_to_new_format(self.account_data_path, self.account_data_path)
            main_menu.main_menu.ResetMainMenu = True
            return
        # ============================================

        # Get currentAccountID from account data
        status, current_account_id, e = get_current_account_id(self.account_data_path)
        if not status:
            # If getting currentAccountID failed, suspend AccountInfo.
            print("Could not get current account id. | AccountInfo suspend.", color='lightyellow')
            suspend_account_info_process()
            return

        # Skip print Account Info if currentAccountID undefined
        if current_account_id is None:
            return

        # Get current account data from AccountData
        status, current_account_data, e = get_account_data_use_account_id(self.account_data_path, current_account_id)

        if not status:
            # If getting current account's data failed, set to front mode
            set_current_account_id(self.account_data_path, None)
            return

        # Account Info
        access_token = current_account_data.get("AccessToken", None)
        username = current_account_data.get("Username", None)
        refresh_token = current_account_data.get("RefreshToken", None)
        tag = current_account_data.get("tag", "")

        # Flag
        expired = True if tag == "Expired" else False
        status = check_access_token_are_valid(access_token)
        online = status

        if not status and not expired and not self.skip_login_check:
            print("Your Minecraft token has expired. Refreshing...", color='lightyellow')

            status, _, refresh_token, _ = get_microsoft_account_token(refresh_token, "RefreshToken")

            if not status:
                print("Refreshing token failed. | Token session expired.", color='red')
                update_specified_account_data(self.account_data_path, current_account_id, "!skip",
                                              "!skip", "!skip", tag="Expired")
                main_menu.main_menu.ResetMainMenu = True
                return

            status, new_access_token, new_refresh_token, e = get_account_token_msa(refresh_token, refresh_code=True)

            status, new_username, acc_uuid, e = get_account_username_and_uuid(new_access_token)

            if not status:
                print("Getting username failed. | AccountInfo suspend.", color='red')
                suspend_account_info_process()
                return

            status = update_specified_account_data(self.account_data_path, current_account_id, new_username,
                                                   new_refresh_token, new_access_token)

            if not status:
                print("Updating new account info failed. | AccountInfo suspend.", color='red')
                suspend_account_info_process()
                return

            main_menu.main_menu.ResetMainMenu = True
            return

        if online:
            print("Login Status: Online", color='lightgreen')
            print("Hi,", username, color="lightblue")
        elif self.skip_login_check:
            print("Login Status: *Skipped", color='lightgreen')
            print("Hi,", username, color="lightblue")
        else:
            print("Login Status: Session Expired", color='lightyellow')
            print("Hi,", username, color="lightblue")

    def SelectDefaultAccount(self):
        while True:
            clear()
            print("AccountList:")

            status, accounts, e = get_all_available_accounts(self.account_data_path)

            for account in accounts:
                for acc_id, username in account.items():
                    print(f"{acc_id}: {username}")

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
                for _, account in enumerate(accounts):
                    for account_id, username in account.items():
                        if account_id == user_input:
                            status, e = set_current_account_id(self.account_data_path, account_id)

                            if status:
                                print(f"Set current account id to {account_id} | Username: {username}", color='green')
                            else:
                                print(f"Set current account id failed. | {e}", color='red')

                            found = True
                            break

                if not found:
                    print(f"Cannot find account with ID {user_input} :(", color='lightred')
                    print("Please check the ID you entered and try again.", color='lightyellow')
                    time.sleep(3)
            except ValueError:
                print("Invalid ID format. Please enter a valid integer.", color='lightred')
                time.sleep(2)

    def DeleteAccount(self):
        while True:
            clear()
            print("AccountList:")

            status, accounts, e = get_all_available_accounts(self.account_data_path)

            for account in accounts:
                for acc_id, username in account.items():
                    print(f"{acc_id}: {username}")

            # Get user input
            print("Please enter the account ID you want to delete.", color='lightblue')
            print("Type 'exit' to go back to the main menu.")
            user_input = input(":")

            if str(user_input).lower() == "exit":
                print("Exiting...", color='green')
                return

            try:
                user_input = int(user_input)
                found = False
                for _, account in enumerate(accounts):
                    for account_id, username in account.items():
                        if account_id == user_input:
                            status, e = delete_specified_account_data(self.account_data_path, account_id)

                            if status:
                                print(f"Deleted target id {account_id} account data. | Username: {username}",
                                      color='green')
                            else:
                                print(f"Delete target id {account_id} account data failed. "
                                      f"| {e}", color='red')

                            found = True
                            break

                if not found:
                    print(f"Cannot find account with ID {user_input} :(", color='lightred')
                    print("Please check the ID you entered and try again.", color='lightyellow')
                    time.sleep(3)
            except ValueError:
                print("Invalid ID format. Please enter a valid integer.", color='lightred')
                time.sleep(2)

    def clear_account_data(self):
        print("Clearing...")
        status = create_account_data(self.account_data_path, overwrite=True)

        if not status:
            print("Clearing account data failed.", color='lightgreen')
        else:
            print("Cleared account data successfully!", color='lightgreen')

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
                self.clear_account_data()
            elif user_input == "5" or user_input.lower() == "exit":
                return
            elif user_input.lower() == "disableinfo":
                self.SuspendAccountInfo = True
            elif user_input.lower() == "enableinfo":
                self.SuspendAccountInfo = False
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
