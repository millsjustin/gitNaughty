import re

SEARCH_PATTERN = "access_token"
total_results_count = [0]
naughty_count = [0]
tokens = set()

def get_search_pattern():
    return SEARCH_PATTERN

def check_for_token(potential_token):
    # first remove any additional occurrences of the search pattern
    potential_token = potential_token.replace("access_token", "")
    potential_token = potential_token.replace("accessToken", "")
    potential_token = potential_token.replace("expires", "")

    pattern = re.compile("[a-zA-Z0-9\._]{10,80}")
    match_object = pattern.search(potential_token)
    if match_object is None:
        return [False, None]
    else:
        return [True, match_object.group(0)]

def verify(file_content: str, search_pattern: str):
    total_results_count[0] += 1
    print("Processing results #" + str(total_results_count[0]))
    start_index = -1 # initialize
    try:
        start_index = file_content.index(search_pattern)
    except ValueError:
        print("ERROR: search pattern not found in file content")

    if len(file_content[start_index:]) < 100:
        end_index = start_index + len(file_content[start_index:])
    else:
        end_index = start_index + 100

    potential_token = file_content[start_index:end_index]
    [is_token, naughty_token] = check_for_token(potential_token)
    if is_token:
        naughty_count[0] += 1
        tokens.add(naughty_token)

    if (total_results_count[0] % 900) == 0:
        with open("jacksonsResults.txt", "w") as results_file:
            results_file.write("\n-----------------------------------------\n")
            results_file.write("Search pattern: " + SEARCH_PATTERN + "\n")
            results_file.write("This many results have been examined: " + str(total_results_count[0]) + "\n")
            results_file.write("Found this many naughty tokens: " + str(naughty_count[0]) + "\n")
            results_file.write("Unique naughty tokens: " + str(len(tokens)) + "\n")
            for token in tokens:
                results_file.write(token + "\n")
