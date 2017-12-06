import statsClass
import re
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

private_key_search_pattern = "-----BEGIN RSA PRIVATE KEY-----"
rsa_key_re = re.compile("-+BEGIN RSA PRIVATE KEY-+.*?-+END RSA PRIVATE KEY-+", flags=re.DOTALL)

stats = statsClass.Stats()


def get_key_from_bytes(data: bytes):
    try:
        return serialization.load_pem_private_key(
            data,
            password=None,
            backend=default_backend()
        )
    except:
        return None


def verifyPrivateKey(file_content: str, item: dict):
    if stats.already_checked(item["html_url"]):
        return

    stats.checking_file(item["html_url"])

    for potential_key in rsa_key_re.findall(file_content):
        print(potential_key)
        stats.match_found(potential_key, item["html_url"])
        if get_key_from_bytes(potential_key.encode()):
            stats.key_found(potential_key, item["html_url"])
