import MetaTrader5 as mt5
import pandas as pd
import time

class MT5Connector:
    def __init__(self, config):
        self.full_config = config
        self.mt5_config = config['mt5']
        self.connected = False
        self.symbols = config['symbols']['forex'] + config['symbols']['stocks']
        self.timeframe_bias = config['timeframes']['bias']
        self.timeframe_entry = config['timeframes']['entry']

        self._tf_map = {
            'M1': mt5.TIMEFRAME_M1,
            'M5': mt5.TIMEFRAME_M5,
            'M15': mt5.TIMEFRAME_M15,
            'H1': mt5.TIMEFRAME_H1,
        }

    def connect(self):
        if not mt5.initialize():
            init_params = {
                'login': self.mt5_config['login'],
                'password': self.mt5_config['password'],
                'server': self.mt5_config['server'],
            }
            mt5_path = self.mt5_config.get('path', '').strip()
            if mt5_path:
                init_params['path'] = mt5_path
            if not mt5.initialize(**init_params):
                print(f"MT5 initialize failed, error: {mt5.last_error()}")
                print("Make sure MetaTrader 5 is open and you are logged in.")
                return False

        self.connected = True
        print("MT5 connected successfully.")
        return True

    def reconnect(self):
        self.disconnect()
        time.sleep(1)
        return self.connect()

    def get_balance(self):
        account_info = mt5.account_info()
        return account_info.balance if account_info else 0

    def get_equity(self):
        account_info = mt5.account_info()
        return account_info.equity if account_info else 0

    def get_open_trades_count(self):
        positions = mt5.positions_get()
        return len(positions) if positions else 0

    def get_spread(self, symbol):
        info = mt5.symbol_info(symbol)
        return info.spread if info else 0

    def get_point(self, symbol):
        info = mt5.symbol_info(symbol)
        return info.point if info else 0.0

    def pip_value(self, symbol):
        """
        Return monetary value (in account currency) of 1 pip per 1 standard lot.
        Uses trade_tick_value and trade_tick_size from MT5.
        """
        info = mt5.symbol_info(symbol)
        if info is None:
            return 10.0   # fallback for most forex pairs

        if hasattr(info, 'trade_tick_value') and hasattr(info, 'trade_tick_size'):
            tick_value = info.trade_tick_value
            tick_size = info.trade_tick_size
            if tick_size != 0 and tick_value is not None:
                pip_size = info.point * 10
                return tick_value * (pip_size / tick_size)

        return 10.0

    def get_lot_constraints(self, symbol):
        info = mt5.symbol_info(symbol)
        return info.volume_min, info.volume_max, info.volume_step

    def get_tick(self, symbol):
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            return None
        return {'bid': tick.bid, 'ask': tick.ask, 'time': tick.time}

    def get_rates(self, symbol, timeframe, count=100):
        tf = self._tf_map.get(timeframe, mt5.TIMEFRAME_M5)
        rates = mt5.copy_rates_from_pos(symbol, tf, 0, count)
        if rates is None:
            return None
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        return df

    def get_bias_rates(self, symbol):
        return self.get_rates(symbol, self.timeframe_bias, count=100)

    def get_entry_rates(self, symbol):
        return self.get_rates(symbol, self.timeframe_entry, count=30)

    def place_order(self, symbol, order_type, volume, price, sl, tp, magic=123456):
        # Use Fill or Kill (FOK) – widely supported by all brokers
        if order_type == 'BUY':
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": volume,
                "type": mt5.ORDER_TYPE_BUY,
                "price": price,
                "sl": sl,
                "tp": tp,
                "deviation": 10,
                "magic": magic,
                "comment": "SMC_scalper",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_FOK,
            }
        else:
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": volume,
                "type": mt5.ORDER_TYPE_SELL,
                "price": price,
                "sl": sl,
                "tp": tp,
                "deviation": 10,
                "magic": magic,
                "comment": "SMC_scalper",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_FOK,
            }
        result = mt5.order_send(request)
        return result

    def disconnect(self):
        mt5.shutdown()