import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import os
from babel.numbers import format_decimal

def format_in_indian(num):
    """Format numbers in Indian style (e.g., 14,42,705)."""
    return format_decimal(num, locale="en_IN")

def backtest_year(year: int, initial_capital: float, nifty):
    def get_nearest_close(df, target_date):
        nearest_idx = df.index.get_indexer([target_date], method="nearest")[0]
        value = df.iloc[nearest_idx]["Close"]
        return float(value.iloc[0]) if isinstance(value, pd.Series) else float(value)

    start_date = nifty.index.min()
    end_date = nifty.index.max()
    tuesdays = pd.date_range(start=start_date, end=end_date, freq="W-TUE")

    capital = initial_capital
    win_count, loss_count = 0, 0

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

def backtest_range(start_year: int, end_year: int, initial_capital: float = 400000):
    nifty = yf.download("^NSEI", period="max", interval="1d")
    nifty.index = pd.to_datetime(nifty.index)

    summary = []
    capital = initial_capital
    total_wins, total_losses = 0, 0

    for year in range(start_year, end_year + 1):
        result = backtest_year(year, capital, nifty)
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
    filename = f"Option Selling Strategies/Reports/Nifty_IronCondor_Backtest_summary_{start_year}_{end_year}.csv"
    df_summary.to_csv(filename, index=False)

    # Print results in Indian format
    print(f"\nBacktest completed. Summary saved to '{filename}'")
    print(df_summary)
    print("\n" + "-"*40)
    print("Nifty Iron Condor Final Summary")
    print("-"*40)
    print("Initial Investment:", format_in_indian(initial_capital))
    print(f"Corpus after {n_years} years ({start_year}-{end_year}):", format_in_indian(corpus))
    print(f"CAGR: {cagr:.2f}%")
    print(f"Total Weeks: {total_weeks}")
    print(f"Winning Weeks: {total_wins}")
    print(f"Losing Weeks: {total_losses}")

# Example usage
backtest_range(start_year=2015, end_year=2025, initial_capital=200000)