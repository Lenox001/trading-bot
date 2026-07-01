import yaml
import time
import logging
from datetime import datetime, timezone

from connectors.mt5_connector import MT5Connector
from connectors.crypto_connector import CryptoConnector
from strategy.smc_scalper import SMC_Scalper
from risk.risk_manager import RiskManager
from utils.news_filter import NewsFilter
from utils.logger import setup_logger
from entry_manager import EntryManager

# Load config
with open('config/config.yaml', 'r') as f:
    config = yaml.safe_load(f)

logger = setup_logger('MainBot', config['logs']['file'])

# ----- Make all sub‑module logs visible on console and file -----
root_logger = logging.getLogger()
root_logger.setLevel(config['logs']['level'])
for handler in logger.handlers:
    root_logger.addHandler(handler)
# ---------------------------------------------------------------

# Connectors
mt5 = None
crypto = None
if 'mt5' in config['assets']:
    mt5 = MT5Connector(config)
    if not mt5.connect():
        logger.error("MT5 connection failed.")
        exit()
if 'crypto' in config['assets']:
    crypto = CryptoConnector(config)

strategy = SMC_Scalper(config)
news_filter = NewsFilter(quiet_minutes=config['sessions']['news_quiet_minutes']) if config['sessions']['news_filter'] else None

# Session check helper
def is_good_session():
    """Return True if trading is allowed in the current session."""
    hour = datetime.now(timezone.utc).hour
    london = config['sessions'].get('london', False)
    new_york = config['sessions'].get('new_york', False)
    asian = config['sessions'].get('asian', False)

    if not (london or new_york or asian):
        return True

    if london and (7 <= hour < 16):
        return True
    if new_york and (12 <= hour < 20):
        return True
    if asian and (0 <= hour < 8):
        return True

    return False

# Track last candle timestamp per symbol
last_candle_time = {}

def should_generate_signal(symbol, connector):
    """Check if a new candle has closed on entry timeframe."""
    entry_rates = connector.get_entry_rates(symbol)
    if entry_rates is None or entry_rates.empty:
        return False, None
    last_time = entry_rates.iloc[-1]['time']
    if symbol not in last_candle_time or last_time != last_candle_time[symbol]:
        last_candle_time[symbol] = last_time
        return True, entry_rates
    return False, entry_rates

# Risk managers per symbol
risk_mgrs = {}
if mt5:
    for sym in mt5.symbols:
        risk_mgrs[sym] = RiskManager(config, mt5)
if crypto:
    for sym in crypto.symbols:
        risk_mgrs[sym] = RiskManager(config, crypto)

# Entry manager
entry_mgr = EntryManager(mt5 if mt5 else crypto, None, config, logger)

def process_symbol(symbol, conn, risk_mgr):
    """Run strategy and tick execution for one symbol."""
    # 1. Session & news filter (forex only)
    if conn == mt5:
        if not is_good_session():
            return
        if news_filter and not news_filter.is_news_quiet(symbol):
            return

    # 2. Check for new entry candle → generate signal
    new_candle, entry_df = should_generate_signal(symbol, conn)
    if new_candle and entry_df is not None:
        bias_df = conn.get_bias_rates(symbol) if config['smc']['use_mtf'] else None
        signal = strategy.generate_signal(bias_df, entry_df, symbol)
        if signal:
            logger.info(f"Signal generated for {symbol}: {signal['direction']} at {signal['entry']}")
            entry_mgr.add_signal(symbol, signal)
        else:
            entry_mgr.clear_signal(symbol)

    # 3. Tick‑based execution check
    tick = conn.get_tick(symbol)
    if tick is None:
        # Only log once per minute to avoid spam
        if int(time.time()) % 60 == 0:
            logger.warning(f"No tick data for {symbol} – check Market Watch in MT5")
    else:
        entry_mgr.connector = conn
        entry_mgr.risk = risk_mgr
        entry_mgr.check_and_execute(symbol, tick)

def run_bot():
    logger.info("Bot started...")
    while True:
        try:
            if mt5 and not mt5.connected:
                mt5.reconnect()

            for sym in mt5.symbols if mt5 else []:
                process_symbol(sym, mt5, risk_mgrs[sym])
            for sym in crypto.symbols if crypto else []:
                process_symbol(sym, crypto, risk_mgrs[sym])

            time.sleep(0.2)

        except KeyboardInterrupt:
            logger.info("Bot stopped by user.")
            break
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    run_bot()