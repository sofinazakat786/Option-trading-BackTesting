import pandas as pd
import matplotlib.pyplot as plt

# Load Excel file (replace with your actual filename)
df = pd.read_excel("nifty_weekly.xlsx")

# Ensure numeric columns are properly converted
df["Open"] = pd.to_numeric(df["Open"], errors="coerce")
df["High"] = pd.to_numeric(df["High"], errors="coerce")
df["Low"] = pd.to_numeric(df["Low"], errors="coerce")

# Calculate weekly movement as (High - Low)/Open * 100
df["Weekly_Movement_%"] = ((df["High"] - df["Low"]) / df["Open"]) * 100

# Count weeks with movement > 2%
weeks_above_2 = (df["Weekly_Movement_%"] > 2).sum()
total_weeks = len(df)

print(f"Out of {total_weeks} weeks, {weeks_above_2} weeks had movement greater than 2%.")

# Plot histogram of weekly movements
plt.figure(figsize=(8,5))
plt.hist(df["Weekly_Movement_%"], bins=20, color="skyblue", edgecolor="black")
plt.axvline(2, color="red", linestyle="--", label="2% threshold")
plt.title("Distribution of Weekly Nifty Movements")
plt.xlabel("Weekly Movement (%)")
plt.ylabel("Frequency")
plt.legend()
plt.show()