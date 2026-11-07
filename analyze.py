import pandas as pd

financials = pd.read_csv("bart_financials.csv", nrows=0)
districts = pd.read_csv("2025_SpecialDistrict.csv", encoding="cp1252", nrows=0)

print("BART financial columns:")
print(financials.columns.tolist())

print("\n2025 Special District columns:")
print(districts.columns.tolist())
