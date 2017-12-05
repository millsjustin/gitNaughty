import json


class Stats:
    def __init__(self, load_from_disk=False, file_to_load="stats.json"):
        if load_from_disk:
            with open(file_to_load, "r") as stats_file:
                load_dict = json.load(stats_file)
            self._api_total_count = load_dict["api_total_count"]
            self._api_items_checked = load_dict["api_items_checked"]
            self._files_checked = set(load_dict["files_checked"])
            self._matches_found = load_dict["matches_found"]
            self._valid_keys = load_dict["valid_keys"]
        else:
            self._api_total_count = 0
            self._api_items_checked = 0
            self._files_checked = set()
            self._matches_found = dict()
            self._valid_keys = dict()

    def checking_item(self):
        self._api_items_checked += 1

    def add_to_api_total_count(self, n: int):
        self._api_total_count += n

    def checking_file(self, url: str):
        self._files_checked.add(url)

    def match_found(self, match: str, url: str):
        if match in self._matches_found:
            self._matches_found[match].append(url)
        else:
            self._matches_found[match] = [url]

    def key_found(self, key: str, url: str):
        if key in self._valid_keys:
            self._valid_keys[key].append(url)
        else:
            self._valid_keys[key] = [url]

    def already_checked(self, url: str):
        return url in self._files_checked

    def close(self):
        self.save()

    def save(self, file_to_save="stats.json"):
        save_dict = {
            "api_total_count": self._api_total_count,
            "api_items_checked": self._api_items_checked,
            "files_checked": list(self._files_checked),
            "matches_found": self._matches_found,
            "valid_keys": self._valid_keys
        }
        with open(file_to_save, "w") as stats_file:
            json.dump(save_dict, stats_file)

    def extend(self, other):
        self._api_total_count += other._api_total_count
        self._api_items_checked += other._api_items_checked
        self._files_checked = self._files_checked.union(other._files_checked)

        for match in other._matches_found:
            if match in self._matches_found:
                self._matches_found[match].extend(other._matches_found[match])
            else:
                self._matches_found[match] = other._matches_found[match]

        for key in other._valid_keys:
            if key in self._valid_keys:
                self._valid_keys[key].extend(other._valid_keys[key])
            else:
                self._valid_keys[key] = other._valid_keys[key]

    def __repr__(self):
        return """
        Stats:
        api_total_count: {}
        api_items_checked: {}
        files_checked: {}
        matches_found: {}
        valid_keys: {}
        """.format(
            self._api_total_count,
            self._api_items_checked,
            len(self._files_checked),
            len(self._matches_found),
            len(self._valid_keys)
        )
