"""
Synthetic Long Position Back-Testing Package

A self-contained Python package for evaluating covered-call + protective-put
strategies on a daily basis with precise mark-to-market P/L calculations.
"""

__version__ = "1.0.0"

from .engine import BacktestEngine
from .instruments import OptionPosition, StockPosition
from .data import DataManager
from .metrics import calculate_metrics

__all__ = [
    "BacktestEngine",
    "OptionPosition", 
    "StockPosition",
    "DataManager",
    "calculate_metrics"
] 