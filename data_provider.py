import time
import requests
import pandas as pd


class BinanceFuturesProvider:

    def __init__(self, base_url):
        self.base_url = base_url.rstrip("/")

    def exchange_info(self):
        r = requests.get(
            f"{self.base_url}/fapi/v1/exchangeInfo",
            timeout=20
        )
        r.raise_for_status()
        return r.json()

    def usdt_symbols(self):
        info = self.exchange_info()

        return [
            s["symbol"]
            for s in info["symbols"]
            if s.get("status") == "TRADING"
            and s.get("contractType") == "PERPETUAL"
            and s.get("quoteAsset") == "USDT"
        ]

    def klines(
        self,
        symbol,
        interval,
        limit=500,
        end_time=None
    ):
        params = {
            "symbol": symbol,
            "interval": interval,
            "limit": min(limit, 1500)
        }

        if end_time:
            params["endTime"] = end_time

        r = requests.get(
            f"{self.base_url}/fapi/v1/klines",
            params=params,
            timeout=20
        )

        r.raise_for_status()

        cols = [
            "open_time",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "close_time",
            "quote_volume",
            "trades",
            "taker_buy_base",
            "taker_buy_quote",
            "ignore"
        ]

        df = pd.DataFrame(
            r.json(),
            columns=cols
        )

        if df.empty:
            return df

        for c in [
            "open",
            "high",
            "low",
            "close",
            "volume",
            "quote_volume"
        ]:
            df[c] = pd.to_numeric(
                df[c],
                errors="coerce"
            )

        df["open_time"] = pd.to_datetime(
            df["open_time"],
            unit="ms",
            utc=True
        )

        return df.set_index("open_time")

    def history_days(
        self,
        symbol,
        interval,
        days=7
    ):
        frames = []

        end = int(
            time.time() * 1000
        )

        target = days * 24 * 60
        step = 1500

        while target > 0:

            df = self.klines(
                symbol,
                interval,
                step,
                end
            )

            if df.empty:
                break

            frames.append(df)

            end = (
                int(
                    df.index[0].timestamp()
                    * 1000
                )
                - 1
            )

            target -= len(df)

            if len(df) < step:
                break

            time.sleep(0.05)

        if not frames:
            return pd.DataFrame()

        out = pd.concat(frames).sort_index()

        return out[
            ~out.index.duplicated(
                keep="first"
            )
        ]
