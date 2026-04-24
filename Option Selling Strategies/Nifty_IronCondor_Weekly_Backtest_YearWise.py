import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import os

def backtest_iron_condor(year: int, initial_capital: float = 400000):
    # Fetch full history to cover older years
    nifty = yf.download("^NSEI", period="max", interval="1d")
    nifty.index = pd.to_datetime(nifty.index)

    def get_nearest_close(df, target_date):
        nearest_idx = df.index.get_indexer([target_date], method="nearest")[0]
        value = df.iloc[nearest_idx]["Close"]
        return float(value.iloc[0]) if isinstance(value, pd.Series) else float(value)

    results = []
    start_date = nifty.index.min()
    end_date = nifty.index.max()
    tuesdays = pd.date_range(start=start_date, end=end_date, freq="W-TUE")

    capital = initial_capital

    for expiry in tuesdays:
        if expiry.year != year:
            continue
        wednesday = expiry - timedelta(days=6)
        if wednesday < start_date or expiry > end_date:
            continue

        ref_price = get_nearest_close(nifty, wednesday)
        expiry_price = get_nearest_close(nifty, expiry)

        pct_move = ((expiry_price - ref_price) / ref_price) * 100
        outcome = "Win" if abs(pct_move) <= 3.5 else "Loss"

        # Weekly P/L before charges
        if outcome == "Win":
            pl = capital * 0.015
        else:
            pl = -capital * 0.04

        # Deduct weekly charges
        pl -= 300
        capital += pl

        results.append({
            "Week": expiry.date(),
            "Ref_Price": round(ref_price, 2),
            "Expiry_Price": round(expiry_price, 2),
            "Pct_Move": round(pct_move, 2),
            "Outcome": outcome,
            "PL_This_Week": round(pl, 2),
            "Capital": round(capital, 2)
        })

    df_results = pd.DataFrame(results)

    if df_results.empty:
        print(f"\nNo expiry data found for {year}. Try increasing the download period or check symbol.")
        return df_results

    # Win/Loss counts
    win_count = df_results["Outcome"].value_counts().get("Win", 0)
    loss_count = df_results["Outcome"].value_counts().get("Loss", 0)
    win_ratio = (win_count / len(df_results)) * 100

    # Final summary
    final_capital = capital
    gross_profit = final_capital - initial_capital
    tax = gross_profit * 0.20 if gross_profit > 0 else 0
    net_profit = gross_profit - tax
    net_final_capital = initial_capital + net_profit

    print("\n==============================")
    print(f" Nifty Iron Condor Backtest Summary ({year})")
    print("==============================")
    print(f"Wins : {win_count}   Losses: {loss_count}    Win Ratio   : {win_ratio:.2f}%")
    print(f"Initial Investment       : INR {initial_capital:,.2f}")
    print(f"Gross Profit (Before tax): INR {gross_profit:,.2f} ({(gross_profit/initial_capital)*100:.2f}%)")
    print(f"STCG Tax (20%)           : INR {tax:,.2f}")
    print(f"Net Profit (After tax)   : INR {net_profit:,.2f} ({(net_profit/initial_capital)*100:.2f}%)")
    print(f"Net Final Capital        : INR {net_final_capital:,.2f}")
    print("==============================\n")

    os.makedirs("Option Selling Strategies/Reports", exist_ok=True)
    df_results.to_csv(f"Option Selling Strategies/Reports/Nifty_Iron_condor_backtest_{year}.csv", index=False)

    return df_results

# Example usage:
backtest_iron_condor(2011, initial_capital=200000)