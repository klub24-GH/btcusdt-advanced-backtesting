#!/usr/bin/env python3
"""
Strategy Backtester for BTCUSDT Trading
Tests multiple trading strategies on historical data to find winners
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import logging
from datetime import datetime, timedelta
import json
import os
from concurrent.futures import ProcessPoolExecutor, as_completed

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class BacktestResult:
    """Results from a backtest run"""
    strategy_name: str
    timeframe: str
    total_return: float
    annual_return: float
    max_drawdown: float
    win_rate: float
    profit_factor: float
    sharpe_ratio: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    avg_win: float
    avg_loss: float
    largest_win: float
    largest_loss: float
    trades: List[Dict] = field(default_factory=list)
    equity_curve: List[float] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'strategy_name': self.strategy_name,
            'timeframe': self.timeframe,
            'total_return': self.total_return,
            'annual_return': self.annual_return,
            'max_drawdown': self.max_drawdown,
            'win_rate': self.win_rate,
            'profit_factor': self.profit_factor,
            'sharpe_ratio': self.sharpe_ratio,
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'avg_win': self.avg_win,
            'avg_loss': self.avg_loss,
            'largest_win': self.largest_win,
            'largest_loss': self.largest_loss,
        }

class TradingStrategy(ABC):
    """Abstract base class for trading strategies"""
    
    def __init__(self, name: str, params: Dict = None):
        self.name = name
        self.params = params or {}
    
    @abstractmethod
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate trading signals for the given data"""
        pass
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate technical indicators"""
        df = df.copy()
        
        # Simple Moving Averages
        df['sma_10'] = df['close'].rolling(10).mean()
        df['sma_20'] = df['close'].rolling(20).mean()
        df['sma_50'] = df['close'].rolling(50).mean()
        
        # Exponential Moving Averages
        df['ema_12'] = df['close'].ewm(span=12).mean()
        df['ema_26'] = df['close'].ewm(span=26).mean()
        
        # MACD
        df['macd'] = df['ema_12'] - df['ema_26']
        df['macd_signal'] = df['macd'].ewm(span=9).mean()
        df['macd_histogram'] = df['macd'] - df['macd_signal']
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # Bollinger Bands
        df['bb_middle'] = df['close'].rolling(20).mean()
        bb_std = df['close'].rolling(20).std()
        df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
        df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
        
        # Volume indicators
        df['volume_sma'] = df['volume'].rolling(20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_sma']
        
        # Momentum
        df['momentum_1'] = df['close'].pct_change(1)
        df['momentum_5'] = df['close'].pct_change(5)
        df['momentum_10'] = df['close'].pct_change(10)
        
        # Volatility
        df['volatility'] = df['close'].rolling(20).std()
        
        return df

class MomentumStrategy(TradingStrategy):
    """Simple momentum-based strategy"""
    
    def __init__(self, params: Dict = None):
        default_params = {
            'momentum_period': 10,
            'momentum_threshold': 0.005,  # 0.5%
            'volume_threshold': 1.2
        }
        if params:
            default_params.update(params)
        super().__init__("Momentum", default_params)
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = self.calculate_indicators(df)
        
        momentum_period = self.params['momentum_period']
        momentum_threshold = self.params['momentum_threshold']
        volume_threshold = self.params['volume_threshold']
        
        # Calculate momentum
        df['momentum'] = df['close'].pct_change(momentum_period)
        
        # Generate signals
        df['signal'] = 0
        df.loc[(df['momentum'] > momentum_threshold) & 
               (df['volume_ratio'] > volume_threshold), 'signal'] = 1  # Buy
        df.loc[df['momentum'] < -momentum_threshold, 'signal'] = -1  # Sell
        
        return df

class MACDStrategy(TradingStrategy):
    """MACD crossover strategy"""
    
    def __init__(self, params: Dict = None):
        default_params = {
            'fast_period': 12,
            'slow_period': 26,
            'signal_period': 9
        }
        if params:
            default_params.update(params)
        super().__init__("MACD", default_params)
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = self.calculate_indicators(df)
        
        # Generate signals
        df['signal'] = 0
        df.loc[(df['macd'] > df['macd_signal']) & 
               (df['macd'].shift(1) <= df['macd_signal'].shift(1)), 'signal'] = 1  # Buy
        df.loc[(df['macd'] < df['macd_signal']) & 
               (df['macd'].shift(1) >= df['macd_signal'].shift(1)), 'signal'] = -1  # Sell
        
        return df

class MeanReversionStrategy(TradingStrategy):
    """Bollinger Bands mean reversion strategy"""
    
    def __init__(self, params: Dict = None):
        default_params = {
            'bb_period': 20,
            'bb_std': 2.0,
            'rsi_oversold': 30,
            'rsi_overbought': 70
        }
        if params:
            default_params.update(params)
        super().__init__("MeanReversion", default_params)
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = self.calculate_indicators(df)
        
        rsi_oversold = self.params['rsi_oversold']
        rsi_overbought = self.params['rsi_overbought']
        
        # Generate signals
        df['signal'] = 0
        df.loc[(df['close'] <= df['bb_lower']) & (df['rsi'] < rsi_oversold), 'signal'] = 1  # Buy
        df.loc[(df['close'] >= df['bb_upper']) & (df['rsi'] > rsi_overbought), 'signal'] = -1  # Sell
        
        return df

class ScalpingStrategy(TradingStrategy):
    """High-frequency scalping strategy"""
    
    def __init__(self, params: Dict = None):
        default_params = {
            'fast_ema': 5,
            'slow_ema': 10,
            'momentum_threshold': 0.002,  # 0.2%
            'volume_spike': 1.5
        }
        if params:
            default_params.update(params)
        super().__init__("Scalping", default_params)
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = self.calculate_indicators(df)
        
        fast_ema = self.params['fast_ema']
        slow_ema = self.params['slow_ema']
        momentum_threshold = self.params['momentum_threshold']
        volume_spike = self.params['volume_spike']
        
        # Calculate fast EMAs for scalping
        df['ema_fast'] = df['close'].ewm(span=fast_ema).mean()
        df['ema_slow'] = df['close'].ewm(span=slow_ema).mean()
        
        # Generate signals
        df['signal'] = 0
        
        # Buy: Fast EMA above slow EMA + momentum + volume
        buy_condition = (
            (df['ema_fast'] > df['ema_slow']) &
            (df['momentum_1'] > momentum_threshold) &
            (df['volume_ratio'] > volume_spike)
        )
        
        # Sell: Fast EMA below slow EMA or negative momentum
        sell_condition = (
            (df['ema_fast'] < df['ema_slow']) |
            (df['momentum_1'] < -momentum_threshold)
        )
        
        df.loc[buy_condition, 'signal'] = 1
        df.loc[sell_condition, 'signal'] = -1
        
        return df

class BreakoutStrategy(TradingStrategy):
    """Price breakout strategy"""
    
    def __init__(self, params: Dict = None):
        default_params = {
            'lookback_period': 20,
            'breakout_threshold': 0.01,  # 1%
            'volume_confirmation': 1.5
        }
        if params:
            default_params.update(params)
        super().__init__("Breakout", default_params)
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = self.calculate_indicators(df)
        
        lookback = self.params['lookback_period']
        threshold = self.params['breakout_threshold']
        volume_conf = self.params['volume_confirmation']
        
        # Calculate resistance and support levels
        df['resistance'] = df['high'].rolling(lookback).max()
        df['support'] = df['low'].rolling(lookback).min()
        
        # Generate signals
        df['signal'] = 0
        
        # Buy: Break above resistance with volume
        breakout_up = (
            (df['close'] > df['resistance'].shift(1) * (1 + threshold)) &
            (df['volume_ratio'] > volume_conf)
        )
        
        # Sell: Break below support
        breakout_down = (
            df['close'] < df['support'].shift(1) * (1 - threshold)
        )
        
        df.loc[breakout_up, 'signal'] = 1
        df.loc[breakout_down, 'signal'] = -1
        
        return df

class BacktestEngine:
    """Backtesting engine for trading strategies"""
    
    def __init__(self, initial_capital: float = 100000, 
                 commission: float = 0.001,  # 0.1%
                 slippage: float = 0.0005):  # 0.05%
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage
    
    def run_backtest(self, strategy: TradingStrategy, df: pd.DataFrame, 
                    stop_loss: float = None, take_profit: float = None) -> BacktestResult:
        """Run backtest for a strategy"""
        
        # Generate signals
        df_signals = strategy.generate_signals(df)
        
        # Initialize tracking variables
        capital = self.initial_capital
        position = 0  # 0 = no position, 1 = long, -1 = short
        entry_price = 0
        trades = []
        equity_curve = [capital]
        
        for i in range(1, len(df_signals)):
            current_row = df_signals.iloc[i]
            prev_row = df_signals.iloc[i-1]
            
            current_price = current_row['close']
            signal = current_row['signal']
            
            # Check for stop loss or take profit
            if position != 0:
                if position == 1:  # Long position
                    if stop_loss and current_price <= entry_price * (1 - stop_loss):
                        # Stop loss hit
                        exit_price = entry_price * (1 - stop_loss)
                        pnl = (exit_price - entry_price) * (capital / entry_price)
                        pnl -= abs(pnl) * (self.commission + self.slippage)
                        capital += pnl
                        
                        trades.append({
                            'entry_time': entry_time,
                            'exit_time': current_row['timestamp'],
                            'entry_price': entry_price,
                            'exit_price': exit_price,
                            'pnl': pnl,
                            'pnl_pct': (exit_price - entry_price) / entry_price,
                            'reason': 'stop_loss'
                        })
                        position = 0
                        
                    elif take_profit and current_price >= entry_price * (1 + take_profit):
                        # Take profit hit
                        exit_price = entry_price * (1 + take_profit)
                        pnl = (exit_price - entry_price) * (capital / entry_price)
                        pnl -= abs(pnl) * (self.commission + self.slippage)
                        capital += pnl
                        
                        trades.append({
                            'entry_time': entry_time,
                            'exit_time': current_row['timestamp'],
                            'entry_price': entry_price,
                            'exit_price': exit_price,
                            'pnl': pnl,
                            'pnl_pct': (exit_price - entry_price) / entry_price,
                            'reason': 'take_profit'
                        })
                        position = 0
            
            # Process signals
            if signal == 1 and position != 1:  # Buy signal
                if position == -1:  # Close short position first
                    pnl = (entry_price - current_price) * (capital / entry_price)
                    pnl -= abs(pnl) * (self.commission + self.slippage)
                    capital += pnl
                    
                    trades.append({
                        'entry_time': entry_time,
                        'exit_time': current_row['timestamp'],
                        'entry_price': entry_price,
                        'exit_price': current_price,
                        'pnl': pnl,
                        'pnl_pct': (entry_price - current_price) / entry_price,
                        'reason': 'signal'
                    })
                
                # Open long position
                position = 1
                entry_price = current_price * (1 + self.slippage)
                entry_time = current_row['timestamp']
                
            elif signal == -1 and position != -1:  # Sell signal
                if position == 1:  # Close long position first
                    pnl = (current_price - entry_price) * (capital / entry_price)
                    pnl -= abs(pnl) * (self.commission + self.slippage)
                    capital += pnl
                    
                    trades.append({
                        'entry_time': entry_time,
                        'exit_time': current_row['timestamp'],
                        'entry_price': entry_price,
                        'exit_price': current_price,
                        'pnl': pnl,
                        'pnl_pct': (current_price - entry_price) / entry_price,
                        'reason': 'signal'
                    })
                
                # Open short position
                position = -1
                entry_price = current_price * (1 - self.slippage)
                entry_time = current_row['timestamp']
            
            # Update equity curve
            if position == 1:
                unrealized_pnl = (current_price - entry_price) * (capital / entry_price)
                current_equity = capital + unrealized_pnl
            elif position == -1:
                unrealized_pnl = (entry_price - current_price) * (capital / entry_price)
                current_equity = capital + unrealized_pnl
            else:
                current_equity = capital
                
            equity_curve.append(current_equity)
        
        # Close any remaining position
        if position != 0:
            final_price = df_signals.iloc[-1]['close']
            if position == 1:
                pnl = (final_price - entry_price) * (capital / entry_price)
            else:
                pnl = (entry_price - final_price) * (capital / entry_price)
            
            pnl -= abs(pnl) * (self.commission + self.slippage)
            capital += pnl
            
            trades.append({
                'entry_time': entry_time,
                'exit_time': df_signals.iloc[-1]['timestamp'],
                'entry_price': entry_price,
                'exit_price': final_price,
                'pnl': pnl,
                'pnl_pct': pnl / (capital - pnl),
                'reason': 'final'
            })
        
        # Calculate performance metrics
        return self._calculate_performance(strategy.name, trades, equity_curve, df_signals.iloc[0]['timestamp'], df_signals.iloc[-1]['timestamp'])
    
    def _calculate_performance(self, strategy_name: str, trades: List[Dict], 
                             equity_curve: List[float], start_date, end_date) -> BacktestResult:
        """Calculate performance metrics"""
        
        if not trades:
            return BacktestResult(
                strategy_name=strategy_name,
                timeframe="",
                total_return=0.0,
                annual_return=0.0,
                max_drawdown=0.0,
                win_rate=0.0,
                profit_factor=0.0,
                sharpe_ratio=0.0,
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
                avg_win=0.0,
                avg_loss=0.0,
                largest_win=0.0,
                largest_loss=0.0,
                trades=[],
                equity_curve=equity_curve
            )
        
        # Basic metrics
        final_capital = equity_curve[-1]
        total_return = (final_capital - self.initial_capital) / self.initial_capital
        
        # Calculate annualized return
        days = (end_date - start_date).days if hasattr((end_date - start_date), 'days') else 365
        annual_return = ((final_capital / self.initial_capital) ** (365 / max(days, 1))) - 1
        
        # Max drawdown
        peak = self.initial_capital
        max_dd = 0
        for equity in equity_curve:
            if equity > peak:
                peak = equity
            dd = (peak - equity) / peak
            if dd > max_dd:
                max_dd = dd
        
        # Trade statistics
        winning_trades = [t for t in trades if t['pnl'] > 0]
        losing_trades = [t for t in trades if t['pnl'] <= 0]
        
        win_rate = len(winning_trades) / len(trades) if trades else 0
        
        avg_win = np.mean([t['pnl'] for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t['pnl'] for t in losing_trades]) if losing_trades else 0
        
        largest_win = max([t['pnl'] for t in winning_trades]) if winning_trades else 0
        largest_loss = min([t['pnl'] for t in losing_trades]) if losing_trades else 0
        
        # Profit factor
        gross_profit = sum([t['pnl'] for t in winning_trades]) if winning_trades else 0
        gross_loss = abs(sum([t['pnl'] for t in losing_trades])) if losing_trades else 1
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
        
        # Sharpe ratio (simplified)
        returns = np.diff(equity_curve) / equity_curve[:-1]
        sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(252) if len(returns) > 1 and np.std(returns) > 0 else 0
        
        return BacktestResult(
            strategy_name=strategy_name,
            timeframe="",
            total_return=total_return,
            annual_return=annual_return,
            max_drawdown=max_dd,
            win_rate=win_rate,
            profit_factor=profit_factor,
            sharpe_ratio=sharpe_ratio,
            total_trades=len(trades),
            winning_trades=len(winning_trades),
            losing_trades=len(losing_trades),
            avg_win=avg_win,
            avg_loss=avg_loss,
            largest_win=largest_win,
            largest_loss=largest_loss,
            trades=trades,
            equity_curve=equity_curve
        )

def run_comprehensive_backtest():
    """Run comprehensive backtest across all strategies and timeframes"""
    
    logger.info("🚀 Starting comprehensive backtest")
    
    # Define strategies to test
    strategies = [
        MomentumStrategy(),
        MomentumStrategy({'momentum_period': 5, 'momentum_threshold': 0.003}),
        MomentumStrategy({'momentum_period': 20, 'momentum_threshold': 0.01}),
        MACDStrategy(),
        MeanReversionStrategy(),
        ScalpingStrategy(),
        ScalpingStrategy({'fast_ema': 3, 'slow_ema': 7, 'momentum_threshold': 0.001}),
        BreakoutStrategy(),
        BreakoutStrategy({'lookback_period': 10, 'breakout_threshold': 0.005}),
    ]
    
    # Timeframes to test
    timeframes = ['1m', '5m', '15m', '1h']
    
    # Risk management parameters to test
    risk_params = [
        {},  # No stop loss/take profit
        {'stop_loss': 0.02, 'take_profit': 0.04},  # 2% SL, 4% TP
        {'stop_loss': 0.01, 'take_profit': 0.02},  # 1% SL, 2% TP
        {'stop_loss': 0.005, 'take_profit': 0.01}, # 0.5% SL, 1% TP
    ]
    
    results = []
    backtest_engine = BacktestEngine()
    
    for timeframe in timeframes:
        try:
            # Load data
            data_file = f"historical_data/BTCUSDT_{timeframe}_2024-01-01_to_2025-01-01.csv"
            if not os.path.exists(data_file):
                logger.warning(f"📁 Data file not found: {data_file}")
                continue
                
            df = pd.read_csv(data_file)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            logger.info(f"📊 Testing {timeframe} timeframe - {len(df)} candles")
            
            for strategy in strategies:
                for risk_param in risk_params:
                    try:
                        logger.info(f"🔄 Testing {strategy.name} on {timeframe} with risk params: {risk_param}")
                        
                        result = backtest_engine.run_backtest(
                            strategy, df, 
                            stop_loss=risk_param.get('stop_loss'),
                            take_profit=risk_param.get('take_profit')
                        )
                        
                        result.timeframe = timeframe
                        result.strategy_name = f"{strategy.name}_{str(risk_param)}"
                        
                        results.append(result)
                        
                        logger.info(f"✅ {strategy.name}: Return={result.total_return:.2%}, Win Rate={result.win_rate:.2%}, Trades={result.total_trades}")
                        
                    except Exception as e:
                        logger.error(f"❌ Error testing {strategy.name} on {timeframe}: {e}")
                        continue
                        
        except Exception as e:
            logger.error(f"❌ Error loading {timeframe} data: {e}")
            continue
    
    # Save results
    os.makedirs('backtest_results', exist_ok=True)
    
    results_dict = [result.to_dict() for result in results]
    with open('backtest_results/comprehensive_backtest.json', 'w') as f:
        json.dump(results_dict, f, indent=2, default=str)
    
    # Find best strategies
    best_strategies = sorted(results, key=lambda x: x.total_return, reverse=True)[:10]
    
    logger.info("\n🏆 TOP 10 BEST STRATEGIES:")
    for i, result in enumerate(best_strategies, 1):
        logger.info(f"{i:2d}. {result.strategy_name} ({result.timeframe}): "
                   f"Return={result.total_return:.2%}, Win Rate={result.win_rate:.2%}, "
                   f"Sharpe={result.sharpe_ratio:.2f}, Trades={result.total_trades}")
    
    return results

if __name__ == "__main__":
    run_comprehensive_backtest()