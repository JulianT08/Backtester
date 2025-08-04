"""
Financial instruments module for options and stock positions.

Contains classes for managing option and stock positions with pricing and P/L calculations.
"""

import pandas as pd
import numpy as np
from scipy.stats import norm
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple
import warnings


class OptionPosition:
    """
    Represents an option position with pricing and P/L calculations.
    
    Handles both long and short positions with Black-Scholes pricing.
    """
    
    def __init__(self, side: str, option_type: str, strike: float, 
                 premium: float, qty: int, trade_date: str, expiry: str):
        """
        Initialize an option position.
        
        Args:
            side: "long" or "short"
            option_type: "call" or "put"
            strike: Strike price
            premium: Option premium (positive for long, negative for short)
            qty: Number of contracts
            trade_date: Trade date in YYYY-MM-DD format
            expiry: Expiry date in YYYY-MM-DD format
        """
        self.side = side.lower()
        self.option_type = option_type.lower()
        self.strike = float(strike)
        self.premium = float(premium)
        self.qty = int(qty)
        self.trade_date = pd.to_datetime(trade_date)
        self.expiry = pd.to_datetime(expiry)
        
        # Validate inputs
        self._validate_inputs()
        
        # Calculate initial cash flow
        self.initial_cash_flow = self.premium * self.qty * 100  # 100 shares per contract
        
        # Track if position is active
        self.is_active = True
        
    def _validate_inputs(self):
        """Validate option position parameters."""
        if self.side not in ['long', 'short']:
            raise ValueError("Side must be 'long' or 'short'")
        
        if self.option_type not in ['call', 'put']:
            raise ValueError("Option type must be 'call' or 'put'")
        
        if self.strike <= 0:
            raise ValueError("Strike price must be positive")
        
        if self.qty <= 0:
            raise ValueError("Quantity must be positive")
        
        if self.trade_date >= self.expiry:
            raise ValueError("Trade date must be before expiry")
    
    def black_scholes_price(self, spot: float, time_to_expiry: float, 
                           volatility: float, risk_free_rate: float, 
                           dividend_yield: float = 0.0) -> float:
        """
        Calculate option price using Black-Scholes-Merton model.
        
        Args:
            spot: Current stock price
            time_to_expiry: Time to expiry in years
            volatility: Annualized volatility (as decimal)
            risk_free_rate: Risk-free rate (as decimal)
            dividend_yield: Dividend yield (as decimal)
            
        Returns:
            Option price
        """
        if time_to_expiry <= 0:
            # Option has expired
            return self._intrinsic_value(spot)
        
        # Black-Scholes parameters
        S = spot
        K = self.strike
        T = time_to_expiry
        sigma = volatility
        r = risk_free_rate
        q = dividend_yield
        
        # Calculate d1 and d2
        d1 = (np.log(S / K) + (r - q + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        
        # Calculate option price
        if self.option_type == 'call':
            price = S * np.exp(-q * T) * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
        else:  # put
            price = K * np.exp(-r * T) * norm.cdf(-d2) - S * np.exp(-q * T) * norm.cdf(-d1)
        
        return price
    
    def _intrinsic_value(self, spot: float) -> float:
        """Calculate intrinsic value of the option."""
        if self.option_type == 'call':
            return max(0, spot - self.strike)
        else:  # put
            return max(0, self.strike - spot)
    
    def calculate_mtm_value(self, spot: float, time_to_expiry: float,
                           volatility: float, risk_free_rate: float,
                           dividend_yield: float = 0.0) -> float:
        """
        Calculate mark-to-market value of the position.
        
        Args:
            spot: Current stock price
            time_to_expiry: Time to expiry in years
            volatility: Annualized volatility
            risk_free_rate: Risk-free rate
            dividend_yield: Dividend yield
            
        Returns:
            MTM value (positive for long, negative for short)
        """
        if not self.is_active:
            return 0.0
        
        # Calculate option price
        option_price = self.black_scholes_price(
            spot, time_to_expiry, volatility, risk_free_rate, dividend_yield
        )
        
        # Calculate position value
        position_value = option_price * self.qty * 100  # 100 shares per contract
        
        # Adjust for side (short positions have negative value)
        if self.side == 'short':
            position_value = -position_value
        
        return position_value
    
    def calculate_daily_pl(self, current_date: pd.Timestamp, spot: float,
                          volatility: float, risk_free_rate: float,
                          dividend_yield: float = 0.0) -> float:
        """
        Calculate daily P/L for the position.
        
        Args:
            current_date: Current date
            spot: Current stock price
            volatility: Annualized volatility
            risk_free_rate: Risk-free rate
            dividend_yield: Dividend yield
            
        Returns:
            Daily P/L
        """
        if not self.is_active:
            return 0.0
        
        # Calculate time to expiry
        time_to_expiry = (self.expiry - current_date).days / 365.0
        
        # Calculate current MTM value
        current_value = self.calculate_mtm_value(
            spot, time_to_expiry, volatility, risk_free_rate, dividend_yield
        )
        
        # For the first day, compare to initial cash flow
        if current_date == self.trade_date:
            return current_value - self.initial_cash_flow
        
        # For subsequent days, we need to track previous day's value
        # This will be handled by the backtest engine
        return current_value
    
    def check_exercise(self, current_date: pd.Timestamp, spot: float) -> Tuple[bool, float]:
        """
        Check if option should be exercised on expiry date.
        
        Args:
            current_date: Current date
            spot: Current stock price
            
        Returns:
            Tuple of (should_exercise, exercise_value)
        """
        if not self.is_active or current_date != self.expiry:
            return False, 0.0
        
        # Check if option is in-the-money
        intrinsic_value = self._intrinsic_value(spot)
        
        if intrinsic_value > 0:
            # Option is ITM, should exercise
            exercise_value = intrinsic_value * self.qty * 100
            
            # Adjust for side
            if self.side == 'short':
                exercise_value = -exercise_value
            
            return True, exercise_value
        
        return False, 0.0
    
    def exercise(self):
        """Mark the position as exercised (no longer active)."""
        self.is_active = False
    
    def __str__(self) -> str:
        """String representation of the option position."""
        return (f"{self.side.title()} {self.qty} {self.option_type.title()} "
                f"@ {self.strike} (Premium: {self.premium:.2f})")


class StockPosition:
    """
    Represents a stock position with P/L calculations.
    """
    
    def __init__(self, ticker: str, qty: int, initial_price: float):
        """
        Initialize a stock position.
        
        Args:
            ticker: Stock ticker
            qty: Number of shares
            initial_price: Initial stock price
        """
        self.ticker = ticker
        self.qty = int(qty)
        self.initial_price = float(initial_price)
        self.initial_value = self.qty * self.initial_price
        
        # Track dividends received
        self.dividends_received = 0.0
        
    def calculate_mtm_value(self, current_price: float) -> float:
        """
        Calculate mark-to-market value of the position.
        
        Args:
            current_price: Current stock price
            
        Returns:
            MTM value
        """
        return self.qty * current_price
    
    def calculate_daily_pl(self, current_price: float, dividend: float = 0.0) -> float:
        """
        Calculate daily P/L for the position.
        
        Args:
            current_price: Current stock price
            dividend: Dividend received (if any)
            
        Returns:
            Daily P/L
        """
        current_value = self.calculate_mtm_value(current_price)
        
        # Add dividend to P/L
        if dividend > 0:
            self.dividends_received += dividend * self.qty
        
        return current_value - self.initial_value + self.dividends_received
    
    def adjust_for_split(self, split_ratio: float):
        """
        Adjust position for stock split.
        
        Args:
            split_ratio: Split ratio (e.g., 2.0 for 2:1 split)
        """
        self.qty = int(self.qty * split_ratio)
        self.initial_price = self.initial_price / split_ratio
        self.initial_value = self.qty * self.initial_price
    
    def __str__(self) -> str:
        """String representation of the stock position."""
        return f"{self.qty} shares of {self.ticker} @ {self.initial_price:.2f}" 