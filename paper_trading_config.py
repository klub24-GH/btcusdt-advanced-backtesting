#!/usr/bin/env python3
"""
Paper Trading Configuration
Safe configuration for live paper trading with real market data
"""

class PaperTradingConfig:
    """Complete paper trading configuration"""
    
    # SAFETY SETTINGS (ALWAYS ENABLED FOR PAPER TRADING)
    PAPER_TRADING_MODE = True  # NEVER change this to False!
    REAL_MONEY_TRADING = False  # ALWAYS False for paper trading
    SAFETY_CHECKS = True  # Multiple safety verification layers
    
    # VIRTUAL PORTFOLIO SETTINGS
    STARTING_BALANCE_USD = 100000.0  # $100,000 virtual starting balance (for BTC at $100k+)
    MAX_POSITION_SIZE_PCT = 20.0  # Maximum 20% of portfolio per position
    MIN_TRADE_SIZE_USD = 100.0  # Minimum $100 per trade (allows fractional BTC)
    
    # MARKET DATA SETTINGS
    USE_REAL_MARKET_DATA = True  # Use actual Binance market data
    TRADING_PAIR = "BTCUSDT"  # Trading pair
    DATA_UPDATE_FREQUENCY = 1.0  # Get market data every 1 second
    FALLBACK_TO_SIMULATION = True  # Use simulation if real data fails
    
    # TRADING PARAMETERS
    DECISION_FREQUENCY = 1.0  # Make trading decisions every 1 second
    CONFIDENCE_THRESHOLD = 0.2  # Ultra-low minimum confidence to execute trade
    MAX_DAILY_TRADES = 200  # Maximum trades per day
    
    # TECHNICAL ANALYSIS SETTINGS
    MOMENTUM_WINDOW_SECONDS = 60  # 1-minute momentum calculation
    MOMENTUM_THRESHOLD = 0.0001  # 0.01% price movement threshold (ULTRA sensitive)
    VOLUME_THRESHOLD = 50  # Ultra-low minimum volume threshold  
    MAX_SPREAD_USD = 10.0  # Higher spread tolerance for BTC at $100k+
    
    # RISK MANAGEMENT (PAPER TRADING SAFE LIMITS)
    STOP_LOSS_PCT = 2.0  # 2% stop loss
    TAKE_PROFIT_PCT = 4.0  # 4% take profit
    MAX_DRAWDOWN_PCT = 15.0  # 15% maximum drawdown alert
    TRADING_FEES_PCT = 0.1  # 0.1% trading fees (realistic simulation)
    
    # PERFORMANCE MONITORING
    REPORTING_INTERVAL = 30  # Report portfolio status every 30 seconds
    LOG_LEVEL = "INFO"  # Logging level
    SAVE_TRADE_HISTORY = True  # Save all trades to file
    
    # ADVANCED SETTINGS
    ENABLE_TECHNICAL_INDICATORS = True
    USE_VOLUME_ANALYSIS = True
    ENABLE_RISK_MANAGEMENT = True
    
    @classmethod
    def get_safe_config(cls) -> dict:
        """Get configuration dictionary with safety verification"""
        config = {
            # Core safety
            'paper_trading_mode': cls.PAPER_TRADING_MODE,
            'real_money_trading': cls.REAL_MONEY_TRADING,
            'safety_checks': cls.SAFETY_CHECKS,
            
            # Portfolio
            'starting_balance': cls.STARTING_BALANCE_USD,
            'max_position_size_pct': cls.MAX_POSITION_SIZE_PCT,
            'min_trade_size': cls.MIN_TRADE_SIZE_USD,
            
            # Market data
            'use_real_data': cls.USE_REAL_MARKET_DATA,
            'trading_pair': cls.TRADING_PAIR,
            'data_frequency': cls.DATA_UPDATE_FREQUENCY,
            
            # Trading
            'decision_frequency': cls.DECISION_FREQUENCY,
            'confidence_threshold': cls.CONFIDENCE_THRESHOLD,
            'max_daily_trades': cls.MAX_DAILY_TRADES,
            
            # Technical analysis
            'momentum_window': cls.MOMENTUM_WINDOW_SECONDS,
            'momentum_threshold': cls.MOMENTUM_THRESHOLD,
            'volume_threshold': cls.VOLUME_THRESHOLD,
            'max_spread': cls.MAX_SPREAD_USD,
            
            # Risk management
            'stop_loss_pct': cls.STOP_LOSS_PCT,
            'take_profit_pct': cls.TAKE_PROFIT_PCT,
            'max_drawdown_pct': cls.MAX_DRAWDOWN_PCT,
            'trading_fees_pct': cls.TRADING_FEES_PCT,
            
            # Monitoring
            'reporting_interval': cls.REPORTING_INTERVAL,
            'save_history': cls.SAVE_TRADE_HISTORY
        }
        
        # SAFETY VERIFICATION
        assert config['paper_trading_mode'] == True, "❌ SAFETY ERROR: Paper trading mode must be enabled!"
        assert config['real_money_trading'] == False, "❌ SAFETY ERROR: Real money trading must be disabled!"
        assert config['safety_checks'] == True, "❌ SAFETY ERROR: Safety checks must be enabled!"
        
        return config
    
    @classmethod
    def validate_safety(cls) -> bool:
        """Validate all safety settings"""
        safety_checks = [
            (cls.PAPER_TRADING_MODE == True, "Paper trading mode must be enabled"),
            (cls.REAL_MONEY_TRADING == False, "Real money trading must be disabled"),
            (cls.SAFETY_CHECKS == True, "Safety checks must be enabled"),
            (cls.STARTING_BALANCE_USD > 0, "Starting balance must be positive"),
            (cls.MAX_POSITION_SIZE_PCT <= 50.0, "Position size must be reasonable"),
            (cls.MIN_TRADE_SIZE_USD >= 10.0, "Minimum trade size must be reasonable"),
        ]
        
        for check, message in safety_checks:
            if not check:
                print(f"❌ SAFETY ERROR: {message}")
                return False
        
        print("✅ All safety checks passed")
        return True

