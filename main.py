import argparse
from pathlib import Path

import pandas as pd

from config import Config
from data_provider import BinanceFuturesProvider
from scanner import fast_scan
from backtest import backtest_symbol, performance_report


def main():
    cfg = Config()

    out = Path("data")
    out.mkdir(exist_ok=True)

    parser = argparse.ArgumentParser()

    sub = parser.add_subparsers(
        dest="cmd",
        required=True
    )

    s = sub.add_parser("scan")
    s.add_argument(
        "--top",
        type=int,
        default=20
    )

    b = sub.add_parser("backtest")
    b.add_argument(
        "--symbols",
        default="BTCUSDT,ETHUSDT,SOLUSDT"
    )

    b.add_argument(
        "--days",
        type=int,
        default=7
    )

    b.add_argument(
        "--balance",
        type=float,
        default=1000
    )

    args = parser.parse_args()

    provider = BinanceFuturesProvider(
        cfg.base_url
    )

    if args.cmd == "scan":

        df = fast_scan(
            provider,
            provider.usdt_symbols()
        ).head(args.top)

        df.to_csv(
            out / "scan_results.csv",
            index=False
        )

        print(df.to_string(index=False))
        print(
            "Saved",
            out / "scan_results.csv"
        )

    else:

        initial_balance = args.balance
        balance = initial_balance
        trades = []

        symbols = [
            x.strip().upper()
            for x in args.symbols.split(",")
            if x.strip()
        ]

        for symbol in symbols:

            print()
            print("=" * 50)
            print("Backtesting:", symbol)
            print("=" * 50)

            balance, symbol_trades = backtest_symbol(
                provider,
                symbol,
                args.days,
                balance,
                cfg
            )

            trades.extend(symbol_trades)

            print(
                symbol,
                "equity =",
                round(balance, 2),
                "trades =",
                len(symbol_trades)
            )

        df = pd.DataFrame(trades)

        df.to_csv(
            out / "backtest_trades.csv",
            index=False
        )

        report = performance_report(
            trades,
            initial_balance
        )

        print()
        print("=" * 50)
        print("BACKTEST V1.1 REPORT")
        print("=" * 50)

        print(
            "Initial balance:",
            initial_balance
        )

        print(
            "Final equity:",
            report["final_equity"]
        )

        print(
            "Net PnL:",
            report["net_pnl"]
        )

        print(
            "Return:",
            report["return_pct"],
            "%"
        )

        print(
            "Trades:",
            report["trades"]
        )

        print(
            "Wins:",
            report["wins"]
        )

        print(
            "Losses:",
            report["losses"]
        )

        print(
            "Win rate:",
            report["win_rate"],
            "%"
        )

        print(
            "Profit factor:",
            report["profit_factor"]
        )

        print(
            "Max drawdown:",
            report["max_drawdown_pct"],
            "%"
        )

        print(
            "LONG:",
            report["long_trades"]
        )

        print(
            "SHORT:",
            report["short_trades"]
        )

        print()
        print(
            "Saved:",
            out / "backtest_trades.csv"
        )


if __name__ == "__main__":
    main()
