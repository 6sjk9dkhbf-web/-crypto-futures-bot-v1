from dataclasses import dataclass


@dataclass
class Config:
    base_url: str = "https://fapi.binance.com"
    initial_balance: float = 1000.0
    risk_per_trade: float = 0.005
    max_open_risk: float = 0.03
    min_score: float = 85.0
    min_rr: float = 2.0
    swing_length: int = 3
    volume_window: int = 20
    atr_window: int = 14
    fee_rate: float = 0.0005
