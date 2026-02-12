import csv
import discord


def load_matchup_data(prefix: str = "all") -> list[dict]:
    with open(f"out_{prefix}.csv", "r") as csvfile:
        reader = csv.DictReader(csvfile)
        return list(reader)


def fetch_matchups(
    leaders: list[dict], opponents: list[dict] = [], prefix: str = "all"
) -> list[dict]:
    matchup_data = load_matchup_data(prefix)
    matchups = []
    if len(opponents) == 0:
        matchups = [
            m
            for m in matchup_data
            if any(m.get("leader_id") == leader.get("card_id") for leader in leaders)
        ]
        matchups.sort(key=lambda x: int(x.get("total_games")), reverse=True)
        matchups = matchups[0:9]
    else:
        for leader in leaders:
            for opponent in opponents:
                if leader.get("card_id") == opponent.get("leader_id"):
                    continue
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


def round_float(value: str) -> float:
    try:
        return round(float(value), 2)
    except (ValueError, TypeError):
        return 0.0


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
                "name": "Going First Win %",
                "value": f"{round_float(matchup.get('first_w_pct'))}% ({matchup.get('first_total_games')} Games)",
                "inline": True,
            },
            {
                "name": "Going Second Win %",
                "value": f"{round_float(matchup.get('second_w_pct'))}% ({matchup.get('second_total_games')} Games)",
                "inline": True,
            },
        ]
        for field in fields:
            e.add_field(**field)
        response_lines.append(e)
    return response_lines
