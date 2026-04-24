import pandas as pd
from datetime import datetime, timedelta
import os

def backtest_iron_condor_sensex(year: int, initial_capital: float = 200000):
    # Load Sensex CSV
    sensex = pd.read_csv("Option Selling Strategies/Data/BSE_Sensex_30_Historical_Data.csv")

    # Clean data
    sensex["Date"] = pd.to_datetime(sensex["Date"], dayfirst=True, errors="coerce")
    sensex["Price"] = sensex["Price"].str.replace(",", "").astype(float)
    sensex = sensex.dropna(subset=["Date", "Price"])
    sensex = sensex.sort_values("Date")
    sensex.set_index("Date", inplace=True)

    results = []
    start_date = sensex.index.min()
    end_date = sensex.index.max()
    fridays = pd.date_range(start=start_date, end=end_date, freq="W-FRI")

    capital = initial_capital

    for expiry in fridays:
        if expiry.year != year:
            continue
        monday = expiry - timedelta(days=4)
        if monday < start_date or expiry > end_date:
            continue

        # Get nearest close prices using iloc
        ref_idx = sensex.index.get_indexer([monday], method="nearest")[0]
        exp_idx = sensex.index.get_indexer([expiry], method="nearest")[0]

        ref_price = sensex.iloc[ref_idx]["Price"]
        expiry_price = sensex.iloc[exp_idx]["Price"]

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
        print(f"\nNo expiry data found for {year}. Check CSV data range.")
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
    print(f" Sensex Iron Condor Backtest Summary ({year})")
    print("==============================")
    print(f"Wins : {win_count}   Losses: {loss_count}    Win Ratio   : {win_ratio:.2f}%")
    print(f"Initial Investment       : INR {initial_capital:,.2f}")
    print(f"Gross Profit (Before tax): INR {gross_profit:,.2f} ({(gross_profit/initial_capital)*100:.2f}%)")
    print(f"STCG Tax (20%)           : INR {tax:,.2f}")
    print(f"Net Profit (After tax)   : INR {net_profit:,.2f} ({(net_profit/initial_capital)*100:.2f}%)")
    print(f"Net Final Capital        : INR {net_final_capital:,.2f}")
    print("==============================\n")

    # Save weekly results to CSV
    os.makedirs("Option Selling Strategies/Reports", exist_ok=True)
    df_results.to_csv(f"Option Selling Strategies/Reports/Sensex_Iron_condor_backtest_{year}.csv", index=False)

    return df_results

# Example usage:
backtest_iron_condor_sensex(2011, initial_capital=200000)