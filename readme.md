```markdown
# WARNING: This bot trades real money. You can lose all your funds. Use at your own risk. The developer is not responsible for any financial losses.

---

**Disclaimer**

This software is provided "as is", without warranty of any kind. The developer assumes no liability for any financial losses, data loss, or other damages that may occur from using this bot. Always test thoroughly on a demo account before trading with live funds. The user is solely responsible for their trading decisions and account security.

---

**License & Redistribution**

This software and all associated code are the exclusive intellectual property of the developer. The bot is licensed solely to the original intended recipient for personal use. Any redistribution, resale, sublicensing, or sharing of the code — in whole or in part — without explicit written permission from the developer is strictly prohibited.

Modifying, altering, or editing the source code without consulting the developer is also a violation of this license. The developer assumes no responsibility for any malfunction, financial loss, or other damage caused by unauthorised modifications.

Unauthorised distribution or use constitutes a violation of the developer's intellectual property rights and may result in legal action. The developer assumes no liability for any issues, damages, or losses arising from the unauthorised use, modification, or distribution of this software. All risks associated with non‑compliance are borne entirely by the user.
---

# SMC Scalper Trading Bot

A professional scalping bot that uses Smart Money Concepts (SMC) to trade forex, stocks, and crypto. It connects to MetaTrader 5 (for forex and stocks) and Binance (for crypto), with full risk management, live news filtering, session filters, and tick‑level execution.

---

## Features

- Multi‑timeframe SMC strategy (M15 bias, M5 entry)
- Tick‑by‑tick monitoring for ultra‑fast execution
- 1% risk per trade with dynamic lot sizing
- Hard stop‑loss and take‑profit on every trade
- Spread filter, slippage control, and cooldown timer
- Max daily loss kill‑switch and equity protection
- High‑impact economic news filter (live from ForexFactory)
- Session filter (London and New York only)
- Anti‑hedging (max 1 open trade)
- Compound mode (optional)
- Magic number to track bot’s own trades
- Works 24/7 when deployed on a VPS
- Supports MetaTrader 5 (forex/stocks) and Binance (crypto)
- Detailed logging and optional Telegram alerts

---

## Prerequisites

- A Windows PC (for initial setup and testing)
- Python 3.10 or newer (Python 3.13 works)
- MetaTrader 5 **installed and running** (demo or live account logged in)
- A Binance account with API keys (if trading crypto, optional)
- A VPS (Windows, near your broker’s server) for 24/7 operation

---

## Folder Structure

Inside the `smc_scalper_bot` folder you will find the following files and subfolders (already set up for you):

```
smc_scalper_bot/
├── config/
│   └── config.yaml          ← YOU MUST EDIT THIS FILE
├── connectors/
│   ├── __init__.py
│   ├── mt5_connector.py
│   └── crypto_connector.py
├── strategy/
│   ├── __init__.py
│   ├── smc_scalper.py
│   └── indicators.py
├── risk/
│   ├── __init__.py
│   └── risk_manager.py
├── utils/
│   ├── __init__.py
│   ├── news_filter.py
│   ├── logger.py
│   └── helpers.py
├── entry_manager.py
├── main.py
├── requirements.txt
└── README.md                ← This file
```

All `__init__.py` files are empty – they just mark the folders as Python packages.

---

## Step 1 – Edit the Configuration File

Before you run the bot, you must open `config/config.yaml` with Notepad and change at least the following:

### 1.1 MT5 Credentials

```yaml
mt5:
  login: 12345678            # Replace with your MT5 account number
  password: "your_password"  # Replace with your MT5 password
  server: "BrokerServerName" # Exactly as shown in MT5 (e.g. "ICMarkets-Demo")
  path: ""                   # Keep empty – we will open MT5 manually
```

### 1.2 (Optional) Crypto Keys

If you want the bot to trade crypto on Binance, uncomment the `crypto` line in `assets` and fill in:

```yaml
crypto:
  exchange: "binance"
  api_key: "YOUR_BINANCE_API_KEY"
  api_secret: "YOUR_BINANCE_API_SECRET"
  testnet: false
```

If you do **not** want crypto, remove `"crypto"` from the `assets` list or leave that section unchanged – the bot will simply ignore it.

### 1.3 Symbols

Adjust the forex pairs and any stock symbols you want to trade:

```yaml
symbols:
  forex: ["EURUSD", "GBPUSD", "USDJPY"]
  stocks: []   # add MT5 stock symbols if desired, e.g. "AAPL"
