import pandas as pd

from indicators import enrich


def fast_scan(provider, symbols, limit=200):
    rows = []

    for symbol in symbols:

        try:
            df = provider.klines(
                symbol,
                "5m",
                limit
            )

            if len(df) < 50:
                continue

            x = enrich(df)

            last = x.iloc[-1]

            change_1h = float(
                last.close /
                x.close.iloc[-13] - 1
            )

            volume_ratio = (
                float(last.vol_ratio)
                if pd.notna(last.vol_ratio)
                else 0
            )

            atr_pct = (
                float(last.atr / last.close)
                if pd.notna(last.atr)
                else 0
            )

            activity_score = (
                abs(change_1h) * 40
                + max(volume_ratio - 1, 0) * 30
                + atr_pct * 1000
            )

            rows.append({
                "symbol": symbol,
                "change_1h": change_1h,
                "volume_ratio": volume_ratio,
                "atr_pct": atr_pct,
                "activity_score": activity_score
            })

        except Exception:
            continue

    if not rows:
        return pd.DataFrame()

    return (
        pd.DataFrame(rows)
        .sort_values(
            "activity_score",
            ascending=False
        )
    )
