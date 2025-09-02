#!/usr/bin/env python3
"""
VectorBT Ultra-Fast Backtester
Leverages vectorized operations for testing thousands of strategies simultaneously
Uses only standard library + NumPy/Pandas (no VectorBT dependency) for speed
"""

import numpy as np
import pandas as pd
import json
import os
import logging
from datetime import datetime, timezone
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
import concurrent.futures
import itertools

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [VECTORBT] %(message)s',
    handlers=[
        logging.FileHandler('/tmp/vectorbt_backtesting.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class VectorizedBacktestResult:
    """Result from vectorized backtesting"""
    strategy_name: str
    parameters: Dict
    timeframe: str
    total_return: float
    win_rate: float
    sharpe_ratio: float
    max_drawdown: float
    calmar_ratio: float
    total_trades: int
    avg_trade_length: float
    profit_factor: float
    expectancy: float
    confidence_score: float

class UltraFastVectorizedBacktester:
    """Ultra-fast vectorized backtesting using NumPy operations"""
    
    def __init__(self):
        self.results_cache = {}
        
    def load_data(self, file_path: str) -> pd.DataFrame:
        """Load OHLCV data efficiently"""
        try:
            df = pd.read_csv(file_path)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)
            
            # Convert to numeric
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            return df.dropna()
        except Exception as e:
            logger.error(f"Error loading {file_path}: {e}")
            return pd.DataFrame()
    
    def calculate_indicators_vectorized(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate all technical indicators using vectorized operations"""
        
        # Price-based indicators
        df['returns'] = df['close'].pct_change()
        df['log_returns'] = np.log(df['close'] / df['close'].shift(1))
        
        # Moving averages (multiple periods)
        for period in [5, 10, 15, 20, 30, 50]:
            df[f'sma_{period}'] = df['close'].rolling(window=period).mean()
            df[f'ema_{period}'] = df['close'].ewm(span=period).mean()
        
        # RSI for multiple periods
        for period in [7, 14, 21, 28]:
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            df[f'rsi_{period}'] = 100 - (100 / (1 + rs))
        
        # Bollinger Bands
        for period, std_mult in [(10, 1.5), (20, 2.0), (30, 2.5)]:
            rolling_mean = df['close'].rolling(window=period).mean()
            rolling_std = df['close'].rolling(window=period).std()
            df[f'bb_upper_{period}_{std_mult}'] = rolling_mean + (rolling_std * std_mult)
            df[f'bb_lower_{period}_{std_mult}'] = rolling_mean - (rolling_std * std_mult)
            df[f'bb_pct_{period}_{std_mult}'] = (df['close'] - rolling_mean) / (2 * rolling_std * std_mult)
        
        # MACD variants
        for fast, slow, signal in [(8, 21, 6), (12, 26, 9), (16, 35, 12)]:
            exp1 = df['close'].ewm(span=fast).mean()
            exp2 = df['close'].ewm(span=slow).mean()
            df[f'macd_{fast}_{slow}'] = exp1 - exp2
            df[f'macd_signal_{fast}_{slow}_{signal}'] = df[f'macd_{fast}_{slow}'].ewm(span=signal).mean()
            df[f'macd_histogram_{fast}_{slow}_{signal}'] = df[f'macd_{fast}_{slow}'] - df[f'macd_signal_{fast}_{slow}_{signal}']
        
        # ATR
        df['tr1'] = df['high'] - df['low']
        df['tr2'] = abs(df['high'] - df['close'].shift(1))
        df['tr3'] = abs(df['low'] - df['close'].shift(1))
        df['tr'] = df[['tr1', 'tr2', 'tr3']].max(axis=1)
        df['atr_14'] = df['tr'].rolling(window=14).mean()
        df['atr_21'] = df['tr'].rolling(window=21).mean()
        
        # Momentum indicators
        for period in [10, 20, 30]:
            df[f'momentum_{period}'] = df['close'] / df['close'].shift(period)
        
        # Price channels
        for period in [10, 20, 30]:
            df[f'channel_high_{period}'] = df['high'].rolling(window=period).max()
            df[f'channel_low_{period}'] = df['low'].rolling(window=period).min()
        
        return df
    
    def generate_signals_vectorized(self, df: pd.DataFrame, strategy_config: Dict) -> pd.Series:
        """Generate trading signals using vectorized operations"""
        
        strategy_type = strategy_config['type']
        params = strategy_config['params']
        
        if strategy_type == 'rsi_mean_reversion':
            rsi_period = params.get('rsi_period', 14)
            oversold = params.get('oversold', 30)
            overbought = params.get('overbought', 70)
            
            rsi = df[f'rsi_{rsi_period}']
            signals = pd.Series(0, index=df.index)
            signals[rsi < oversold] = 1  # Buy
            signals[rsi > overbought] = -1  # Sell
            
        elif strategy_type == 'sma_crossover':
            fast_period = params.get('fast_period', 10)
            slow_period = params.get('slow_period', 20)
            
            fast_sma = df[f'sma_{fast_period}']
            slow_sma = df[f'sma_{slow_period}']
            
            signals = pd.Series(0, index=df.index)
            signals[(fast_sma > slow_sma) & (fast_sma.shift(1) <= slow_sma.shift(1))] = 1  # Golden cross
            signals[(fast_sma < slow_sma) & (fast_sma.shift(1) >= slow_sma.shift(1))] = -1  # Death cross
            
        elif strategy_type == 'bollinger_mean_reversion':
            period = params.get('period', 20)
            std_mult = params.get('std_mult', 2.0)
            
            bb_pct = df[f'bb_pct_{period}_{std_mult}']
            signals = pd.Series(0, index=df.index)
            signals[bb_pct < -0.5] = 1  # Buy when price near lower band
            signals[bb_pct > 0.5] = -1  # Sell when price near upper band
            
        elif strategy_type == 'macd_momentum':
            fast = params.get('fast', 12)
            slow = params.get('slow', 26)
            signal = params.get('signal', 9)
            
            macd = df[f'macd_{fast}_{slow}']
            macd_signal = df[f'macd_signal_{fast}_{slow}_{signal}']
            
            signals = pd.Series(0, index=df.index)
            signals[(macd > macd_signal) & (macd.shift(1) <= macd_signal.shift(1))] = 1  # MACD above signal
            signals[(macd < macd_signal) & (macd.shift(1) >= macd_signal.shift(1))] = -1  # MACD below signal
            
        elif strategy_type == 'breakout':
            period = params.get('period', 20)
            multiplier = params.get('multiplier', 2.0)
            
            channel_high = df[f'channel_high_{period}']
            channel_low = df[f'channel_low_{period}']
            atr = df['atr_14']
            
            signals = pd.Series(0, index=df.index)
            signals[df['close'] > (channel_high + atr * multiplier)] = 1  # Breakout up
            signals[df['close'] < (channel_low - atr * multiplier)] = -1  # Breakout down
            
        else:
            # Default to simple momentum
            signals = pd.Series(0, index=df.index)
            signals[df['returns'] > 0.01] = 1
            signals[df['returns'] < -0.01] = -1
        
        return signals
    
    def backtest_strategy_vectorized(self, df: pd.DataFrame, signals: pd.Series, 
                                   transaction_cost: float = 0.001) -> Dict[str, float]:
        """Vectorized backtesting with position sizing and risk management"""
        
        # Position and returns calculation
        positions = signals.shift(1).fillna(0)  # Trade on next bar
        
        # Calculate returns
        strategy_returns = positions * df['returns'] - abs(positions.diff()) * transaction_cost
        
        # Performance metrics
        total_return = (1 + strategy_returns).prod() - 1
        
        # Win rate calculation
        winning_trades = strategy_returns[strategy_returns > transaction_cost]
        losing_trades = strategy_returns[strategy_returns < -transaction_cost]
        total_trades = len(winning_trades) + len(losing_trades)
        win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0
        
        # Sharpe ratio
        if strategy_returns.std() > 0:
            sharpe_ratio = strategy_returns.mean() / strategy_returns.std() * np.sqrt(252)
        else:
            sharpe_ratio = 0
        
        # Maximum drawdown
        cumulative_returns = (1 + strategy_returns).cumprod()
        rolling_max = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - rolling_max) / rolling_max
        max_drawdown = abs(drawdown.min())
        
        # Calmar ratio
        calmar_ratio = abs(total_return / max_drawdown) if max_drawdown > 0 else 0
        
        # Profit factor
        gross_profit = winning_trades.sum() if len(winning_trades) > 0 else 0
        gross_loss = abs(losing_trades.sum()) if len(losing_trades) > 0 else 1
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
        
        # Expectancy
        avg_win = winning_trades.mean() if len(winning_trades) > 0 else 0
        avg_loss = losing_trades.mean() if len(losing_trades) > 0 else 0
        expectancy = (win_rate * avg_win) + ((1 - win_rate) * avg_loss)
        
        return {
            'total_return': total_return,
            'win_rate': win_rate,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'calmar_ratio': calmar_ratio,
            'total_trades': total_trades,
            'profit_factor': profit_factor,
            'expectancy': expectancy,
            'avg_trade_length': positions[positions != 0].groupby((positions != positions.shift()).cumsum()).size().mean() if total_trades > 0 else 0
        }
    
    def run_massive_parameter_sweep(self, df: pd.DataFrame, base_strategy: str, 
                                  param_ranges: Dict, timeframe: str) -> List[VectorizedBacktestResult]:
        """Run massive parameter sweeps testing thousands of combinations"""
        
        logger.info(f"🚀 Starting massive parameter sweep for {base_strategy} on {timeframe}")
        
        # Generate all parameter combinations
        param_names = list(param_ranges.keys())
        param_values = [param_ranges[name] for name in param_names]
        param_combinations = list(itertools.product(*param_values))
        
        logger.info(f"📊 Testing {len(param_combinations)} parameter combinations")
        
        results = []
        
        # Process in batches for memory efficiency
        batch_size = 100
        for i in range(0, len(param_combinations), batch_size):
            batch = param_combinations[i:i + batch_size]
            
            for params_tuple in batch:
                try:
                    # Create parameter dict
                    params = dict(zip(param_names, params_tuple))
                    
                    # Create strategy config
                    strategy_config = {
                        'type': base_strategy,
                        'params': params
                    }
                    
                    # Generate signals
                    signals = self.generate_signals_vectorized(df, strategy_config)
                    
                    # Backtest
                    metrics = self.backtest_strategy_vectorized(df, signals)
                    
                    # Calculate confidence score
                    confidence = self._calculate_confidence_score(metrics)
                    
                    # Create result
                    result = VectorizedBacktestResult(
                        strategy_name=f"{base_strategy}_{self._params_to_string(params)}",
                        parameters=params,
                        timeframe=timeframe,
                        total_return=metrics['total_return'],
                        win_rate=metrics['win_rate'],
                        sharpe_ratio=metrics['sharpe_ratio'],
                        max_drawdown=metrics['max_drawdown'],
                        calmar_ratio=metrics['calmar_ratio'],
                        total_trades=metrics['total_trades'],
                        avg_trade_length=metrics['avg_trade_length'],
                        profit_factor=metrics['profit_factor'],
                        expectancy=metrics['expectancy'],
                        confidence_score=confidence
                    )
                    
                    results.append(result)
                    
                except Exception as e:
                    logger.error(f"Error testing {params}: {e}")
            
            # Progress update
            if i % (batch_size * 10) == 0:
                logger.info(f"   Processed {i + len(batch)}/{len(param_combinations)} combinations...")
        
        return results
    
    def _params_to_string(self, params: Dict) -> str:
        """Convert parameters to string representation"""
        return "_".join([f"{k}{v}" for k, v in params.items()])
    
    def _calculate_confidence_score(self, metrics: Dict) -> float:
        """Calculate confidence score based on multiple factors"""
        
        # Sample size score (more trades = higher confidence)
        sample_score = min(1.0, metrics['total_trades'] / 100)
        
        # Performance consistency score
        performance_score = 0
        if metrics['total_return'] > 0 and metrics['sharpe_ratio'] > 0:
            performance_score = min(1.0, (metrics['total_return'] + metrics['sharpe_ratio']) / 2)
        
        # Risk-adjusted score
        risk_score = 0
        if metrics['max_drawdown'] < 0.2:  # Less than 20% drawdown
            risk_score = 1.0 - metrics['max_drawdown']
        
        # Combined confidence
        confidence = (sample_score + performance_score + risk_score) / 3
        return confidence
    
    def run_comprehensive_sweep(self, timeframes: List[str] = None) -> Dict[str, List[VectorizedBacktestResult]]:
        """Run comprehensive parameter sweeps across multiple strategies and timeframes"""
        
        if not timeframes:
            timeframes = ['5m', '15m', '1h', '4h', '1d']
        
        logger.info("🚀 STARTING ULTRA-FAST VECTORIZED BACKTESTING")
        
        # Define strategy parameter ranges for massive testing
        strategy_configs = {
            'rsi_mean_reversion': {
                'rsi_period': [7, 14, 21, 28],
                'oversold': [20, 25, 30, 35],
                'overbought': [65, 70, 75, 80]
            },
            'sma_crossover': {
                'fast_period': [5, 8, 10, 12, 15],
                'slow_period': [20, 25, 30, 35, 40, 50]
            },
            'bollinger_mean_reversion': {
                'period': [10, 15, 20, 25, 30],
                'std_mult': [1.5, 2.0, 2.5, 3.0]
            },
            'macd_momentum': {
                'fast': [8, 12, 16],
                'slow': [21, 26, 35],
                'signal': [6, 9, 12]
            },
            'breakout': {
                'period': [10, 15, 20, 25, 30],
                'multiplier': [1.5, 2.0, 2.5, 3.0]
            }
        }
        
        all_results = {}
        
        for timeframe in timeframes:
            # Load data
            data_file = f"historical_data/BTCUSDT_{timeframe}_*.csv"
            import glob
            files = glob.glob(data_file)
            
            if not files:
                logger.warning(f"No data file found for {timeframe}")
                continue
            
            df = self.load_data(files[0])
            if df.empty:
                continue
            
            # Calculate indicators
            df = self.calculate_indicators_vectorized(df)
            
            logger.info(f"📊 {timeframe}: Testing on {len(df)} candles")
            
            timeframe_results = []
            
            # Test each strategy type
            for strategy_name, param_ranges in strategy_configs.items():
                logger.info(f"   🔬 Testing {strategy_name}...")
                
                strategy_results = self.run_massive_parameter_sweep(
                    df, strategy_name, param_ranges, timeframe
                )
                
                timeframe_results.extend(strategy_results)
                logger.info(f"   ✅ Completed {len(strategy_results)} variations")
            
            # Sort by performance
            timeframe_results.sort(key=lambda x: x.total_return, reverse=True)
            all_results[timeframe] = timeframe_results
            
            # Log top performers for this timeframe
            logger.info(f"🏆 TOP 5 PERFORMERS FOR {timeframe}:")
            for i, result in enumerate(timeframe_results[:5], 1):
                logger.info(
                    f"{i:2d}. {result.strategy_name[:30]:<30}: "
                    f"Return={result.total_return:+7.2%} | "
                    f"Sharpe={result.sharpe_ratio:+5.2f} | "
                    f"Trades={result.total_trades:3d} | "
                    f"Conf={result.confidence_score:.2f}"
                )
        
        # Save results
        self._save_comprehensive_results(all_results)
        
        return all_results
    
    def _save_comprehensive_results(self, all_results: Dict):
        """Save comprehensive results to files"""
        os.makedirs('backtest_results', exist_ok=True)
        
        # Save detailed results
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        filename = f'backtest_results/vectorbt_comprehensive_{timestamp}.json'
        
        # Convert to serializable format
        serializable_results = {}
        for timeframe, results in all_results.items():
            serializable_results[timeframe] = [
                {
                    'strategy_name': r.strategy_name,
                    'parameters': r.parameters,
                    'timeframe': r.timeframe,
                    'total_return': r.total_return,
                    'win_rate': r.win_rate,
                    'sharpe_ratio': r.sharpe_ratio,
                    'max_drawdown': r.max_drawdown,
                    'calmar_ratio': r.calmar_ratio,
                    'total_trades': r.total_trades,
                    'avg_trade_length': r.avg_trade_length,
                    'profit_factor': r.profit_factor,
                    'expectancy': r.expectancy,
                    'confidence_score': r.confidence_score
                } for r in results
            ]
        
        with open(filename, 'w') as f:
            json.dump(serializable_results, f, indent=2)
        
        # Create summary report
        self._create_summary_report(all_results, timestamp)
    
    def _create_summary_report(self, all_results: Dict, timestamp: str):
        """Create summary report of best strategies"""
        
        # Find absolute best performers across all timeframes
        all_strategies = []
        for timeframe_results in all_results.values():
            all_strategies.extend(timeframe_results)
        
        all_strategies.sort(key=lambda x: x.total_return, reverse=True)
        
        summary = {
            'timestamp': timestamp,
            'total_strategies_tested': len(all_strategies),
            'best_overall': {
                'strategy': all_strategies[0].strategy_name if all_strategies else None,
                'return': all_strategies[0].total_return if all_strategies else 0,
                'timeframe': all_strategies[0].timeframe if all_strategies else None,
                'parameters': all_strategies[0].parameters if all_strategies else {}
            },
            'top_10_overall': [
                {
                    'rank': i + 1,
                    'strategy': s.strategy_name,
                    'timeframe': s.timeframe,
                    'return': s.total_return,
                    'sharpe': s.sharpe_ratio,
                    'trades': s.total_trades,
                    'confidence': s.confidence_score
                } for i, s in enumerate(all_strategies[:10])
            ],
            'best_by_timeframe': {}
        }
        
        for timeframe, results in all_results.items():
            if results:
                best = results[0]
                summary['best_by_timeframe'][timeframe] = {
                    'strategy': best.strategy_name,
                    'return': best.total_return,
                    'parameters': best.parameters
                }
        
        # Save summary
        with open(f'backtest_results/vectorbt_summary_{timestamp}.json', 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info("📝 COMPREHENSIVE BACKTESTING SUMMARY:")
        logger.info(f"   Total strategies tested: {summary['total_strategies_tested']:,}")
        if summary['best_overall']['strategy']:
            logger.info(f"   🏆 ABSOLUTE BEST: {summary['best_overall']['strategy']}")
            logger.info(f"   📈 Return: {summary['best_overall']['return']:+.2%}")
            logger.info(f"   ⏰ Timeframe: {summary['best_overall']['timeframe']}")

def main():
    """Main function for ultra-fast backtesting"""
    backtester = UltraFastVectorizedBacktester()
    
    logger.info("🚀 Starting Ultra-Fast Vectorized Backtesting Suite")
    logger.info("📊 This will test thousands of strategy combinations...")
    
    # Run comprehensive sweep
    results = backtester.run_comprehensive_sweep()
    
    logger.info("✅ Ultra-fast backtesting completed!")
    logger.info("📁 Results saved to backtest_results/ directory")

if __name__ == "__main__":
    main()