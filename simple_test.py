#!/usr/bin/env python3
"""
Simple test script for the backtesting package.
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all modules can be imported."""
    try:
        from backtester.instruments import OptionPosition, StockPosition
        print("✓ Instruments module imported successfully")
        
        from backtester.data import DataManager
        print("✓ Data module imported successfully")
        
        from backtester.engine import BacktestEngine
        print("✓ Engine module imported successfully")
        
        from backtester.metrics import calculate_metrics
        print("✓ Metrics module imported successfully")
        
        from backtester.cli import main
        print("✓ CLI module imported successfully")
        
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False

def test_black_scholes():
    """Test Black-Scholes option pricing."""
    try:
        from backtester.instruments import OptionPosition
        
        # Create a test option position
        option = OptionPosition(
            side="long",
            option_type="call",
            strike=100.0,
            premium=5.0,
            qty=1,
            trade_date="2024-01-01",
            expiry="2024-04-01"
        )
        
        # Test option pricing
        price = option.black_scholes_price(
            spot=105.0,
            time_to_expiry=0.25,
            volatility=0.3,
            risk_free_rate=0.05,
            dividend_yield=0.02
        )
        
        print(f"✓ Black-Scholes pricing test passed")
        print(f"  Call option price: ${price:.2f}")
        
        return price > 0
    except Exception as e:
        print(f"✗ Black-Scholes test failed: {e}")
        return False

def test_stock_position():
    """Test stock position functionality."""
    try:
        from backtester.instruments import StockPosition
        
        stock = StockPosition("AAPL", 100, 150.0)
        
        # Test MTM calculation
        mtm = stock.calculate_mtm_value(160.0)
        expected_mtm = 100 * 160.0
        
        print(f"✓ Stock position test passed")
        print(f"  MTM value: ${mtm:.2f}")
        
        return abs(mtm - expected_mtm) < 0.01
    except Exception as e:
        print(f"✗ Stock position test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("Testing backtesting package...")
    print("=" * 50)
    
    tests = [
        ("Module Imports", test_imports),
        ("Black-Scholes Pricing", test_black_scholes),
        ("Stock Position", test_stock_position),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\nRunning {test_name} test...")
        if test_func():
            passed += 1
        else:
            print(f"✗ {test_name} failed")
    
    print("\n" + "=" * 50)
    print(f"Tests completed: {passed}/{total} passed")
    
    if passed == total:
        print("✓ All tests passed! The backtesting package is ready to use.")
        print("\nUSAGE INSTRUCTIONS:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Create a config file (see backtester/examples/demo_config.json)")
        print("3. Run backtest: python -m backtester.cli run config.json")
        return 0
    else:
        print("✗ Some tests failed. Please check the implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 