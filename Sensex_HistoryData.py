import yfinance as yf
import pandas as pd
import numpy as np
import os
from datetime import datetime

ticker = "^BSESN"  # Sensex index

# Fetch today's 1-min data
df = yf.download(ticker, period="1d", interval="1m")

# Ensure index is datetime and remove timezone
df.index = pd.to_datetime(df.index).tz_localize(None)

# Function to get nearest price
def get_nearest_price(df, target_time_str):
    target_time = pd.to_datetime(str(df.index[0].date()) + " " + target_time_str)
    diffs = np.abs((df.index - target_time).astype('timedelta64[s]'))
    nearest_idx = diffs.argmin()
    value = df.iloc[nearest_idx]['Close']
    # Ensure scalar
    if isinstance(value, pd.Series):
        return float(value.values[0])
    else:
        return float(value)

# Get prices near 2:00 PM and 2:45 PM
price_2pm = get_nearest_price(df, "14:00:00")
price_245pm = get_nearest_price(df, "14:45:00")

move = price_245pm - price_2pm
pct_move = (move / price_2pm) * 100

print(f"Move between 2:00–2:45 PM: {move:.2f} points ({pct_move:.2f}%)")

# Prepare result row
result = pd.DataFrame([{
    "Date": df.index[0].date(),
    "Price_2PM": price_2pm,
    "Price_245PM": price_245pm,
    "Move": move,
    "Pct_Move": pct_move
}])

# Append to CSV (create if not exists)
csv_file = "expiry_moves.csv"
if not os.path.exists(csv_file):
    result.to_csv(csv_file, index=False)
else:
    result.to_csv(csv_file, mode="a", header=False, index=False)