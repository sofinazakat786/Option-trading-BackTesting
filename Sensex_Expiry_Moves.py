import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta

# Assume you have a function fetch_minute_data(date) that returns 1-min Sensex data for that date
# Replace this with broker API / vendor data call
def fetch_minute_data(date):
    # Example placeholder: replace with actual API call
    # Must return DataFrame with datetime index and 'Close' column
    pass

def get_nearest_price(df, target_time_str):
    target_time = pd.to_datetime(str(df.index[0].date()) + " " + target_time_str)
    diffs = np.abs((df.index - target_time).astype('timedelta64[s]'))
    nearest_idx = diffs.argmin()
    value = df.iloc[nearest_idx]['Close']
    return float(value)

results = []

# Generate last 52 Thursdays (≈ 1 year of expiries)
today = datetime.today()
dates = [today - timedelta(days=today.weekday() - 3 + 7*i) for i in range(52)]  # Thursday = weekday 3

for d in dates:
    df = fetch_minute_data(d)
    if df is None or df.empty:
        continue
    
    df.index = pd.to_datetime(df.index).tz_localize(None)
    
    price_2pm = get_nearest_price(df, "14:00:00")
    price_245pm = get_nearest_price(df, "14:45:00")
    
    move = price_245pm - price_2pm
    pct_move = (move / price_2pm) * 100
    
    results.append([d.date(), price_2pm, price_245pm, move, pct_move])

# Save results to CSV
df_results = pd.DataFrame(results, columns=["Date","Price_2PM","Price_245PM","Move","Pct_Move"])
df_results.to_csv("expiry_moves.csv", index=False)
print(df_results)