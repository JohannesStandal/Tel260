import pandas as pd

df = pd.read_csv("TEMP__measurements_cold.csv")

print(df.describe())