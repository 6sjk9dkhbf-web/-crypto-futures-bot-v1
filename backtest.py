import pandas as pd
from strategy import make_signal
from risk import position_size
def backtest_symbol(provider, symbol, days, balance, cfg):
    d5 = provider.history_days(symbol, "5m", days)
    d15 = provider.history_days(symbol, "15m", days)
    d1h = provider.history_days(symbol, "1h", days)
    if min(len(d5), len(d15), len(d1h)) < 100:
        return balance, []
    trades = []
    equity = float(balance)
    cooldown = 0
    for i in range(80, len(d5) - 1):
        if cooldown > 0:
            cooldown -= 1
            continue
        ts = d5.index[i]
        sig = make_signal(
            d5.iloc[:i + 1],
            d15.loc[:ts],
            d1h.loc[:ts],
            cfg.min_score,
            cfg.min_rr,
            cfg.swing_length
        )
        if not sig:
            continue
        qty = position_size(
            equity,
            cfg.risk_per_trade,
            sig.entry,
            sig.stop
        )
        if qty <= 0:
            continue
        result = None
        exit_price = None
        exit_time = None
        for j in range(i + 1, len(d5)):
            bar = d5.iloc[j]
            if sig.side == "LONG":
                stop_hit = bar.low <= sig.stop
                tp_hit = bar.high >= sig.tp2
                if stop_hit and tp_hit:
                    result = "LOSS"
                    exit_price = sig.stop
                elif stop_hit:
                    result = "LOSS"
                    exit_price = sig.stop
                elif tp_hit:
                    result = "WIN"
                    exit_price = sig.tp2
            else:
                stop_hit = bar.high >= sig.stop
                tp_hit = bar.low <= sig.tp2
                if stop_hit and tp_hit:
                    result = "LOSS"
                    exit_price = sig.stop
                elif stop_hit:
                    result = "LOSS"
                    exit_price = sig.stop
                elif tp_hit:
                    result = "WIN"
                    exit_price = sig.tp2
            if result:
                exit_time = d5.index[j]
                break
        if result is None:
            continue
        if sig.side == "LONG":
            gross = (
                exit_price - sig.entry
            ) * qty
        else:
            gross = (
                sig.entry - exit_price
            ) * qty
        fees = (
            (sig.entry * qty)
            + (exit_price * qty)
        ) * cfg.fee_rate
        pnl = gross - fees
        equity += pnl
        trades.append({
            "symbol": symbol,
            "time": ts.isoformat(),
            "side": sig.side,
            "score": round(sig.score, 2),
            "entry": round(sig.entry, 8),
            "stop": round(sig.stop, 8),
            "tp1": round(sig.tp1, 8),
            "tp2": round(sig.tp2, 8),
            "rr": round(sig.rr, 2),
            "qty": round(qty, 8),
            "gross_pnl": round(gross, 6),
            "fees": round(fees, 6),
            "pnl": round(pnl, 6),
            "equity": round(equity, 6),
            "result": result,
            "exit_time": exit_time.isoformat(),
            "reason": sig.reason
        })
        cooldown = 3
    return equity, trades
def performance_report(trades, initial_balance):
    if not trades:
        return {
            "trades": 0,
            "wins": 0,
            "losses": 0,
            "win_rate": 0,
            "net_pnl": 0,
            "final_equity": initial_balance,
            "return_pct": 0,
            "max_drawdown_pct": 0,
            "profit_factor": 0,
            "long_trades": 0,
            "short_trades": 0,
        }
    df = pd.DataFrame(trades)
    wins = df[
        df["result"] == "WIN"
    ]
    losses = df[
        df["result"] == "LOSS"
    ]
    total_trades = len(df)
    win_count = len(wins)
    loss_count = len(losses)
    win_rate = (
        win_count / total_trades * 100
        if total_trades
        else 0
    )
    net_pnl = float(
        df["pnl"].sum()
    )
    final_equity = float(
        df["equity"].iloc[-1]
    )
    return_pct = (
        (final_equity - initial_balance)
        / initial_balance
        * 100
    )
    equity_curve = pd.Series(
        [initial_balance]
        + df["equity"].tolist()
    )
    running_max = (
        equity_curve.cummax()
    )
    drawdown = (
        (equity_curve - running_max)
        / running_max
        * 100
    )
    max_drawdown_pct = abs(
        float(drawdown.min())
    )
    gross_profit = (
        float(wins["pnl"].sum())
        if len(wins)
        else 0
    )
    gross_loss = abs(
        float(losses["pnl"].sum())
    ) if len(losses) else 0
    if gross_loss > 0:
        profit_factor = (
            gross_profit / gross_loss
        )
    else:
        profit_factor = (
            float("inf")
            if gross_profit > 0
            else 0
        )
    long_trades = int(
        (df["side"] == "LONG").sum()
    )
    short_trades = int(
        (df["side"] == "SHORT").sum()
    )
    return {
        "trades": total_trades,
        "wins": win_count,
        "losses": loss_count,
        "win_rate": round(
            win_rate,
            2
        ),
        "net_pnl": round(
            net_pnl,
            2
        ),
        "final_equity": round(
            final_equity,
            2
        ),
        "return_pct": round(
            return_pct,
            2
        ),
        "max_drawdown_pct": round(
            max_drawdown_pct,
            2
        ),
        "profit_factor": (
            round(
                profit_factor,
                2
            )
            if profit_factor != float("inf")
            else "inf"
        ),
        "long_trades": long_trades,
        "short_trades": short_trades,
    }
