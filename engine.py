"""
Core backtesting engine for synthetic long positions.

Handles the main backtest loop, daily P/L calculations, and position management.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json
import os

from .data import DataManager
from .instruments import OptionPosition, StockPosition


class BacktestEngine:
    """
    Main backtesting engine for synthetic long positions.
    
    Orchestrates daily P/L calculations, position management, and data handling.
    """
    
    def __init__(self, config_path: str):
        """
        Initialize the backtest engine.
        
        Args:
            config_path: Path to JSON configuration file
        """
        self.config = self._load_config(config_path)
        self.data_manager = DataManager()
        
        # Extract configuration
        self.ticker = self.config['ticker']
        self.share_qty = self.config['share_qty']
        self.legs = self.config['legs']
        
        # Date range
        self.start_date = self.config.get('start_date')
        self.end_date = self.config.get('end_date')
        
        # Initialize positions
        self.stock_position = None
        self.option_positions = []
        self._initialize_positions()
        
        # Results storage
        self.equity_curve = []
        self.daily_pl = []
        
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from JSON file."""
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Validate required fields
        required_fields = ['ticker', 'share_qty', 'legs']
        for field in required_fields:
            if field not in config:
                raise ValueError(f"Missing required field: {field}")
        
        return config
    
    def _initialize_positions(self):
        """Initialize stock and option positions from configuration."""
        # Determine date range if not specified
        if not self.start_date or not self.end_date:
            self._determine_date_range()
        
        # Get initial stock price
        stock_data = self.data_manager.get_stock_data(
            self.ticker, self.start_date, self.start_date
        )
        initial_price = stock_data['Adj_Close'].iloc[0]
        
        # Initialize stock position
        self.stock_position = StockPosition(self.ticker, self.share_qty, initial_price)
        
        # Initialize option positions
        for leg in self.legs:
            option = OptionPosition(
                side=leg['side'],
                option_type=leg['type'],
                strike=leg['strike'],
                premium=leg['premium'],
                qty=leg['qty'],
                trade_date=leg['trade_date'],
                expiry=leg['expiry']
            )
            self.option_positions.append(option)
    
    def _determine_date_range(self):
        """Determine start and end dates from option legs."""
        trade_dates = [pd.to_datetime(leg['trade_date']) for leg in self.legs]
        expiry_dates = [pd.to_datetime(leg['expiry']) for leg in self.legs]
        
        self.start_date = min(trade_dates).strftime('%Y-%m-%d')
        self.end_date = max(expiry_dates).strftime('%Y-%m-%d')
    
    def run_backtest(self) -> pd.DataFrame:
        """
        Run the complete backtest.
        
        Returns:
            DataFrame with daily equity curve and P/L data
        """
        print(f"Running backtest for {self.ticker} from {self.start_date} to {self.end_date}")
        
        # Download data
        stock_data = self.data_manager.get_stock_data(self.ticker, self.start_date, self.end_date)
        risk_free_rates = self.data_manager.get_risk_free_rate(self.start_date, self.end_date)
        volatility = self.data_manager.calculate_historical_volatility(stock_data)
        dividend_yield = self.data_manager.get_dividend_yield(self.ticker, self.start_date, self.end_date)
        
        # Initialize tracking variables
        previous_stock_value = 0.0
        previous_option_value = 0.0
        
        # Run daily loop
        for date, row in stock_data.iterrows():
            current_price = row['Adj_Close']
            
            # Get risk-free rate for this date
            if date in risk_free_rates.index:
                risk_free_rate = risk_free_rates[date]
            else:
                # Forward fill if missing
                risk_free_rate = risk_free_rates.fillna(method='ffill').loc[date]
            
            # Get volatility for this date
            if date in volatility.index:
                vol = volatility[date]
            else:
                # Use last available volatility
                vol = volatility.fillna(method='ffill').loc[date]
            
            # Calculate stock P/L
            stock_pl = self.stock_position.calculate_daily_pl(current_price)
            
            # Calculate option P/L
            option_pl = 0.0
            current_option_value = 0.0
            
            for option in self.option_positions:
                if option.is_active:
                    # Calculate time to expiry
                    time_to_expiry = (option.expiry - date).days / 365.0
                    
                    # Check for exercise on expiry date
                    should_exercise, exercise_value = option.check_exercise(date, current_price)
                    
                    if should_exercise:
                        option_pl += exercise_value
                        option.exercise()
                    else:
                        # Calculate daily option P/L
                        option_value = option.calculate_mtm_value(
                            current_price, time_to_expiry, vol, risk_free_rate, dividend_yield
                        )
                        current_option_value += option_value
                        
                        # Calculate daily change
                        if date == option.trade_date:
                            # First day: compare to initial cash flow
                            option_pl += option_value - option.initial_cash_flow
                        else:
                            # Subsequent days: use previous day's value
                            option_pl += option_value - previous_option_value
            
            # Calculate total P/L
            total_pl = stock_pl + option_pl
            
            # Store results
            self.equity_curve.append({
                'Date': date,
                'Stock_PL': stock_pl,
                'Option_PL': option_pl,
                'Total_PL': total_pl,
                'Daily_Change': total_pl - (previous_stock_value + previous_option_value),
                'Equity': total_pl
            })
            
            # Update previous values for next iteration
            previous_stock_value = stock_pl
            previous_option_value = current_option_value
        
        # Convert to DataFrame
        results_df = pd.DataFrame(self.equity_curve)
        results_df.set_index('Date', inplace=True)
        
        return results_df
    
    def save_results(self, output_dir: str = "results"):
        """
        Save backtest results to CSV file.
        
        Args:
            output_dir: Directory to save results
        """
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        results_df = self.run_backtest()
        
        # Save equity curve
        output_path = os.path.join(output_dir, "equity_curve.csv")
        results_df.to_csv(output_path)
        
        print(f"Results saved to {output_path}")
        
        return results_df
    
    def print_summary(self):
        """Print backtest summary statistics."""
        results_df = self.run_backtest()
        
        # Calculate metrics
        total_return = results_df['Total_PL'].iloc[-1]
        initial_value = self.stock_position.initial_value
        
        # Calculate CAGR
        start_date = results_df.index[0]
        end_date = results_df.index[-1]
        years = (end_date - start_date).days / 365.0
        cagr = (total_return / initial_value) ** (1 / years) - 1 if years > 0 else 0
        
        # Calculate max drawdown
        cumulative_returns = results_df['Total_PL'] + initial_value
        running_max = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - running_max) / running_max
        max_drawdown = drawdown.min()
        
        # Calculate Sharpe ratio (assuming 0% risk-free rate for simplicity)
        daily_returns = results_df['Daily_Change'] / initial_value
        sharpe = daily_returns.mean() / daily_returns.std() * np.sqrt(252) if daily_returns.std() > 0 else 0
        
        print("\n" + "="*50)
        print("BACKTEST SUMMARY")
        print("="*50)
        print(f"Ticker: {self.ticker}")
        print(f"Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        print(f"Initial Position: {self.stock_position}")
        print(f"Number of Option Legs: {len(self.option_positions)}")
        print()
        print(f"Total Return: {total_return:,.2f}")
        print(f"CAGR: {cagr:.2%}")
        print(f"Max Drawdown: {max_drawdown:.2%}")
        print(f"Sharpe Ratio: {sharpe:.2f}")
        print("="*50)
        
        return {
            'total_return': total_return,
            'cagr': cagr,
            'max_drawdown': max_drawdown,
            'sharpe': sharpe
        } 