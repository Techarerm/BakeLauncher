"""
AccountData(v3):
[
    {
        "_account_data_header_info": "DO NOT MODIFY THIS",
        "currentAccountID": null, # Current account ID
        "creationDate": datetime.datetime.now()  # Created date
    },
    {
        "id": 1,  # For account management
        "Username": "Player",
        "UUID": "Unknown",
        "RefreshToken": null,
        "AccessToken": null,
        "tag": null, # Unused
        "AccountType": "offline", # Account type (msa = Microsoft Account, mojang = Yggdrasil(Not working),
        legacy = Legacy authentication(Not working), offline = (DEBUG ONLY)
    },
    {
        "id": 2,
        "Username": "TedKai", # Your username
        "UUID": "576477ee9099488798f478d81e6f9fae", # Your Minecraft Account UUID
        "RefreshToken": "Example RefreshToken", # Your Microsoft Account Refresh Token(it use on refresh token)
        "AccessToken": "Example AccessToken", # Your Minecraft Account Token(Or session token. Expire in one day)
        "AccountType": "msa"
    }
]
"""
import datetime
import json
import os

now_time = datetime.datetime.now()

account_data_sample = [
    {
        "_account_data_header_info": "***WARNING*** | DO NOT MODIFY THIS FILE",
        "currentAccountID": None,
        "creationDate": "{}".format(now_time),
    }
]


def create_account_data(account_data_path, overwrite=False):
    """
    Create AccountData (if the file exists set overwrite=True)
    :param account_data_path: Account data path (AccountData.json)
    :param overwrite: Overwrite existing account data if it exists
    :return: Status
    """
    if os.path.exists(account_data_path) and not overwrite:
        return False

    try:
        with open(account_data_path, 'w') as f:
            json.dump(account_data_sample, f, indent=4)
        f.close()
    except Exception as e:
        print("[DEBUG] Unable to write account_data_sample to AccountData. ERR:{}".format(e))
        return False

    return True


def read_account_data(account_data_path):
    """
    Read AccountData
    :param account_data_path: Account data path (AccountData.json)
    :return: Status, AccountData, ErrorMEssage
    """
    if not os.path.exists(account_data_path):
        return False, None, "Target AccountData does not exist"

    try:
        with open(account_data_path, 'r') as f:
            return True, json.load(f), None
    except Exception as e:
        return False, None, "Unable to read AccountData. ERR:{}".format(e)


def write_back_account_data(account_data_path, updated_account_data):
    """
    ### Not recommended to use this function
    Write new data back to the AccountData
    :param account_data_path: Account data path (AccountData.json)
    :param updated_account_data: Updated AccountData
    :return: Status, ErrorMessage
    """

    if not os.path.exists(account_data_path):
        return False, None, "White back AccountData failed | Target AccountData does not exist."

    try:
        with open(account_data_path, 'w') as f:
            f.write(updated_account_data)
    except Exception as e:
        return False, None, "Unable to read AccountData. ERR:{}".format(e)


def get_new_account_id(account_data_path):
    """
    Get new account ID
    :param: account_data_path: Account data path (AccountData.json)
    :return: Status, new_account_id: int
    """

    try:
        with open(account_data_path, 'r') as f:
            account_data = json.load(f)
    except Exception as e:
        return False, e

    # Get all id inside the AccountData
    ids = [entry['id'] for entry in account_data]
    new_id = 1
    while new_id in ids:
        # If id 1 is in data, new_id + 1 until can't find same one.
        new_id += 1

    return True, new_id


def rearrange_all_accounts(account_data_path):
    """
    Rearrange all accounts ID
    :param: account_data_path: Account data path (AccountData.json)
    :return: Status, ErrorMessage
    """

    try:
        with open(account_data_path, 'r') as f:
            account_data = json.load(f)
    except Exception as e:
        return False, e

    account_id_count = 1 + len(account_data)

    for new_account_id, account_data in zip(range(account_id_count), account_data):
        # Skip account data header
        is_header = account_data.get("_account_data_header_info", None)

        if is_header is not None:
            continue

        account_data["id"] = new_account_id

    try:
        with open(account_data_path, 'w') as f:
            json.dump(account_data, f)
    except Exception as e:
        return False, e

    return True, None


