import pandas as pd
import numpy as np
import yfinance as yf

# -----------------------------
# CONFIG
# -----------------------------
NIFTY50 = [
    "RELIANCE.NS","TCS.NS","INFY.NS","HDFCBANK.NS","ICICIBANK.NS",
    "LT.NS","SBIN.NS","AXISBANK.NS","KOTAKBANK.NS","ITC.NS"
]

INTERVAL = "5m"
PERIOD = "60d"
RISK_REWARD = 2
CAPITAL = 100000
RISK_PER_TRADE = 0.01

# -----------------------------
# BACKTEST FUNCTION
# -----------------------------
def backtest_stock(symbol):
    print(f"Processing {symbol}...")

    df = yf.download(symbol, interval=INTERVAL, period=PERIOD, progress=False)

    if df.empty:
        return []

    # Fix multi-index columns
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df.reset_index()
    df['Date'] = df['Datetime'].dt.date

    trades = []

    all_dates = sorted(df['Date'].unique())

    for idx in range(1, len(all_dates)):

        date = all_dates[idx]
        prev_date = all_dates[idx - 1]

        day_data = df[df['Date'] == date].copy()
        prev_day = df[df['Date'] == prev_date].copy()

        if day_data.empty or prev_day.empty:
            continue

        prev_close = float(prev_day.iloc[-1]['Close'])
        open_price = float(day_data.iloc[0]['Open'])

        if pd.isna(prev_close) or pd.isna(open_price):
            continue

        # -----------------------------
        # GAP DOWN CONDITION
        # -----------------------------
        if open_price >= prev_close:
            continue

        # -----------------------------
        # PRE-CALCULATIONS
        # -----------------------------
        day_data['VWAP'] = (day_data['Close'] * day_data['Volume']).cumsum() / day_data['Volume'].cumsum()
        rolling_vol = day_data['Volume'].rolling(10).mean()

        gap_percent = ((prev_close - open_price) / prev_close) * 100
        if gap_percent < 0.5 or gap_percent > 3:
            continue

        trade_taken = False

        # -----------------------------
        # MAIN LOOP
        # -----------------------------
        for i in range(1, len(day_data)):

            candle = day_data.iloc[i]

            # TIME FILTER (9:30–11:30)
            candle_time = candle['Datetime'].time()
            if candle_time < pd.to_datetime("09:30").time() or candle_time > pd.to_datetime("11:30").time():
                continue

            # SKIP FIRST 15 MIN
            if i < 3:
                continue

            # VOLUME FILTER
            if i < 10:
                continue
            # if candle['Volume'] < 1.5 * rolling_vol.iloc[i]:
            if candle['Volume'] < 1.2 * rolling_vol.iloc[i]:
                continue

            # VWAP FILTER
            if candle['Close'] < 0.995 * candle['VWAP']:
                continue

            # -----------------------------
            # ENTRY CONDITION
            # -----------------------------
            if candle['Close'] > prev_close and not trade_taken:

                entry_price = float(candle['Close'])
                sl = float(candle['Low'])
                risk = entry_price - sl

                if risk <= 0:
                    continue

                target = entry_price + (risk * RISK_REWARD)

                qty = int((CAPITAL * RISK_PER_TRADE) / risk)
                if qty == 0:
                    continue

                exit_price = None
                result = None

                # -----------------------------
                # FORWARD SIMULATION
                # -----------------------------
                for j in range(i + 1, len(day_data)):

                    future = day_data.iloc[j]

                    # TRAILING SL (only after profit)
                    if future['Close'] > entry_price:
                        sl = max(sl, future['Low'])

                    # SL HIT
                    if future['Low'] <= sl:
                        exit_price = sl
                        result = 'SL'
                        break

                    # TARGET HIT
                    if future['High'] >= target:
                        exit_price = target
                        result = 'Target'
                        break

                # EOD EXIT
                if exit_price is None:
                    exit_price = float(day_data.iloc[-1]['Close'])
                    result = 'EOD'

                pnl = (exit_price - entry_price) * qty

                trades.append({
                    'Symbol': symbol,
                    'Date': date,
                    'Entry': entry_price,
                    'Exit': exit_price,
                    'SL': sl,
                    'Target': target,
                    'Qty': qty,
                    'PnL': pnl,
                    'Result': result
                })

                trade_taken = True

    return trades


# -----------------------------
# RUN BACKTEST
# -----------------------------
all_trades = []

for stock in NIFTY50:
    trades = backtest_stock(stock)
    all_trades.extend(trades)

results_df = pd.DataFrame(all_trades)

# -----------------------------
# PERFORMANCE METRICS
# -----------------------------
if not results_df.empty:

    total_trades = len(results_df)
    wins = len(results_df[results_df['PnL'] > 0])
    losses = len(results_df[results_df['PnL'] <= 0])

    total_pnl = results_df['PnL'].sum()
    win_rate = (wins / total_trades) * 100

    avg_win = results_df[results_df['PnL'] > 0]['PnL'].mean()
    avg_loss = results_df[results_df['PnL'] <= 0]['PnL'].mean()

    print("\n===== BACKTEST RESULTS =====")
    print(f"Total Trades: {total_trades}")
    print(f"Wins: {wins}")
    print(f"Losses: {losses}")
    print(f"Win Rate: {win_rate:.2f}%")
    print(f"Total PnL: Rs {total_pnl:.2f}")
    print(f"Avg Win: Rs {avg_win:.2f}")
    print(f"Avg Loss: Rs {avg_loss:.2f}")

    results_df.to_csv("gap_down_strategy_results.csv", index=False)
    print("\nSaved to gap_down_strategy_results.csv")

else:
    print("No trades found.")