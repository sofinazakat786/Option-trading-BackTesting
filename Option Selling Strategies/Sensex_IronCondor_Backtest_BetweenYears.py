import pandas as pd
from datetime import datetime, timedelta
import os
from babel.numbers import format_decimal

def format_in_indian(num):
    """Format numbers in Indian style (e.g., 14,42,705)."""
    return format_decimal(num, locale="en_IN")

def backtest_year(year: int, initial_capital: float, sensex):
    capital = initial_capital
    win_count, loss_count = 0, 0

    start_date = sensex.index.min()
    end_date = sensex.index.max()
    fridays = pd.date_range(start=start_date, end=end_date, freq="W-FRI")

    for expiry in fridays:
        if expiry.year != year:
            continue
        monday = expiry - timedelta(days=4)
        if monday < start_date or expiry > end_date:
            continue

        # Use iloc for integer positions
        ref_idx = sensex.index.get_indexer([monday], method="nearest")[0]
        exp_idx = sensex.index.get_indexer([expiry], method="nearest")[0]

        ref_price = sensex.iloc[ref_idx]["Price"]
        expiry_price = sensex.iloc[exp_idx]["Price"]

        pct_move = ((expiry_price - ref_price) / ref_price) * 100
        outcome = "Win" if abs(pct_move) <= 3.5 else "Loss"

        if outcome == "Win":
            pl = capital * 0.015
            win_count += 1
        else:
            pl = -capital * 0.04
            loss_count += 1

        pl -= 300  # weekly charges
        capital += pl

    # Summary calculations
    final_capital = capital
    gross_profit = final_capital - initial_capital
    tax = gross_profit * 0.20 if gross_profit > 0 else 0
    net_profit = gross_profit - tax
    net_final_capital = initial_capital + net_profit
    net_profit_pct = (net_profit / initial_capital) * 100

    return {
        "Year": year,
        "Initial Investment": round(initial_capital, 2),
        "Wins": win_count,
        "Losses": loss_count,
        "Total Weeks": win_count + loss_count,
        "Final Capital": round(final_capital, 2),
        "Net Profit (After Tax)": round(net_profit, 2),
        "Net Profit %": round(net_profit_pct, 2),
        "Next Year Investment": round(net_final_capital, 2)
    }

def backtest_range_sensex(start_year: int, end_year: int, initial_capital: float = 400000):
    # Load Sensex CSV
    sensex = pd.read_csv("Option Selling Strategies/Data/BSE_Sensex_30_Historical_Data.csv")

    # Clean data
    sensex["Date"] = pd.to_datetime(sensex["Date"], dayfirst=True, errors="coerce")
    sensex["Price"] = sensex["Price"].str.replace(",", "").astype(float)
    sensex = sensex.dropna(subset=["Date", "Price"])
    sensex = sensex.sort_values("Date")
    sensex.set_index("Date", inplace=True)

    summary = []
    capital = initial_capital
    total_wins, total_losses = 0, 0

    for year in range(start_year, end_year + 1):
        result = backtest_year(year, capital, sensex)
        summary.append(result)
        capital = result["Next Year Investment"]
        total_wins += result["Wins"]
        total_losses += result["Losses"]

    df_summary = pd.DataFrame(summary)

    # Corpus after range
    corpus = capital
    n_years = end_year - start_year + 1
    cagr = ((corpus / initial_capital) ** (1 / n_years) - 1) * 100
    total_weeks = total_wins + total_losses

    # Ensure folder exists
    os.makedirs("Option Selling Strategies/Reports", exist_ok=True)

    # Save to CSV
    filename = f"Option Selling Strategies/Reports/Sensex_IronCondor_Backtest_summary_{start_year}_{end_year}.csv"
    df_summary.to_csv(filename, index=False)

    # Print results in Indian format
    print(f"\nBacktest completed. Summary saved to '{filename}'")
    print(df_summary)
    print("\n" + "-"*40)
    print("Sensex Iron Condor Final Summary")
    print("-"*40)
    print("Initial Investment:", format_in_indian(initial_capital))
    print(f"Corpus after {n_years} years ({start_year}-{end_year}):", format_in_indian(corpus))
    print(f"CAGR: {cagr:.2f}%")
    print(f"Total Weeks: {total_weeks}")
    print(f"Winning Weeks: {total_wins}")
    print(f"Losing Weeks: {total_losses}")

# Example usage
backtest_range_sensex(start_year=2015, end_year=2025, initial_capital=200000)