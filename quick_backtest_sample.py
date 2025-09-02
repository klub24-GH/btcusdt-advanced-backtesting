#!/usr/bin/env python3
"""
Quick Backtesting Sample
Download smaller data samples and test strategies quickly
"""

import json
import requests
import csv
from datetime import datetime, timezone, timedelta
import time
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class QuickBacktester:
    """Quick backtesting with sample data"""
    
    def __init__(self):
        self.base_url = "https://api.binance.com/api/v3/klines"
        
    def download_sample_data(self, symbol="BTCUSDT", interval="5m", days=30):
        """Download sample data for quick testing"""
        
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(days=days)
        
        start_ts = int(start_time.timestamp() * 1000)
        end_ts = int(end_time.timestamp() * 1000)
        
        logger.info(f"📊 Downloading {days} days of {symbol} {interval} data")
        
        params = {
            'symbol': symbol,
            'interval': interval,
            'startTime': start_ts,
            'endTime': end_ts,
            'limit': 1000
        }
        
        try:
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # Process data
            processed_data = []
            for candle in data:
                processed_candle = {
                    'timestamp': datetime.fromtimestamp(candle[0] / 1000, tz=timezone.utc).isoformat(),
                    'open': float(candle[1]),
                    'high': float(candle[2]),
                    'low': float(candle[3]),
                    'close': float(candle[4]),
                    'volume': float(candle[5])
                }
                processed_data.append(processed_candle)
            
            # Save data
            os.makedirs('sample_data', exist_ok=True)
            filename = f"sample_data/{symbol}_{interval}_{days}days.csv"
            
            with open(filename, 'w', newline='') as csvfile:
                fieldnames = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(processed_data)
            
            logger.info(f"✅ Downloaded {len(processed_data)} candles to {filename}")
            return filename, processed_data
            
        except Exception as e:
            logger.error(f"❌ Download failed: {e}")
            return None, []

    def simple_momentum_strategy(self, data, momentum_period=5, threshold=0.01):
        """Simple momentum strategy"""
        
        if len(data) < momentum_period + 1:
            return []
        
        trades = []
        position = None  # None, 'long', 'short'
        entry_price = 0
        
        for i in range(momentum_period, len(data)):
            current_price = data[i]['close']
            past_price = data[i - momentum_period]['close']
            momentum = (current_price - past_price) / past_price
            
            # Buy signal
            if momentum > threshold and position != 'long':
                if position == 'short':
                    # Close short position
                    pnl = (entry_price - current_price) / entry_price
                    trades.append({
                        'type': 'close_short',
                        'price': current_price,
                        'pnl': pnl,
                        'timestamp': data[i]['timestamp']
                    })
                
                # Open long position
                position = 'long'
                entry_price = current_price
                trades.append({
                    'type': 'open_long',
                    'price': current_price,
                    'timestamp': data[i]['timestamp']
                })
            
            # Sell signal
            elif momentum < -threshold and position != 'short':
                if position == 'long':
                    # Close long position
                    pnl = (current_price - entry_price) / entry_price
                    trades.append({
                        'type': 'close_long',
                        'price': current_price,
                        'pnl': pnl,
                        'timestamp': data[i]['timestamp']
                    })
                
                # Open short position
                position = 'short'
                entry_price = current_price
                trades.append({
                    'type': 'open_short',
                    'price': current_price,
                    'timestamp': data[i]['timestamp']
                })
        
        return trades
    
    def simple_mean_reversion_strategy(self, data, window=20, std_mult=2):
        """Simple mean reversion strategy using price bands"""
        
        if len(data) < window + 1:
            return []
        
        trades = []
        position = None
        entry_price = 0
        
        for i in range(window, len(data)):
            current_price = data[i]['close']
            
            # Calculate moving average and standard deviation
            prices = [data[j]['close'] for j in range(i - window, i)]
            avg_price = sum(prices) / len(prices)
            
            variance = sum((p - avg_price) ** 2 for p in prices) / len(prices)
            std_dev = variance ** 0.5
            
            upper_band = avg_price + (std_dev * std_mult)
            lower_band = avg_price - (std_dev * std_mult)
            
            # Buy signal (price below lower band)
            if current_price < lower_band and position != 'long':
                if position == 'short':
                    pnl = (entry_price - current_price) / entry_price
                    trades.append({
                        'type': 'close_short',
                        'price': current_price,
                        'pnl': pnl,
                        'timestamp': data[i]['timestamp']
                    })
                
                position = 'long'
                entry_price = current_price
                trades.append({
                    'type': 'open_long',
                    'price': current_price,
                    'timestamp': data[i]['timestamp']
                })
            
            # Sell signal (price above upper band)
            elif current_price > upper_band and position != 'short':
                if position == 'long':
                    pnl = (current_price - entry_price) / entry_price
                    trades.append({
                        'type': 'close_long',
                        'price': current_price,
                        'pnl': pnl,
                        'timestamp': data[i]['timestamp']
                    })
                
                position = 'short'
                entry_price = current_price
                trades.append({
                    'type': 'open_short',
                    'price': current_price,
                    'timestamp': data[i]['timestamp']
                })
        
        return trades
    
    def scalping_strategy(self, data, fast_window=3, slow_window=8, min_move=0.003):
        """Simple scalping strategy"""
        
        if len(data) < slow_window + 1:
            return []
        
        trades = []
        position = None
        entry_price = 0
        
        for i in range(slow_window, len(data)):
            current_price = data[i]['close']
            
            # Calculate fast and slow moving averages
            fast_prices = [data[j]['close'] for j in range(i - fast_window, i)]
            slow_prices = [data[j]['close'] for j in range(i - slow_window, i)]
            
            fast_avg = sum(fast_prices) / len(fast_prices)
            slow_avg = sum(slow_prices) / len(slow_prices)
            
            # Short-term momentum
            momentum = (current_price - data[i-1]['close']) / data[i-1]['close']
            
            # Buy signal
            if fast_avg > slow_avg and momentum > min_move and position != 'long':
                if position == 'short':
                    pnl = (entry_price - current_price) / entry_price
                    trades.append({
                        'type': 'close_short',
                        'price': current_price,
                        'pnl': pnl,
                        'timestamp': data[i]['timestamp']
                    })
                
                position = 'long'
                entry_price = current_price
                trades.append({
                    'type': 'open_long',
                    'price': current_price,
                    'timestamp': data[i]['timestamp']
                })
            
            # Sell signal
            elif fast_avg < slow_avg and momentum < -min_move and position != 'short':
                if position == 'long':
                    pnl = (current_price - entry_price) / entry_price
                    trades.append({
                        'type': 'close_long',
                        'price': current_price,
                        'pnl': pnl,
                        'timestamp': data[i]['timestamp']
                    })
                
                position = 'short'
                entry_price = current_price
                trades.append({
                    'type': 'open_short',
                    'price': current_price,
                    'timestamp': data[i]['timestamp']
                })
        
        return trades
    
    def analyze_trades(self, trades, strategy_name):
        """Analyze trading results"""
        
        if not trades:
            return {
                'strategy': strategy_name,
                'total_trades': 0,
                'profitable_trades': 0,
                'win_rate': 0,
                'total_return': 0,
                'avg_return': 0
            }
        
        # Filter only closing trades (with PnL)
        pnl_trades = [t for t in trades if 'pnl' in t]
        
        if not pnl_trades:
            return {
                'strategy': strategy_name,
                'total_trades': len(trades),
                'profitable_trades': 0,
                'win_rate': 0,
                'total_return': 0,
                'avg_return': 0
            }
        
        profitable_trades = [t for t in pnl_trades if t['pnl'] > 0]
        total_return = sum(t['pnl'] for t in pnl_trades)
        
        results = {
            'strategy': strategy_name,
            'total_trades': len(pnl_trades),
            'profitable_trades': len(profitable_trades),
            'win_rate': len(profitable_trades) / len(pnl_trades) if pnl_trades else 0,
            'total_return': total_return,
            'avg_return': total_return / len(pnl_trades) if pnl_trades else 0,
            'best_trade': max(t['pnl'] for t in pnl_trades) if pnl_trades else 0,
            'worst_trade': min(t['pnl'] for t in pnl_trades) if pnl_trades else 0
        }
        
        return results
    
    def run_quick_backtest(self):
        """Run quick backtest on sample data"""
        
        logger.info("🚀 Starting Quick Backtest")
        
        # Download sample data (30 days of 5-minute data)
        filename, data = self.download_sample_data("BTCUSDT", "5m", 30)
        
        if not data:
            logger.error("❌ Failed to download data")
            return
        
        logger.info(f"📊 Testing strategies on {len(data)} data points")
        
        # Test different strategies
        strategies = [
            ('Momentum (5, 0.5%)', lambda d: self.simple_momentum_strategy(d, 5, 0.005)),
            ('Momentum (10, 1%)', lambda d: self.simple_momentum_strategy(d, 10, 0.01)),
            ('Momentum (3, 0.3%)', lambda d: self.simple_momentum_strategy(d, 3, 0.003)),
            ('Mean Reversion (20, 2)', lambda d: self.simple_mean_reversion_strategy(d, 20, 2)),
            ('Mean Reversion (10, 1.5)', lambda d: self.simple_mean_reversion_strategy(d, 10, 1.5)),
            ('Scalping (3,8,0.3%)', lambda d: self.scalping_strategy(d, 3, 8, 0.003)),
            ('Scalping (5,12,0.2%)', lambda d: self.scalping_strategy(d, 5, 12, 0.002)),
        ]
        
        results = []
        
        for strategy_name, strategy_func in strategies:
            try:
                logger.info(f"🔄 Testing {strategy_name}")
                trades = strategy_func(data)
                analysis = self.analyze_trades(trades, strategy_name)
                results.append(analysis)
                
                logger.info(f"✅ {strategy_name}: {analysis['total_trades']} trades, "
                           f"{analysis['win_rate']:.1%} win rate, "
                           f"{analysis['total_return']:.2%} total return")
                           
            except Exception as e:
                logger.error(f"❌ Error testing {strategy_name}: {e}")
        
        # Sort by total return
        results.sort(key=lambda x: x['total_return'], reverse=True)
        
        # Save results
        os.makedirs('backtest_results', exist_ok=True)
        with open('backtest_results/quick_backtest_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        # Display top results
        logger.info("\n🏆 TOP 5 STRATEGIES:")
        for i, result in enumerate(results[:5], 1):
            logger.info(f"{i:2d}. {result['strategy']:<25} | "
                       f"Return: {result['total_return']:+7.2%} | "
                       f"Win Rate: {result['win_rate']:5.1%} | "
                       f"Trades: {result['total_trades']:3d}")
        
        logger.info(f"\n💾 Results saved to backtest_results/quick_backtest_results.json")
        
        return results

def main():
    """Run quick backtesting"""
    backtester = QuickBacktester()
    results = backtester.run_quick_backtest()
    
    if results:
        logger.info("🎉 Quick backtest completed successfully!")
        
        # Find best strategy
        best_strategy = results[0] if results else None
        if best_strategy and best_strategy['total_return'] > 0:
            logger.info(f"\n🥇 WINNING STRATEGY: {best_strategy['strategy']}")
            logger.info(f"   Total Return: {best_strategy['total_return']:.2%}")
            logger.info(f"   Win Rate: {best_strategy['win_rate']:.1%}")
            logger.info(f"   Total Trades: {best_strategy['total_trades']}")
            logger.info("\n✨ This strategy can be applied to real-time paper trading!")
        else:
            logger.info("⚠️  No profitable strategies found in this sample")
    else:
        logger.error("❌ Backtest failed")

if __name__ == "__main__":
    main()