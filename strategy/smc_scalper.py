import pandas as pd
import numpy as np
from strategy.indicators import atr
import logging

class SMC_Scalper:
    def __init__(self, config):
        self.logger = logging.getLogger('SMC_Scalper')
        # Config – all keys from config.yaml
        self.ob_min_body = config['smc']['ob_min_body_pips']
        self.ob_max_wick_pct = config['smc']['ob_max_wick_pct'] / 100.0
        self.retrace_pct = config['smc']['ob_retracement_pct'] / 100.0
        self.use_breaker = config['smc']['breaker_block']
        self.trigger_disp = config['smc']['entry_trigger_displacement_pips']
        self.min_rr = config['smc']['min_rr']
        self.max_sl_pips = config['smc']['max_sl_pips']
        self.tp_pips = config['smc']['take_profit_pips']
        self.min_atr = config['smc']['min_atr_pips']
        self.use_mtf = config['smc']['use_mtf']

        self.pip_func = None  # set per symbol

    def set_pip_size(self, symbol):
        """Return pip size for the given symbol."""
        if 'JPY' in symbol:
            return 0.01
        elif 'BTC' in symbol or 'ETH' in symbol:
            return 0.01
        else:
            return 0.0001

    def _pip(self):
        return self.pip_func()

    def _candle_body(self, c):
        return abs(c['close'] - c['open'])

    def _candle_range(self, c):
        return c['high'] - c['low']

    def _is_bullish(self, c):
        return c['close'] > c['open']

    def _is_bearish(self, c):
        return c['close'] < c['open']

    def _upper_wick_pct(self, c):
        body_high = max(c['open'], c['close'])
        return (c['high'] - body_high) / self._candle_range(c) if self._candle_range(c) > 0 else 0

    def _lower_wick_pct(self, c):
        body_low = min(c['open'], c['close'])
        return (body_low - c['low']) / self._candle_range(c) if self._candle_range(c) > 0 else 0

    def find_order_blocks(self, df):
        obs = []
        for i in range(len(df)-3, 2, -1):
            c = df.iloc[i]
            # Bullish OB: large bearish candle acting as support
            if self._is_bearish(c) and self._candle_body(c) >= self.ob_min_body * self._pip():
                if self._upper_wick_pct(c) <= self.ob_max_wick_pct:
                    obs.append({
                        'type': 'bullish',
                        'high': c['high'],
                        'low': c['low'],
                        'sl': c['low'] - self._pip()
                    })
            # Bearish OB: large bullish candle acting as resistance
            if self._is_bullish(c) and self._candle_body(c) >= self.ob_min_body * self._pip():
                if self._lower_wick_pct(c) <= self.ob_max_wick_pct:
                    obs.append({
                        'type': 'bearish',
                        'high': c['high'],
                        'low': c['low'],
                        'sl': c['high'] + self._pip()
                    })
        return obs

    def check_bias(self, df_bias):
        if len(df_bias) < 5:
            return 'neutral'
        highs = df_bias['high'].values
        lows = df_bias['low'].values
        recent_low = min(lows[-5:])
        recent_high = max(highs[-5:])
        earlier_low = min(lows[-10:-5])
        earlier_high = max(highs[-10:-5])

        if recent_low > earlier_low and recent_high > earlier_high:
            return 'bullish'
        elif recent_low < earlier_low and recent_high < earlier_high:
            return 'bearish'
        else:
            if df_bias.iloc[-1]['close'] > df_bias.iloc[-2]['close']:
                return 'bullish'
            else:
                return 'bearish'

    def generate_signal(self, df_bias, df_entry, symbol):
        if df_entry is None or len(df_entry) < 20:
            return None

        self.pip_func = lambda: self.set_pip_size(symbol)
        pip = self._pip()

        # ------------------------------------------------------------
        # 1. Multi‑timeframe bias (logged at INFO level)
        # ------------------------------------------------------------
        bias = 'neutral'
        if self.use_mtf and df_bias is not None:
            bias = self.check_bias(df_bias)
            self.logger.info(f"Bias for {symbol}: {bias}")

        # ------------------------------------------------------------
        # 2. Find order blocks (logged at INFO level)
        # ------------------------------------------------------------
        if self.use_mtf and df_bias is not None:
            obs = self.find_order_blocks(df_bias)
        else:
            obs = self.find_order_blocks(df_entry)

        if not obs:
            self.logger.info(f"No order blocks found for {symbol} (bias: {bias})")
            return None
        else:
            self.logger.info(f"Found {len(obs)} order block(s) for {symbol} (bias: {bias})")

        # ------------------------------------------------------------
        # 3. ATR / Liquidity filter (logged at INFO level if rejected)
        # ------------------------------------------------------------
        atr_val = atr(df_entry, 14).iloc[-1]
        if atr_val < self.min_atr * pip:
            self.logger.info(f"ATR too low for {symbol}: {atr_val/pip:.1f} pips -- signal skipped")
            return None

        # ------------------------------------------------------------
        # 4. Check entry conditions (retracement + displacement)
        # ------------------------------------------------------------
        current_candle = df_entry.iloc[-1]
        current_high = current_candle['high']
        current_low = current_candle['low']
        current_close = current_candle['close']

        for ob in obs:
            ob_range = ob['high'] - ob['low']
            if ob_range <= 0:
                continue
            if ob['type'] == 'bullish':
                entry_zone_top = ob['high']
                entry_zone_bottom = ob['low'] + ob_range * self.retrace_pct
                if current_low <= entry_zone_top and current_close > entry_zone_bottom:
                    if len(df_entry) >= 2:
                        prev_close = df_entry.iloc[-2]['close']
                        if current_close > prev_close + self.trigger_disp * pip:
                            if self.use_mtf and bias == 'bearish':
                                self.logger.info(f"Bullish OB skipped: bias is bearish")
                                continue
                            entry = entry_zone_top
                            sl = ob['low'] - pip
                            tp = entry + self.tp_pips * pip
                            if abs(entry - sl) / pip > self.max_sl_pips:
                                self.logger.info(f"Bullish OB skipped: SL too wide ({abs(entry - sl)/pip:.1f} pips)")
                                continue
                            self.logger.info(f"Signal generated for {symbol}: BUY at {entry}")
                            return {
                                'direction': 'BUY',
                                'entry': entry,
                                'sl': sl,
                                'tp': tp
                            }
            else:  # bearish OB
                entry_zone_bottom = ob['low']
                entry_zone_top = ob['high'] - ob_range * self.retrace_pct
                if current_high >= entry_zone_bottom and current_close < entry_zone_top:
                    if len(df_entry) >= 2:
                        prev_close = df_entry.iloc[-2]['close']
                        if current_close < prev_close - self.trigger_disp * pip:
                            if self.use_mtf and bias == 'bullish':
                                self.logger.info(f"Bearish OB skipped: bias is bullish")
                                continue
                            entry = entry_zone_bottom
                            sl = ob['high'] + pip
                            tp = entry - self.tp_pips * pip
                            if abs(entry - sl) / pip > self.max_sl_pips:
                                self.logger.info(f"Bearish OB skipped: SL too wide ({abs(entry - sl)/pip:.1f} pips)")
                                continue
                            self.logger.info(f"Signal generated for {symbol}: SELL at {entry}")
                            return {
                                'direction': 'SELL',
                                'entry': entry,
                                'sl': sl,
                                'tp': tp
                            }
        return None