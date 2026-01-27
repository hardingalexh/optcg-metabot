import json


def retrieve_leaders():
    with open("leaders.json", "r") as jsonfile:
        leaders = json.load(jsonfile)
    return leaders


def as_color(token: str) -> list[str] | bool:
    color_map = {
        "u": "blue",
        "y": "yellow",
        "b": "black",
        "g": "green",
        "p": "purple",
        "r": "red",
    }
    token = token.lower()
    if len(token) == 0:
        return False
    if len(token) == 1 and token in color_map.keys():
        ## case 1: single color abbreviation
        return [color_map[token]]
    elif len(token) == 2 and all(char in color_map.keys() for char in token):
        ## case 2: multi color abbreviation
        return [color_map[char] for char in token]
    elif all(char in color_map.values() for char in token.split("/")):
        ## case 3: full color names separated by /
        return token.split("/")
    else:
        return False


def as_leader(token: str) -> list[dict]:
    return [
        leader
        for leader in retrieve_leaders()
        if token.lower() in leader.get("name").lower()
    ]


def as_set(token: str) -> str | bool:
    set_types = ["op", "eb", "prb", "st", "p"]
    token = token.lower().replace("-", "")
    match = False
    for set_type in set_types:
        if token.startswith(set_type):
            number_part = token[len(set_type) :]
            if number_part == "":
                match = set_type.upper()
            elif number_part.isdigit():
                match = f"{set_type.upper()}{int(number_part)}"
        if match:
            break
    return match


def parse_leader(leader):
    leaders = retrieve_leaders()
    leader_tokens = leader.split(" ")
    print(leader_tokens)
    for token in leader_tokens:
        if as_color(token):
            leaders = [
                l
                for l in leaders
                if set(as_color(token)).issubset(set(l.get("color").lower().split("/")))
            ]
        elif as_set(token):
            leaders = [
                l for l in leaders if as_set(token).lower() == l.get("set").lower()
            ]
        elif as_leader(token):
            leaders = [l for l in leaders if token.lower() in l.get("name").lower()]
        else:
            leaders = [l for l in leaders if token.lower() in l.get("card_id").lower()]
    return leaders


def test():
    patterns = [
        "PB Luffy",
        "UP Luffy",
        "OP12 Zoro",
        "Zoro",
        "OP-13 Sabo",
        "Boa",
        "Blue Jinbe",
    ]

    for pattern in patterns:
        result = parse_leader(pattern)
        print(f"Pattern: {pattern}")
        for leader in result:
            print(f"  - {leader['name']} ({leader['card_id']})")
        print()
