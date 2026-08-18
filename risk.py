def position_size(balance, risk_pct, entry, stop):
    distance = abs(entry - stop)

    if distance <= 0:
        return 0.0

    risk_amount = balance * risk_pct

    return risk_amount / distance
