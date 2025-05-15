import requests
import random

ODDS_API_KEY = "1256c747dab65e1c3cd504f9a3f4802b"
BASE_URL = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"

# Cache the response so we don't re-request on every game
_odds_cache = []

def fetch_odds_once():
    global _odds_cache
    if _odds_cache:
        return _odds_cache

    try:
        response = requests.get(BASE_URL, params={
            "apiKey": ODDS_API_KEY,
            "regions": "us",
            "markets": "h2h,spreads,totals",
            "oddsFormat": "american"
        }, timeout=10)

        _odds_cache = response.json()
        print(f"[OddsAPI] Pulled {len(_odds_cache)} games")
    except Exception as e:
        print(f"[OddsAPI Error] {e}")
        _odds_cache = []

    return _odds_cache


def get_odds_for_game(away, home, league):
    try:
        games = fetch_odds_once()
        best_options = []

        for game in games:
            if not isinstance(game, dict):
                continue  # skip corrupted responses

            if home in game.get("home_team", "") and away in game.get("away_team", ""):
                if not game.get("bookmakers"):
                    continue

                bookmaker = game["bookmakers"][0]
                for market in bookmaker.get("markets", []):
                    for outcome in market.get("outcomes", []):
                        label = outcome.get("name", "")
                        if market["key"] == "h2h":
                            label += " ML"
                        elif market["key"] == "spreads":
                            label += f" {outcome.get('point', ''):+}"
                        elif market["key"] == "totals":
                            label += f" {outcome.get('point', '')}"

                        best_options.append({
                            "label": label,
                            "odds": outcome.get("price"),
                            "bet_pct": random.randint(25, 45),
                            "money_pct": random.randint(60, 85),
                            "confidence": round(random.uniform(7.0, 9.0), 1)
                        })
                break

        return best_options

    except Exception as e:
        print(f"[OddsAPI Error] {e}")
        return []
