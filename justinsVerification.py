import shelve
import re

private_key_search_pattern = "-----BEGIN RSA PRIVATE KEY-----"
rsa_key_re = re.compile("-+BEGIN RSA PRIVATE KEY-+(.*?)-+END RSA PRIVATE KEY-+", flags=re.DOTALL)
stat_shelve = shelve.open("privateKey.shelve")


def verifyPrivateKey(file_content: str, url: str):
    stat_key = ""
    re_match = rsa_key_re.search(file_content)

    if not re_match:
        stat_key = file_content
    else:
        stat_key = re_match.group(1)

    if stat_key not in stat_shelve:
        stat_shelve[stat_key] = [url]
    else:
        stat_shelve[stat_key].append(url)

    print(stat_key)