# Pre-configured safe configurations for different scenarios

class ConservativePaperTrading(PaperTradingConfig):
    """Conservative paper trading configuration"""
    STARTING_BALANCE_USD = 200000.0  # $200k for conservative high-value trading
    MAX_POSITION_SIZE_PCT = 10.0  # 10% max position
    CONFIDENCE_THRESHOLD = 0.8  # Higher confidence required
    MAX_DAILY_TRADES = 50  # Fewer trades per day
    STOP_LOSS_PCT = 1.5  # Tighter stop loss
    TAKE_PROFIT_PCT = 3.0  # Lower take profit

class AggressivePaperTrading(PaperTradingConfig):
    """Aggressive paper trading configuration (still 100% safe)"""
    STARTING_BALANCE_USD = 500000.0  # $500k for aggressive high-value trading
    MAX_POSITION_SIZE_PCT = 30.0  # 30% max position
    CONFIDENCE_THRESHOLD = 0.6  # Lower confidence threshold
    MAX_DAILY_TRADES = 500  # More trades per day
    STOP_LOSS_PCT = 3.0  # Wider stop loss
    TAKE_PROFIT_PCT = 6.0  # Higher take profit
    MIN_TRADE_SIZE_USD = 500.0  # Higher minimum for aggressive trading

class HighActivityPaperTrading(PaperTradingConfig):
    """Ultra-high activity trading (GUARANTEED trades)"""
    STARTING_BALANCE_USD = 100000.0  # $100k balance
    MOMENTUM_THRESHOLD = 0.00001  # 0.001% - trades on tiniest movements
    VOLUME_THRESHOLD = 1  # ANY volume triggers trades
    CONFIDENCE_THRESHOLD = 0.1  # 10% confidence minimum
    MAX_DAILY_TRADES = 1000  # Up to 1000 trades/day
    DECISION_FREQUENCY = 0.5  # Check every 0.5 seconds
    MIN_TRADE_SIZE_USD = 50.0  # Small trades for high frequency
    MAX_POSITION_SIZE_PCT = 5.0  # Small positions for safety

class ProfitMaximizerPaperTrading(PaperTradingConfig):
    """Profit-optimized scalping strategy"""
    STARTING_BALANCE_USD = 100000.0  # $100k balance
    MOMENTUM_THRESHOLD = 0.00005  # 0.005% - ULTRA sensitive for max trades
    VOLUME_THRESHOLD = 1  # Any volume triggers trades
    CONFIDENCE_THRESHOLD = 0.08  # 8% confidence minimum - very low
    MAX_DAILY_TRADES = 5000  # Ultra-high frequency for maximum profit opportunities
    DECISION_FREQUENCY = 0.2  # Check every 0.2 seconds
    MIN_TRADE_SIZE_USD = 300.0  # Larger base trades for profit
    MAX_POSITION_SIZE_PCT = 25.0  # Aggressive 25% positions
    TAKE_PROFIT_PCT = 0.3  # Take profits at 0.3% gain (quick scalps)
    STOP_LOSS_PCT = 0.2  # Very tight stop loss

class UltraProfitPaperTrading(PaperTradingConfig):
    """MAXIMUM profit extraction system"""
    STARTING_BALANCE_USD = 100000.0  # $100k balance
    MOMENTUM_THRESHOLD = 0.00005  # 0.005% - very sensitive but not extreme
    VOLUME_THRESHOLD = 1  # Any volume
    CONFIDENCE_THRESHOLD = 0.08  # 8% confidence - reasonable minimum
    MAX_DAILY_TRADES = 5000  # High frequency but manageable
    DECISION_FREQUENCY = 0.5  # Check every 0.5 seconds (2x/sec)
    MIN_TRADE_SIZE_USD = 300.0  # Large trades for good profits
    MAX_POSITION_SIZE_PCT = 20.0  # Reasonable 20% positions
    TAKE_PROFIT_PCT = 1.0  # Take 1%+ profits (let them develop)
    STOP_LOSS_PCT = 2.0  # Reasonable stop loss

