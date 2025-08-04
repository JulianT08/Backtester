# Synthetic Long Position Back-Testing Package

A self-contained Python package for evaluating covered-call + protective-put strategies on a daily basis with precise mark-to-market P/L calculations.

## Features

- **Accurate Daily P/L**: Precise mark-to-market calculations using Black-Scholes option pricing
- **Real Market Data**: Stock prices from Yahoo Finance, risk-free rates from FRED
- **Comprehensive Metrics**: Returns, drawdowns, Sharpe ratio, and benchmark comparisons
- **Flexible Configuration**: JSON-based configuration for easy strategy definition
- **Command-Line Interface**: Simple CLI for running backtests
- **Data Caching**: Efficient caching to avoid repeated API calls

## Quick Start

### Installation

1. Clone or download the package
2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up FRED API key (optional, will use fallback if not available):
```bash
export FRED_API_KEY=your_api_key_here
```

### Running a Backtest

1. Create a configuration file (see `backtester/examples/demo_config.json` for format)

2. Run the backtest:
```bash
python -m backtester.cli run config.json
```

3. View results in the `results/` directory

### Example Configuration

```json
{
  "ticker": "AAPL",
  "share_qty": 100,
  "legs": [
    {
      "side": "short",
      "type": "call",
      "strike": 150.0,
      "premium": 5.50,
      "qty": 1,
      "trade_date": "2024-01-15",
      "expiry": "2024-04-19"
    },
    {
      "side": "long",
      "type": "put",
      "strike": 130.0,
      "premium": 3.25,
      "qty": 1,
      "trade_date": "2024-01-15",
      "expiry": "2024-04-19"
    }
  ]
}
```

## Configuration Format

### Required Fields

- `ticker`: Stock symbol (e.g., "AAPL")
- `share_qty`: Number of shares owned
- `legs`: Array of option positions

### Option Leg Fields

Each leg must contain:
- `side`: "long" or "short"
- `type`: "call" or "put"
- `strike`: Strike price
- `premium`: Option premium (positive for long, negative for short)
- `qty`: Number of contracts
- `trade_date`: Trade date (YYYY-MM-DD)
- `expiry`: Expiry date (YYYY-MM-DD)

### Optional Fields

- `start_date`: Custom start date (defaults to earliest trade date)
- `end_date`: Custom end date (defaults to latest expiry date)

## CLI Usage

### Run Backtest
```bash
python -m backtester.cli run config.json
python -m backtester.cli run config.json --output results/
python -m backtester.cli run config.json --verbose
```

### Validate Configuration
```bash
python -m backtester.cli validate config.json
```

### List Examples
```bash
python -m backtester.cli examples
```

## Output Files

The backtest generates:
- `equity_curve.csv`: Daily P/L data with columns:
  - `Date`: Trading date
  - `Stock_PL`: Cumulative stock P/L
  - `Option_PL`: Cumulative option P/L
  - `Total_PL`: Total cumulative P/L
  - `Daily_Change`: One-day P/L change
  - `Equity`: Total equity value

## Performance Metrics

The package calculates:
- **Return Metrics**: Total return, CAGR, average daily return
- **Risk Metrics**: Volatility, Sharpe ratio, Sortino ratio, max daily loss
- **Drawdown Metrics**: Maximum drawdown, average drawdown, recovery time
- **Benchmark Metrics**: Alpha, beta, information ratio, correlation (if benchmark provided)

## Technical Details

### Option Pricing
- Uses Black-Scholes-Merton model with continuous dividend yield
- Volatility: 20-day rolling historical volatility (annualized)
- Risk-free rate: FRED 1-Month T-Bill rate (forward-filled)
- Dividend yield: Trailing 12-month cash dividends / current price

### Data Sources
- **Stock Prices**: Yahoo Finance (adjusted for splits/dividends)
- **Risk-Free Rates**: FRED DGS1MO series
- **Caching**: Local cache to avoid repeated API calls

### Exercise Logic
- Automatic exercise of ITM options on expiry date
- Uses closing price for exercise decisions
- Handles both long and short positions

### Error Handling
- Missing stock prices: Forward-fill from previous close
- Missing risk-free rates: Forward-fill last known rate
- Invalid parameters: Early validation with clear error messages

## Dependencies

- `numpy`: Numerical computations
- `pandas`: Data manipulation
- `yfinance`: Stock price data
- `scipy`: Statistical functions (normal distribution)
- `fredapi`: Risk-free rate data
- `matplotlib`: Optional plotting
- `pytest`: Testing framework

## Development

### Running Tests
```bash
pytest backtester/
```

### Code Style
- Follows PEP-8
- Google-style docstrings
- Type hints throughout

## Limitations

- Assumes European-style options (no early exercise except on expiry)
- Uses historical volatility as fallback (no implied volatility from market)
- Simplified dividend handling (constant yield)
- No transaction costs or slippage
- No margin requirements or interest

## License

This package is provided as-is for educational and research purposes.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## Support

For issues or questions, please check the documentation or create an issue in the repository. 