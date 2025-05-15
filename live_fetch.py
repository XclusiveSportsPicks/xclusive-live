import requests
from datetime import datetime
import pytz
from odds_fetch import get_odds_for_game
from ml_models import mlb_confidence
from mlb_pitchers import get_pitchers_for_game
from stake_calc import calculate_units
from why_i_like_it import generate_reasoning

TARGET_TZ = pytz.timezone("US/Eastern")

def fetch_espn_games():
    all_games = []
    today = datetime.now(TARGET_TZ).date()
    league_name = "MLB"

    url = f'https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard'
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        events = data.get('events', [])

        print(f"[{league_name}] Games found: {len(events)}")

        for event in events:
            comp = event['competitions'][0]
            game_time = datetime.fromisoformat(comp['date'].replace('Z', '+00:00')).astimezone(TARGET_TZ)
            if game_time.date() != today:
                continue

            teams = comp['competitors']
            home = next(t['team']['displayName'] for t in teams if t['homeAway'] == 'home')
            away = next(t['team']['displayName'] for t in teams if t['homeAway'] == 'away')
            game = f"{away} vs {home}"
            status = event['status']['type']['description']
            is_final = event['status']['type']['name'] == 'STATUS_FINAL'

            odds_data = get_odds_for_game(away, home, league_name)
            if not odds_data:
                continue

            best = odds_data[0]
            sharp_percent = best['money_pct'] - best['bet_pct']
            if best['confidence'] < 7.5 or sharp_percent < 30:
                continue

            pitchers = get_pitchers_for_game(away, home)
            pitcher_diff = 0.0
            if "ERA" in pitchers['home_pitcher'] and "ERA" in pitchers['away_pitcher']:
                try:
                    home_era = float(pitchers['home_pitcher'].split("(")[-1].split("ERA")[0].strip())
                    away_era = float(pitchers['away_pitcher'].split("(")[-1].split("ERA")[0].strip())
                    pitcher_diff = away_era - home_era
                except:
                    pitcher_diff = 0.0

            confidence = mlb_confidence.predict_confidence(away, home, pitcher_diff)
            stake_units = calculate_units(confidence, best['odds'])
            reasoning = generate_reasoning(pitchers, sharp_percent, confidence)

            all_games.append({
                'game': game,
                'league': league_name,
                'pick': best['label'],
                'odds': best['odds'],
                'confidence': confidence,
                'sharp_percent': sharp_percent,
                'stake_units': stake_units,
                'status': status,
                'result': best.get('result', 'Win') if is_final else None,
                'away_pitcher': pitchers['away_pitcher'],
                'home_pitcher': pitchers['home_pitcher'],
                'why_i_like_it': reasoning
            })

    except Exception as e:
        print(f"[ESPN Fetch Error] {e}")

    all_games.sort(key=lambda x: x['confidence'], reverse=True)
    return all_games