def write_new_account_to_account_data(account_data_path, account_name, uuid, refresh_token, access_token, account_type,
                                      tag=""):
    """
    Write the new account_data
    :param account_data_path: Account data path (AccountData.json)
    :param account_name: Account name
    :param uuid: Account UUID
    :param refresh_token: Refresh token
    :param access_token: Access token
    :param account_type: Account type
    :param tag: Account tag
    :return: Status, ErrorMessage
    """
    status, new_account_id = get_new_account_id(account_data_path)

    if not status:
        return False, None, "Could not get new account ID"

    new_account_data = {
        "id": new_account_id,
        "Username": account_name,
        "UUID": uuid,
        "RefreshToken": refresh_token,
        "AccessToken": access_token,
        "AccountType": account_type,
        "tag": tag
    }

    try:
        with open(account_data_path, 'r') as f:
            AccountData = json.load(f, encoding='utf-8')
    except Exception as e:
        return False, None, e

    AccountData.append(new_account_data)

    try:
        with open(account_data_path, 'w') as f:
            json.dump(AccountData, f, indent=4)
    except Exception as e:
        return False, None, e

    return True, new_account_id, None


def check_target_account_exists_using_uuid(account_data_path, uuid):
    """
    Check if the target account exists
    :param account_data_path: AccountData path (AccountData.json)
    :param uuid: Account UUID
    :return: account_exists_status, exists_account_id, ErrorMessage
    """
    status, AccountData, e = read_account_data(account_data_path)

    if not status:
        return False, None, "Checking target account exists failed while reading AccountData. ERR:{}".format(e)

    existing_entry = next((entry for entry in AccountData if entry.get("UUID", None) == uuid), None)

    if existing_entry:
        return True, existing_entry["id"], None

    return False, None, "Account ID exists"


def get_account_data_use_account_id(account_data_path, target_id):
    """
    Get account data (subitem) from AccountData
    :param account_data_path: Account data path (AccountData.json)
    :param target_id: Target account ID
    :return: Status, AccountData, ErrorMessage
    """
    if os.path.exists(account_data_path):
        with open(account_data_path, 'r') as f:
            try:
                json_data = json.load(f)
                # Loop through the data and find the matching ID
                for entry in json_data:
                    if entry.get("id", None) is None:
                        continue

                    if entry.get("id", None) == int(target_id):
                        # Return the matching entry
                        return True, entry, None
                return False, None, "Target ID not found."
            except Exception as e:
                return False, None, e
    else:
        return False, None, "Specified AccountData file does not exist."


def get_account_info_from_account_data(account_data_path, target_id):
    """
    Get account data by account ID
    :param account_data_path: Account data path (AccountData.json)
    :param target_id: The target account ID
    :return: Status, username, UUID, ErrorMessage
    """
    Status, accData, e = get_account_data_use_account_id(account_data_path, target_id)

    if Status:
        accName = accData.get("Username", None)
        accUUID = accData.get("UUID", None)
        return True, accName, accUUID, None
    else:
        return False, None, None, e


def update_specified_account_data(account_data_path, target_account_id, username, refresh_token, access_token,
                                  tag="!skip", uuid="!skip", account_type="!skip"):
    """
    Update specified account data from AccountData
    :param account_data_path: Account data path (AccountData.json)
    :param target_account_id: Target account ID
    :param username: Minecraft username
    :param refresh_token: Refresh token
    :param access_token: Access token
    :param tag: Account tag
    :param uuid: Account UUID
    :param account_type: Account type
    :return: Status, ErrorMessage
    # If you want skip update some param, Set parameters to "!skip" to skip the update process
    """
    # mappings
    account_info_mappings = {
        "Username": username,
        "RefreshToken": refresh_token,
        "AccessToken": access_token,
        "UUID": uuid,
        "AccountType": account_type,
        "tag": tag
    }

    # Convert target id to integer
    if type(target_account_id) != int:
        try:
            target_account_id = int(target_account_id)
        except Exception as e:
            return False, "Updating target account data failed while converting target id to integer. ERR:{}".format(e)

    # Load JSON data
    status, AccountData, e = read_account_data(account_data_path)
    if not status:
        return False, f"Updating target account data failed: {e} | Get main AccountData data failed."

    # Update "select" account data
    account_found = False
    try:
        for account in AccountData:
            if account.get("id", None) is None:
                continue

            if account['id'] == target_account_id:
                for key, value in account_info_mappings.items():
                    if value != "!skip":
                        account[key] = value
                account_found = True
                break
    except Exception as e:
        return False, "Updating target account data failed while replacing old information. ERR:{}".format(e)

    # Write back to the AccountData if the target account was found and updated
    if account_found:
        try:
            with open(account_data_path, "w") as jsonFile:
                json.dump(AccountData, jsonFile, indent=4)
            return True, None
        except IOError as e:
            return False, f"Updating target account data failed while writing back account data. ERR:{e}."

    return False, f"Target account ID {target_account_id} not found."


