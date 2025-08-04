"""
Performance metrics calculation module.

Provides functions for calculating various performance metrics including
returns, drawdowns, Sharpe ratio, and alpha vs. buy-and-hold.
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional, List


def calculate_metrics(equity_curve: pd.DataFrame, 
                     benchmark_curve: Optional[pd.DataFrame] = None,
                     risk_free_rate: float = 0.02) -> Dict:
    """
    Calculate comprehensive performance metrics.
    
    Args:
        equity_curve: DataFrame with Date index and Total_PL column
        benchmark_curve: Optional benchmark data for comparison
        risk_free_rate: Annual risk-free rate (default 2%)
        
    Returns:
        Dictionary containing all calculated metrics
    """
    metrics = {}
    
    # Basic return metrics
    metrics.update(_calculate_return_metrics(equity_curve))
    
    # Risk metrics
    metrics.update(_calculate_risk_metrics(equity_curve, risk_free_rate))
    
    # Drawdown analysis
    metrics.update(_calculate_drawdown_metrics(equity_curve))
    
    # Benchmark comparison (if provided)
    if benchmark_curve is not None:
        metrics.update(_calculate_benchmark_metrics(equity_curve, benchmark_curve))
    
    return metrics


def _calculate_return_metrics(equity_curve: pd.DataFrame) -> Dict:
    """Calculate return-related metrics."""
    total_pl = equity_curve['Total_PL'].iloc[-1]
    initial_value = equity_curve['Total_PL'].iloc[0] if len(equity_curve) > 0 else 0
    
    # Calculate time period
    start_date = equity_curve.index[0]
    end_date = equity_curve.index[-1]
    years = (end_date - start_date).days / 365.0
    
    # Total return
    total_return = total_pl - initial_value
    total_return_pct = (total_return / abs(initial_value)) * 100 if initial_value != 0 else 0
    
    # CAGR
    cagr = ((total_pl / abs(initial_value)) ** (1 / years) - 1) * 100 if years > 0 and initial_value != 0 else 0
    
    # Average daily return
    daily_returns = equity_curve['Daily_Change'].dropna()
    avg_daily_return = daily_returns.mean()
    avg_daily_return_pct = (avg_daily_return / abs(initial_value)) * 100 if initial_value != 0 else 0
    
    return {
        'total_return': total_return,
        'total_return_pct': total_return_pct,
        'cagr': cagr,
        'avg_daily_return': avg_daily_return,
        'avg_daily_return_pct': avg_daily_return_pct,
        'period_years': years
    }


def _calculate_risk_metrics(equity_curve: pd.DataFrame, risk_free_rate: float) -> Dict:
    """Calculate risk-related metrics."""
    daily_returns = equity_curve['Daily_Change'].dropna()
    initial_value = equity_curve['Total_PL'].iloc[0] if len(equity_curve) > 0 else 1
    
    # Convert to percentage returns
    daily_return_pcts = daily_returns / abs(initial_value) * 100
    
    # Volatility (annualized)
    volatility = daily_return_pcts.std() * np.sqrt(252)
    
    # Sharpe ratio
    excess_returns = daily_return_pcts - (risk_free_rate * 100 / 252)  # Daily risk-free rate
    sharpe = excess_returns.mean() / daily_return_pcts.std() * np.sqrt(252) if daily_return_pcts.std() > 0 else 0
    
    # Sortino ratio (using downside deviation)
    downside_returns = daily_return_pcts[daily_return_pcts < 0]
    downside_deviation = downside_returns.std() * np.sqrt(252) if len(downside_returns) > 0 else 0
    sortino = excess_returns.mean() / downside_deviation * np.sqrt(252) if downside_deviation > 0 else 0
    
    # Maximum daily loss
    max_daily_loss = daily_returns.min()
    max_daily_loss_pct = daily_return_pcts.min()
    
    return {
        'volatility': volatility,
        'sharpe_ratio': sharpe,
        'sortino_ratio': sortino,
        'max_daily_loss': max_daily_loss,
        'max_daily_loss_pct': max_daily_loss_pct
    }


def _calculate_drawdown_metrics(equity_curve: pd.DataFrame) -> Dict:
    """Calculate drawdown-related metrics."""
    # Calculate cumulative equity
    cumulative_equity = equity_curve['Total_PL'].cumsum()
    
    # Calculate running maximum
    running_max = cumulative_equity.expanding().max()
    
    # Calculate drawdown
    drawdown = (cumulative_equity - running_max) / running_max * 100
    
    # Maximum drawdown
    max_drawdown = drawdown.min()
    
    # Find drawdown periods
    drawdown_periods = _find_drawdown_periods(drawdown)
    
    # Average drawdown
    avg_drawdown = drawdown[drawdown < 0].mean() if len(drawdown[drawdown < 0]) > 0 else 0
    
    # Time to recovery (from max drawdown)
    recovery_time = _calculate_recovery_time(cumulative_equity, drawdown)
    
    return {
        'max_drawdown': max_drawdown,
        'avg_drawdown': avg_drawdown,
        'recovery_time_days': recovery_time,
        'drawdown_periods': drawdown_periods
    }


def _find_drawdown_periods(drawdown: pd.Series) -> List[Dict]:
    """Find all drawdown periods."""
    periods = []
    in_drawdown = False
    start_date = None
    
    for date, dd in drawdown.items():
        if dd < 0 and not in_drawdown:
            # Start of drawdown
            in_drawdown = True
            start_date = date
        elif dd >= 0 and in_drawdown:
            # End of drawdown
            in_drawdown = False
            periods.append({
                'start_date': start_date,
                'end_date': date,
                'max_drawdown': drawdown.loc[start_date:date].min()
            })
    
    # Handle case where drawdown continues to end
    if in_drawdown:
        periods.append({
            'start_date': start_date,
            'end_date': drawdown.index[-1],
            'max_drawdown': drawdown.loc[start_date:].min()
        })
    
    return periods


def _calculate_recovery_time(cumulative_equity: pd.Series, drawdown: pd.Series) -> int:
    """Calculate time to recovery from maximum drawdown."""
    max_dd_idx = drawdown.idxmin()
    max_dd_value = drawdown.loc[max_dd_idx]
    
    if max_dd_value >= 0:
        return 0  # No drawdown
    
    # Find when equity recovers to the level it was at max drawdown
    recovery_level = cumulative_equity.loc[max_dd_idx]
    
    # Find next time equity reaches this level
    recovery_mask = cumulative_equity.loc[max_dd_idx:] >= recovery_level
    recovery_dates = recovery_mask[recovery_mask].index
    
    if len(recovery_dates) > 0:
        recovery_date = recovery_dates[0]
        recovery_time = (recovery_date - max_dd_idx).days
        return recovery_time
    
    return -1  # No recovery found


def _calculate_benchmark_metrics(equity_curve: pd.DataFrame, 
                                benchmark_curve: pd.DataFrame) -> Dict:
    """Calculate metrics comparing to benchmark."""
    # Align dates
    common_dates = equity_curve.index.intersection(benchmark_curve.index)
    strategy_returns = equity_curve.loc[common_dates, 'Daily_Change']
    benchmark_returns = benchmark_curve.loc[common_dates, 'Daily_Change']
    
    # Calculate excess returns
    excess_returns = strategy_returns - benchmark_returns
    
    # Information ratio
    info_ratio = excess_returns.mean() / excess_returns.std() * np.sqrt(252) if excess_returns.std() > 0 else 0
    
    # Beta (regression coefficient)
    beta = np.cov(strategy_returns, benchmark_returns)[0, 1] / np.var(benchmark_returns) if np.var(benchmark_returns) > 0 else 0
    
    # Alpha (intercept)
    alpha = strategy_returns.mean() - beta * benchmark_returns.mean()
    alpha_annualized = alpha * 252
    
    # Correlation
    correlation = np.corrcoef(strategy_returns, benchmark_returns)[0, 1]
    
    # Tracking error
    tracking_error = excess_returns.std() * np.sqrt(252)
    
    return {
        'information_ratio': info_ratio,
        'beta': beta,
        'alpha': alpha_annualized,
        'correlation': correlation,
        'tracking_error': tracking_error
    }


def calculate_rolling_metrics(equity_curve: pd.DataFrame, 
                            window: int = 252) -> pd.DataFrame:
    """
    Calculate rolling performance metrics.
    
    Args:
        equity_curve: DataFrame with Date index and Total_PL column
        window: Rolling window size in days
        
    Returns:
        DataFrame with rolling metrics
    """
    daily_returns = equity_curve['Daily_Change'].dropna()
    
    # Rolling volatility
    rolling_vol = daily_returns.rolling(window=window).std() * np.sqrt(252)
    
    # Rolling Sharpe ratio
    rolling_mean = daily_returns.rolling(window=window).mean()
    rolling_sharpe = (rolling_mean / rolling_vol) * np.sqrt(252)
    
    # Rolling drawdown
    cumulative = equity_curve['Total_PL'].cumsum()
    rolling_max = cumulative.rolling(window=window).max()
    rolling_dd = (cumulative - rolling_max) / rolling_max * 100
    
    rolling_metrics = pd.DataFrame({
        'rolling_volatility': rolling_vol,
        'rolling_sharpe': rolling_sharpe,
        'rolling_drawdown': rolling_dd
    })
    
    return rolling_metrics


def print_metrics_summary(metrics: Dict):
    """Print a formatted summary of all metrics."""
    print("\n" + "="*60)
    print("PERFORMANCE METRICS SUMMARY")
    print("="*60)
    
    # Return metrics
    print("\nRETURN METRICS:")
    print(f"  Total Return: {metrics['total_return']:,.2f} ({metrics['total_return_pct']:.2f}%)")
    print(f"  CAGR: {metrics['cagr']:.2f}%")
    print(f"  Average Daily Return: {metrics['avg_daily_return']:.2f} ({metrics['avg_daily_return_pct']:.2f}%)")
    
    # Risk metrics
    print("\nRISK METRICS:")
    print(f"  Volatility: {metrics['volatility']:.2f}%")
    print(f"  Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
    print(f"  Sortino Ratio: {metrics['sortino_ratio']:.2f}")
    print(f"  Maximum Daily Loss: {metrics['max_daily_loss']:.2f} ({metrics['max_daily_loss_pct']:.2f}%)")
    
    # Drawdown metrics
    print("\nDRAWDOWN METRICS:")
    print(f"  Maximum Drawdown: {metrics['max_drawdown']:.2f}%")
    print(f"  Average Drawdown: {metrics['avg_drawdown']:.2f}%")
    if metrics['recovery_time_days'] >= 0:
        print(f"  Recovery Time: {metrics['recovery_time_days']} days")
    else:
        print("  Recovery Time: No recovery yet")
    
    # Benchmark metrics (if available)
    if 'information_ratio' in metrics:
        print("\nBENCHMARK COMPARISON:")
        print(f"  Information Ratio: {metrics['information_ratio']:.2f}")
        print(f"  Beta: {metrics['beta']:.2f}")
        print(f"  Alpha: {metrics['alpha']:.2f}%")
        print(f"  Correlation: {metrics['correlation']:.2f}")
        print(f"  Tracking Error: {metrics['tracking_error']:.2f}%")
    
    print("="*60) 