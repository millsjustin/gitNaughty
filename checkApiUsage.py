# A script used for verifying whether keys found on Github are actually used
# anywhere in the repo.
#
# Input: a text file of keys and their corresponding github file urls.
#       (File is supplied as the first commandline argument)
#       Note: Expected input file format is:
#
#           <any file metadata>
#           SEARCH_PATTERN: <e.g. access_key>
#           <key e.g. AIzaSyB_39asQPB4fpAQTg3k3RpDU1E9>
#           <github file url where key was found>
#           <new line>
#           ... (repeat the 3 lines above)
#
#
# Output: a text file keyUsageResults.txt that gives results and statistics
#
# Written by Jackson Murphy. Last updated on December 3, 2017.

import gitNaughty as lib
from pprint import pprint
import requests
import sys

with open("github_token3.txt", "r") as token_file:
    GITHUB_TOKEN = token_file.read().strip()

# username/repos that we know contain a ton of bogus keys
BLACKLIST = {"lvoursl/gotohack", "alt-f13/cm-spb.ru"}

def api_key_is_used(file_contents: str, key_string: str, search_pattern: str):
    api_key_used = False # initialize
    api_call_keywords = {
        "url", ".com", ".org", ".io", ".net", "www."}
    for line in file_contents.splitlines():
        if search_pattern not in line:
            continue
        for keyword in api_call_keywords:
            if keyword in line:
                return [True, line]
        # Also check if search_pattern is a parameter in a function call
    return [False, None]

def build_api_query(search_pattern: str, url: str):
    username_slash_repo = url[url.find("github.com/") + 11 : url.find("/blob")]
    return "{}+repo:{}".format(search_pattern, username_slash_repo)

def check_for_input_argument():
    if len(sys.argv) < 2:
        print("ERROR: No input file found. Please supply a file as the first commandline argument:")
        print("$ python3.6 verify_key_usage.py <input_file>")
        exit(0)

def determine_key_type(search_pattern: str):
    api_patterns = {
        "access_key", "accessKey", "access_token", "accessToken", "secret_key", "secretKey", \
        "api_key", "apiKey" }
    if search_pattern in api_patterns:
        return "api_key"
    else:
        print("The search pattern you used: {}, cannot yet be handled by this program.".format(search_pattern))
        exit(0)
        # TODO handle other key types (e.g. encryption keys, integrity keys, ...)
        #return "unknown_key"

def get_input_file_contents():
    input_file_contents = ""
    with open(sys.argv[1], "r") as input_file:
        input_file_contents = input_file.read()
    # Remove any metadata that precedes the line SEARCH PATTERN = ...
    index = input_file_contents.find("PATTERN = ")
    if index == -1:
        print("ERROR: No search pattern was supplied in the input file.")
        print("At the top of the file, please include the line: SEARCH PATTERN = <search pattern used>")
        exit(0)
    return input_file_contents[index:]

def is_in_user_blacklist(url: str):
    """
    Returns True if url belongs to a github user who we know has a ton of
    bogus keys stored. We don't want to include these keys in our findings
    """
    username_slash_repo = url[url.find("github.com/") + 11 : url.find("/blob")]
    if username_slash_repo in BLACKLIST:
        print("user is in the blacklist!")
        return True
    else:
        return False

def key_is_used(key_string: str, url: str, search_pattern: str, key_type: str):
    api_response = query_api(url, search_pattern)
    if api_response is None: return [False, None, None]
    lib.check_rate_limit(api_response.headers)
    response_json = api_response.json()
    #print("total count was {} for repo {}".format(response_json["total_count"], url))
    for item in response_json["items"]:
        raw_url = lib.get_raw_url(item)
        raw_file_response = requests.get(raw_url)
        if key_type == "api_key":
            [result, line] = api_key_is_used(raw_file_response.text, key_string, search_pattern)
            if result == True:
                return [True, line, raw_url]
    return [False, None, None]

def not_really_key(string_key: str):
    """
    Performs a simplistic check to make sure the key isn't something like
    test_key123 or S3_Key
    """
    potential_key = string_key.lower()
    keywords = {"test", "aws", "s3", "sha", "digest", "key", "user", "token", \
        "access", "auth"}
    for keyword in keywords:
        if keyword in potential_key:
            return True
    return False

def query_api(url: str, search_pattern: str):
    payload = {
        "q": build_api_query(search_pattern, url),
        "access_token": GITHUB_TOKEN,
        "per_page": 100
    }
    api_response = requests.get(lib.GITHUB_CODE_SEARCH_URL, params=payload)
    if not api_response.ok:
        if api_response.status_code == 403:
            lib.check_abuse_limit(api_response)
            api_response = query_api(url, search_pattern)
        else:
            print("There was an error with the github api: {}".format(api_response.text))
            return None
    if "items" not in api_response.json():
        print("The api response did not contain an 'items' field")
        return None
    return api_response

def remove_search_pattern(file_contents: str):
    first_new_line = file_contents.find("\n")
    pattern_equal_sign = file_contents.find("=")
    search_pattern = file_contents[pattern_equal_sign + 1 : first_new_line].strip()
    content_body = file_contents[first_new_line + 1:].strip()
    return [search_pattern, content_body]

def write_to_file(used_keys: dict, total_keys_checked: int, search_pattern: str):
    output_filename = "keyUsageResults" + search_pattern.title() + ".txt"
    with open(output_filename, "w") as results_file:
        results_file.write("--------Key Usage Statistics--------\n\n")
        results_file.write("Token var: " + search_pattern + "\n")
        results_file.write("From input file: " + sys.argv[1] + "\n")
        results_file.write("Tokens examined: " + str(total_keys_checked) + "\n")
        results_file.write("Tokens found to be used: " + str(len(used_keys)) + "\n")
        results_file.write("\n-----------------------------------------\n\n")
        for key, tuple in used_keys.items():
            results_file.write("Key: " + key + "\n")
            results_file.write("Code: " + tuple[0] + "\n") # line where key is used
            results_file.write("File Url: " + tuple[1] + "\n\n")


def main():
    check_for_input_argument()
    input_file_contents = get_input_file_contents()
    [search_pattern, input_file_contents] = remove_search_pattern(input_file_contents)
    key_type = determine_key_type(search_pattern)
    used_keys = {}
    total_keys_checked = 0

    lines = input_file_contents.split("\n")
    for i in range(0, len(lines), 3): # assumes a new line follows every result in input file
        key_string = lines[i]
        if not_really_key(key_string): continue
        url = lines[i + 1]
        if is_in_user_blacklist(url): continue
        [is_used, line, file_url] = key_is_used(key_string, url, search_pattern, key_type)
        if is_used:
            print("Key {} was used on this line:\n{}\n".format(key_string, line))
            used_keys[key_string] = (line, file_url)
        else:
            print("Key {} does not appear to be used\n".format(key_string))
        total_keys_checked += 1

        if total_keys_checked % 50  == 0: # periodically write to output file
            write_to_file(used_keys, total_keys_checked, search_pattern)

    write_to_file(used_keys, total_keys_checked, search_pattern)





if __name__ == "__main__":
    main()
