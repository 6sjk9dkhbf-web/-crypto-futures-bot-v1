import numpy as np
from dataclasses import dataclass

from indicators import enrich


@dataclass
class Signal:
    side: str
    score: float
    entry: float
    stop: float
    tp1: float
    tp2: float
    rr: float
    reason: str


def swings(df, n=3):
    hi = df["high"].rolling(
        2 * n + 1,
        center=True
    ).max()

    lo = df["low"].rolling(
        2 * n + 1,
        center=True
    ).min()

    return (
        df["high"].where(df["high"] == hi),
        df["low"].where(df["low"] == lo)
    )


def features(df, n=3):
    sh, sl = swings(df, n)

    rsh = sh.ffill().shift(1)
    rsl = sl.ffill().shift(1)

    bull_bos = (
        df["close"] > rsh
    ).fillna(False)

    bear_bos = (
        df["close"] < rsl
    ).fillna(False)

    sweep_low = (
        (df["low"] < rsl)
        & (df["close"] > rsl)
    ).fillna(False)

    sweep_high = (
        (df["high"] > rsh)
        & (df["close"] < rsh)
    ).fillna(False)

    return (
        rsh,
        rsl,
        bull_bos,
        bear_bos,
        sweep_low,
        sweep_high
    )


def trend(df):
    fast = df["close"].rolling(20).mean()
    slow = df["close"].rolling(50).mean()

    return np.where(
        fast > slow,
        1,
        np.where(
            fast < slow,
            -1,
            0
        )
    )


def make_signal(
    df5,
    df15,
    df1h,
    min_score=85,
    min_rr=2,
    swing_length=3
):
    if min(
        len(df5),
        len(df15),
        len(df1h)
    ) < 80:
        return None

    a = enrich(df5)
    b = enrich(df15)
    c = enrich(df1h)

    i = len(a) - 1
    row = a.iloc[i]

    atr = (
        float(row.atr)
        if np.isfinite(row.atr)
        else 0
    )

    if atr <= 0:
        return None

    (
        rsh,
        rsl,
        bull,
        bear,
        sweep_l,
        sweep_h
    ) = features(
        a,
        swing_length
    )

    t15 = int(trend(b)[-1])
    t1h = int(trend(c)[-1])

    resistance = (
        float(rsh.iloc[i])
        if np.isfinite(rsh.iloc[i])
        else None
    )

    support = (
        float(rsl.iloc[i])
        if np.isfinite(rsl.iloc[i])
        else None
    )

    vr = (
        float(row.vol_ratio)
        if np.isfinite(row.vol_ratio)
        else 0
    )

    rv = (
        float(row.rsi)
        if np.isfinite(row.rsi)
        else 50
    )

    ls = 0
    ss = 0

    # 1H trend
    if t1h > 0:
        ls += 15

    if t1h < 0:
        ss += 15

    # 15M trend
    if t15 > 0:
        ls += 15

    if t15 < 0:
        ss += 15

    # RSI
    if rv > 52:
        ls += 10

    if rv < 48:
        ss += 10

    # Volume
    if vr >= 1.5:
        ls += 5
        ss += 5

    elif vr >= 1.2:
        ls += 3
        ss += 3

    # BOS
    if bull.iloc[i]:
        ls += 15

    if bear.iloc[i]:
        ss += 15

    # Sweep
    if sweep_l.iloc[i]:
        ls += 15

    if sweep_h.iloc[i]:
        ss += 15

    # Structure
    if resistance and row.close >= resistance:
        ls += 10

    if support and row.close <= support:
        ss += 10

    # Short-term momentum
    if i >= 3:

        ch = (
            row.close
            / a.close.iloc[i - 3]
            - 1
        )

        if ch > 0:
            ls += 5

        if ch < 0:
            ss += 5

    side = (
        "LONG"
        if ls >= ss
        else "SHORT"
    )

    score = max(ls, ss)

    if score < min_score:
        return None

    # Trend confirmation
    if side == "LONG" and not (
        t1h > 0 and t15 >= 0
    ):
        return None

    if side == "SHORT" and not (
        t1h < 0 and t15 <= 0
    ):
        return None

    entry = float(row.close)

    # LONG
    if side == "LONG":

        stop = min(
            float(row.low),
            support
            if support
            else float(row.low)
        ) - 0.2 * atr

        risk = entry - stop

        if risk <= 0:
            return None

        tp1 = entry * 1.03

        tp2 = entry + max(
            2 * risk,
            entry * 0.03
        )

    # SHORT
    else:

        stop = max(
            float(row.high),
            resistance
            if resistance
            else float(row.high)
        ) + 0.2 * atr

        risk = stop - entry

        if risk <= 0:
            return None

        tp1 = entry * 0.97

        tp2 = entry - max(
            2 * risk,
            entry * 0.03
        )

    rr = abs(
        tp2 - entry
    ) / risk

    if rr < min_rr:
        return None

    reason = (
        f"{side}: "
        f"score={score:.1f}, "
        f"1H={t1h}, "
        f"15M={t15}, "
        f"vol={vr:.2f}, "
        f"RSI={rv:.1f}"
    )

    return Signal(
        side=side,
        score=score,
        entry=entry,
        stop=stop,
        tp1=tp1,
        tp2=tp2,
        rr=rr,
        reason=reason
    )
