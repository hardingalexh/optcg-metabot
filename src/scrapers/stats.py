import base64
import csv
import gzip
import json

import requests

# URLS = [
#     "https://opbountypck.s3.amazonaws.com/stats/regular/Stats_lw.json",
#     "https://opbountypck.s3.amazonaws.com/stats/regular/Stats_LWW1BillionBounty.json",
#     "https://opbountypck.s3.amazonaws.com/stats/regular/Stats_LWW2BillionBounty.json",
#     "https://opbountypck.s3.amazonaws.com/stats/regular/Stats_lw_eastern.json",
#     ## old stats appear to also exist as exports from previous metas
#     ## for example "https://opbountypck.s3.amazonaws.com/stats/regular/Stats_OP13.json" has the stats for the OP-13 meta
# ]


def get_file(url: str):
    # bas64encoded gzipped json file
    file = requests.get(url)
    contents = file.text
    data = base64.b64decode(contents)
    out = gzip.decompress(data)
    return json.loads(out)


def format_name(obj):
    return f"{obj.get('set')} {obj.get('name')}"


def parse_matchups(data):
    leader_map = map_leaders()
    output = []
    meta_report = []
    for leader in data["leaders_presence"]:
        leader_obj = find_leader(leader, leader_map)
        leader_name = format_name(leader_obj)
        if leader_obj:
            ## data format is a list of leaders, each with a list of subjects
            ## each subject has first and second win/loss counts
            ## these are not keyed, it's referenced by position in the list
            for subject in leader["subject"]:
                subject_obj = find_leader(subject, leader_map)
                subject_name = format_name(subject_obj)
                pos = leader["subject"].index(subject)

                first_wins = leader["subject_first_wins"][pos]
                first_losses = leader["subject_first_losses"][pos]
                first_total_games = first_wins + first_losses
                second_wins = leader["subject_second_wins"][pos]
                second_losses = leader["subject_second_losses"][pos]
                second_total_games = second_wins + second_losses
                first_win_percent = 0
                second_win_percent = 0
                total_win_percent = 0
                if (first_wins + first_losses) > 0:
                    first_win_percent = (first_wins / (first_wins + first_losses)) * 100
                if (second_wins + second_losses) > 0:
                    second_win_percent = (
                        second_wins / (second_wins + second_losses)
                    ) * 100
                if (first_total_games + second_total_games) > 0:
                    total_win_percent = (
                        (first_wins + second_wins)
                        / (first_total_games + second_total_games)
                    ) * 100

                if leader_obj and subject_obj:
                    output.append(
                        {
                            "leader": leader_name,
                            "leader_id": leader_obj.get("card_id"),
                            "opponent": subject_name,
                            "opponent_id": subject_obj.get("card_id"),
                            "total_games": first_total_games + second_total_games,
                            "total_w_pct": total_win_percent,
                            "first_w_pct": first_win_percent,
                            "first_total_games": first_total_games,
                            "second_w_pct": second_win_percent,
                            "second_total_games": second_total_games,
                        }
                    )
            meta_report.append(
                {
                    "leader": leader_name,
                    "leader_id": leader_obj.get("card_id"),
                    "total_games": leader.get("number_of_matches", 0),
                    "wins": leader.get("wins", 0),
                    "losses": leader.get("losses", 0),
                    "total_w_pct": (
                        leader.get("wins", 0) / leader.get("number_of_matches", 0)
                    )
                    * 100
                    if leader.get("number_of_matches", 0) > 0
                    else "N/A",
                }
            )
    return output, meta_report


def map_leaders():
    with open("data/leaders.json", "r") as f:
        lookup = json.load(f)
    return lookup


def find_leader(leader, leaders):
    if type(leader) is not str:
        leader_name = leader.get("leader")
    else:
        leader_name = leader
    if leader_name[1] == "x":
        leader_name = leader_name[2:]
    try:
        leader_obj = next(
            lead for lead in leaders if lead.get("card_id") == leader_name
        )
        return leader_obj
    except Exception:
        # if leader != "Mobile" and type(leader) is not str:
        #     print(f"Invalid Leader card ID: {leader_name}")
        #     print(f"Games Played: {leader.get('number_of_matches')}")
        return {}


def scrape():
    files = {
        "all": "https://opbountypck.s3.amazonaws.com/stats/regular/Stats_lw.json",
        "1b": "https://opbountypck.s3.amazonaws.com/stats/regular/Stats_LWW1BillionBounty.json",
        "2b": "https://opbountypck.s3.amazonaws.com/stats/regular/Stats_LWW2BillionBounty.json",
        "eastern": "https://opbountypck.s3.amazonaws.com/stats/regular/Stats_lw_eastern.json",
        "special": "https://opbountypck.s3.amazonaws.com/stats/regular/Stats_Special_Queue.json",
    }
    for set in range(8, 16):
        set_filled = str(set).zfill(2)
        files[f"OP{set_filled}"] = (
            f"https://opbountypck.s3.amazonaws.com/stats/regular/Stats_OP{set_filled}.json"
        )

    for key, url in files.items():
        data = get_file(url)
        output, meta_report = parse_matchups(data)
        output = sorted(output, key=lambda x: (x["leader"], x["opponent"]))
        meta_report = sorted(meta_report, key=lambda x: x["total_games"], reverse=True)
        with open(f"data/out_{key}.csv", "w") as outfile:
            c = csv.DictWriter(outfile, fieldnames=output[0].keys())
            c.writeheader()
            c.writerows(output)
        with open(f"data/meta_{key}.csv", "w") as outfile:
            c = csv.DictWriter(outfile, fieldnames=meta_report[0].keys())
            c.writeheader()
            c.writerows(meta_report)


if __name__ == "__main__":
    scrape()
