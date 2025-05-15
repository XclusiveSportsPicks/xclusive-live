def calculate_units(confidence, odds):
    """
    Calculates stake size using 50% Kelly Criterion.
    Returns unit size (e.g. 1.2u).
    """
    b = abs(odds) / 100 if odds < 0 else odds / 100
    p = (confidence - 5.0) / 5.0  # Scaled confidence to implied win%
    q = 1 - p

    try:
        kelly_fraction = (b * p - q) / b
        stake_units = max(0.25, round(0.5 * kelly_fraction * 5, 1))  # Cap at reasonable value
    except:
        stake_units = 1.0  # fallback if math fails

    return round(stake_units, 1)
