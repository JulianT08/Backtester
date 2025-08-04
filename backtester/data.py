import pandas as pd
import numpy as np
from datetime import datetime

try:
    import yfinance as yf
except Exception:  # pragma: no cover - yfinance might not be installed
    yf = None


class DataManager:
    """Utility class for fetching market data and simple analytics.

    The implementation is intentionally lightweight.  It retrieves price
    information using :mod:`yfinance` when available and falls back to a
    deterministic synthetic data set when network access is not possible.
    Risk‑free rates and dividend yields are returned as simple constants so
    that the rest of the backtesting engine can operate without external
    dependencies.
    """

    def get_stock_data(self, ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
        """Return adjusted close prices for *ticker*.

        Parameters
        ----------
        ticker: str
            Equity ticker symbol.
        start_date, end_date: str
            Date range in ``YYYY-MM-DD`` format.
        """
        dates = pd.date_range(start_date, end_date, freq="B")
        if yf is not None:
            try:
                data = yf.download(ticker, start=start_date, end=end_date, progress=False)
                data = data[["Adj Close"]].rename(columns={"Adj Close": "Adj_Close"})
                return data.reindex(dates)
            except Exception:
                pass  # fall back to synthetic data

        # Fallback: generate a simple price series so tests can run without IO.
        prices = pd.Series(100 + np.linspace(0, 1, len(dates)), index=dates)
        return pd.DataFrame({"Adj_Close": prices})

    def get_risk_free_rate(self, start_date: str, end_date: str) -> pd.Series:
        """Return a constant daily risk-free rate series.

        Currently this method returns a 2% annualised rate for each business
        day in the requested range.  This is sufficient for unit tests and
        makes the engine deterministic when external data is unavailable.
        """
        dates = pd.date_range(start_date, end_date, freq="B")
        return pd.Series(0.02, index=dates)

    def calculate_historical_volatility(self, stock_data: pd.DataFrame, window: int = 30) -> pd.Series:
        """Compute annualised rolling volatility from price data."""
        returns = np.log(stock_data["Adj_Close"]).diff()
        vol = returns.rolling(window=window).std() * np.sqrt(252)
        return vol.fillna(method="bfill")

    def get_dividend_yield(self, ticker: str, start_date: str, end_date: str) -> float:
        """Return a placeholder dividend yield.

        A constant 0% yield keeps the example self-contained while still
        allowing the pricing functions to receive a value.
        """
        return 0.0
