import json
import glob
import time
import statsClass
import justinsVerification
import collections
import pprint

_total_stats_file = "total_stats.json"


def combine_total_stats():
    total_stats = statsClass.Stats()

    for f in glob.glob("stats-*.json"):
        print(f"getting stats from: {f}")
        s = statsClass.Stats(load_from_disk=True, file_to_load=f)
        total_stats.extend(s)

    print(total_stats)
    return total_stats


def load_total_stats():
    return statsClass.Stats(load_from_disk=True, file_to_load=_total_stats_file)


def save_total_stats(total_stats: statsClass):
    total_stats.save(_total_stats_file)


def display_number_unique_urls(total_stats):
    num_uses = set()
    for urls in total_stats._valid_keys.values():
        for url in urls:
            num_uses.add(url)

    print(len(num_uses))
    num_uses = set()
    for urls in total_stats._matches_found.values():
        for url in urls:
            num_uses.add(url)
    print(len(num_uses))


def display_key_size_counts(total_stats):
    key_lens = collections.defaultdict(int)

    for key_str in total_stats._valid_keys:
        key = justinsVerification.get_key_from_bytes(key_str.encode())
        key_lens[key.key_size] += 1

    pprint.pprint(sorted(key_lens.items(), key=lambda p: p[1], reverse=True))


def display_unique_rsa_numbers(total_stats):
    print(f"unique keys: {len(total_stats._valid_keys)}")

    # public
    e = set()
    n = set()
    # private
    p = set()
    q = set()
    d = set()

    for key_str in total_stats._valid_keys.keys():
        key = justinsVerification.get_key_from_bytes(key_str.encode())
        pri_nums = key.private_numbers()
        p.add(pri_nums.p)
        q.add(pri_nums.q)
        d.add(pri_nums.d)
        e.add(pri_nums.public_numbers.e)
        n.add(pri_nums.public_numbers.n)

    print(f"e: {len(e)}")
    print(f"n: {len(n)}")
    print(f"p: {len(p)}")
    print(f"q: {len(q)}")
    print(f"d: {len(d)}")



def main():
    total_stats = load_total_stats()
    print(total_stats)


if __name__ == "__main__":
    main()

