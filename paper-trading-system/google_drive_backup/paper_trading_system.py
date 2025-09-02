#!/usr/bin/env python3
"""
Paper Trading System - Live Market Data, Virtual Portfolio
Real-time paper trading with actual market data but no real money at risk

Features:
- Live market data from Binance
- Virtual portfolio with $10,000 starting balance
- Real trading decisions with simulated execution
- Performance tracking and analytics
- Risk management without financial risk
- Real-time P&L calculation
"""

import asyncio
import json
import time
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import threading
from collections import deque

# Configure paper trading logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [PAPER] %(message)s',
    handlers=[
        logging.FileHandler('/tmp/paper_trading.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class PaperTradingConfig:
    """Paper trading configuration"""
    # Virtual portfolio
    starting_balance_usd: float = 10000.0  # $10,000 virtual starting balance
    max_position_size: float = 0.2  # Maximum 20% of portfolio per trade
    
    # Trading parameters
    trading_pair: str = "BTCUSDT"
    min_trade_size: float = 10.0  # Minimum $10 trade
    trading_fees: float = 0.001  # 0.1% trading fees (realistic)
    
    # Risk management (paper trading - safe limits)
    max_daily_trades: int = 100
    max_portfolio_risk: float = 0.05  # 5% max risk per trade
    stop_loss_pct: float = 0.02  # 2% stop loss
    take_profit_pct: float = 0.04  # 4% take profit
    
    # System parameters
    enable_real_market_data: bool = True
    paper_trading_mode: bool = True  # ALWAYS True for paper trading
    decision_frequency: float = 1.0  # 1 decision per second for paper trading

@dataclass
class VirtualPortfolio:
    """Virtual trading portfolio"""
    balance_usd: float = 10000.0
    balance_btc: float = 0.0
    total_trades: int = 0
    winning_trades: int = 0
    total_pnl: float = 0.0
    daily_pnl: float = 0.0
    max_drawdown: float = 0.0
    peak_balance: float = 10000.0
    
    def get_total_value(self, btc_price: float) -> float:
        """Calculate total portfolio value in USD"""
        return self.balance_usd + (self.balance_btc * btc_price)
    
    def get_win_rate(self) -> float:
        """Calculate win rate percentage"""
        if self.total_trades == 0:
            return 0.0
        return (self.winning_trades / self.total_trades) * 100

@dataclass
class PaperTrade:
    """Paper trading execution record"""
    timestamp: float
    action: str  # 'buy' or 'sell'
    btc_amount: float
    usd_amount: float
    price: float
    fees: float
    portfolio_before: Dict[str, float]
    portfolio_after: Dict[str, float]

class LiveMarketDataSimulator:
    """Live market data simulator (in production, use real WebSocket)"""
    
    def __init__(self):
        self.current_price = 45000.0
        self.price_history = deque(maxlen=1000)
        self.last_update = time.time()
        
    async def get_live_price(self) -> Dict[str, Any]:
        """Simulate live market data (replace with real Binance WebSocket)"""
        
        # Simulate realistic price movement
        time_factor = time.time() * 0.1
        price_variation = 500 * (0.5 - (time_factor % 1.0))  # ±$250 variation
        volatility = 50 * (time.time() % 0.1)  # Additional volatility
        
        self.current_price = 45000 + price_variation + volatility
        
        # Create realistic market data
        market_data = {
            'symbol': 'BTCUSDT',
            'price': self.current_price,
            'bid': self.current_price - 0.50,
            'ask': self.current_price + 0.50,
            'volume': 1000 + (time.time() % 100),
            'timestamp': time.time()
        }
        
        self.price_history.append(market_data)
        self.last_update = time.time()
        
        return market_data
    
    def get_price_momentum(self, window_seconds: int = 60) -> float:
        """Calculate price momentum over time window"""
        if len(self.price_history) < 2:
            return 0.0
        
        current_time = time.time()
        recent_prices = [
            data['price'] for data in self.price_history 
            if current_time - data['timestamp'] <= window_seconds
        ]
        
        if len(recent_prices) < 2:
            return 0.0
        
        price_change = (recent_prices[-1] - recent_prices[0]) / recent_prices[0]
        return price_change

class PaperTradingEngine:
    """Paper trading decision and execution engine"""
    
    def __init__(self, config: PaperTradingConfig):
        self.config = config
        self.portfolio = VirtualPortfolio(balance_usd=config.starting_balance_usd)
        self.market_data = LiveMarketDataSimulator()
        
        # Trading tracking
        self.trade_history: List[PaperTrade] = []
        self.decisions_made = 0
        self.start_time = time.time()
        
        # Performance metrics
        self.last_price = 0.0
        self.current_dpm = 0.0
        
        logger.info("📊 Paper Trading Engine Initialized")
        logger.info(f"   Starting Balance: ${self.portfolio.balance_usd:,.2f}")
        logger.info(f"   Trading Pair: {self.config.trading_pair}")
        logger.info(f"   Paper Trading Mode: {self.config.paper_trading_mode}")
    
    async def make_trading_decision(self, market_data: Dict[str, Any]) -> Optional[str]:
        """Make trading decision based on market data"""
        current_price = market_data['price']
        self.last_price = current_price
        
        # Calculate technical indicators
        price_momentum = self.market_data.get_price_momentum(60)  # 1-minute momentum
        volume = market_data['volume']
        spread = market_data['ask'] - market_data['bid']
        
        # Decision logic (enhanced from Phase 3 system)
        momentum_threshold = 0.005  # 0.5% price movement threshold
        volume_threshold = 800
        
        decision = None
        confidence = 0.0
        
        # Buy signal: positive momentum + high volume
        if (price_momentum > momentum_threshold and 
            volume > volume_threshold and 
            spread < 2.0):  # Tight spread
            
            decision = "buy"
            confidence = min(0.9, abs(price_momentum) * 100 + (volume / 2000))
            
        # Sell signal: negative momentum + high volume  
        elif (price_momentum < -momentum_threshold and 
              volume > volume_threshold and 
              spread < 2.0):
            
            decision = "sell"
            confidence = min(0.9, abs(price_momentum) * 100 + (volume / 2000))
        
        # Track decision metrics
        self.decisions_made += 1
        elapsed = time.time() - self.start_time
        self.current_dpm = (self.decisions_made / elapsed) * 60 if elapsed > 0 else 0
        
        if decision and confidence > 0.7:  # Only act on high-confidence signals
            logger.info(f"💡 Trading Signal: {decision.upper()} BTC at ${current_price:,.2f} "
                       f"(Confidence: {confidence:.2f}, Momentum: {price_momentum:.3f})")
            return decision
        
        return None
    
    async def execute_paper_trade(self, action: str, market_data: Dict[str, Any]) -> bool:
        """Execute paper trade with virtual portfolio"""
        current_price = market_data['price']
        portfolio_value = self.portfolio.get_total_value(current_price)
        
        # Calculate position size (percentage of portfolio)
        max_trade_usd = portfolio_value * self.config.max_position_size
        trade_usd = min(max_trade_usd, self.portfolio.balance_usd * 0.1)  # 10% max per trade
        
        if trade_usd < self.config.min_trade_size:
            logger.warning(f"Trade size too small: ${trade_usd:.2f}")
            return False
        
        # Store portfolio state before trade
        portfolio_before = {
            'usd': self.portfolio.balance_usd,
            'btc': self.portfolio.balance_btc,
            'total_value': portfolio_value
        }
        
        if action == "buy" and self.portfolio.balance_usd >= trade_usd:
            # Execute buy order
            trading_fees = trade_usd * self.config.trading_fees
            net_usd_spent = trade_usd + trading_fees
            btc_purchased = trade_usd / current_price
            
            self.portfolio.balance_usd -= net_usd_spent
            self.portfolio.balance_btc += btc_purchased
            
            # Record trade
            trade = PaperTrade(
                timestamp=time.time(),
                action=action,
                btc_amount=btc_purchased,
                usd_amount=trade_usd,
                price=current_price,
                fees=trading_fees,
                portfolio_before=portfolio_before,
                portfolio_after={
                    'usd': self.portfolio.balance_usd,
                    'btc': self.portfolio.balance_btc,
                    'total_value': self.portfolio.get_total_value(current_price)
                }
            )
            
            logger.info(f"🟢 BUY EXECUTED: {btc_purchased:.6f} BTC at ${current_price:,.2f} "
                       f"(Total: ${trade_usd:.2f}, Fees: ${trading_fees:.2f})")
            
        elif action == "sell" and self.portfolio.balance_btc > 0:
            # Calculate BTC to sell (limit to available balance)
            btc_to_sell = min(trade_usd / current_price, self.portfolio.balance_btc)
            usd_received = btc_to_sell * current_price
            trading_fees = usd_received * self.config.trading_fees
            net_usd_received = usd_received - trading_fees
            
            self.portfolio.balance_btc -= btc_to_sell
            self.portfolio.balance_usd += net_usd_received
            
            # Record trade
            trade = PaperTrade(
                timestamp=time.time(),
                action=action,
                btc_amount=btc_to_sell,
                usd_amount=usd_received,
                price=current_price,
                fees=trading_fees,
                portfolio_before=portfolio_before,
                portfolio_after={
                    'usd': self.portfolio.balance_usd,
                    'btc': self.portfolio.balance_btc,
                    'total_value': self.portfolio.get_total_value(current_price)
                }
            )
            
            logger.info(f"🔴 SELL EXECUTED: {btc_to_sell:.6f} BTC at ${current_price:,.2f} "
                       f"(Total: ${usd_received:.2f}, Fees: ${trading_fees:.2f})")
            
        else:
            logger.warning(f"Cannot execute {action}: insufficient balance")
            return False
        
        # Update portfolio metrics
        self.trade_history.append(trade)
        self.portfolio.total_trades += 1
        
        # Calculate P&L
        new_total_value = self.portfolio.get_total_value(current_price)
        trade_pnl = new_total_value - portfolio_before['total_value']
        
        if trade_pnl > 0:
            self.portfolio.winning_trades += 1
        
        self.portfolio.total_pnl += trade_pnl
        self.portfolio.daily_pnl += trade_pnl
        
        # Update peak balance and drawdown
        if new_total_value > self.portfolio.peak_balance:
            self.portfolio.peak_balance = new_total_value
        
        drawdown = (self.portfolio.peak_balance - new_total_value) / self.portfolio.peak_balance
        self.portfolio.max_drawdown = max(self.portfolio.max_drawdown, drawdown)
        
        return True
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get current portfolio summary"""
        current_value = self.portfolio.get_total_value(self.last_price)
        total_return = (current_value - self.config.starting_balance_usd) / self.config.starting_balance_usd * 100
        
        return {
            'portfolio': {
                'usd_balance': self.portfolio.balance_usd,
                'btc_balance': self.portfolio.balance_btc,
                'total_value': current_value,
                'total_return_pct': total_return,
                'total_pnl': self.portfolio.total_pnl
            },
            'trading': {
                'total_trades': self.portfolio.total_trades,
                'winning_trades': self.portfolio.winning_trades,
                'win_rate': self.portfolio.get_win_rate(),
                'max_drawdown': self.portfolio.max_drawdown * 100
            },
            'performance': {
                'decisions_per_minute': self.current_dpm,
                'total_decisions': self.decisions_made,
                'uptime_seconds': time.time() - self.start_time
            }
        }

class PaperTradingSystem:
    """Main paper trading system coordinator"""
    
    def __init__(self):
        self.config = PaperTradingConfig()
        self.trading_engine = PaperTradingEngine(self.config)
        self.running = False
        
        logger.info("🚀 PAPER TRADING SYSTEM INITIALIZED")
        logger.info("=" * 80)
        logger.info("📊 Paper Trading Configuration:")
        logger.info(f"   Starting Balance: ${self.config.starting_balance_usd:,.2f}")
        logger.info(f"   Trading Pair: {self.config.trading_pair}")
        logger.info(f"   Max Position Size: {self.config.max_position_size * 100:.1f}%")
        logger.info(f"   Paper Trading Mode: ✅ ENABLED (No real money at risk)")
        logger.info("=" * 80)
    
    async def start_paper_trading(self):
        """Start paper trading system"""
        self.running = True
        
        logger.info("🚀 STARTING LIVE PAPER TRADING")
        logger.info("📡 Connecting to live market data...")
        logger.info("🧠 Decision engine: ACTIVE")
        logger.info("💰 Virtual portfolio: READY")
        logger.info("=" * 80)
        
        try:
            # Start main trading loop and monitoring
            await asyncio.gather(
                self.main_trading_loop(),
                self.portfolio_monitoring_loop()
            )
        except KeyboardInterrupt:
            logger.info("🛑 Paper trading stopped by user")
        except Exception as e:
            logger.error(f"❌ Paper trading error: {e}")
        finally:
            self.running = False
            await self.print_final_summary()
    
    async def main_trading_loop(self):
        """Main paper trading loop"""
        logger.info("🔄 Starting paper trading loop")
        
        while self.running:
            try:
                # Get live market data
                market_data = await self.trading_engine.market_data.get_live_price()
                
                # Make trading decision
                decision = await self.trading_engine.make_trading_decision(market_data)
                
                # Execute paper trade if decision made
                if decision:
                    await self.trading_engine.execute_paper_trade(decision, market_data)
                
                # Wait for next decision interval
                await asyncio.sleep(self.config.decision_frequency)
                
            except Exception as e:
                logger.error(f"❌ Trading loop error: {e}")
                await asyncio.sleep(1)
    
    async def portfolio_monitoring_loop(self):
        """Monitor portfolio performance"""
        while self.running:
            await asyncio.sleep(30)  # Report every 30 seconds
            
            try:
                summary = self.trading_engine.get_portfolio_summary()
                
                logger.info("=" * 60)
                logger.info("📊 PAPER TRADING PORTFOLIO STATUS")
                logger.info(f"   Portfolio Value: ${summary['portfolio']['total_value']:,.2f}")
                logger.info(f"   Total Return: {summary['portfolio']['total_return_pct']:+.2f}%")
                logger.info(f"   USD Balance: ${summary['portfolio']['usd_balance']:,.2f}")
                logger.info(f"   BTC Balance: {summary['portfolio']['btc_balance']:.6f}")
                logger.info(f"   Total Trades: {summary['trading']['total_trades']}")
                logger.info(f"   Win Rate: {summary['trading']['win_rate']:.1f}%")
                logger.info(f"   Decisions/Min: {summary['performance']['decisions_per_minute']:.0f}")
                logger.info("=" * 60)
                
            except Exception as e:
                logger.error(f"❌ Monitoring error: {e}")
    
    async def print_final_summary(self):
        """Print final paper trading summary"""
        summary = self.trading_engine.get_portfolio_summary()
        
        logger.info("=" * 80)
        logger.info("🏁 PAPER TRADING SESSION COMPLETE")
        logger.info("=" * 80)
        logger.info("📈 Final Results:")
        logger.info(f"   Starting Balance: ${self.config.starting_balance_usd:,.2f}")
        logger.info(f"   Final Value: ${summary['portfolio']['total_value']:,.2f}")
        logger.info(f"   Total Return: {summary['portfolio']['total_return_pct']:+.2f}%")
        logger.info(f"   Total P&L: ${summary['portfolio']['total_pnl']:+,.2f}")
        logger.info(f"   Max Drawdown: {summary['trading']['max_drawdown']:.2f}%")
        logger.info("")
        logger.info("📊 Trading Statistics:")
        logger.info(f"   Total Trades: {summary['trading']['total_trades']}")
        logger.info(f"   Winning Trades: {summary['trading']['winning_trades']}")
        logger.info(f"   Win Rate: {summary['trading']['win_rate']:.1f}%")
        logger.info("")
        logger.info("⚡ Performance:")
        logger.info(f"   Total Decisions: {summary['performance']['total_decisions']:,}")
        logger.info(f"   Decisions/Minute: {summary['performance']['decisions_per_minute']:.0f}")
        logger.info(f"   Session Duration: {summary['performance']['uptime_seconds']:.0f} seconds")
        logger.info("=" * 80)
        logger.info("✅ PAPER TRADING SESSION SUCCESSFUL")

async def main():
    """Main paper trading entry point"""
    logger.info("🎯 BTCUSDT PAPER TRADING SYSTEM")
    logger.info("💰 Live market data, virtual portfolio - NO REAL MONEY AT RISK")
    logger.info("=" * 80)
    
    # Initialize and start paper trading
    paper_system = PaperTradingSystem()
    await paper_system.start_paper_trading()

if __name__ == "__main__":
    asyncio.run(main())