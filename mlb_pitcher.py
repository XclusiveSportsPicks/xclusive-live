import requests
from bs4 import BeautifulSoup

def get_pitchers_for_game(away_team, home_team):
    url = "https://www.espn.com/mlb/probablepitchers"
    try:
        resp = requests.get(url, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        table = soup.find('table')
        rows = table.find_all('tr') if table else []

        for row in rows:
            cells = row.find_all('td')
            if len(cells) < 4:
                continue

            teams = cells[0].text.strip().split(" at ")
            if len(teams) != 2:
                continue

            away, home = teams
            if away_team.lower() in away.lower() and home_team.lower() in home.lower():
                away_pitcher = cells[1].text.strip()
                home_pitcher = cells[2].text.strip()
                return {
                    "away_pitcher": away_pitcher,
                    "home_pitcher": home_pitcher
                }

    except Exception as e:
        print(f"[Pitcher Scrape Error] {e}")

    return {
        "away_pitcher": "Unknown",
        "home_pitcher": "Unknown"
    }
