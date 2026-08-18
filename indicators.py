import numpy as np
import pandas as pd


def atr(df, n=14):
    prev = df["close"].shift(1)

    tr = pd.concat(
        [
            df["high"] - df["low"],
            (df["high"] - prev).abs(),
            (df["low"] - prev).abs(),
        ],
        axis=1,
    ).max(axis=1)

    return tr.rolling(n).mean()


def rsi(df, n=14):
    d = df["close"].diff()

    gain = d.clip(lower=0).rolling(n).mean()
    loss = (-d.clip(upper=0)).rolling(n).mean()

    rs = gain / loss.replace(0, np.nan)

    return 100 - 100 / (1 + rs)


def enrich(df):
    x = df.copy()

    x["atr"] = atr(x)
    x["rsi"] = rsi(x)

    x["vol_ma20"] = x["volume"].rolling(20).mean()
    x["vol_ratio"] = x["volume"] / x["vol_ma20"]

    return x
