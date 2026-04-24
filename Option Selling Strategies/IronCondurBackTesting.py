import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# Fetch 2 years of Nifty data (daily)
nifty = yf.download("^NSEI", period="2y", interval="1d")
nifty.index = pd.to_datetime(nifty.index)

# Helper: get nearest available close price as a scalar
def get_nearest_close(df, target_date):
    nearest_idx = df.index.get_indexer([target_date], method="nearest")[0]
    # iloc returns a row, so take the "Close" column and force scalar
    value = df.iloc[nearest_idx]["Close"]
    if isinstance(value, pd.Series):
        return float(value.iloc[0])
    else:
        return float(value)

results = []

# Generate expiry Tuesdays for last 2 years
start_date = nifty.index.min()
end_date = nifty.index.max()
tuesdays = pd.date_range(start=start_date, end=end_date, freq="W-TUE")

for expiry in tuesdays:
    wednesday = expiry - timedelta(days=6)  # Wednesday before expiry
    if wednesday < start_date or expiry > end_date:
        continue

    # Get nearest closes
    ref_price = get_nearest_close(nifty, wednesday)
    expiry_price = get_nearest_close(nifty, expiry)

    pct_move = ((expiry_price - ref_price) / ref_price) * 100
    outcome = "Win" if abs(pct_move) <= 3 else "Loss"

    results.append({
        "Week": expiry.date(),
        "Ref_Price": ref_price,
        "Expiry_Price": expiry_price,
        "Pct_Move": pct_move,
        "Outcome": outcome
    })

# Save results
df_results = pd.DataFrame(results)
df_results.to_csv("iron_condor_backtest.csv", index=False)
print(df_results.tail())