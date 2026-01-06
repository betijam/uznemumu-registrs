import pandas as pd

# Test the corrected delimiter
df = pd.read_csv("temp_addresses/aw_dziv.csv", sep=',', encoding='utf-8', dtype=str, low_memory=False, nrows=10)
print(f"Loaded {len(df)} rows with {len(df.columns)} columns")
print("Columns:", list(df.columns))
print("\nFirst row sample:")
print(f"KODS: {df.iloc[0]['KODS']}")
print(f"TIPS_CD: {df.iloc[0]['TIPS_CD']}")
print(f"STD (address): {df.iloc[0]['STD'][:50]}...")
print(f"VKUR_CD (parent): {df.iloc[0]['VKUR_CD']}")
print(f"VKUR_TIPS (parent type): {df.iloc[0]['VKUR_TIPS']}")
