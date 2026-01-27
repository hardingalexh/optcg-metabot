import csv
import discord


def load_matchup_data():
    with open("out.csv", "r") as csvfile:
        reader = csv.DictReader(csvfile)
        return list(reader)


def fetch_matchups(leaders: list[dict]) -> list[dict]:
    matchup_data = load_matchup_data()
    matchups = []
    for leader in leaders:
        for opponent in leaders:
            if leader.get("card_id") == opponent.get("leader_id"):
                continue
            print(leader.get("card_id"), opponent.get("leader_id"))
            matchup = next(
                (
                    m
                    for m in matchup_data
                    if m.get("leader_id") == leader.get("card_id")
                    and m.get("opponent_id") == opponent.get("card_id")
                ),
                None,
            )
            if matchup:
                matchups.append(matchup)
    return matchups


def format_matchup_response(matchups: list[dict]) -> str:
    response_lines = []
    for matchup in matchups:
        e = discord.Embed()
        fields = [
            {"name": "Leader", "value": matchup.get("leader"), "inline": True},
            {"name": "Opponent", "value": matchup.get("opponent"), "inline": True},
            {
                "name": "Games Played",
                "value": matchup.get("total_games"),
                "inline": True,
            },
            {
                "name": "First Win %",
                "value": f"{round(matchup.get('first_w_pct'), 2)}% ({matchup.get('first_total_games')} Games)",
                "inline": True,
            },
            {
                "name": "Second Win %",
                "value": f"{round(matchup.get('second_w_pct'), 2)}% ({matchup.get('second_total_games')} Games)",
                "inline": True,
            },
        ]
        for field in fields:
            e.add_field(**field)
        response_lines.append(e)
    return response_lines
