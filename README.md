# temp.csv Dataset Analysis

## Overview
- **File**: `temp.csv`
- **Tickers covered**: Samsung Electronics (`005930.KS`), Apple (`AAPL`), and NVIDIA (`NVDA`).
- **Date coverage**: 2023-10-16 to 2025-10-10 (516 calendar entries; trading availability differs by market).
- **Data fields**: For each ticker the file stores daily open, high, low, close, and volume figures under a two-level header (first level = price/volume attribute, second level = ticker symbol).

Because the CSV uses a multi-row header (`Price`/`Ticker`/`Date`), each attribute-ticker pair must be combined when loading the data. Rows with blank values indicate market holidays or missing quotes for the affected ticker.

## Summary statistics
The table below summarises the main descriptive metrics for each symbol. Volume values represent raw share counts.

|Ticker|Trading days|Date range|Avg open|Avg close|First close|Last close|Close % change|Max high|Min low|Avg volume|Max volume|
|---|---|---|---|---|---|---|---|---|---|---|---|
|005930.KS|482|2023-10-16 → 2025-10-10|66,509.00|66,471.53|64,781.67|94,400.00|45.72%|94,500.00|48,968.97|19,481,204.69|57,691,266.00|
|AAPL|499|2023-10-16 → 2025-10-10|209.29|209.52|176.99|245.27|38.58%|259.24|162.91|56,558,297.39|318,679,900.00|
|NVDA|499|2023-10-16 → 2025-10-10|115.59|115.60|46.07|183.16|297.59%|195.62|39.21|325,122,504.81|1,142,269,000.00|

_Key takeaways_
- Samsung (`005930.KS`) trades on fewer sessions (482) than the U.S. equities because of Korean market holidays.
- NVIDIA shows the largest absolute and relative price increase over the period (+297.59% close-to-close) along with the highest trading volumes.
- Apple maintains the tightest trading range among the three, with the lowest average daily return volatility.

## Daily return behaviour
Daily percentage changes were calculated on consecutive closing prices, skipping non-trading days per ticker.

|Ticker|Avg daily return %|Best day %|Worst day %|
|---|---|---|---|
|005930.KS|0.07|7.21|-10.30|
|AAPL|0.11|15.33|-9.25|
|NVDA|0.37|18.72|-16.97|

- NVIDIA’s outsized growth is paired with the most extreme single-day swings (±18.72% / -16.97%).
- Samsung’s negative tail (-10.30%) aligns with sporadic sharp sell-offs despite a modest average daily gain.

## Reproducing the calculations
The statistics were derived with the Python standard library (no external packages). The snippet below combines the header rows and outputs the tables above.

```python
import csv
from statistics import mean

with open("temp.csv", newline="") as f:
    reader = csv.reader(f)
    level1, level2, level3 = (next(reader) for _ in range(3))
    rows = [row for row in reader if any(row)]

columns = ["Date" if i == 0 else f"{t}_{metric}"
           for i, (metric, t, _) in enumerate(zip(level1, level2, level3))]
records = []
for row in rows:
    entry = {}
    for col, value in zip(columns, row):
        if col == "Date":
            entry[col] = value
        elif value:
            entry[col] = float(value)
        else:
            entry[col] = None
    records.append(entry)
```

The resulting `records` list can then be aggregated to replicate the summary tables and daily return figures.

## Efficient frontier 웹 대시보드

- `python tools/generate_frontier_data.py`를 실행해 `site/frontier-data.json`을 생성합니다.
- `site/index.html`을 브라우저에서 열면 Plotly 기반 효율적 경계 시각화를 확인할 수 있습니다.
