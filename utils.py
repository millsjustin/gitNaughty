# helper functions

import time
import datetime
import requests
import pickle
import sys
import itertools
import glob

# add things to this list that need to be closed when the program ends
things_to_close = []

# load the github api tokens into an itertools.cycle
github_tokens = []
for file_str in glob.glob("github_token*.txt"):
    with open(file_str) as token_file:
        github_tokens.append(token_file.read().strip())
token_cycle = itertools.cycle(github_tokens)


def get_raw_url(item):
    return item["html_url"].replace(
        "https://github.com/",
        "https://raw.githubusercontent.com/"
    ).replace(
        "/blob/",
        "/"
    )


def get_repo(url: str):
    split_url = url.split("/")
    user = split_url[3]
    repo = split_url[4]
    return "{}/{}".format(user, repo)


def get_filename(url: str):
    return url.split("/")[-1]


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
        elif time_to_wait.seconds >= 180:
            print("Time to wait was more than 180 seconds. Only sleeping: 180")
            time.sleep(180)
        else:
            print("Rate Limit Hit, Sleeping: {}".format(time_to_wait.seconds + 1))
            time.sleep(time_to_wait.seconds + 1)


def check_abuse_limit(api_response: requests.Response):
    if "Retry-After" not in api_response.headers:
        log_error_and_exit("api response returned status code: 403 and 'Retry-After' is not in the headers", api_response)

    time_to_wait = int(api_response.headers["Retry-After"]) + 1
    print("Abuse rate limit hit, Sleeping: {}".format(time_to_wait))
    time.sleep(time_to_wait)


def log_error_and_exit(message: str, api_response: requests.Response):
    print(message)
    with open("api_response.pickle", "wb") as api_res_file:
        pickle.dump(api_response, api_res_file)
    cleanup_and_exit()


def cleanup_and_exit():
    for item in things_to_close:
        item.close()
    sys.exit()
