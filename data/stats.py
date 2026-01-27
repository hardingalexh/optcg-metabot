import base64
import csv
import json
import gzip

import requests

# URLS = [
#     "https://opbountypck.s3.amazonaws.com/stats/regular/Stats_lw.json",
#     "https://opbountypck.s3.amazonaws.com/stats/regular/Stats_LWW1BillionBounty.json",
#     "https://opbountypck.s3.amazonaws.com/stats/regular/Stats_LWW2BillionBounty.json",
#     "https://opbountypck.s3.amazonaws.com/stats/regular/Stats_lw_eastern.json",
#     ## old stats appear to also exist as exports from previous metas
#     ## for example "https://opbountypck.s3.amazonaws.com/stats/regular/Stats_OP13.json" has the stats for the OP-13 meta
# ]


def get_file():
    # bas64encoded gzipped json file
    url = "https://opbountypck.s3.amazonaws.com/stats/regular/Stats_lw.json"
    file = requests.get(url)
    contents = file.text
    data = base64.b64decode(contents)
    out = gzip.decompress(data)
    return json.loads(out)


def parse_matchups(data):
    leader_map = map_leaders()
    output = []
    for leader in data["leaders_presence"]:
        ## data format is a list of leaders, each with a list of subjects
        ## each subject has first and second win/loss counts
        ## these are not keyed, it's referenced by position in the list
        for subject in leader["subject"]:
            pos = leader["subject"].index(subject)
            first_wins = leader["subject_first_wins"][pos]
            first_losses = leader["subject_first_losses"][pos]
            first_total_games = first_wins + first_losses
            second_wins = leader["subject_second_wins"][pos]
            second_losses = leader["subject_second_losses"][pos]
            second_total_games = second_wins + second_losses
            first_win_percent = "N/A"
            second_win_percent = "N/A"
            if first_wins and first_losses:
                first_win_percent = (first_wins / (first_wins + first_losses)) * 100
            if second_wins and second_losses:
                second_win_percent = (second_wins / (second_wins + second_losses)) * 100

            leader_obj = find_leader(leader["leader"], leader_map)
            subject_obj = find_leader(subject, leader_map)

            def format_name(obj):
                return f"{obj.get('set')} {obj.get('name')}"

            leader_name = format_name(leader_obj)
            subject_name = format_name(subject_obj)
            output.append(
                {
                    "leader": leader_name,
                    "leader_id": leader_obj.get("card_id"),
                    "opponent": subject_name,
                    "opponent_id": subject_obj.get("card_id"),
                    "total_games": first_total_games + second_total_games,
                    "first_w_pct": first_win_percent,
                    "first_total_games": first_total_games,
                    "second_w_pct": second_win_percent,
                    "second_total_games": second_total_games,
                }
            )
    return output


def map_leaders():
    with open("leaders.json", "r") as f:
        lookup = json.load(f)
    return lookup


def find_leader(leader, leaders):
    leader = leader.replace("1x", "")
    try:
        leader_obj = next(lead for lead in leaders if lead.get("card_id") == leader)
        return leader_obj
    except Exception:
        return {}


def scrape():
    data = get_file()
    output = parse_matchups(data)
    output = sorted(output, key=lambda x: (x["leader"], x["opponent"]))
    with open("out.csv", "w") as outfile:
        c = csv.DictWriter(outfile, fieldnames=output[0].keys())
        c.writeheader()
        c.writerows(output)
