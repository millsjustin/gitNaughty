import requests
import statsAdder
import json
from collections import defaultdict
from utils import *

GITHUB_CODE_SEARCH_URL = "https://api.github.com/search/code"

def save_stats(unique_urls, used_keys, missed_urls):
    print("Saving Stats")
    with open("unique_urls.json", "w") as unique_urls_file:
        json.dump(list(unique_urls), unique_urls_file)
    with open("used_keys.json", "w") as used_keys_file:
        json.dump(used_keys, used_keys_file)
    with open("missed_urls.json", "w") as missed_urls_file:
        json.dump(list(missed_urls), missed_urls_file)


def main():
    total_stats = statsAdder.combine_total_stats()

    unique_urls = set()
    used_keys = defaultdict(list)
    missed_urls = set()

    for key in total_stats._valid_keys:
        for url in total_stats._valid_keys[key]:
            if url in unique_urls:
                print("Duplicate url: {}".format(url))
                continue
            else:
                print("Checking: {}".format(url))
                unique_urls.add(url)

            payload = {
                "q": "{}+repo:{}".format(get_filename(url), get_repo(url)),
                "access_token": github_token,
                "per_page": 100
            }

            api_response = requests.get(GITHUB_CODE_SEARCH_URL, params=payload)

            if not api_response.ok:
                if api_response.status_code == 403:
                    check_abuse_limit(api_response)
                    missed_urls.add(url)
                    continue
                else:
                    log_error_and_exit("error with github api while searching repo: {}".format(get_repo(url)), api_response)

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
                save_stats(unique_urls, used_keys, missed_urls)

            check_rate_limit(api_response.headers)


if __name__ == "__main__":
    main()
