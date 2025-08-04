"""
Command-line interface for the backtesting package.

Provides a simple CLI for running backtests from configuration files.
"""

import argparse
import sys
import os
from pathlib import Path
import json

from .engine import BacktestEngine
from .metrics import calculate_metrics, print_metrics_summary


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Synthetic Long Position Back-Testing Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m backtester.cli run config.json
  python -m backtester.cli run config.json --output results/
  python -m backtester.cli validate config.json
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Run command
    run_parser = subparsers.add_parser('run', help='Run a backtest')
    run_parser.add_argument('config', help='Path to configuration JSON file')
    run_parser.add_argument('--output', '-o', default='results',
                          help='Output directory for results (default: results)')
    run_parser.add_argument('--verbose', '-v', action='store_true',
                          help='Verbose output')
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate configuration file')
    validate_parser.add_argument('config', help='Path to configuration JSON file')
    
    # List examples command
    list_parser = subparsers.add_parser('examples', help='List example configurations')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    if args.command == 'run':
        run_backtest(args.config, args.output, args.verbose)
    elif args.command == 'validate':
        validate_config(args.config)
    elif args.command == 'examples':
        list_examples()


def run_backtest(config_path: str, output_dir: str, verbose: bool):
    """Run a backtest with the given configuration."""
    try:
        # Validate config file exists
        if not os.path.exists(config_path):
            print(f"Error: Configuration file '{config_path}' not found.")
            sys.exit(1)
        
        # Initialize and run backtest
        if verbose:
            print(f"Loading configuration from {config_path}")
        
        engine = BacktestEngine(config_path)
        
        if verbose:
            print("Running backtest...")
        
        # Run the backtest
        results_df = engine.save_results(output_dir)
        
        # Calculate and print metrics
        if verbose:
            print("Calculating performance metrics...")
        
        metrics = calculate_metrics(results_df)
        print_metrics_summary(metrics)
        
        # Print position summary
        print_position_summary(engine)
        
        print(f"\nBacktest completed successfully!")
        print(f"Results saved to: {output_dir}/equity_curve.csv")
        
    except Exception as e:
        print(f"Error running backtest: {str(e)}")
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def validate_config(config_path: str):
    """Validate a configuration file."""
    try:
        # Check file exists
        if not os.path.exists(config_path):
            print(f"Error: Configuration file '{config_path}' not found.")
            sys.exit(1)
        
        # Load and validate JSON
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Check required fields
        required_fields = ['ticker', 'share_qty', 'legs']
        missing_fields = [field for field in required_fields if field not in config]
        
        if missing_fields:
            print(f"Error: Missing required fields: {missing_fields}")
            sys.exit(1)
        
        # Validate legs
        for i, leg in enumerate(config['legs']):
            leg_required = ['side', 'type', 'strike', 'premium', 'qty', 'trade_date', 'expiry']
            missing_leg_fields = [field for field in leg_required if field not in leg]
            
            if missing_leg_fields:
                print(f"Error: Leg {i+1} missing required fields: {missing_leg_fields}")
                sys.exit(1)
            
            # Validate side
            if leg['side'] not in ['long', 'short']:
                print(f"Error: Leg {i+1} invalid side '{leg['side']}'. Must be 'long' or 'short'.")
                sys.exit(1)
            
            # Validate type
            if leg['type'] not in ['call', 'put']:
                print(f"Error: Leg {i+1} invalid type '{leg['type']}'. Must be 'call' or 'put'.")
                sys.exit(1)
            
            # Validate numeric fields
            try:
                float(leg['strike'])
                float(leg['premium'])
                int(leg['qty'])
            except ValueError:
                print(f"Error: Leg {i+1} has invalid numeric values.")
                sys.exit(1)
        
        print("✓ Configuration file is valid!")
        print(f"  Ticker: {config['ticker']}")
        print(f"  Shares: {config['share_qty']}")
        print(f"  Option Legs: {len(config['legs'])}")
        
        # Show date range
        trade_dates = [leg['trade_date'] for leg in config['legs']]
        expiry_dates = [leg['expiry'] for leg in config['legs']]
        
        start_date = min(trade_dates)
        end_date = max(expiry_dates)
        print(f"  Date Range: {start_date} to {end_date}")
        
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in configuration file: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error validating configuration: {str(e)}")
        sys.exit(1)


def list_examples():
    """List available example configurations."""
    examples_dir = Path(__file__).parent / 'examples'
    
    if not examples_dir.exists():
        print("No examples directory found.")
        return
    
    print("Available example configurations:")
    print()
    
    for example_file in examples_dir.glob('*.json'):
        print(f"  {example_file.name}")
        
        # Try to load and show basic info
        try:
            with open(example_file, 'r') as f:
                config = json.load(f)
            
            print(f"    Ticker: {config.get('ticker', 'N/A')}")
            print(f"    Legs: {len(config.get('legs', []))}")
            print()
        except:
            print(f"    (Could not parse file)")
            print()


def print_position_summary(engine: BacktestEngine):
    """Print a summary of the positions in the backtest."""
    print("\n" + "="*50)
    print("POSITION SUMMARY")
    print("="*50)
    
    print(f"Stock Position: {engine.stock_position}")
    
    print("\nOption Positions:")
    for i, option in enumerate(engine.option_positions, 1):
        print(f"  {i}. {option}")
    
    print("="*50)


if __name__ == '__main__':
    main() 