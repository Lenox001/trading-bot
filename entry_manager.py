import time
import logging

class EntryManager:
    def __init__(self, connector, risk_manager, config, logger):
        self.connector = connector
        self.risk = risk_manager
        self.config = config
        self.logger = logger
        self.pending_orders = {}

    def add_signal(self, symbol, signal):
        if symbol in self.pending_orders:
            self.logger.info(f"Replacing existing pending order for {symbol}")
        self.pending_orders[symbol] = signal
        self.logger.info(f"Pending order set: {symbol} {signal['direction']} at {signal['entry']}")

    def clear_signal(self, symbol):
        self.pending_orders.pop(symbol, None)

    def check_and_execute(self, symbol, tick):
        if symbol not in self.pending_orders:
            return False

        order = self.pending_orders[symbol]
        direction = order['direction']
        entry = order['entry']
        sl = order['sl']
        tp = order['tp']

        # Spread filter
        if not self.risk.check_spread(symbol):
            self.clear_signal(symbol)
            return False

        if direction == 'BUY':
            if tick['ask'] <= entry:
                max_allowed = entry + self.config['max_slippage_pips'] * self.connector.pip_value(symbol)
                if tick['ask'] > max_allowed:
                    self.logger.warning(f"Slippage too high: ask={tick['ask']}, max={max_allowed}")
                    self.clear_signal(symbol)
                    return False

                # Calculate SL distance in pips (price distance)
                point = self.connector.get_point(symbol)
                if point == 0:
                    return False
                sl_pips = abs(entry - sl) / (point * 10)

                # Dynamic lot size based on risk
                lot = self.risk.calculate_lot_size(symbol, sl_pips)
                if lot <= 0:
                    self.logger.warning(f"Lot size is zero or negative ({lot}), trade skipped")
                    return False

                result = self.connector.place_order(symbol, 'BUY', lot, tick['ask'], sl, tp, magic=123456)
                self.logger.info(f"BUY EXECUTED {symbol} at {tick['ask']}, lot={lot}, sl={sl}, tp={tp}, result={result}")
                self.risk.record_trade('entry')
                self.clear_signal(symbol)
                return True
            else:
                self.logger.info(f"Waiting for BUY: ask={tick['ask']:.5f} > entry={entry:.5f}")

        else:  # SELL
            if tick['bid'] >= entry:
                max_allowed = entry - self.config['max_slippage_pips'] * self.connector.pip_value(symbol)
                if tick['bid'] < max_allowed:
                    self.logger.warning(f"Slippage too high: bid={tick['bid']}, max={max_allowed}")
                    self.clear_signal(symbol)
                    return False

                point = self.connector.get_point(symbol)
                if point == 0:
                    return False
                sl_pips = abs(entry - sl) / (point * 10)

                lot = self.risk.calculate_lot_size(symbol, sl_pips)
                if lot <= 0:
                    self.logger.warning(f"Lot size is zero or negative ({lot}), trade skipped")
                    return False

                result = self.connector.place_order(symbol, 'SELL', lot, tick['bid'], sl, tp, magic=123456)
                self.logger.info(f"SELL EXECUTED {symbol} at {tick['bid']}, lot={lot}, sl={sl}, tp={tp}, result={result}")
                self.risk.record_trade('entry')
                self.clear_signal(symbol)
                return True
            else:
                self.logger.info(f"Waiting for SELL: bid={tick['bid']:.5f} < entry={entry:.5f}")

        return False