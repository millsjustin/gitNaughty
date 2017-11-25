import requests
import sys
import time
import datetime
import jacksonsVerification as jackson


github_token = "0fb611b3f988aa081c180af3a4a15a938753cace"
github_api_url = "https://api.github.com/search/code"
search_pattern = jackson.get_search_pattern()
GITHUB_API_MAX_FILESIZE = 383999 # < 384 KB
INITIAL_MIN_FILESIZE = 20 # initialize (in bytes)
INITIAL_MAX_FILESIZE = 40
last_url_file = "last_url.txt"


def verify(file_content: str, search_pattern: str):
    jackson.verify(file_content, search_pattern)

def check_rate_limit(count_remaining: str, reset_time: str):
    if count_remaining == "0":
        reset_time = datetime.datetime.fromtimestamp(float(reset_time))
        time_to_wait = reset_time - datetime.datetime.now()
        if time_to_wait.seconds <= 0:
            return
        print("Rate Limit Hit, Sleeping: {}".format(time_to_wait.seconds + 1))
        time.sleep(time_to_wait.seconds + 1)

def  get_raw_url(item):
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
    q = search_pattern + "+size:" + str(min_filesize) + ".." + str(max_filesize)
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



def main():
    min_filesize = INITIAL_MIN_FILESIZE
    max_filesize = INITIAL_MAX_FILESIZE
    filesize_step = max_filesize - min_filesize
    q = search_pattern + "+size:" + str(min_filesize) + ".." + str(max_filesize)
    payload = {"q": q, "access_token": github_token}

    if len(sys.argv) > 1:
        with open(last_url_file, "r") as last_file:
            last_file_content = last_file.read().strip()
            [min_filesize, max_filesize, filesize_step] = get_filesize_info(last_file_content)
            api_response = requests.get(last_file_content)
    else:
        api_response = requests.get(github_api_url, params=payload)

    print("This many matches found: " + str(api_response.json()["total_count"]))
    while True:

        while "next" in api_response.links:
            res_json = api_response.json()
            items = res_json["items"]

            for item in items:
                raw_url = get_raw_url(item)
                file_res = requests.get(raw_url)
                verify(file_res.text, search_pattern)

            with open(last_url_file, "w") as last_file:
                last_file.write(api_response.links["next"]["url"])

            check_rate_limit(api_response.headers["X-RateLimit-Remaining"], api_response.headers["X-RateLimit-Reset"])

            api_response = requests.get(api_response.links["next"]["url"])

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


if __name__ == "__main__":
    main()
