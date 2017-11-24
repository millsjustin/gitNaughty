total_results_count = [0]
naughty_count = [0]

def verify(file_content: str, search_pattern: str):
    total_results_count[0] += 1
    print("\nResult #" + str(total_results_count[0]))
    try:
        start_index = file_content.index(search_pattern)
        if len(file_content[start_index:]) < 100:
            end_index = start_index + len(file_content[start_index:])
        else:
            end_index = start_index + 100

        print(file_content[start_index:end_index])
    except ValueError:
        print("ERROR: search pattern not found in file content")
