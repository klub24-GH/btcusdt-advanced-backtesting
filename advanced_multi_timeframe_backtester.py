#!/usr/bin/env python3
"""
Advanced Multi-Timeframe Backtester
Tests multiple strategies across all timeframes to find the best combinations
"""

import json
import csv
from datetime import datetime
import os
import logging
from typing import Dict, List, Tuple, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Strategy:
    """Base strategy class"""
    
    def __init__(self, name: str, params: Dict):
        self.name = name
        self.params = params
        
    def calculate_indicators(self, data: List[Dict]) -> List[Dict]:
        """Calculate technical indicators"""
        for i in range(len(data)):
            if i >= 20:  # Need at least 20 periods
                # SMA calculations
                closes = [float(data[j]['close']) for j in range(i-19, i+1)]
                data[i]['sma_20'] = sum(closes) / 20
                
                # Price change
                data[i]['change'] = (float(data[i]['close']) - float(data[i-1]['close'])) / float(data[i-1]['close'])
                
                # RSI calculation (simplified)
                if i >= 34:  # RSI needs 14 periods
                    gains = []
                    losses = []
                    for j in range(i-13, i+1):
                        change = float(data[j]['close']) - float(data[j-1]['close'])
                        if change > 0:
                            gains.append(change)
                            losses.append(0)
                        else:
                            gains.append(0)
                            losses.append(abs(change))
                    
                    avg_gain = sum(gains) / 14 if gains else 0
                    avg_loss = sum(losses) / 14 if losses else 0
                    
                    if avg_loss != 0:
                        rs = avg_gain / avg_loss
                        data[i]['rsi'] = 100 - (100 / (1 + rs))
                    else:
                        data[i]['rsi'] = 100
                        
                # Bollinger Bands
                if i >= 20:
                    mean = data[i]['sma_20']
                    variance = sum((float(data[j]['close']) - mean) ** 2 for j in range(i-19, i+1)) / 20
                    std_dev = variance ** 0.5
                    data[i]['bb_upper'] = mean + (2 * std_dev)
                    data[i]['bb_lower'] = mean - (2 * std_dev)
                    
        return data

class MeanReversionStrategy(Strategy):
    """Mean reversion strategy using Bollinger Bands"""
    
    def generate_signals(self, data: List[Dict]) -> List[Dict]:
        """Generate buy/sell signals"""
        data = self.calculate_indicators(data)
        trades = []
        position = None
        entry_price = 0
        
        for i in range(20, len(data)):
            if 'bb_lower' not in data[i]:
                continue
                
            close = float(data[i]['close'])
            
            # Buy signal: price below lower band
            if close < data[i]['bb_lower'] * self.params.get('buy_threshold', 1.0) and position != 'long':
                if position == 'short':
                    # Close short
                    pnl = (entry_price - close) / entry_price
                    trades.append({
                        'exit_time': data[i]['timestamp'],
                        'exit_price': close,
                        'pnl': pnl,
                        'type': 'close_short'
                    })
                
                # Open long
                position = 'long'
                entry_price = close
                trades.append({
                    'entry_time': data[i]['timestamp'],
                    'entry_price': close,
                    'type': 'open_long'
                })
            
            # Sell signal: price above upper band
            elif close > data[i]['bb_upper'] * self.params.get('sell_threshold', 1.0) and position != 'short':
                if position == 'long':
                    # Close long
                    pnl = (close - entry_price) / entry_price
                    trades.append({
                        'exit_time': data[i]['timestamp'],
                        'exit_price': close,
                        'pnl': pnl,
                        'type': 'close_long'
                    })
                
                # Open short
                position = 'short'
                entry_price = close
                trades.append({
                    'entry_time': data[i]['timestamp'],
                    'entry_price': close,
                    'type': 'open_short'
                })
        
        return trades

