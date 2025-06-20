import pandas as pd
from pathlib import Path

DATA_PATH = Path('data') / 'processed' / 'dataset.csv'


def main():
    df = pd.read_csv(DATA_PATH)
    print(f"Loaded {len(df)} records")


if __name__ == '__main__':
    main()
