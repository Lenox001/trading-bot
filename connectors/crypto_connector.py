import ccxt
import pandas as pd
import time

class CryptoConnector:
    def __init__(self, config):
        # Keep the full config for symbols and timeframes
        self.full_config = config
        # Extract the crypto-specific config
        self.crypto_config = config['crypto']
        self.exchange_id = self.crypto_config['exchange']
        self.api_key = self.crypto_config['api_key']
        self.api_secret = self.crypto_config['api_secret']
        self.testnet = self.crypto_config.get('testnet', False)

        # Create the exchange object
        exchange_class = getattr(ccxt, self.exchange_id)
        self.exchange = exchange_class({
            'apiKey': self.api_key,
            'secret': self.api_secret,
            'enableRateLimit': True,
        })
        if self.testnet:
            self.exchange.set_sandbox_mode(True)

        # Read symbols from the top-level config
        self.symbols = config['symbols']['crypto']
        # Timeframes
        self.timeframe_bias = config['timeframes']['bias']
        self.timeframe_entry = config['timeframes'].get('crypto', '5m')

    def get_balance(self):
        balance = self.exchange.fetch_balance()
        return balance['total'].get('USDT', 0)

    def get_equity(self):
        return self.get_balance()

    def get_open_trades_count(self):
        orders = self.exchange.fetch_open_orders()
        return len(orders)

    def get_spread(self, symbol):
        orderbook = self.exchange.fetch_order_book(symbol)
        ask = orderbook['asks'][0][0]
        bid = orderbook['bids'][0][0]
        return ask - bid

    def pip_value(self, symbol):
        price = self.exchange.fetch_ticker(symbol)['last']
        if price < 1:
            return 1e-6
        return 1e-4 * price   # approximate

    def get_lot_constraints(self, symbol):
        market = self.exchange.market(symbol)
        min_amount = market['limits']['amount']['min']
        max_amount = market['limits']['amount']['max']
        step = market['precision']['amount']
        return min_amount, max_amount, 10**(-step) if step else 0.0001

    def get_tick(self, symbol):
        ticker = self.exchange.fetch_ticker(symbol)
        return {'bid': ticker['bid'], 'ask': ticker['ask'], 'time': ticker['timestamp']}

    def get_rates(self, symbol, timeframe, limit=100):
        ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=['time', 'open', 'high', 'low', 'close', 'volume'])
        df['time'] = pd.to_datetime(df['time'], unit='ms')
        return df

    def get_bias_rates(self, symbol):
        return self.get_rates(symbol, self.timeframe_bias, limit=100)

    def get_entry_rates(self, symbol):
        return self.get_rates(symbol, self.timeframe_entry, limit=30)

    def place_order(self, symbol, side, amount, price, sl=None, tp=None):
        if side == 'BUY':
            return self.exchange.create_limit_buy_order(symbol, amount, price)
        else:
            return self.exchange.create_limit_sell_order(symbol, amount, price)