class RSIStrategy(Strategy):
    """RSI-based strategy"""
    
    def generate_signals(self, data: List[Dict]) -> List[Dict]:
        """Generate buy/sell signals based on RSI"""
        data = self.calculate_indicators(data)
        trades = []
        position = None
        entry_price = 0
        
        oversold = self.params.get('oversold', 30)
        overbought = self.params.get('overbought', 70)
        
        for i in range(34, len(data)):
            if 'rsi' not in data[i]:
                continue
                
            close = float(data[i]['close'])
            rsi = data[i]['rsi']
            
            # Buy signal: RSI oversold
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
                    'type': 'open_long'
                })
            
            # Sell signal: RSI overbought
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
                    'type': 'open_short'
                })
        
        return trades

class TrendFollowingStrategy(Strategy):
    """Simple trend following using moving averages"""
    
    def generate_signals(self, data: List[Dict]) -> List[Dict]:
        """Generate signals based on SMA crossovers"""
        data = self.calculate_indicators(data)
        trades = []
        position = None
        entry_price = 0
        
        for i in range(20, len(data)):
            if 'sma_20' not in data[i]:
                continue
                
            close = float(data[i]['close'])
            sma = data[i]['sma_20']
            
            # Calculate fast SMA (5 period)
            if i >= 5:
                fast_sma = sum(float(data[j]['close']) for j in range(i-4, i+1)) / 5
            else:
                continue
            
            # Buy signal: fast SMA crosses above slow SMA
            if fast_sma > sma * self.params.get('crossover_threshold', 1.0) and position != 'long':
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
                    'type': 'open_long'
                })
            
            # Sell signal: fast SMA crosses below slow SMA
            elif fast_sma < sma * self.params.get('crossunder_threshold', 1.0) and position != 'short':
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
                    'type': 'open_short'
                })
        
        return trades

