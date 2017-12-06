import requests
import sys
import time
import datetime
import json
import pickle
import jacksonsVerification
import justinsVerification
from utils import *

# the state of the script will be saved in this file in json format
# - the next api url
# - the current min file size
# - the current max file size
state_filename = "api_state.txt"

# file size paramaters
GITHUB_API_MAX_FILESIZE = 383999  # < 384 KB
INITIAL_MIN_FILESIZE = 1  # initialize (in bytes)
INITIAL_MAX_FILESIZE = 1

GITHUB_CODE_SEARCH_URL = "https://api.github.com/search/code"
SEARCH_PATTERN = justinsVerification.private_key_search_pattern


def verify(item: dict):
    justinsVerification.stats.checking_item()

    raw_url = get_raw_url(item)
    raw_file_response = requests.get(raw_url)

    if not raw_file_response.ok:
        print("There was an error getting this raw file: {}".format(raw_url))
        return

    justinsVerification.verifyPrivateKey(raw_file_response.text, item)


def get_next_1000(min: int, max: int, payload: dict):
    """
    try to get less then 1000 results in the api search query
    :param min: the current min file size
    :param max: the current max file size
    :return: try to return a request.Response with fewer than 1000 results
    """
    print("Getting next 1000 results.")
    print("Current sizes are, min: {}, max: {}".format(min, max))
    step = max - min
    min = max + 1
    new_payload = payload.copy()
    num_attempts = 0
    steps_tried = []

    if min >= GITHUB_API_MAX_FILESIZE:
        log_error_and_exit("Reached Github max file size", None)

    while num_attempts < 20:
        num_attempts += 1
        max = min + step
        steps_tried.append(step)

        if max >= GITHUB_API_MAX_FILESIZE:
            max = GITHUB_API_MAX_FILESIZE

        print("Trying: Min: {}, Max: {}".format(min, max))
        new_payload["q"] = build_api_query(SEARCH_PATTERN, min, max)
        api_response = requests.get(GITHUB_CODE_SEARCH_URL, params=new_payload)

        if not api_response.ok:
            if api_response.status_code == 403:
                check_abuse_limit(api_response)
                continue
            else:
                log_error_and_exit("Error with github api while trying to get next 1000", api_response)

        response_json = api_response.json()

        if "total_count" not in response_json:
            log_error_and_exit("while trying to get next 1000 'total_count' not in api response", api_response)

        total_count = response_json["total_count"]
        print("total_count: {}".format(total_count))

        if total_count < 100:
            if steps_tried.count(step) > 1:
                return (api_response, min, max)
            elif step == 0:
                step = 1
            else:
                step *= 2
        elif total_count > 1000:
            if step == 0:
                return (api_response, min, max)
            elif step == 1:
                step = 0
            else:
                step //= 2
        else:
            return (api_response, min, max)

    print("tried 20 times to get less than 1000 results but didn't")
    return (api_response, min, max)


def build_api_query(search_term: str, min: int, max: int):
    return "{}+size:{}..{}".format(search_term, min, max)


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
        "q": build_api_query(SEARCH_PATTERN, api_state["min_filesize"], api_state["max_filesize"]),
        "access_token": token_cycle.__next__(),
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
            justinsVerification.stats.add_to_api_total_count(int(response_json["total_count"]))
            justinsVerification.stats.save()
            save_api_state(api_state)

            if api_state["max_filesize"] >= GITHUB_API_MAX_FILESIZE:
                log_error_and_exit("Reached github max filesize", api_response)

            try:
                print("just finished a batch press ctrl+c in the next 5 seconds to exit")
                time.sleep(5)
            except KeyboardInterrupt:
                log_error_and_exit("user pressed ctrl+c", api_response)

            api_response, api_state["min_filesize"], api_state["max_filesize"] = get_next_1000(api_state["min_filesize"], api_state["max_filesize"], payload)
            continue
            # log_error_and_exit("There was no 'next' item in the api headers", api_response)

        # TODO find a better way to persist stats data
        justinsVerification.stats.save()

        api_state["next_url"] = api_response.links["next"]["url"]
        save_api_state(api_state)
        check_rate_limit(api_response.headers)
        api_response = requests.get(api_state["next_url"])


if __name__ == "__main__":
    things_to_close.append(justinsVerification.stats)
    main()
    cleanup_and_exit()
