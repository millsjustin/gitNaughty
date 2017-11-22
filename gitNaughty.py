import requests
import sys


search_pattern = "-----BEGIN RSA PRIVATE KEY-----"
github_api_url = "https://api.github.com/search/code"
github_token = ""
last_url_file = "last_url.txt"


def verfiy(file_content: str):
    print(file_content)


def main():
    if len(sys.argv) > 1:
        with open(last_url_file, "r") as last_file:
            api_response = requests.get(last_file.read().strip())
    else:
        payload = {"q": search_pattern, "access_token": github_token}
        api_response = requests.get(github_api_url, params=payload)

    while "next" in api_response.links:
        res_json = api_response.json()

        items = res_json["items"]

        for item in items:
            raw_url = item["html_url"].replace(
                "https://github.com/",
                "https://raw.githubusercontent.com/"
            ).replace(
                "/blob/",
                "/"
            )

            file_res = requests.get(raw_url)
            verfiy(file_res.text)

        with open(last_url_file, "w") as last_file:
            last_file.write(api_response.links["next"]["url"])

        api_response = requests.get(api_response.links["next"]["url"])

    # handle the last case


if __name__ == "__main__":
    main()