class MultiTimeframeBacktester:
    """Backtest strategies across multiple timeframes"""
    
    def __init__(self):
        self.results = []
        
    def load_data(self, filepath: str) -> List[Dict]:
        """Load CSV data"""
        data = []
        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append(row)
        return data
    
    def analyze_trades(self, trades: List[Dict], strategy_name: str, timeframe: str) -> Dict:
        """Analyze trading performance"""
        if not trades:
            return {
                'strategy': strategy_name,
                'timeframe': timeframe,
                'total_trades': 0,
                'win_rate': 0,
                'total_return': 0,
                'avg_return': 0,
                'max_win': 0,
                'max_loss': 0
            }
        
        # Get only completed trades
        completed_trades = [t for t in trades if 'pnl' in t]
        
        if not completed_trades:
            return {
                'strategy': strategy_name,
                'timeframe': timeframe,
                'total_trades': 0,
                'win_rate': 0,
                'total_return': 0,
                'avg_return': 0,
                'max_win': 0,
                'max_loss': 0
            }
        
        winning_trades = [t for t in completed_trades if t['pnl'] > 0]
        total_return = sum(t['pnl'] for t in completed_trades)
        
        return {
            'strategy': strategy_name,
            'timeframe': timeframe,
            'total_trades': len(completed_trades),
            'win_rate': len(winning_trades) / len(completed_trades) if completed_trades else 0,
            'total_return': total_return,
            'avg_return': total_return / len(completed_trades) if completed_trades else 0,
            'max_win': max([t['pnl'] for t in completed_trades]) if completed_trades else 0,
            'max_loss': min([t['pnl'] for t in completed_trades]) if completed_trades else 0,
            'sharpe_ratio': self.calculate_sharpe(completed_trades)
        }
    
    def calculate_sharpe(self, trades: List[Dict]) -> float:
        """Calculate simplified Sharpe ratio"""
        if not trades or len(trades) < 2:
            return 0
        
        returns = [t['pnl'] for t in trades if 'pnl' in t]
        if not returns:
            return 0
            
        avg_return = sum(returns) / len(returns)
        variance = sum((r - avg_return) ** 2 for r in returns) / len(returns)
        std_dev = variance ** 0.5
        
        if std_dev == 0:
            return 0
            
        # Annualized Sharpe (simplified)
        return (avg_return / std_dev) * (252 ** 0.5)  # Assuming daily trading
    
    def run_comprehensive_backtest(self):
        """Run backtests across all timeframes and strategies"""
        
        # Define strategies to test
        strategies = [
            MeanReversionStrategy('MeanRev_Standard', {}),
            MeanReversionStrategy('MeanRev_Tight', {'buy_threshold': 0.98, 'sell_threshold': 1.02}),
            MeanReversionStrategy('MeanRev_Wide', {'buy_threshold': 1.02, 'sell_threshold': 0.98}),
            RSIStrategy('RSI_Standard', {}),
            RSIStrategy('RSI_Conservative', {'oversold': 25, 'overbought': 75}),
            RSIStrategy('RSI_Aggressive', {'oversold': 35, 'overbought': 65}),
            TrendFollowingStrategy('Trend_Standard', {}),
            TrendFollowingStrategy('Trend_Sensitive', {'crossover_threshold': 1.01, 'crossunder_threshold': 0.99}),
        ]
        
        # Timeframes to test
        timeframes = ['5m', '15m', '1h', '4h', '1d']
        
        all_results = []
        
        for timeframe in timeframes:
            filepath = f"historical_data/BTCUSDT_{timeframe}_*.csv"
            
            # Find the file
            import glob
            files = glob.glob(filepath)
            if not files:
                logger.warning(f"No data file found for {timeframe}")
                continue
                
            filepath = files[0]
            logger.info(f"📊 Testing {timeframe} timeframe: {filepath}")
            
            # Load data
            data = self.load_data(filepath)
            logger.info(f"   Loaded {len(data)} candles")
            
            for strategy in strategies:
                try:
                    # Generate signals
                    trades = strategy.generate_signals(data)
                    
                    # Analyze performance
                    result = self.analyze_trades(trades, strategy.name, timeframe)
                    all_results.append(result)
                    
                    logger.info(f"   {strategy.name}: {result['total_trades']} trades, "
                               f"{result['win_rate']:.1%} win rate, "
                               f"{result['total_return']:.2%} return")
                    
                except Exception as e:
                    logger.error(f"   Error testing {strategy.name}: {e}")
        
        # Save results
        os.makedirs('backtest_results', exist_ok=True)
        with open('backtest_results/multi_timeframe_results.json', 'w') as f:
            json.dump(all_results, f, indent=2, default=str)
        
        # Find best combinations
        all_results.sort(key=lambda x: x['total_return'], reverse=True)
        
        logger.info("\n🏆 TOP 10 STRATEGY-TIMEFRAME COMBINATIONS:")
        for i, result in enumerate(all_results[:10], 1):
            logger.info(f"{i:2d}. {result['strategy']:<20} ({result['timeframe']:>3}): "
                       f"Return={result['total_return']:+7.2%} | "
                       f"WinRate={result['win_rate']:5.1%} | "
                       f"Sharpe={result['sharpe_ratio']:+5.2f} | "
                       f"Trades={result['total_trades']:3d}")
        
        return all_results

def main():
    """Run comprehensive multi-timeframe backtesting"""
    
    logger.info("🚀 Starting Advanced Multi-Timeframe Backtesting")
    logger.info("📈 Testing 8 strategies across 5 timeframes")
    
    backtester = MultiTimeframeBacktester()
    results = backtester.run_comprehensive_backtest()
    
    if results:
        # Find absolute best
        best = results[0]
        logger.info(f"\n🥇 ABSOLUTE BEST STRATEGY:")
        logger.info(f"   Strategy: {best['strategy']}")
        logger.info(f"   Timeframe: {best['timeframe']}")
        logger.info(f"   Total Return: {best['total_return']:.2%}")
        logger.info(f"   Win Rate: {best['win_rate']:.1%}")
        logger.info(f"   Sharpe Ratio: {best['sharpe_ratio']:.2f}")
        logger.info(f"   Total Trades: {best['total_trades']}")
        
        logger.info("\n✅ Results saved to backtest_results/multi_timeframe_results.json")
    else:
        logger.error("❌ No results generated")

if __name__ == "__main__":
    main()