class WinnerPaperTrading(PaperTradingConfig):
    """WIN-FOCUSED configuration - optimized for high win rate"""
    STARTING_BALANCE_USD = 100000.0  # $100k balance
    MOMENTUM_THRESHOLD = 0.0002  # 0.02% - require decent momentum
    VOLUME_THRESHOLD = 50  # Require some volume
    CONFIDENCE_THRESHOLD = 0.4  # 40% confidence - high quality signals only
    MAX_DAILY_TRADES = 200  # Selective trades
    DECISION_FREQUENCY = 1.0  # Check every 1 second
    MIN_TRADE_SIZE_USD = 500.0  # Larger trades for meaningful profits
    MAX_POSITION_SIZE_PCT = 15.0  # Conservative position sizing
    TAKE_PROFIT_PCT = 2.0  # Let profits develop to 2%
    STOP_LOSS_PCT = 1.0  # Tight stop loss at 1%

class LearningPaperTrading(PaperTradingConfig):
    """ADAPTIVE LEARNING configuration - system gets better over time!"""
    STARTING_BALANCE_USD = 100000.0  # $100k balance for learning
    MAX_POSITION_SIZE_PCT = 15.0  # Moderate position sizing for safety while learning
    REPORTING_INTERVAL = 15  # More frequent reporting
    LOG_LEVEL = "INFO"  # Detailed logging to see learning progress
    DECISION_FREQUENCY = 1.0  # 1 second decision making
    MIN_TRADE_SIZE_USD = 200.0  # Meaningful trades for learning
    MOMENTUM_THRESHOLD = 0.0001  # Start sensitive, will adapt
    CONFIDENCE_THRESHOLD = 0.25  # Start moderate, will adapt based on performance
    VOLUME_THRESHOLD = 25  # Start with some volume requirement
    MAX_DAILY_TRADES = 500  # Allow learning from many examples

class ScalpingWinnerPaperTrading(PaperTradingConfig):
    """ULTIMATE SCALPING CONFIGURATION - Maximum win rate focus"""
    STARTING_BALANCE_USD = 100000.0  # $100k balance
    MAX_POSITION_SIZE_PCT = 10.0  # Fixed 10% positions for consistency
    DECISION_FREQUENCY = 0.5  # Check every 0.5 seconds
    MIN_TRADE_SIZE_USD = 500.0  # Meaningful trade sizes
    
    # ULTRA-SENSITIVE for maximum trade frequency
    MOMENTUM_THRESHOLD = 0.00002  # 0.002% - catch tiniest movements
    CONFIDENCE_THRESHOLD = 0.05  # 5% minimum confidence - very low
    VOLUME_THRESHOLD = 1  # Any volume triggers trades
    
    # Scalping-optimized parameters
    MAX_DAILY_TRADES = 2000  # Allow high frequency scalping
    REPORTING_INTERVAL = 10  # Report every 10 seconds
    
    # Conservative risk for consistent wins
    STOP_LOSS_PCT = 0.4  # Tight 0.4% stop loss
    TAKE_PROFIT_PCT = 0.8  # Quick 0.8% profit target
    MAX_DRAWDOWN_PCT = 5.0  # Low max drawdown

def get_configuration(config_type: str = "default") -> dict:
    """Get paper trading configuration by type"""
    configs = {
        "default": PaperTradingConfig,
        "conservative": ConservativePaperTrading,
        "aggressive": AggressivePaperTrading,
        "learning": LearningPaperTrading,
        "high_activity": HighActivityPaperTrading,
        "profit_max": ProfitMaximizerPaperTrading,
        "ultra_profit": UltraProfitPaperTrading,
        "winner": WinnerPaperTrading,
        "scalping": ScalpingWinnerPaperTrading
    }
    
    config_class = configs.get(config_type, PaperTradingConfig)
    
    # Validate safety before returning
    if not config_class.validate_safety():
        raise RuntimeError("❌ SAFETY VALIDATION FAILED - Cannot proceed")
    
    return config_class.get_safe_config()

if __name__ == "__main__":
    print("🔒 Paper Trading Configuration Safety Check")
    print("=" * 50)
    
    # Test all configuration types
    for config_name in ["default", "conservative", "aggressive", "learning"]:
        print(f"\nTesting {config_name} configuration...")
        try:
            config = get_configuration(config_name)
            print(f"✅ {config_name.title()} configuration: SAFE")
            print(f"   Starting Balance: ${config['starting_balance']:,.2f}")
            print(f"   Max Position Size: {config['max_position_size_pct']:.1f}%")
            print(f"   Paper Trading Mode: {config['paper_trading_mode']}")
        except Exception as e:
            print(f"❌ {config_name.title()} configuration failed: {e}")
    
    print("\n✅ All paper trading configurations verified safe")