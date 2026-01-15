
import pandas as pd

CSV_PATH = "backend/data/financial_statements.csv"

def show_headers():
    df = pd.read_csv(CSV_PATH, sep=';', nrows=1)
    print("CSV Headers:", df.columns.tolist())

if __name__ == "__main__":
    show_headers()