def delete_specified_account_data(account_data_path, target_account_id):
    """
    Delete specified account data from AccountData
    :param account_data_path: Account data path (AccountData.json)
    :param target_account_id: Target account ID you want to delete
    """

    # Convert target id to integer
    if type(target_account_id) != int:
        try:
            target_account_id = int(target_account_id)
        except Exception as e:
            return False, "Deleting target account data failed while converting target id to integer. ERR:{}".format(e)

    # Load JSON data
    status, AccountData, e = read_account_data(account_data_path)
    if not status:
        return False, f"Deleting target account data failed: {e} | Get main AccountData data failed."

    # "Delete" target account's  data
    new_AccountData = []
    try:
        for account in AccountData:
            if account.get("id", None) is None:
                new_AccountData.append(account)
                continue

            if account['id'] != target_account_id:
                new_AccountData.append(account)
    except Exception as e:
        return False, "Deleting target account data failed while replacing old information. ERR:{}".format(e)

    # Write back to the AccountData if the target account was found and deleted
    try:
        with open(account_data_path, "w") as jsonFile:
            json.dump(new_AccountData, jsonFile, indent=4)
        return True, None
    except IOError as e:
        return False, f"Deleting target account data failed while writing back account data. ERR:{e}."


def get_current_account_id(account_data_path):
    """
    Get current account ID from AccountData
    :param account_data_path: Account data path (AccountData.json)
    :return: Status, id, ErrorMessage
    """

    status, acc_data, e = read_account_data(account_data_path)

    if status:
        try:
            account_data_header = acc_data[0]
        except Exception as e:
            return False, None, f"Failed to get first item from AccountData. ERR:{e}."

        if account_data_header.get("_account_data_header_info", None) is not None:
            current_account_id = account_data_header.get("currentAccountID", None)

            return True, current_account_id, None
        else:
            """
            for account in acc_data:
                if account.get("_account_data_header_info", None) is not None:
                    current_account_id = account.get("currentAccountID", None)
                    found = True
                    break
            """
            return False, None, "AccountData header missing."

    return False, None, "Get current account ID failed. ERR:{}".format(e)


def set_current_account_id(account_data_path, new_current_account_id):
    """
    Set current account ID from AccountData
    :param account_data_path: Account data path (AccountData.json)
    :param new_current_account_id: New current accID
    :return: Status, ErrorMessage
    """

    status, acc_data, e = read_account_data(account_data_path)

    if status:
        try:
            account_data_header = acc_data[0]
        except Exception as e:
            return False, f"Failed to get first item from AccountData. ERR:{e}."

        if account_data_header.get("_account_data_header_info", None) is not None:
            account_data_header["currentAccountID"] = new_current_account_id
            acc_data[0] = account_data_header
        else:
            return False, "AccountData header missing."

        # Write back to the AccountData
        try:
            with open(account_data_path, "w") as jsonFile:
                json.dump(acc_data, jsonFile, indent=4)
            return True, None
        except Exception as e:
            return False, f"Set current account ID failed. ERR:{e}."

    return False, "Set current account ID failed. ERR:{}".format(e)


