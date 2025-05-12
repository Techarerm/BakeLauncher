from libs.account.msa import *
from libs.account.mojang_api import *
from libs.account.yggdrasil import *


def get_account_token_msa(msa_auth_code, refresh_code=False):
    code_type = "AuthToken"
    if refresh_code:
        code_type = "RefreshToken"
    msa_tk_status, microsoft_token, microsoft_refresh_token, err = get_microsoft_account_token(msa_auth_code, code_type)
    if not msa_tk_status:
        return False, None, None, f"GetMicrosoftAccToken>{err}"

    xbl_tk_status, xbl_token, err = get_xbl_token(microsoft_token)
    if not xbl_tk_status:
        return False, None, None, f"GetXblToken>{err}"

    xsts_tk_status, xsts_userhash, xsts_token, err = get_xsts_token(xbl_token)
    if not xsts_tk_status:
        return False, None, None, f"GetXstsToken>{err}"

    access_tk_status, access_token, err = get_access_token(xsts_userhash, xsts_token)
    if not access_tk_status:
        return False, None, None, f"GetAccessToken>{err}"

    return True, access_token, microsoft_refresh_token, None

# If you want to get accessToken using yggdrasil api. Using get_access_token_yggdrasil (from ibs.account.yggdrasil)