```

---

## Step 2 – Install Python Dependencies

### 2.1 Install Python

Download and install Python 3.10 or newer from [python.org](https://www.python.org/downloads/).  
**Important:** During installation, check the box **“Add Python to PATH”.**

### 2.2 Create a Virtual Environment

Open a Command Prompt (cmd) and navigate to the `smc_scalper_bot` folder:

```bash
cd C:\Users\YourName\Desktop\smc_scalper_bot
```

Then create and activate a virtual environment:

```bash
python -m venv venv
venv\Scripts\activate
```

You should see `(venv)` at the beginning of the command line.

### 2.3 Install the Required Packages

With the virtual environment active, run:

```bash
pip install --upgrade pip wheel setuptools
pip install -r requirements.txt
```

This installs all needed libraries. All of them are pure Python or have pre‑built wheels – no C++ compiler is required.

---

## Step 3 – Open MetaTrader 5 and Run the Bot

**Before you start the bot, you must open MetaTrader 5 manually and log in to your account.**  
The bot connects to the running MT5 terminal; it does **not** launch MT5 on its own.

1. Launch MetaTrader 5.  
2. Log in with the same credentials you put in `config.yaml`.  
3. Keep MT5 running (you can minimise it).

Now, in the same Command Prompt (with `(venv)` active), type:

```bash
python main.py
```

You should see:

```
MT5 connected successfully.
Bot started...
```

The bot is now scanning for trade signals and will execute orders when conditions are met.

- To stop the bot, press **Ctrl+C**.

---

## Step 4 – Deploy on a VPS (24/7 Operation)

For the bot to trade around the clock, even when your PC is turned off, you can rent a Windows VPS near your broker’s servers.

### 4.1 Choose a VPS

Popular forex‑focused VPS providers:

- ForexVPS.net
- CheapForexVPS.com
- CNS Forex VPS
- Some brokers offer free VPS if you trade a minimum volume.

Select a plan with at least 2 GB RAM, Windows Server, and a location close to your broker (e.g., London for ICMarkets, New York for US brokers).

After purchase you will receive:
- IP address
- Username (usually `Administrator`)
- Password

### 4.2 Connect to the VPS

1. On your PC, open **Remote Desktop Connection** (search for `rdp` in the Start menu).  
2. Enter the VPS IP address and click Connect.  
3. Log in with the username and password.

You now see a remote Windows desktop.

### 4.3 Set Up the VPS

Do the same steps as on your local PC:

- Install Python (from python.org, check “Add to PATH”).
- Install MetaTrader 5 from your broker’s website.
- **Open MT5, log in, and leave it running** (minimise it).
- Copy the entire `smc_scalper_bot` folder to the VPS desktop (you can copy‑paste over RDP).
- Open a Command Prompt on the VPS, navigate to the bot folder, and install the dependencies (see Step 2).

### 4.4 Test the Bot on the VPS

With MT5 running, type:

```bash
python main.py
```

Make sure you see the connection message. Stop the bot with **Ctrl+C**.

### 4.5 Run the Bot as a Windows Service (Stays On When You Disconnect)

To keep the bot alive 24/7 even after closing the remote desktop, install it as a Windows service using **NSSM**.

1. Download NSSM from [https://nssm.cc/download](https://nssm.cc/download).  
2. Extract the zip file and copy `nssm.exe` from the `win64` folder to `C:\Windows\System32`.  
3. Open a Command Prompt **as Administrator** and run:
   ```bash
   nssm install SMCBot
   ```
4. In the dialog that appears, fill in:
   - **Application path**: `C:\Python313\python.exe` (or wherever Python is installed; find it with `where python`)
   - **Startup directory**: `C:\Users\Administrator\Desktop\smc_scalper_bot`
   - **Arguments**: `main.py`
   - **Service name**: `SMCBot`
   Click **Install service**.

5. Open **Services** (type `services.msc` in the Start menu), find `SMCBot`, right‑click and select **Start**. The bot now runs in the background.

6. You can disconnect from the VPS; the bot will continue trading. To stop or restart the bot later, use the Services window or the commands:
   ```bash
   nssm stop SMCBot
   nssm start SMCBot
   ```

---

## Important Notes for Small Accounts (e.g., $70)

- The bot risks 1% of your balance per trade. With a $70 account, that is $0.70.
- Standard lots (0.01) have a pip value of about $0.10, so a stop loss of 7 pips would already risk $0.70. The bot calculates the correct lot size, but it may refuse to trade if the required lot is below your broker’s minimum.
- **Solution**: Use a **cent account** (offered by many brokers). On a cent account, 0.01 lot = $0.01 per pip, so you can set stop losses up to 70 pips while still risking only $0.70. Simply change the `server` in `config.yaml` to your cent account server.
- The bot will automatically stop trading if your equity drops below `min_balance` (default $30).

---

## Troubleshooting

- **“MT5 initialize failed” / error -10003**  
  → MetaTrader 5 is not running. **Open MT5, log in, and try again.**

- **“No such file: config.yaml”**  
  → You are not running the command from inside the `smc_scalper_bot` folder. Navigate there first.

- **“Module not found” errors**  
  → The virtual environment is not active. Run `venv\Scripts\activate` before starting the bot.

- **Bot does not trade**  
  → Check the log file `bot.log`. The session filter or news filter may be blocking trades. For testing, you can temporarily disable them in `config.yaml`:
  ```yaml
  sessions:
    london: false
    new_york: false
    news_filter: false
  ```
  (Remember to turn them back on for live trading.)

- **Pandas installation error on Python 3.13**  
  → Your `requirements.txt` already contains `pandas>=2.2.3`, which provides a pre‑built wheel. No compilation is needed.

---

## Customisation

You can modify the bot without touching the code:

- **SMC parameters** – in the `smc` section of `config.yaml`.
- **Risk settings** – `risk_percent`, `max_daily_loss_percent`, etc.
- **News quiet minutes** – `news_quiet_minutes` under `sessions`.
- **Telegram alerts** – set `enabled: true` and fill in your bot token and chat ID.

Always test on a demo account before making changes on a live account.

---

## Support & Updates

For support, custom development, or to check for newer versions of this bot, visit **[lenox.codes](https://lenox.codes)**.  
You can also contact the developer through the website.

**Remember**: The developer is **not responsible** for any financial losses. Use this bot at your own risk, and never trade money you cannot afford to lose.
```