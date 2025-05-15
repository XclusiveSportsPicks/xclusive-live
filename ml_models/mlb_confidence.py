import requests
from bs4 import BeautifulSoup

def fetch_team_stats(team_name):
    try:
        url = 'https://www.espn.com/mlb/standings'
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        team_rows = soup.select('table tbody tr')

        for row in team_rows:
            cells = row.find_all('td')
            if not cells or len(cells) < 10:
                continue

            name = cells[0].text.strip()
            if team_name.lower() in name.lower():
                wins = int(cells[1].text.strip())
                losses = int(cells[2].text.strip())
                runs_for = int(cells[8].text.strip())
                runs_against = int(cells[9].text.strip())
                win_pct = wins / (wins + losses)
                run_diff = runs_for - runs_against
                return win_pct, run_diff

    except Exception as e:
        print(f"[Stat Fetch Error] {e}")

    return 0.5, 0

def predict_confidence(away_team, home_team, pitcher_diff=0.0):
    home_win_pct, home_diff = fetch_team_stats(home_team)
    away_win_pct, away_diff = fetch_team_stats(away_team)
    edge = (home_win_pct - away_win_pct) + ((home_diff - away_diff) / 100) + (pitcher_diff / 10)
    base = 8.0 + edge * 3.5
    return max(7.0, min(round(base, 1), 9.8))
