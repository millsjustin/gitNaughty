import requests
import statsAdder
import json
from collections import defaultdict
from utils import *
import sys

GITHUB_CODE_SEARCH_URL = "https://api.github.com/search/code"

def save_stats(unique_urls, used_keys, missed_urls, errors):
    print("Saving Stats")
    with open("unique_urls.json", "w") as unique_urls_file:
        json.dump(list(unique_urls), unique_urls_file)
    with open("used_keys.json", "w") as used_keys_file:
        json.dump(used_keys, used_keys_file)
    with open("missed_urls.json", "w") as missed_urls_file:
        json.dump(list(missed_urls), missed_urls_file)
    with open("errors.json", "w") as errors_file:
        json.dump(errors, errors_file)


def load_stats():
    print("Loading Stats")
    with open("unique_urls.json") as unique_urls_file:
        unique_urls = set(json.load(unique_urls_file))
    with open("used_keys.json") as used_keys_file:
        used_keys = defaultdict(list)
        used_keys.update(json.load(used_keys_file))
    with open("missed_urls.json") as missed_urls_file:
        missed_urls = set(json.load(missed_urls_file))
    with open("errors.json") as errors_file:
        errors = json.load(errors_file)

    return unique_urls, used_keys, missed_urls, errors


def main():
    if len(sys.argv) > 1:
        total_stats = statsAdder.load_total_stats()
        unique_urls, used_keys, missed_urls, errors = load_stats()
        for url_list in used_keys.values():
            for url in url_list:
                unique_urls.add(url)
    else:
        total_stats = statsAdder.combine_total_stats()
        unique_urls = set()
        used_keys = defaultdict(list)
        missed_urls = set()
        errors = []

    for key in total_stats._valid_keys:
        checked_file_names = set()
        checked_repos = set()

        for url in total_stats._valid_keys[key]:
            filename = get_filename(url)
            repo = get_repo(url)

            if url in unique_urls:
                print("Duplicate url: {}".format(url))
                continue
            elif repo in checked_repos:
                print("Already checked this repo")
                continue
            elif filename in checked_file_names:
                print("Already checked this file name")
                continue

            print("Checking: {}".format(url))
            unique_urls.add(url)

            payload = {
                "q": "{}+repo:{}".format(filename, repo),
                "access_token": token_cycle.__next__(),
                "per_page": 100
            }

            api_response = requests.get(GITHUB_CODE_SEARCH_URL, params=payload)

            if not api_response.ok:
                if api_response.status_code == 403:
                    check_abuse_limit(api_response)
                    missed_urls.add(url)
                    continue
                else:
                    errors.append(api_response.text)
                    continue

            checked_file_names.add(filename)
            checked_repos.add(repo)

            response_json = api_response.json()

            if "total_count" not in response_json:
                print("'total_count' not in json response")
                continue

            total_count = response_json["total_count"]

            if total_count >= 1:
                used_keys[key].append(url)
                print("used: {}".format(total_count))
            else:
                print("not used")

            if len(unique_urls) % 30 == 0:
                save_stats(unique_urls, used_keys, missed_urls, errors)

            check_rate_limit(api_response.headers)

    save_stats(unique_urls, used_keys, missed_urls, errors)


if __name__ == "__main__":
    main()
