import requests
import sys
import time
import datetime
import json
import pickle
import jacksonsVerification
import justinsVerification

# the state of the script will be saved in this file in json format
# - the next api url
# - the current min file size
# - the current max file size
state_filename = "api_state.txt"

# load the github api token from a file
with open("github_token.txt", "r") as token_file:
    github_token = token_file.read().strip()

# file size paramaters
GITHUB_API_MAX_FILESIZE = 383999  # < 384 KB
INITIAL_MIN_FILESIZE = 1024  # initialize (in bytes)
INITIAL_MAX_FILESIZE = 2048

GITHUB_CODE_SEARCH_URL = "https://api.github.com/search/code"
SEARCH_PATTERN = justinsVerification.private_key_search_pattern


def verify(item: dict):
    raw_url = get_raw_url(item)
    raw_file_response = requests.get(raw_url)

    if not raw_file_response.ok:
        print("There was an error getting this raw file: {}".format(raw_url))
        return

    justinsVerification.verifyPrivateKey(raw_file_response.text, raw_url)


def check_rate_limit(headers: dict):
    if "X-RateLimit-Remaining" not in headers or "X-RateLimit-Reset" not in headers:
        print("Rate limit info was not in the api response headers")
        return

    count_remaining = headers["X-RateLimit-Remaining"]
    reset_time = headers["X-RateLimit-Reset"]

    if count_remaining == "0":
        reset_time = datetime.datetime.fromtimestamp(float(reset_time))
        time_to_wait = reset_time - datetime.datetime.now()
        if time_to_wait.seconds <= 0:
            return
        print("Rate Limit Hit, Sleeping: {}".format(time_to_wait.seconds + 1))
        time.sleep(time_to_wait.seconds + 1)


def check_abuse_limit(api_response: requests.Response):
    if "Retry-After" not in api_response.headers:
        log_error_and_exit("api response returned status code: 403 and 'Retry-After' is not in the headers", api_response)

    time_to_wait = int(api_response.headers["Retry-After"]) + 1
    print("Abuse rate limit hit, Sleeping: {}".format(time_to_wait))
    time.sleep(time_to_wait)


def get_raw_url(item):
    return item["html_url"].replace(
        "https://github.com/",
        "https://raw.githubusercontent.com/"
    ).replace(
        "/blob/",
        "/"
    )


def update_filesize_window(min_filesize: int, max_filesize: int):
    filesize_step = max_filesize - min_filesize
    if max_filesize == GITHUB_API_MAX_FILESIZE:
        max_filesize += filesize_step
    else:
        min_filesize += filesize_step
        max_filesize += filesize_step
        if max_filesize > GITHUB_API_MAX_FILESIZE:
            max_filesize = GITHUB_API_MAX_FILESIZE
    return [min_filesize, max_filesize]


def update_payload(min_filesize: int, max_filesize: int):
    q = SEARCH_PATTERN + "+size:" + str(min_filesize) + ".." + str(max_filesize)
    payload = {"q": q, "access_token": github_token}
    return payload


def get_filesize_info(last_file_content: str):
    begin_min = last_file_content.index("size%3A") + 7
    end_min = last_file_content.index("..", begin_min)
    begin_max = end_min + 2
    end_max = last_file_content.index("&", begin_max)
    min_filesize = int(last_file_content[begin_min:end_min])
    max_filesize = int(last_file_content[begin_max:end_max])
    filesize_step = max_filesize - min_filesize
    return [min_filesize, max_filesize, filesize_step]


def log_error_and_exit(message: str, api_response: requests.Response):
    print(message)
    with open("api_response.pickle", "wb") as api_res_file:
        pickle.dump(api_response, api_res_file)
    cleanup_and_exit()


def load_api_state():
    with open(state_filename, "r") as state_file:
        return json.load(state_file)


def save_api_state(api_state: dict):
    with open(state_filename, "w") as state_file:
        json.dump(api_state, state_file)


def main():
    api_state = {
        "next_url": "",
        "min_filesize": INITIAL_MIN_FILESIZE,
        "max_filesize": INITIAL_MAX_FILESIZE
    }
    payload = {
        "q": "{}+size:{}..{}".format(SEARCH_PATTERN, api_state["min_filesize"], api_state["max_filesize"]),
        "access_token": github_token,
        "per_page": 100
    }

    if len(sys.argv) > 1:
        api_state = load_api_state()
        api_response = requests.get(api_state["next_url"])
    else:
        api_response = requests.get(GITHUB_CODE_SEARCH_URL, params=payload)

    while True:
        if not api_response.ok:
            if api_response.status_code == 403:
                check_abuse_limit(api_response)
                api_response = requests.get(api_state["next_url"])
                continue
            else:
                log_error_and_exit("There was an error with the github api: {}".format(api_response.text), api_response)

        response_json = api_response.json()

        if "items" not in response_json:
            log_error_and_exit("The api response did not contain an 'items' field", api_response)

        for item in response_json["items"]:
            verify(item)

        if "next" not in api_response.links:
            log_error_and_exit("There was no 'next' item in the api headers", api_response)

        api_state["next_url"] = api_response.links["next"]["url"]
        save_api_state(api_state)

        check_rate_limit(api_response.headers)

        api_response = requests.get(api_state["next_url"])


"""
    print("This many matches found: " + str(api_response.json()["total_count"]))
    while True:

        while "next" in api_response.links:

            # handle the last case

        print("Exhausted the response links")
        [min_filesize, max_filesize] = update_filesize_window(min_filesize, max_filesize)
        payload = update_payload(min_filesize, max_filesize)
        if max_filesize <= GITHUB_API_MAX_FILESIZE:
            print("Updated filesize parameters, making a new api call")
            print("Minimum file size is now: " + str(min_filesize) + " and max is: " + str(max_filesize))
            try:
                api_response = requests.get(github_api_url, params=payload)
                print("This many matches found: " + str(api_response.json()["total_count"])) # sometimes returns KeyError...
            except KeyError:
                # Wait and then try one more time
                time.sleep(2)
                api_response = requests.get(github_api_url, params=payload)
                print("This many matches found: " + str(api_response.json()["total_count"]))

        else:
            print("Search has completed for all filesizes")
            break
"""


def cleanup_and_exit():
    justinsVerification.stat_shelve.close()
    sys.exit()


if __name__ == "__main__":
    main()
    cleanup_and_exit()
