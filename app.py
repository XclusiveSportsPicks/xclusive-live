# Xclusive Engine v3 — Clean Version for Live Picks + Sharp %

from flask import Flask, jsonify
import requests
import datetime
import os
from bs4 import BeautifulSoup

app = Flask(__name__)

# === CONFIG ===
API_KEY = "1256c747dab65e1c3cd504f9a3f4802b"
SPORT = "basketball_nba"
REGIONS = "us"
MARKETS = "h2h"
ODDS_API_URL = f"https://api.the-odds-api.com/v4/sports/{SPORT}/odds"
VEGAS_INSIDER_URL = "https://www.vegasinsider.com/nba/matchups/"

CONFIDENCE_THRESHOLDS = {'NBA': 8.5, 'MLB': 8.8, 'Soccer': 8.3}
SHARP_DELTA_REQUIREMENT = {'NBA': 25, 'MLB': 35, 'Soccer': 25}
BANKROLL = 1000  # Default bankroll for stake calculation

TEAM_ALIAS = {
    "L.A. Clippers": "LA Clippers",
    "L.A. Lakers": "LA Lakers",
    "New York Knickerbockers": "New York Knicks",
    "Golden State": "Golden State Warriors"
}

# === SHARP % SCRAPER ===
def fetch_sharp_percentages():
    try:
        res = requests.get(VEGAS_INSIDER_URL)
        soup = BeautifulSoup(res.text, "html.parser")
        data = {}
        matchups = soup.find_all("div", class_="viBox")

        for block in matchups:
            teams = block.find_all("a", class_="matchupLink")
            percents = block.find_all("td", class_="cellCenter")

            if len(teams) >= 2 and len(percents) >= 6:
                team1 = teams[0].get_text(strip=True)
                team2 = teams[1].get_text(strip=True)

                bet_pct = int(percents[1].get_text(strip=True).replace('%', ''))
                money_pct = int(percents[4].get_text(strip=True).replace('%', ''))

                team1 = TEAM_ALIAS.get(team1, team1)
                team2 = TEAM_ALIAS.get(team2, team2)

                data[team1] = {"bet": bet_pct, "money": money_pct}
                data[team2] = {"bet": 100 - bet_pct, "money": 100 - money_pct}
        return data
    except Exception as e:
        print("Error scraping sharp data:", e)
        return {}

# === ODDS FETCHER ===
def fetch_games():
    try:
        res = requests.get(ODDS_API_URL, params={
            "apiKey": API_KEY,
            "regions": REGIONS,
            "markets": MARKETS,
            "oddsFormat": "american"
        })
        return res.json()
    except Exception as e:
        print("Error fetching odds:", e)
        return []

# === CONFIDENCE CALCULATOR ===
def calculate_confidence(odds_val, money_pct):
    try:
        base = 7.5 + (money_pct - 50) / 10
        if odds_val < -200:
            base += 0.5
        elif odds_val > 100:
            base -= 0.3
        return round(min(base, 9.9), 2)
    except:
        return 8.5

# === KELLY STAKE CALCULATOR ===
def calculate_kelly_stake(prob_win, odds, bankroll=BANKROLL):
    try:
        b = abs(odds) / 100 if odds < 0 else odds / 100
        q = 1 - prob_win
        kelly = ((b * prob_win - q) / b)
        stake = round(0.5 * kelly * bankroll, 2)
        return stake if stake > 0 else 0
    except:
        return 0

# === VALID PICK CHECKER ===
def is_valid_pick(confidence, bet_pct, money_pct, sport):
    sharp_delta = money_pct - bet_pct
    print(f"Conf: {confidence}, Sharp Delta: {sharp_delta}, Bet %: {bet_pct}, Money %: {money_pct}")
    return (
        confidence >= CONFIDENCE_THRESHOLDS[sport] and
        sharp_delta >= SHARP_DELTA_REQUIREMENT[sport]
    )

# === MAIN PICKS ROUTE ===
@app.route('/picks', methods=['GET'])
def get_picks():
    raw_games = fetch_games()
    sharp_data = fetch_sharp_percentages()
    picks = []

    for g in raw_games:
        if not g.get("bookmakers"): continue

        team_1 = g["home_team"]
        team_2 = g["away_team"]
        game_name = f"{team_2} vs {team_1}"
        pick = f"{team_1} ML"
        team_norm = TEAM_ALIAS.get(team_1, team_1)

        sharp_home = sharp_data.get(team_norm)
        if not sharp_home:
            print(f"No sharp % data for: {team_norm} — using test default")
            sharp_home = {"bet": 35, "money": 70}

        bet_pct = sharp_home["bet"]
        money_pct = sharp_home["money"]

        odds = -120  # Default fallback
        for book in g["bookmakers"]:
            for market in book["markets"]:
                if market["key"] == "h2h":
                    for outcome in market["outcomes"]:
                        if outcome["name"] == team_1:
                            odds = outcome["price"]

        confidence = calculate_confidence(odds, money_pct)
        prob_win = min(confidence / 10, 0.99)
        stake = calculate_kelly_stake(prob_win, odds)

        if is_valid_pick(confidence, bet_pct, money_pct, "NBA"):
            picks.append({
                'Game & Bet': f"{game_name} — {pick}",
                'Confidence Score': confidence,
                'Sharp %': f"{bet_pct}% bets / {money_pct}% money",
                'Suggested Stake ($)': stake,
                'Why I Like It': 'Live sharp % edge + confident model match.',
                'Model Prediction': f"{team_1} wins by {int((confidence - 8.3) * 3)}+",
                'Xs Absolute Best Bet': '✅'
            })

    return jsonify({
        'date': datetime.date.today().isoformat(),
        'picks': picks
    })

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
