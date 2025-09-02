#!/usr/bin/env python3
"""
Enhanced Paper Trading System with Real Market Data
Complete paper trading implementation with actual Binance data

SAFETY: 100% paper trading - NO REAL MONEY AT RISK
Features real market data integration for authentic trading experience
"""

import asyncio
import json
import time
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import os
import signal

from real_market_data_integration import SafePaperTradingDataProvider
from paper_trading_config import get_configuration

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [PAPER] %(message)s',
    handlers=[
        logging.FileHandler('/tmp/paper_trading.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class PaperTrade:
    """Paper trade execution record"""
    id: int
    timestamp: float
    action: str
    btc_amount: float
    usd_amount: float
    price: float
    fees: float
    confidence: float
    portfolio_value_before: float
    portfolio_value_after: float
    pnl: float = 0.0

@dataclass
class VirtualPortfolio:
    """Virtual trading portfolio with comprehensive tracking"""
    balance_usd: float = 10000.0
    balance_btc: float = 0.0
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    total_pnl: float = 0.0
    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0
    max_drawdown: float = 0.0
    peak_balance: float = 10000.0
    start_time: float = field(default_factory=time.time)
    
    def get_total_value(self, btc_price: float) -> float:
        return self.balance_usd + (self.balance_btc * btc_price)
    
    def get_win_rate(self) -> float:
        if self.total_trades == 0:
            return 0.0
        return (self.winning_trades / self.total_trades) * 100
    
    def get_profit_factor(self) -> float:
        """Calculate profit factor (gross profit / gross loss)"""
        if self.losing_trades == 0:
            return float('inf') if self.winning_trades > 0 else 0.0
        
        avg_win = self.total_pnl / max(self.winning_trades, 1) if self.winning_trades > 0 else 0
        avg_loss = abs(self.total_pnl) / self.losing_trades if self.losing_trades > 0 else 1
        
        return abs(avg_win / avg_loss) if avg_loss != 0 else 0.0

class EnhancedTradingDecisionEngine:
    """Enhanced decision engine with real market analysis"""
    
    def __init__(self, config: dict):
        self.config = config
        self.decisions_made = 0
        self.price_history = []
        self.volume_history = []
        self.decision_history = []
        # Portfolio tracking for profit optimization
        self.current_btc_balance = 0.0
        self.current_usd_balance = 100000.0
        self.avg_btc_cost = 0.0  # Track average cost basis for profit calculations
        self.last_buy_time = 0  # Track when we last bought for hold time logic
        
        # ADAPTIVE LEARNING SYSTEM
        self.trade_performance_history = []  # Track each trade's performance
        self.successful_patterns = {}  # Track what conditions lead to wins
        self.learning_rate = 0.1  # How fast to adapt
        self.confidence_adjustment = 0.0  # Dynamic confidence adjustment
        self.momentum_adjustment = 0.0  # Dynamic momentum threshold adjustment
        
    async def analyze_market_and_decide(self, market_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Comprehensive market analysis and decision making"""
        
        price = market_data['price']
        volume = market_data.get('volume', 1000)
        bid = market_data.get('bid', price - 0.5)
        ask = market_data.get('ask', price + 0.5)
        spread = ask - bid
        
        # Update history
        self.price_history.append({'price': price, 'timestamp': time.time()})
        self.volume_history.append({'volume': volume, 'timestamp': time.time()})
        
        # Limit history size
        max_history = 300  # 5 minutes at 1 second intervals
        self.price_history = self.price_history[-max_history:]
        self.volume_history = self.volume_history[-max_history:]
        
        # Technical analysis
        technical_signals = self._calculate_technical_indicators()
        
        # Generate trading decision
        decision = await self._generate_decision(
            price, volume, spread, technical_signals, market_data
        )
        
        self.decisions_made += 1
        
        if decision:
            self.decision_history.append({
                'timestamp': time.time(),
                'decision': decision,
                'price': price,
                'signals': technical_signals
            })
        
        return decision
    
    def _calculate_technical_indicators(self) -> Dict[str, Any]:
        """Calculate technical indicators from price history"""
        if len(self.price_history) < 10:
            return {'insufficient_data': True}
        
        prices = [p['price'] for p in self.price_history]
        volumes = [v['volume'] for v in self.volume_history]
        
        # Simple moving averages
        sma_10 = sum(prices[-10:]) / 10 if len(prices) >= 10 else prices[-1]
        sma_30 = sum(prices[-30:]) / 30 if len(prices) >= 30 else prices[-1]
        
        # Price momentum
        momentum_5min = (prices[-1] - prices[-min(300, len(prices))]) / prices[-min(300, len(prices))] * 100
        momentum_1min = (prices[-1] - prices[-min(60, len(prices))]) / prices[-min(60, len(prices))] * 100
        
        # Volume analysis
        avg_volume = sum(volumes[-30:]) / min(30, len(volumes))
        volume_ratio = volumes[-1] / avg_volume if avg_volume > 0 else 1.0
        
        # Volatility
        if len(prices) >= 20:
            recent_prices = prices[-20:]
            volatility = (max(recent_prices) - min(recent_prices)) / sum(recent_prices) * len(recent_prices)
        else:
            volatility = 0.01
        
        return {
            'sma_10': sma_10,
            'sma_30': sma_30,
            'momentum_5min': momentum_5min,
            'momentum_1min': momentum_1min,
            'volume_ratio': volume_ratio,
            'volatility': volatility,
            'price_above_sma10': prices[-1] > sma_10,
            'price_above_sma30': prices[-1] > sma_30,
            'sma_crossover': sma_10 > sma_30 if len(prices) >= 30 else None
        }
    
    async def _generate_decision(self, price: float, volume: float, spread: float, 
                                signals: Dict[str, Any], market_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """SIMPLE SCALPING DECISIONS - Buy any upward momentum, let scalping logic handle exits"""
        
        if signals.get('insufficient_data'):
            return None
        
        # Get simple signals
        momentum_1min = signals['momentum_1min']
        volume_ratio = signals['volume_ratio']
        
        # Check if we have BTC to determine action
        current_btc = getattr(self, 'current_btc_balance', 0)
        current_usd = getattr(self, 'current_usd_balance', 100000)
        
        decision = None
        confidence = 0.7  # High confidence for simple strategy
        reason = ""
        
        # SIMPLE SCALPING RULES
        if current_btc > 0.001:
            # Already holding BTC - always try to sell for scalping logic to evaluate
            decision = "sell"
            reason = f"SCALP-CHECK: Hold BTC, check if profit target met"
            
        elif current_usd > 1000:  # Have USD to buy
            # Buy on ANY positive momentum (let scalping handle exits)
            if momentum_1min > 0.02:  # 0.02% upward momentum 
                decision = "buy"
                reason = f"SCALP-BUY: Upward momentum {momentum_1min:.3f}%"
            # Also buy on strong volume spikes even with small momentum
            elif volume_ratio > 1.5 and momentum_1min > -0.1:  # Volume spike + not falling hard
                decision = "buy" 
                reason = f"VOLUME-BUY: {volume_ratio:.2f}x volume"
        
        if decision:
            return {
                'action': decision,
                'confidence': confidence,
                'reason': reason,
                'price': price,
                'signals': signals,
                'market_data': market_data
            }
        
        return None
    
    def learn_from_trade_result(self, trade_data: dict, profit_pct: float):
        """ADAPTIVE LEARNING: Learn from each trade result to improve future decisions"""
        
        # Extract trade conditions
        momentum = trade_data.get('momentum', 0)
        confidence = trade_data.get('confidence', 0)  
        volatility = trade_data.get('volatility', 0)
        volume_ratio = trade_data.get('volume_ratio', 1)
        
        # Record trade result
        trade_result = {
            'momentum': momentum,
            'confidence': confidence,
            'volatility': volatility, 
            'volume_ratio': volume_ratio,
            'profit_pct': profit_pct,
            'profitable': profit_pct > 0,
            'timestamp': time.time()
        }
        
        self.trade_performance_history.append(trade_result)
        
        # Keep only last 100 trades for learning
        if len(self.trade_performance_history) > 100:
            self.trade_performance_history = self.trade_performance_history[-100:]
        
        # ADAPTIVE PARAMETER ADJUSTMENT
        if len(self.trade_performance_history) >= 10:  # Need minimum data
            recent_trades = self.trade_performance_history[-20:]  # Last 20 trades
            profitable_trades = [t for t in recent_trades if t['profitable']]
            losing_trades = [t for t in recent_trades if not t['profitable']]
            
            win_rate = len(profitable_trades) / len(recent_trades)
            
            # ADJUST CONFIDENCE THRESHOLD based on performance
            if win_rate < 0.3:  # Low win rate - be more selective
                self.confidence_adjustment += self.learning_rate * 0.1
                logger.info(f"🧠 LEARNING: Low win rate {win_rate:.1%}, increasing confidence requirement by {self.confidence_adjustment:.3f}")
            elif win_rate > 0.7:  # High win rate - be more aggressive
                self.confidence_adjustment -= self.learning_rate * 0.05  
                logger.info(f"🧠 LEARNING: High win rate {win_rate:.1%}, decreasing confidence requirement by {abs(self.confidence_adjustment):.3f}")
            
            # ADJUST MOMENTUM SENSITIVITY based on successful patterns
            if profitable_trades:
                avg_profitable_momentum = sum(t['momentum'] for t in profitable_trades) / len(profitable_trades)
                avg_losing_momentum = sum(abs(t['momentum']) for t in losing_trades) / max(1, len(losing_trades))
                
                if avg_profitable_momentum > avg_losing_momentum:
                    self.momentum_adjustment -= self.learning_rate * 0.0001  # More sensitive
                    logger.info(f"🧠 LEARNING: Strong momentum = profits, increasing sensitivity")
                else:
                    self.momentum_adjustment += self.learning_rate * 0.0001  # Less sensitive  
                    logger.info(f"🧠 LEARNING: Weak momentum = better, decreasing sensitivity")
            
            # Limit adjustments to reasonable ranges
            self.confidence_adjustment = max(-0.3, min(0.3, self.confidence_adjustment))
            self.momentum_adjustment = max(-0.001, min(0.001, self.momentum_adjustment))

class EnhancedPaperTradingSystem:
    """Enhanced paper trading system with real market data"""
    
    def __init__(self, config_type: str = "default"):
        self.config = get_configuration(config_type)
        self.portfolio = VirtualPortfolio(balance_usd=self.config['starting_balance'])
        self.market_provider = SafePaperTradingDataProvider(use_real_data=self.config['use_real_data'])
        self.decision_engine = EnhancedTradingDecisionEngine(self.config)
        
        self.trade_history: List[PaperTrade] = []
        self.running = False
        self.trade_id_counter = 1
        self.last_report_time = time.time()
        
        # Performance tracking
        self.session_start = time.time()
        self.total_decisions = 0
        self.trades_executed = 0
        
        # SIMPLE SCALPING STATE - Focus on wins!
        self.last_buy_price = 0.0
        self.last_buy_time = 0.0
        self.target_profit_pct = 0.8  # Target 0.8% profit per trade
        self.stop_loss_pct = 0.4     # Stop loss at 0.4% loss
        self.min_hold_seconds = 10   # Hold for at least 10 seconds
        
        # Safety verification
        self._verify_paper_trading_safety()
        
        logger.info("🚀 Enhanced Paper Trading System Initialized")
        logger.info(f"   Configuration: {config_type.title()}")
        logger.info(f"   Starting Balance: ${self.portfolio.balance_usd:,.2f} (VIRTUAL)")
        logger.info(f"   Paper Trading Mode: ✅ ENABLED")
        logger.info(f"   Real Market Data: {'✅ ENABLED' if self.config['use_real_data'] else '❌ DISABLED'}")
    
    def _verify_paper_trading_safety(self):
        """Verify all safety settings"""
        safety_checks = [
            (self.config['paper_trading_mode'] == True, "Paper trading mode must be enabled"),
            (self.config['real_money_trading'] == False, "Real money trading must be disabled"),
            (self.config['safety_checks'] == True, "Safety checks must be enabled"),
        ]
        
        for check, message in safety_checks:
            if not check:
                raise RuntimeError(f"❌ SAFETY ERROR: {message}")
        
        logger.info("✅ Paper trading safety verified")
    
    async def execute_paper_trade(self, decision: Dict[str, Any]) -> bool:
        """Execute SIMPLE SCALPING TRADES for consistent wins"""
        
        action = decision['action']
        price = decision['price']
        confidence = decision['confidence']
        current_time = time.time()
        
        # SIMPLE SCALPING LOGIC - Focus on small consistent profits
        if action == "buy":
            # Only buy if we don't already have BTC
            if self.portfolio.balance_btc > 0:
                return False
                
            # Use fixed trade size for consistency (10% of portfolio)
            portfolio_value = self.portfolio.get_total_value(price)
            trade_size_usd = portfolio_value * 0.10  # Fixed 10% per trade
            
            if trade_size_usd < self.config['min_trade_size']:
                trade_size_usd = self.config['min_trade_size']
                
            if self.portfolio.balance_usd >= trade_size_usd:
                fees = trade_size_usd * (self.config['trading_fees_pct'] / 100)
                net_usd_spent = trade_size_usd + fees
                btc_purchased = trade_size_usd / price
                
                self.portfolio.balance_usd -= net_usd_spent
                self.portfolio.balance_btc += btc_purchased
                
                # Store buy details for scalping logic
                self.last_buy_price = price
                self.last_buy_time = current_time
                
                logger.info(f"🟢 SCALP BUY: {btc_purchased:.6f} BTC at ${price:,.2f} (${trade_size_usd:.0f}) Target: +{self.target_profit_pct}%")
                return True
                
        elif action == "sell" and self.portfolio.balance_btc > 0:
            # SCALPING SELL LOGIC - Take profits or cut losses quickly
            
            # Calculate current profit/loss percentage
            current_profit_pct = ((price - self.last_buy_price) / self.last_buy_price) * 100
            time_held = current_time - self.last_buy_time
            
            should_sell = False
            sell_reason = ""
            
            # Sell conditions for scalping
            if current_profit_pct >= self.target_profit_pct:
                should_sell = True
                sell_reason = f"TARGET PROFIT: +{current_profit_pct:.2f}%"
            elif current_profit_pct <= -self.stop_loss_pct:
                should_sell = True  
                sell_reason = f"STOP LOSS: {current_profit_pct:.2f}%"
            elif time_held >= 60 and current_profit_pct > 0.1:  # Take any profit after 1 minute
                should_sell = True
                sell_reason = f"TIME PROFIT: +{current_profit_pct:.2f}% after {time_held:.0f}s"
            elif time_held >= 120:  # Force exit after 2 minutes regardless
                should_sell = True
                sell_reason = f"TIME EXIT: {current_profit_pct:.2f}% after {time_held:.0f}s"
                
            if should_sell and time_held >= self.min_hold_seconds:
                # Sell all BTC
                btc_to_sell = self.portfolio.balance_btc
                usd_received = btc_to_sell * price
                fees = usd_received * (self.config['trading_fees_pct'] / 100)
                net_usd_received = usd_received - fees
                
                self.portfolio.balance_btc = 0.0
                self.portfolio.balance_usd += net_usd_received
                
                logger.info(f"🔴 SCALP SELL: {btc_to_sell:.6f} BTC at ${price:,.2f} - {sell_reason}")
                return True
        
        
        # Update portfolio statistics
        self.portfolio.total_trades += 1
        if trade.pnl > 0:
            self.portfolio.winning_trades += 1
        else:
            self.portfolio.losing_trades += 1
        
        self.portfolio.total_pnl += trade.pnl
        self.portfolio.realized_pnl += trade.pnl
        
        # Update peak and drawdown
        current_value = self.portfolio.get_total_value(price)
        if current_value > self.portfolio.peak_balance:
            self.portfolio.peak_balance = current_value
        
        drawdown = (self.portfolio.peak_balance - current_value) / self.portfolio.peak_balance
        self.portfolio.max_drawdown = max(self.portfolio.max_drawdown, drawdown)
        
        return True
    
    async def main_trading_loop(self):
        """Main paper trading loop"""
        logger.info("🔄 Starting enhanced paper trading loop")
        
        while self.running:
            try:
                # Get market data
                market_data = await self.market_provider.get_market_data()
                
                # Analyze and make decision
                decision = await self.decision_engine.analyze_market_and_decide(market_data)
                self.total_decisions += 1
                
                # Execute trade if decision made
                if decision:
                    await self.execute_paper_trade(decision)
                
                # Periodic reporting
                if time.time() - self.last_report_time > self.config['reporting_interval']:
                    await self.report_status(market_data)
                    self.last_report_time = time.time()
                
                # Wait for next cycle
                await asyncio.sleep(self.config['decision_frequency'])
                
            except Exception as e:
                logger.error(f"❌ Trading loop error: {e}")
                await asyncio.sleep(1)
    
    async def report_status(self, market_data: Dict[str, Any]):
        """Report current portfolio and performance status"""
        current_price = market_data['price']
        portfolio_value = self.portfolio.get_total_value(current_price)
        total_return = (portfolio_value - self.config['starting_balance']) / self.config['starting_balance'] * 100
        session_duration = time.time() - self.session_start
        
        # Calculate performance metrics
        decisions_per_minute = (self.total_decisions / session_duration) * 60 if session_duration > 0 else 0
        trades_per_hour = (self.trades_executed / session_duration) * 3600 if session_duration > 0 else 0
        
        # Market data status
        connection_status = self.market_provider.get_connection_status()
        
        logger.info("=" * 80)
        logger.info("📊 ENHANCED PAPER TRADING STATUS")
        logger.info(f"   Current BTC Price: ${current_price:,.2f} ({market_data.get('source', 'unknown')})")
        logger.info(f"   Portfolio Value: ${portfolio_value:,.2f} (Return: {total_return:+.2f}%)")
        logger.info(f"   USD Balance: ${self.portfolio.balance_usd:,.2f}")
        logger.info(f"   BTC Balance: {self.portfolio.balance_btc:.6f}")
        logger.info(f"   Total P&L: ${self.portfolio.total_pnl:+,.2f}")
        logger.info(f"   Total Trades: {self.portfolio.total_trades} (Win Rate: {self.portfolio.get_win_rate():.1f}%)")
        logger.info(f"   Max Drawdown: {self.portfolio.max_drawdown * 100:.2f}%")
        logger.info(f"   Decisions/Min: {decisions_per_minute:.0f}, Trades/Hour: {trades_per_hour:.1f}")
        logger.info(f"   Data Quality: {connection_status['data_quality'].title()}")
        logger.info("=" * 80)
    
    async def start_paper_trading(self):
        """Start the enhanced paper trading system"""
        self.running = True
        
        # Setup signal handlers
        def signal_handler(signum, frame):
            logger.info(f"🛑 Received signal {signum}, stopping paper trading...")
            self.running = False
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        logger.info("🚀 STARTING ENHANCED PAPER TRADING")
        logger.info("📡 Real market data: CONNECTING")
        logger.info("🧠 Enhanced decision engine: ACTIVE")  
        logger.info("💰 Virtual portfolio: READY")
        logger.info("🔒 Paper trading mode: VERIFIED")
        logger.info("=" * 80)
        
        try:
            await self.main_trading_loop()
        except KeyboardInterrupt:
            logger.info("🛑 Paper trading stopped by user")
        finally:
            await self.print_final_summary()
    
    async def print_final_summary(self):
        """Print comprehensive final summary"""
        session_duration = time.time() - self.session_start
        final_value = self.portfolio.get_total_value(self.market_provider.real_provider.last_price if self.market_provider.real_provider else 45000)
        total_return = (final_value - self.config['starting_balance']) / self.config['starting_balance'] * 100
        
        logger.info("=" * 80)
        logger.info("🏁 ENHANCED PAPER TRADING SESSION COMPLETE")
        logger.info("=" * 80)
        logger.info("📈 Final Portfolio Results:")
        logger.info(f"   Starting Balance: ${self.config['starting_balance']:,.2f}")
        logger.info(f"   Final Value: ${final_value:,.2f}")
        logger.info(f"   Total Return: {total_return:+.2f}%")
        logger.info(f"   Total P&L: ${self.portfolio.total_pnl:+,.2f}")
        logger.info(f"   Maximum Drawdown: {self.portfolio.max_drawdown * 100:.2f}%")
        logger.info("")
        logger.info("📊 Trading Performance:")
        logger.info(f"   Total Trades: {self.portfolio.total_trades}")
        logger.info(f"   Winning Trades: {self.portfolio.winning_trades}")
        logger.info(f"   Losing Trades: {self.portfolio.losing_trades}")
        logger.info(f"   Win Rate: {self.portfolio.get_win_rate():.1f}%")
        logger.info(f"   Profit Factor: {self.portfolio.get_profit_factor():.2f}")
        logger.info("")
        logger.info("⚡ System Performance:")
        logger.info(f"   Session Duration: {session_duration:.0f} seconds ({session_duration/60:.1f} minutes)")
        logger.info(f"   Total Decisions: {self.total_decisions:,}")
        logger.info(f"   Decisions/Minute: {(self.total_decisions/session_duration)*60:.0f}")
        logger.info(f"   Trades Executed: {self.trades_executed}")
        logger.info("=" * 80)
        logger.info("✅ PAPER TRADING SESSION SUCCESSFUL - NO REAL MONEY WAS INVOLVED")
        logger.info("💰 All trading was simulated with virtual funds")

async def main():
    """Main entry point for enhanced paper trading"""
    # Get configuration type from environment or use default
    config_type = os.getenv('PAPER_TRADING_CONFIG', 'default')
    
    logger.info("🎯 BTCUSDT ENHANCED PAPER TRADING SYSTEM")
    logger.info("💰 Real market data, virtual portfolio - 100% SAFE")
    logger.info("=" * 80)
    
    # Initialize and start enhanced paper trading
    paper_system = EnhancedPaperTradingSystem(config_type)
    await paper_system.start_paper_trading()

if __name__ == "__main__":
    asyncio.run(main())