def convert_legacy_format_account_data_to_new_format(legacy_account_data_path, new_account_data_path):
    """
    Convert legacy account data to ACCv3 format
    :param legacy_account_data_path: Legacy AccountData path (AccountData.json)
    :param new_account_data_path: Converted AccountData path(AccountData.json |
    Can be the same as legacy_account_data_path)
    :return: Status, ErrorMessage
    """

    # Read legacy AccountData
    status, old_acc_data, e = read_account_data(legacy_account_data_path)

    # Check legacy AccountData type (
    legacy_v1_type = True if not type(old_acc_data) == list else False

    if not status:
        return False, ("Converting legacy account data to ACCv3 failed while reading legacy account data."
                       " ERR:{}").format(e)

    try:
        if os.path.exists(legacy_account_data_path + ".old"):
            os.remove(legacy_account_data_path + ".old")
        os.rename(legacy_account_data_path, legacy_account_data_path + ".old")
    except Exception as e:
        return False, "Converting legacy account data to ACCv3 failed. ERR:{}".format(e)

    if not os.path.exists(new_account_data_path):
        status = create_account_data(new_account_data_path)
        if not status:
            return False, ("Converting legacy account data to ACCv3 failed while creating new AccountData."
                           " ERR:{}").format(e)

    status, AccountData, e = read_account_data(new_account_data_path)

    if not status:
        return False, ("Converting legacy account data to ACCv3 failed while reading new AccountData."
                       " ERR:{}").format(e)

    if legacy_v1_type:
        username = old_acc_data.get("AccountName", None)
        uuid = old_acc_data.get("UUID", None)
        refresh_token = old_acc_data.get("RefreshToken", None)
        access_token = old_acc_data.get("Token", None)

        status, new_id = get_new_account_id(new_account_data_path)

        if not status:
            return False, "Converting legacy account data to ACCv3 failed. Could not get new account ID."

        new_account_data = {
            "id": new_id,
            "Username": username,
            "UUID": uuid,
            "RefreshToken": refresh_token,
            "AccessToken": access_token,
            "AccountType": None
        }

        AccountData.append(new_account_data)
    else:
        try:
            for account in old_acc_data:
                acc_id = account.get("id", None)
                username = account.get("Username", None)
                uuid = account.get("UUID", None)
                refresh_token = account.get("RefreshToken", None)
                access_token = account.get("AccessToken", None)

                new_account_data = {
                    "id": acc_id,
                    "Username": username,
                    "UUID": uuid,
                    "RefreshToken": refresh_token,
                    "AccessToken": access_token,
                    "AccountType": None
                }

                AccountData.append(new_account_data)
        except Exception as e:
            return False, ("Converting legacy account data to ACCv3 failed while appending account info to AccountData."
                           " ERR:{}").format(e)

    with open(new_account_data_path, "w") as new_account_file:
        json.dump(AccountData, new_account_file, indent=4)

    return True, None


def check_account_data_version(account_data_path):
    """
    Check account data type
    :param account_data_path: Account data path
    :return: Status, version(v1, v2, v3), ErrorMessage
    """

    status, AccountData, e = read_account_data(account_data_path)
    if status:
        if not (type(AccountData) == list):
            return True, "v1", None
        else:
            try:
                account_data_header = AccountData[0]
            except Exception as e:
                return False, None, "Check account data type failed. | ERR:{}".format(e)

            if account_data_header.get("_account_data_header_info", None) is not None:
                return True, "v3", None

            return True, "v2", None

    return False, None, "Check account data type failed. | ERR:{}".format(e)


def get_all_available_accounts(account_data_path):
    """
    Get all available accounts
    :param account_data_path: Account data path
    :return: Status, accounts :list, ErrorMessage
    accounts List look like: [{1: "Player"}, {2: "AAA"}, {3: "BBB"}]
    """
    # Lista
    accounts = []

    status, acc_data, e = read_account_data(account_data_path)

    if status:
        for account in acc_data:
            acc_name = account.get("Username", None)
            acc_id = account.get("id", None)

            if acc_name is not None:
                accounts.append({acc_id: acc_name})

        return True, accounts, None

    return False, None, "Get all available accounts failed. ERR:{}".format(e)


def get_current_account_data(account_data_path):
    """
    Get current account data
    :param account_data_path: Account data path
    :return: Status, account_data : dict, ErrorMessage
    """
    status, curr_acc_id, e = get_current_account_id(account_data_path)

    if status:
        status, acc_data, e = get_account_data_use_account_id(account_data_path, curr_acc_id)

        if not status:
            return False, None, "Get current account data failed. ERR:{}".format(e)

        return True, acc_data, None

    return False, None, "Get current account data failed. ERR:{}".format(e)