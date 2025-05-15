from flask import Flask, jsonify, render_template, send_file, request
from flask_caching import Cache
import pdfkit
from datetime import datetime
import pytz
from XclusiveApp.live_fetch import get_all_live_games

app = Flask(__name__)
cache = Cache(app, config={'CACHE_TYPE': 'simple'})

# --- Config ---
AUTO_REFRESH_MINUTES = 10
TARGET_TZ = pytz.timezone("US/Eastern")

# --- League Alias Mapping ---
LEAGUE_ALIASES = {
    'EPL': 'Soccer',
    'La Liga': 'Soccer',
    'Serie A': 'Soccer',
    'Bundesliga': 'Soccer',
    'Ligue 1': 'Soccer',
    'MLS': 'Soccer',
    'UCL': 'Soccer',
    'UEL': 'Soccer',
    'NBA': 'NBA',
    'MLB': 'MLB',
    'NHL': 'NHL',
    'UFC': 'UFC',
}

# --- Per-Sport Thresholds ---
SPORT_THRESHOLDS = {
    'NBA': {'confidence': 7.5, 'sharp': 30},
    'MLB': {'confidence': 7.0, 'sharp': 25},
    'NHL': {'confidence': 7.0, 'sharp': 25},
    'Soccer': {'confidence': 7.5, 'sharp': 30},
    'UFC': {'confidence': 8.0, 'sharp': 35},
}

# --- Utility ---
def calculate_sharp_percent(bet_pct, money_pct):
    return round(money_pct - bet_pct)

# --- Core Fetch & Filter Logic ---
def fetch_picks():
    today = datetime.now(TARGET_TZ).date()
    picks = []

    for item in get_all_live_games():
        try:
            raw_league = item['league']
            normalized_league = LEAGUE_ALIASES.get(raw_league)
            if not normalized_league:
                continue

            game_time = datetime.fromisoformat(item['match_time']).astimezone(TARGET_TZ)
            if game_time.date() != today:
                continue

            sharp_delta = calculate_sharp_percent(item['bet_pct'], item['money_pct'])
            thresholds = SPORT_THRESHOLDS[normalized_league]

            if sharp_delta >= thresholds['sharp'] and item['confidence'] >= thresholds['confidence']:
                picks.append({
                    'game': item['game'],
                    'league': raw_league,  # Show original label on frontend
                    'pick': item['bet'],
                    'odds': item['odds'],
                    'confidence': item['confidence'],
                    'sharp_percent': sharp_delta,
                    'status': item['status'],
                    'result': item.get('final_result', ''),
                    'match_time': game_time.strftime('%I:%M %p')
                })
        except Exception as e:
            print(f"[Error] {e} for item: {item}")

    picks = sorted(picks, key=lambda x: x['confidence'], reverse=True)
    return picks

# --- Routes ---
@app.route('/')
def home():
    league_filter = request.args.get('league')
    picks = fetch_picks()
    if league_filter:
        picks = [p for p in picks if p['league'].lower() == league_filter.lower()]
    return render_template('index.html', picks=picks, now=datetime.now(TARGET_TZ), league_filter=league_filter)

@app.route('/api/auto-picks')
@cache.cached(timeout=AUTO_REFRESH_MINUTES * 60, key_prefix='auto_picks')
def api_auto_picks():
    return jsonify({'picks': fetch_picks(), 'updated': datetime.now(TARGET_TZ).isoformat()})

@app.route('/export/pdf')
def export_pdf():
    picks = fetch_picks()
    rendered = render_template('pdf_template.html', picks=picks, now=datetime.now(TARGET_TZ))
    pdf_path = 'xclusive_daily_picks.pdf'
    config = pdfkit.configuration(wkhtmltopdf='/usr/bin/wkhtmltopdf')  # Adjust path if needed
    pdfkit.from_string(rendered, pdf_path, configuration=config)
    return send_file(pdf_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
