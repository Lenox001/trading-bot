import math
import time

class RiskManager:
    def __init__(self, config, connector):
        self.config = config
        self.connector = connector
        self.risk_pct = config['risk_percent'] / 100.0
        self.max_daily_loss_pct = config['max_daily_loss_percent'] / 100.0
        self.min_balance = config['min_balance']
        self.max_open = config['max_open_trades']
        self.max_spread = config['max_spread_pips']
        self.max_slippage = config['max_slippage_pips']
        self.compound = config['compound_mode']
        self.daily_pnl = 0.0
        self.last_trade_time = 0
        self.cooldown = config['cooldown_minutes'] * 60
        self.starting_balance = None

    def update_daily_pnl(self):
        if self.starting_balance is None:
            self.starting_balance = self.connector.get_balance()
        equity = self.connector.get_equity()
        self.daily_pnl = equity - self.starting_balance

    def can_trade(self):
        self.update_daily_pnl()
        if self.daily_pnl < -self.max_daily_loss_pct * self.starting_balance:
            print("Daily max loss reached.")
            return False
        if self.connector.get_equity() < self.min_balance:
            print("Equity below minimum.")
            return False
        if self.connector.get_open_trades_count() >= self.max_open:
            return False
        if time.time() - self.last_trade_time < self.cooldown:
            return False
        return True

    def check_spread(self, symbol):
        """Return True if current spread (in pips) is within the allowed maximum."""
        spread = self.connector.get_spread(symbol)        # integer, in points
        point = self.connector.get_point(symbol)          # point size (e.g. 0.00001)
        if point == 0:
            return False
        # 1 pip = 10 points for 5‑digit brokers, or 10 points for JPY pairs (3 digits)
        spread_pips = spread / 10.0                       # works for all standard brokers
        if spread_pips > self.max_spread:
            print(f"Spread too high: {spread_pips:.1f} pips (max {self.max_spread})")
            return False
        return True

    def calculate_lot_size(self, symbol, sl_pips):
        balance = self.connector.get_balance()
        if self.compound:
            risk_amount = balance * self.risk_pct
        else:
            initial = self.starting_balance if self.starting_balance else balance
            risk_amount = initial * self.risk_pct
        pip_value = self.connector.pip_value(symbol)   # monetary value of 1 pip
        lot = risk_amount / (sl_pips * pip_value)
        min_lot, max_lot, step = self.connector.get_lot_constraints(symbol)
        lot = max(min_lot, min(max_lot, math.floor(lot / step) * step))
        return lot

    def record_trade(self, trade_result):
        self.last_trade_time = time.time()