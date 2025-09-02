#!/usr/bin/env python3
"""
Continuous Backtesting Engine
Runs parallel historical backtesting while live trading operates
Compares live performance vs historical predictions in real-time
"""

import asyncio
import json
import csv
import os
import time
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass, asdict
import concurrent.futures
import threading
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [CONTINUOUS] %(message)s',
    handlers=[
        logging.FileHandler('/tmp/continuous_backtesting.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class BacktestResult:
    """Backtest result with performance metrics"""
    strategy_name: str
    timeframe: str
    total_return: float
    win_rate: float
    sharpe_ratio: float
    max_drawdown: float
    total_trades: int
    avg_trade_duration: float
    confidence_score: float
    timestamp: str

@dataclass
class LiveVsHistoricalComparison:
    """Compare live trading performance vs historical predictions"""
    strategy_name: str
    live_return: float
    predicted_return: float
    live_win_rate: float
    predicted_win_rate: float
    accuracy_score: float
    deviation: float
    timestamp: str

class AdvancedBacktestingFramework:
    """Advanced backtesting with multiple strategies and adaptive learning"""
    
    def __init__(self):
        self.strategies_config = self._load_strategies_config()
        self.results_history = []
        self.live_comparison_data = []
        self.running = False
        
    def _load_strategies_config(self) -> Dict:
        """Load comprehensive strategies configuration"""
        return {
            'momentum_strategies': [
                {'name': 'RSI_Momentum', 'params': {'rsi_period': 14, 'oversold': 30, 'overbought': 70}},
                {'name': 'RSI_Adaptive', 'params': {'rsi_period': 21, 'oversold': 25, 'overbought': 75}},
                {'name': 'MACD_Standard', 'params': {'fast': 12, 'slow': 26, 'signal': 9}},
                {'name': 'MACD_Aggressive', 'params': {'fast': 8, 'slow': 21, 'signal': 6}},
            ],
            'trend_strategies': [
                {'name': 'SMA_Cross_Fast', 'params': {'fast_period': 5, 'slow_period': 15}},
                {'name': 'SMA_Cross_Medium', 'params': {'fast_period': 10, 'slow_period': 30}},
                {'name': 'SMA_Cross_Slow', 'params': {'fast_period': 20, 'slow_period': 50}},
                {'name': 'EMA_Cross', 'params': {'fast_period': 12, 'slow_period': 26}},
            ],
            'mean_reversion_strategies': [
                {'name': 'Bollinger_Bands', 'params': {'period': 20, 'std_dev': 2}},
                {'name': 'Bollinger_Tight', 'params': {'period': 10, 'std_dev': 1.5}},
                {'name': 'Mean_Reversion_Fast', 'params': {'period': 10, 'threshold': 0.02}},
                {'name': 'Mean_Reversion_Slow', 'params': {'period': 50, 'threshold': 0.05}},
            ],
            'volatility_strategies': [
                {'name': 'ATR_Breakout', 'params': {'atr_period': 14, 'multiplier': 2.0}},
                {'name': 'VIX_Based', 'params': {'lookback': 20, 'threshold': 0.3}},
                {'name': 'Range_Trading', 'params': {'range_period': 20, 'breakout_threshold': 0.02}},
            ],
            'hybrid_strategies': [
                {'name': 'Trend_Mean_Hybrid', 'params': {'trend_weight': 0.6, 'mean_weight': 0.4}},
                {'name': 'Multi_Timeframe', 'params': {'short_tf': '15m', 'long_tf': '1h'}},
                {'name': 'Adaptive_ML', 'params': {'learning_rate': 0.01, 'lookback': 100}},
            ]
        }
    
    def _advanced_rsi_strategy(self, data: List[Dict], params: Dict) -> List[Dict]:
        """Advanced RSI strategy with adaptive parameters"""
        trades = []
        position = None
        entry_price = 0
        rsi_values = []
        
        period = params.get('rsi_period', 14)
        oversold = params.get('oversold', 30)
        overbought = params.get('overbought', 70)
        
        for i in range(len(data)):
            close = float(data[i]['close'])
            
            # Calculate RSI
            if i >= period:
                gains = []
                losses = []
                for j in range(period):
                    prev_close = float(data[i-j-1]['close'])
                    curr_close = float(data[i-j]['close'])
                    change = curr_close - prev_close
                    if change > 0:
                        gains.append(change)
                        losses.append(0)
                    else:
                        gains.append(0)
                        losses.append(abs(change))
                
                avg_gain = sum(gains) / period
                avg_loss = sum(losses) / period
                
                if avg_loss != 0:
                    rs = avg_gain / avg_loss
                    rsi = 100 - (100 / (1 + rs))
                else:
                    rsi = 100
                
                rsi_values.append(rsi)
                
                # Generate signals
                if rsi < oversold and position != 'long':
                    if position == 'short':
                        pnl = (entry_price - close) / entry_price
                        trades.append({
                            'exit_time': data[i]['timestamp'],
                            'exit_price': close,
                            'pnl': pnl,
                            'type': 'close_short'
                        })
                    
                    position = 'long'
                    entry_price = close
                    trades.append({
                        'entry_time': data[i]['timestamp'],
                        'entry_price': close,
                        'type': 'open_long',
                        'rsi': rsi
                    })
                
                elif rsi > overbought and position != 'short':
                    if position == 'long':
                        pnl = (close - entry_price) / entry_price
                        trades.append({
                            'exit_time': data[i]['timestamp'],
                            'exit_price': close,
                            'pnl': pnl,
                            'type': 'close_long'
                        })
                    
                    position = 'short'
                    entry_price = close
                    trades.append({
                        'entry_time': data[i]['timestamp'],
                        'entry_price': close,
                        'type': 'open_short',
                        'rsi': rsi
                    })
        
        return trades
    
    def _macd_strategy(self, data: List[Dict], params: Dict) -> List[Dict]:
        """MACD crossover strategy"""
        trades = []
        position = None
        entry_price = 0
        
        fast_period = params.get('fast', 12)
        slow_period = params.get('slow', 26)
        signal_period = params.get('signal', 9)
        
        macd_line = []
        signal_line = []
        
        for i in range(len(data)):
            close = float(data[i]['close'])
            
            if i >= slow_period:
                # Calculate MACD
                fast_ema = self._calculate_ema(data, i, fast_period)
                slow_ema = self._calculate_ema(data, i, slow_period)
                macd = fast_ema - slow_ema
                macd_line.append(macd)
                
                # Calculate Signal line (EMA of MACD)
                if len(macd_line) >= signal_period:
                    signal = sum(macd_line[-signal_period:]) / signal_period
                    signal_line.append(signal)
                    
                    # Generate signals
                    if len(macd_line) > 1 and len(signal_line) > 1:
                        prev_macd = macd_line[-2]
                        prev_signal = signal_line[-2]
                        
                        # Bullish crossover
                        if prev_macd <= prev_signal and macd > signal and position != 'long':
                            if position == 'short':
                                pnl = (entry_price - close) / entry_price
                                trades.append({
                                    'exit_time': data[i]['timestamp'],
                                    'exit_price': close,
                                    'pnl': pnl,
                                    'type': 'close_short'
                                })
                            
                            position = 'long'
                            entry_price = close
                            trades.append({
                                'entry_time': data[i]['timestamp'],
                                'entry_price': close,
                                'type': 'open_long',
                                'macd': macd,
                                'signal': signal
                            })
                        
                        # Bearish crossover
                        elif prev_macd >= prev_signal and macd < signal and position != 'short':
                            if position == 'long':
                                pnl = (close - entry_price) / entry_price
                                trades.append({
                                    'exit_time': data[i]['timestamp'],
                                    'exit_price': close,
                                    'pnl': pnl,
                                    'type': 'close_long'
                                })
                            
                            position = 'short'
                            entry_price = close
                            trades.append({
                                'entry_time': data[i]['timestamp'],
                                'entry_price': close,
                                'type': 'open_short',
                                'macd': macd,
                                'signal': signal
                            })
        
        return trades
    
    def _calculate_ema(self, data: List[Dict], index: int, period: int) -> float:
        """Calculate Exponential Moving Average"""
        if index < period:
            return float(data[index]['close'])
        
        multiplier = 2 / (period + 1)
        ema = float(data[index]['close'])
        
        for i in range(index - period + 1, index):
            price = float(data[i]['close'])
            ema = (price * multiplier) + (ema * (1 - multiplier))
        
        return ema
    
    def _analyze_performance(self, trades: List[Dict], strategy_name: str, timeframe: str) -> BacktestResult:
        """Comprehensive performance analysis"""
        if not trades:
            return BacktestResult(
                strategy_name=strategy_name,
                timeframe=timeframe,
                total_return=0,
                win_rate=0,
                sharpe_ratio=0,
                max_drawdown=0,
                total_trades=0,
                avg_trade_duration=0,
                confidence_score=0,
                timestamp=datetime.now(timezone.utc).isoformat()
            )
        
        completed_trades = [t for t in trades if 'pnl' in t]
        if not completed_trades:
            return BacktestResult(
                strategy_name=strategy_name,
                timeframe=timeframe,
                total_return=0,
                win_rate=0,
                sharpe_ratio=0,
                max_drawdown=0,
                total_trades=0,
                avg_trade_duration=0,
                confidence_score=0,
                timestamp=datetime.now(timezone.utc).isoformat()
            )
        
        returns = [t['pnl'] for t in completed_trades]
        total_return = sum(returns)
        winning_trades = [r for r in returns if r > 0]
        win_rate = len(winning_trades) / len(returns) if returns else 0
        
        # Calculate Sharpe ratio
        if len(returns) > 1:
            avg_return = sum(returns) / len(returns)
            variance = sum((r - avg_return) ** 2 for r in returns) / len(returns)
            std_dev = variance ** 0.5
            sharpe_ratio = (avg_return / std_dev) * (252 ** 0.5) if std_dev > 0 else 0
        else:
            sharpe_ratio = 0
        
        # Calculate max drawdown
        cumulative_returns = []
        cumulative = 0
        for r in returns:
            cumulative += r
            cumulative_returns.append(cumulative)
        
        max_drawdown = 0
        peak = cumulative_returns[0] if cumulative_returns else 0
        for value in cumulative_returns:
            if value > peak:
                peak = value
            drawdown = (peak - value) / peak if peak != 0 else 0
            max_drawdown = max(max_drawdown, drawdown)
        
        # Calculate confidence score based on multiple factors
        sample_size_score = min(1.0, len(completed_trades) / 50)  # More trades = higher confidence
        consistency_score = win_rate * 2 if win_rate > 0.4 else win_rate  # Reward higher win rates
        return_score = min(1.0, total_return / 0.1)  # 10% return = full score
        confidence_score = (sample_size_score + consistency_score + return_score) / 3
        
        return BacktestResult(
            strategy_name=strategy_name,
            timeframe=timeframe,
            total_return=total_return,
            win_rate=win_rate,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            total_trades=len(completed_trades),
            avg_trade_duration=0,  # TODO: Calculate actual duration
            confidence_score=confidence_score,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
    
    async def run_continuous_backtesting(self, timeframes: List[str] = None):
        """Run continuous backtesting on multiple strategies and timeframes"""
        if not timeframes:
            timeframes = ['5m', '15m', '1h', '4h', '1d']
        
        logger.info("🚀 STARTING CONTINUOUS BACKTESTING ENGINE")
        logger.info(f"📊 Timeframes: {timeframes}")
        
        self.running = True
        iteration = 1
        
        while self.running:
            try:
                logger.info(f"🔄 Backtesting Iteration #{iteration}")
                
                # Run parallel backtests
                all_results = []
                
                for timeframe in timeframes:
                    # Load historical data
                    data_file = f"historical_data/BTCUSDT_{timeframe}_*.csv"
                    import glob
                    files = glob.glob(data_file)
                    
                    if not files:
                        logger.warning(f"No data file found for {timeframe}")
                        continue
                    
                    data = self._load_csv_data(files[0])
                    logger.info(f"   {timeframe}: Testing {len(data)} candles")
                    
                    # Test all strategy categories in parallel
                    tasks = []
                    for category, strategies in self.strategies_config.items():
                        for strategy_config in strategies:
                            task = self._run_single_backtest(
                                data, strategy_config, timeframe, category
                            )
                            tasks.append(task)
                    
                    # Execute backtests concurrently
                    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
                        futures = [executor.submit(task) for task in tasks]
                        for future in concurrent.futures.as_completed(futures):
                            try:
                                result = future.result()
                                if result:
                                    all_results.append(result)
                            except Exception as e:
                                logger.error(f"Backtest failed: {e}")
                
                # Sort and analyze results
                all_results.sort(key=lambda x: x.total_return, reverse=True)
                
                # Log top performers
                logger.info("🏆 TOP 10 CURRENT PERFORMERS:")
                for i, result in enumerate(all_results[:10], 1):
                    logger.info(
                        f"{i:2d}. {result.strategy_name:<20} ({result.timeframe:>3}): "
                        f"Return={result.total_return:+7.2%} | "
                        f"WinRate={result.win_rate:5.1%} | "
                        f"Sharpe={result.sharpe_ratio:+5.2f} | "
                        f"Confidence={result.confidence_score:.2f}"
                    )
                
                # Save results
                self._save_backtest_results(all_results, iteration)
                
                # Compare with live trading performance
                await self._compare_with_live_performance(all_results)
                
                iteration += 1
                
                # Wait before next iteration (run every 30 minutes)
                await asyncio.sleep(1800)
                
            except Exception as e:
                logger.error(f"❌ Error in continuous backtesting: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error
    
    def _run_single_backtest(self, data: List[Dict], strategy_config: Dict, timeframe: str, category: str):
        """Run a single backtest for a strategy"""
        def backtest():
            try:
                strategy_name = f"{category}_{strategy_config['name']}"
                params = strategy_config['params']
                
                # Route to appropriate strategy implementation
                if 'RSI' in strategy_config['name']:
                    trades = self._advanced_rsi_strategy(data, params)
                elif 'MACD' in strategy_config['name']:
                    trades = self._macd_strategy(data, params)
                else:
                    # Default to RSI for now, TODO: implement other strategies
                    trades = self._advanced_rsi_strategy(data, params)
                
                return self._analyze_performance(trades, strategy_name, timeframe)
                
            except Exception as e:
                logger.error(f"Error in {strategy_config['name']}: {e}")
                return None
        
        return backtest
    
    def _load_csv_data(self, filepath: str) -> List[Dict]:
        """Load CSV data"""
        data = []
        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append(row)
        return data
    
    def _save_backtest_results(self, results: List[BacktestResult], iteration: int):
        """Save backtest results to file"""
        os.makedirs('backtest_results', exist_ok=True)
        
        # Save current iteration
        filename = f'backtest_results/continuous_results_iteration_{iteration}.json'
        with open(filename, 'w') as f:
            json.dump([asdict(r) for r in results], f, indent=2)
        
        # Update master results file
        self.results_history.extend(results)
        with open('backtest_results/continuous_master_results.json', 'w') as f:
            json.dump([asdict(r) for r in self.results_history], f, indent=2)
    
    async def _compare_with_live_performance(self, backtest_results: List[BacktestResult]):
        """Compare backtesting results with live trading performance"""
        try:
            # Read live trading logs to extract performance
            live_performance = await self._extract_live_performance()
            
            if not live_performance:
                return
            
            # Find matching strategies and compare
            for backtest_result in backtest_results[:5]:  # Top 5 strategies
                comparison = LiveVsHistoricalComparison(
                    strategy_name=backtest_result.strategy_name,
                    live_return=live_performance.get('return', 0),
                    predicted_return=backtest_result.total_return,
                    live_win_rate=live_performance.get('win_rate', 0),
                    predicted_win_rate=backtest_result.win_rate,
                    accuracy_score=0,  # TODO: Calculate accuracy
                    deviation=0,  # TODO: Calculate deviation
                    timestamp=datetime.now(timezone.utc).isoformat()
                )
                
                self.live_comparison_data.append(comparison)
        
        except Exception as e:
            logger.error(f"Error comparing with live performance: {e}")
    
    async def _extract_live_performance(self) -> Optional[Dict]:
        """Extract performance metrics from live trading logs"""
        try:
            # Check multiple log files
            log_files = [
                '/tmp/superior_strategy.log',
                '/tmp/proven_strategy.log',
                '/tmp/paper_trading.log'
            ]
            
            for log_file in log_files:
                if os.path.exists(log_file):
                    with open(log_file, 'r') as f:
                        lines = f.readlines()[-50:]  # Last 50 lines
                    
                    # Extract performance metrics from logs
                    for line in reversed(lines):
                        if "STATUS:" in line and "Return" in line:
                            # Parse live performance data
                            # TODO: Implement proper parsing
                            return {'return': 0, 'win_rate': 0}
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting live performance: {e}")
            return None
    
    def stop(self):
        """Stop continuous backtesting"""
        logger.info("🛑 Stopping continuous backtesting engine...")
        self.running = False

class ContinuousBacktestingManager:
    """Manager for continuous backtesting operations"""
    
    def __init__(self):
        self.framework = AdvancedBacktestingFramework()
        self.running = False
    
    async def start(self):
        """Start continuous backtesting"""
        if self.running:
            logger.info("Continuous backtesting already running")
            return
        
        self.running = True
        logger.info("🚀 Starting Continuous Backtesting Manager")
        
        # Start backtesting in background
        await self.framework.run_continuous_backtesting()
    
    def stop(self):
        """Stop continuous backtesting"""
        self.framework.stop()
        self.running = False

async def main():
    """Main function"""
    manager = ContinuousBacktestingManager()
    
    try:
        await manager.start()
    except KeyboardInterrupt:
        logger.info("👋 Continuous backtesting stopped by user")
        manager.stop()
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        manager.stop()

if __name__ == "__main__":
    asyncio.run(main())