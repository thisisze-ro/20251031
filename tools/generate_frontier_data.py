from __future__ import annotations

import csv
import json
import math
from dataclasses import dataclass
from pathlib import Path
from statistics import mean
from typing import Dict, Iterable, List, Sequence, Tuple


@dataclass
class AssetStats:
    ticker: str
    expected_return: float
    risk: float


@dataclass
class PortfolioPoint:
    weights: Dict[str, float]
    expected_return: float
    risk: float


def read_price_table(csv_path: Path) -> Tuple[List[str], List[Dict[str, float]], int]:
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        try:
            level1 = next(reader)
            level2 = next(reader)
            level3 = next(reader)
        except StopIteration as exc:  # pragma: no cover - defensive
            raise ValueError("CSV file is missing header rows") from exc

        columns: List[str] = []
        for idx, (metric, ticker, label) in enumerate(zip(level1, level2, level3)):
            if idx == 0:
                columns.append("Date")
            else:
                metric_name = metric.strip()
                ticker_name = ticker.strip()
                if not metric_name:
                    raise ValueError(f"Empty metric in header column {idx}")
                if not ticker_name:
                    raise ValueError(f"Empty ticker in header column {idx}")
                columns.append(f"{metric_name}_{ticker_name}")

        rows: List[Dict[str, float]] = []
        raw_rows = 0
        for row in reader:
            if not any(row):
                continue
            raw_rows += 1
            entry: Dict[str, float] = {}
            for column_name, value in zip(columns, row):
                if column_name == "Date":
                    entry[column_name] = value
                else:
                    entry[column_name] = float(value) if value else float("nan")
            rows.append(entry)

    tickers = sorted({
        col.split("_", 1)[1]
        for col in columns
        if col.startswith("Close_")
    })

    return tickers, rows, raw_rows


def compute_daily_returns(rows: Sequence[Dict[str, float]], tickers: Sequence[str]) -> List[Dict[str, float]]:
    previous_close: Dict[str, float] = {ticker: math.nan for ticker in tickers}
    returns: List[Dict[str, float]] = []
    for row in rows:
        daily: Dict[str, float] = {}
        skip_row = False
        for ticker in tickers:
            close_key = f"Close_{ticker}"
            close_price = row.get(close_key, math.nan)
            if math.isnan(close_price):
                previous_close[ticker] = math.nan
                skip_row = True
                break
            prev_price = previous_close.get(ticker, math.nan)
            if math.isnan(prev_price):
                previous_close[ticker] = close_price
                skip_row = True
                break
            daily_return = close_price / prev_price - 1
            daily[ticker] = daily_return
            previous_close[ticker] = close_price
        if not skip_row and daily:
            returns.append(daily)
    return returns


def sample_covariance(values_a: Sequence[float], values_b: Sequence[float]) -> float:
    if len(values_a) != len(values_b):
        raise ValueError("Return series must have identical lengths")
    n = len(values_a)
    if n < 2:
        return 0.0
    mean_a = mean(values_a)
    mean_b = mean(values_b)
    return sum((a - mean_a) * (b - mean_b) for a, b in zip(values_a, values_b)) / (n - 1)


def build_covariance_matrix(return_series: Dict[str, List[float]], tickers: Sequence[str]) -> List[List[float]]:
    matrix: List[List[float]] = []
    for ticker_i in tickers:
        row: List[float] = []
        for ticker_j in tickers:
            cov = sample_covariance(return_series[ticker_i], return_series[ticker_j])
            row.append(cov)
        matrix.append(row)
    return matrix


def portfolio_variance(weights: Sequence[float], covariance_matrix: Sequence[Sequence[float]]) -> float:
    variance = 0.0
    for i, weight_i in enumerate(weights):
        for j, weight_j in enumerate(weights):
            variance += weight_i * weight_j * covariance_matrix[i][j]
    return variance


def enumerate_portfolios(tickers: Sequence[str], expected_returns: Sequence[float], covariance_matrix: Sequence[Sequence[float]]) -> List[PortfolioPoint]:
    step = 0.02
    weight_points: List[PortfolioPoint] = []
    num_assets = len(tickers)
    if num_assets != 3:
        raise ValueError("This generator currently assumes exactly three assets")

    for i in range(int(1 / step) + 1):
        w1 = i * step
        for j in range(int((1 - w1) / step) + 1):
            w2 = j * step
            w3 = 1.0 - w1 - w2
            if w3 < -1e-9:
                continue
            weights = [w1, w2, max(w3, 0.0)]
            if not math.isclose(sum(weights), 1.0, abs_tol=1e-9):
                continue
            portfolio_return = sum(w * r for w, r in zip(weights, expected_returns))
            variance = portfolio_variance(weights, covariance_matrix)
            risk = math.sqrt(max(variance, 0.0))
            weight_map = {ticker: weight for ticker, weight in zip(tickers, weights)}
            weight_points.append(PortfolioPoint(weight_map, portfolio_return, risk))
    return weight_points


def trace_efficient_frontier(points: Iterable[PortfolioPoint]) -> List[PortfolioPoint]:
    sorted_points = sorted(points, key=lambda p: p.risk)
    frontier: List[PortfolioPoint] = []
    max_return = -math.inf
    for point in sorted_points:
        if point.expected_return > max_return + 1e-12:
            frontier.append(point)
            max_return = point.expected_return
    return frontier


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    csv_path = project_root / "temp.csv"
    tickers, rows, total_rows = read_price_table(csv_path)
    daily_returns = compute_daily_returns(rows, tickers)
    if not daily_returns:
        raise RuntimeError("No daily return data available to build efficient frontier")

    return_series: Dict[str, List[float]] = {ticker: [] for ticker in tickers}
    for entry in daily_returns:
        for ticker in tickers:
            return_series[ticker].append(entry[ticker])

    expected_returns = [mean(return_series[ticker]) for ticker in tickers]
    covariance_matrix = build_covariance_matrix(return_series, tickers)
    asset_stats = [
        AssetStats(ticker=ticker, expected_return=mean(return_series[ticker]), risk=math.sqrt(sample_covariance(return_series[ticker], return_series[ticker])))
        for ticker in tickers
    ]

    portfolios = enumerate_portfolios(tickers, expected_returns, covariance_matrix)
    frontier = trace_efficient_frontier(portfolios)

    output = {
        "metadata": {
            "tickers": tickers,
            "observations": len(daily_returns),
            "raw_rows": total_rows,
        },
        "assets": [
            {
                "ticker": stats.ticker,
                "expected_return": stats.expected_return,
                "risk": stats.risk,
            }
            for stats in asset_stats
        ],
        "portfolios": [
            {
                "weights": point.weights,
                "expected_return": point.expected_return,
                "risk": point.risk,
            }
            for point in portfolios
        ],
        "efficient_frontier": [
            {
                "weights": point.weights,
                "expected_return": point.expected_return,
                "risk": point.risk,
            }
            for point in frontier
        ],
    }

    output_path = project_root / "site" / "frontier-data.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
