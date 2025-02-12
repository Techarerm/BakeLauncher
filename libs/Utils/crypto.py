import hashlib


def verify_checksum(file_path, expected_sha1):
    sha1 = hashlib.sha1()
    with open(file_path, "rb") as f:
        while True:
            data = f.read(65536)  # Read in 64KB chunks
            if not data:
                break
            sha1.update(data)
    file_sha1 = sha1.hexdigest()
    return file_sha1 == expected_sha1


def verify_checksum_v2(file_path, expected_hash, crypto_type):
    hash_dict = {
        'sha1': hashlib.sha1,
        'sha256': hashlib.sha256,
        'md5': hashlib.md5
    }

    if crypto_type not in hash_dict:
        raise ValueError(f"Unsupported hash type: {crypto_type}")

    hash_obj = hash_dict[crypto_type]()

    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hash_obj.update(chunk)

    file_sha1 = hash_obj.hexdigest()
    return file_sha1 == expected_hash
