def generate_reasoning(pitchers, sharp_percent, confidence):
    away = pitchers.get("away_pitcher", "Unknown")
    home = pitchers.get("home_pitcher", "Unknown")

    lines = []

    if "Unknown" not in (away, home):
        lines.append(f"{home} is starting {home} vs {away} — pitching edge favors our side.")
    
    if sharp_percent >= 35:
        lines.append("Heavy sharp money has moved toward this side (Sharp % ≥ 35%).")

    if confidence >= 8.5:
        lines.append("Model confidence is high based on team momentum and matchup factors.")

    return " ".join(lines)
