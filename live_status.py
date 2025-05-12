# live_status.py — Multi-sport + Expanded Soccer Support
import requests

API_KEY = "3"  # Free tier key

LEAGUES = {
    "NBA": "4387",
    "MLB": "4424",
    "NHL": "4380",
    # Soccer
    "Premier League": "4328",
    "La Liga": "4335",
    "Serie A": "4332",
    "Champions League": "4480",
    "Copa Libertadores": "4501",
    "World Cup": "4429"
}

def fetch_live_scores():
    all_games = []

    for league, league_id in LEAGUES.items():
        url = f"https://www.thesportsdb.com/api/v1/json/{API_KEY}/eventspastleague.php?id={league_id}"
        try:
            res = requests.get(url)
            data = res.json()

            for event in data.get("events", []):
                home_score = event.get("intHomeScore")
                away_score = event.get("intAwayScore")
                status = "Final" if home_score is not None and away_score is not None else "Scheduled"

                game = {
                    "league": league,
                    "home_team": event.get("strHomeTeam"),
                    "away_team": event.get("strAwayTeam"),
                    "home_score": home_score,
                    "away_score": away_score,
                    "status": status,
                    "date": event.get("dateEvent"),
                    "time": event.get("strTime")
                }
                all_games.append(game)

        except Exception as e:
            print(f"Error loading {league}: {e}")

    return all_games
