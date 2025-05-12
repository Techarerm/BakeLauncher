import os.path
from libs.Utils.utils import download_file


def download_client(version_data, client_dest, **kwargs):
    """
    Download client
    :param version_data: Specified Minecraft version data (used to obtain client download URL)
    :param client_dest: The client file download destination.
    ***Other parameters***
    :param custom_client_url: Custom client download URL
    (Priority: custom_client_url > obtain client download URL from version_data)
    """
    dest_base_path = os.path.basename(client_dest)
    os.makedirs(dest_base_path, exist_ok=True)

    # parameter stuff (If the custom_client_url is available, priority uses it first.)
    custom_client_url = kwargs.get('custom_client_url', None)
    client_hash = None
    if custom_client_url is not None:
        client_url = custom_client_url
    else:
        # Download client.jar
        client_info = version_data['downloads']['client']
        client_url = client_info['url']
        client_hash = client_info("sha1", None)

    if client_hash is None:
        print("[Warning] Could not find the client file hash from the version data.")

    download_file(client_url, client_dest)

    if os.path.exists(client_dest):
        return True
    else:
        return False
