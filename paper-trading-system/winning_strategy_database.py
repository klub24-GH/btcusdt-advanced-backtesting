#!/usr/bin/env python3
"""
Winning Strategy Database & Auto-Deployment System
Continuously scores strategies, maintains winner database, and auto-deploys best performers
"""

import json
import os
import time
import logging
import sqlite3
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass, asdict
import subprocess
import threading
import glob
import shutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [WINNERS] %(message)s',
    handlers=[
        logging.FileHandler('/tmp/winning_strategies.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class StrategyScore:
    """Comprehensive strategy scoring"""
    strategy_id: str
    strategy_name: str
    timeframe: str
    parameters: Dict
    
    # Performance metrics
    total_return: float
    win_rate: float
    sharpe_ratio: float
    max_drawdown: float
    calmar_ratio: float
    profit_factor: float
    
    # Reliability metrics
    total_trades: int
    avg_trade_duration: float
    consistency_score: float
    
    # Meta scores
    overall_score: float
    profit_score: float
    risk_score: float
    reliability_score: float
    
    # Deployment tracking
    times_deployed: int
    live_performance: float
    last_updated: str
    status: str  # 'testing', 'approved', 'deployed', 'retired'

class StrategyScorer:
    """Advanced strategy scoring system"""
    
    def __init__(self):
        self.weights = {
            'return': 0.30,      # 30% weight on returns
            'risk_adjusted': 0.25, # 25% weight on risk-adjusted metrics
            'consistency': 0.20,   # 20% weight on consistency
            'reliability': 0.15,   # 15% weight on trade reliability
            'live_performance': 0.10 # 10% weight on live performance
        }
    
    def calculate_comprehensive_score(self, strategy_data: Dict) -> StrategyScore:
        """Calculate comprehensive strategy score"""
        
        # Extract basic data
        strategy_name = strategy_data.get('strategy', 'Unknown')
        timeframe = strategy_data.get('timeframe', '1h')
        parameters = strategy_data.get('parameters', {})
        
        # Performance metrics
        total_return = strategy_data.get('total_return', 0)
        win_rate = strategy_data.get('win_rate', 0)
        sharpe_ratio = strategy_data.get('sharpe_ratio', 0)
        max_drawdown = strategy_data.get('max_drawdown', 0)
        total_trades = strategy_data.get('total_trades', 0)
        
        # Calculate individual scores (0-1 scale)
        profit_score = self._calculate_profit_score(total_return, win_rate)
        risk_score = self._calculate_risk_score(sharpe_ratio, max_drawdown)
        reliability_score = self._calculate_reliability_score(total_trades, win_rate)
        consistency_score = self._calculate_consistency_score(strategy_data)
        
        # Calculate overall score
        overall_score = (
            profit_score * self.weights['return'] +
            risk_score * self.weights['risk_adjusted'] +
            consistency_score * self.weights['consistency'] +
            reliability_score * self.weights['reliability']
        )
        
        # Generate unique strategy ID
        strategy_id = f"{strategy_name}_{timeframe}_{hash(str(parameters)) % 10000:04d}"
        
        return StrategyScore(
            strategy_id=strategy_id,
            strategy_name=strategy_name,
            timeframe=timeframe,
            parameters=parameters,
            total_return=total_return,
            win_rate=win_rate,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            calmar_ratio=abs(total_return / max_drawdown) if max_drawdown > 0 else 0,
            profit_factor=strategy_data.get('profit_factor', 0),
            total_trades=total_trades,
            avg_trade_duration=strategy_data.get('avg_trade_duration', 0),
            consistency_score=consistency_score,
            overall_score=overall_score,
            profit_score=profit_score,
            risk_score=risk_score,
            reliability_score=reliability_score,
            times_deployed=0,
            live_performance=0.0,
            last_updated=datetime.now(timezone.utc).isoformat(),
            status='testing'
        )
    
    def _calculate_profit_score(self, total_return: float, win_rate: float) -> float:
        """Calculate profit-focused score"""
        # Normalize return (100% return = 1.0 score)
        return_score = min(1.0, max(0.0, total_return / 1.0))
        
        # Win rate bonus
        win_rate_bonus = min(0.5, win_rate)  # Up to 0.5 bonus for high win rate
        
        return min(1.0, return_score + win_rate_bonus)
    
    def _calculate_risk_score(self, sharpe_ratio: float, max_drawdown: float) -> float:
        """Calculate risk-adjusted score"""
        # Sharpe ratio score (3.0 Sharpe = 1.0 score)
        sharpe_score = min(1.0, max(0.0, sharpe_ratio / 3.0))
        
        # Drawdown penalty (20% drawdown = 0.5 penalty)
        drawdown_penalty = min(0.5, max_drawdown / 0.2)
        
        return max(0.0, sharpe_score - drawdown_penalty)
    
    def _calculate_reliability_score(self, total_trades: int, win_rate: float) -> float:
        """Calculate reliability score based on sample size and consistency"""
        # Sample size score (100 trades = 1.0 score)
        sample_score = min(1.0, total_trades / 100)
        
        # Win rate consistency (50% = 0.5, higher is better)
        win_consistency = min(1.0, win_rate / 0.5)
        
        return (sample_score + win_consistency) / 2
    
    def _calculate_consistency_score(self, strategy_data: Dict) -> float:
        """Calculate consistency score based on various factors"""
        # This is a simplified consistency score
        # In practice, you'd analyze trade distribution, equity curve stability, etc.
        
        win_rate = strategy_data.get('win_rate', 0)
        total_return = strategy_data.get('total_return', 0)
        
        # Balanced performance is more consistent
        balance_score = 1.0 - abs(win_rate - 0.5)  # Closer to 50% win rate = more balanced
        
        # Positive return consistency
        return_consistency = min(1.0, max(0.0, total_return / 0.1))  # 10% return = full score
        
        return (balance_score + return_consistency) / 2

class WinningStrategyDatabase:
    """Database to store and manage winning strategies"""
    
    def __init__(self, db_path: str = 'winning_strategies.db'):
        self.db_path = db_path
        self.scorer = StrategyScorer()
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS strategies (
                strategy_id TEXT PRIMARY KEY,
                strategy_name TEXT,
                timeframe TEXT,
                parameters TEXT,
                total_return REAL,
                win_rate REAL,
                sharpe_ratio REAL,
                max_drawdown REAL,
                calmar_ratio REAL,
                profit_factor REAL,
                total_trades INTEGER,
                avg_trade_duration REAL,
                consistency_score REAL,
                overall_score REAL,
                profit_score REAL,
                risk_score REAL,
                reliability_score REAL,
                times_deployed INTEGER,
                live_performance REAL,
                last_updated TEXT,
                status TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS deployment_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                strategy_id TEXT,
                deployment_time TEXT,
                performance_period TEXT,
                live_return REAL,
                benchmark_return REAL,
                success BOOLEAN,
                notes TEXT,
                FOREIGN KEY (strategy_id) REFERENCES strategies (strategy_id)
            )
        ''')
        
        conn.commit()
        conn.close()
        
        logger.info("✅ Winning Strategy Database initialized")
    
    def add_or_update_strategy(self, strategy_data: Dict) -> StrategyScore:
        """Add new strategy or update existing one"""
        
        # Calculate comprehensive score
        strategy_score = self.scorer.calculate_comprehensive_score(strategy_data)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if strategy already exists
        cursor.execute('SELECT strategy_id FROM strategies WHERE strategy_id = ?', 
                      (strategy_score.strategy_id,))
        exists = cursor.fetchone()
        
        if exists:
            # Update existing strategy
            cursor.execute('''
                UPDATE strategies SET
                    total_return = ?, win_rate = ?, sharpe_ratio = ?, max_drawdown = ?,
                    calmar_ratio = ?, profit_factor = ?, total_trades = ?,
                    avg_trade_duration = ?, consistency_score = ?, overall_score = ?,
                    profit_score = ?, risk_score = ?, reliability_score = ?,
                    last_updated = ?, status = ?
                WHERE strategy_id = ?
            ''', (
                strategy_score.total_return, strategy_score.win_rate, strategy_score.sharpe_ratio,
                strategy_score.max_drawdown, strategy_score.calmar_ratio, strategy_score.profit_factor,
                strategy_score.total_trades, strategy_score.avg_trade_duration, strategy_score.consistency_score,
                strategy_score.overall_score, strategy_score.profit_score, strategy_score.risk_score,
                strategy_score.reliability_score, strategy_score.last_updated, strategy_score.status,
                strategy_score.strategy_id
            ))
            logger.info(f"📝 Updated strategy: {strategy_score.strategy_name} (Score: {strategy_score.overall_score:.3f})")
        else:
            # Insert new strategy
            cursor.execute('''
                INSERT INTO strategies (
                    strategy_id, strategy_name, timeframe, parameters,
                    total_return, win_rate, sharpe_ratio, max_drawdown, calmar_ratio, profit_factor,
                    total_trades, avg_trade_duration, consistency_score,
                    overall_score, profit_score, risk_score, reliability_score,
                    times_deployed, live_performance, last_updated, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                strategy_score.strategy_id, strategy_score.strategy_name, strategy_score.timeframe,
                json.dumps(strategy_score.parameters), strategy_score.total_return, strategy_score.win_rate,
                strategy_score.sharpe_ratio, strategy_score.max_drawdown, strategy_score.calmar_ratio,
                strategy_score.profit_factor, strategy_score.total_trades, strategy_score.avg_trade_duration,
                strategy_score.consistency_score, strategy_score.overall_score, strategy_score.profit_score,
                strategy_score.risk_score, strategy_score.reliability_score, strategy_score.times_deployed,
                strategy_score.live_performance, strategy_score.last_updated, strategy_score.status
            ))
            logger.info(f"🆕 Added new strategy: {strategy_score.strategy_name} (Score: {strategy_score.overall_score:.3f})")
        
        conn.commit()
        conn.close()
        
        return strategy_score
    
    def get_top_strategies(self, limit: int = 10, min_score: float = 0.6) -> List[StrategyScore]:
        """Get top performing strategies"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM strategies 
            WHERE overall_score >= ? 
            ORDER BY overall_score DESC 
            LIMIT ?
        ''', (min_score, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        strategies = []
        for row in rows:
            strategies.append(StrategyScore(
                strategy_id=row[0], strategy_name=row[1], timeframe=row[2],
                parameters=json.loads(row[3]), total_return=row[4], win_rate=row[5],
                sharpe_ratio=row[6], max_drawdown=row[7], calmar_ratio=row[8],
                profit_factor=row[9], total_trades=row[10], avg_trade_duration=row[11],
                consistency_score=row[12], overall_score=row[13], profit_score=row[14],
                risk_score=row[15], reliability_score=row[16], times_deployed=row[17],
                live_performance=row[18], last_updated=row[19], status=row[20]
            ))
        
        return strategies
    
    def get_deployment_candidates(self) -> List[StrategyScore]:
        """Get strategies ready for deployment"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get strategies with high scores that haven't been deployed recently
        cursor.execute('''
            SELECT * FROM strategies 
            WHERE overall_score >= 0.7 
            AND status IN ('testing', 'approved')
            AND (times_deployed = 0 OR live_performance >= 0)
            ORDER BY overall_score DESC, total_return DESC
            LIMIT 5
        ''', )
        
        rows = cursor.fetchall()
        conn.close()
        
        candidates = []
        for row in rows:
            candidates.append(StrategyScore(
                strategy_id=row[0], strategy_name=row[1], timeframe=row[2],
                parameters=json.loads(row[3]), total_return=row[4], win_rate=row[5],
                sharpe_ratio=row[6], max_drawdown=row[7], calmar_ratio=row[8],
                profit_factor=row[9], total_trades=row[10], avg_trade_duration=row[11],
                consistency_score=row[12], overall_score=row[13], profit_score=row[14],
                risk_score=row[15], reliability_score=row[16], times_deployed=row[17],
                live_performance=row[18], last_updated=row[19], status=row[20]
            ))
        
        return candidates

class AutoDeploymentSystem:
    """Automatically deploy winning strategies"""
    
    def __init__(self, db: WinningStrategyDatabase):
        self.db = db
        self.current_strategy = None
        self.deployment_start_time = None
        self.min_deployment_time = 3600  # 1 hour minimum deployment
        
    def should_deploy_new_strategy(self) -> bool:
        """Check if we should deploy a new strategy"""
        
        # Get deployment candidates
        candidates = self.db.get_deployment_candidates()
        if not candidates:
            return False
        
        best_candidate = candidates[0]
        
        # Don't deploy if current strategy is performing well
        if self.current_strategy and self.deployment_start_time:
            deployment_time = time.time() - self.deployment_start_time
            if deployment_time < self.min_deployment_time:
                logger.info(f"⏳ Current strategy deployed for {deployment_time/3600:.1f}h, waiting...")
                return False
        
        # Deploy if significantly better strategy found
        if self.current_strategy:
            if best_candidate.overall_score > self.current_strategy.overall_score + 0.1:
                logger.info(f"🚀 Found better strategy: {best_candidate.overall_score:.3f} vs {self.current_strategy.overall_score:.3f}")
                return True
            else:
                return False
        else:
            # No current strategy, deploy the best
            return True
    
    def deploy_strategy(self, strategy: StrategyScore) -> bool:
        """Deploy a winning strategy"""
        
        try:
            logger.info(f"🚀 DEPLOYING WINNING STRATEGY: {strategy.strategy_name}")
            logger.info(f"   Score: {strategy.overall_score:.3f}")
            logger.info(f"   Return: {strategy.total_return:+.2%}")
            logger.info(f"   Win Rate: {strategy.win_rate:.1%}")
            logger.info(f"   Sharpe: {strategy.sharpe_ratio:.2f}")
            
            # Generate strategy implementation file
            strategy_file = self._generate_strategy_file(strategy)
            
            # Stop current trading system
            self._stop_current_strategy()
            
            # Deploy new strategy
            success = self._start_new_strategy(strategy_file)
            
            if success:
                # Update database
                self._update_deployment_record(strategy)
                self.current_strategy = strategy
                self.deployment_start_time = time.time()
                
                logger.info(f"✅ Successfully deployed: {strategy.strategy_name}")
                return True
            else:
                logger.error(f"❌ Failed to deploy: {strategy.strategy_name}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Deployment error: {e}")
            return False
    
    def _generate_strategy_file(self, strategy: StrategyScore) -> str:
        """Generate strategy implementation file"""
        
        strategy_code = f'''#!/usr/bin/env python3
"""
Auto-Generated Winning Strategy: {strategy.strategy_name}
Generated by Winning Strategy Database
Score: {strategy.overall_score:.3f} | Return: {strategy.total_return:+.2%} | Win Rate: {strategy.win_rate:.1%}
"""

import asyncio
import json
import time
import logging
from datetime import datetime, timezone
from superior_trend_sensitive_strategy import SuperiorTrendSensitiveStrategy, SuperiorTradingSystem

# Enhanced strategy with winning parameters
class AutoGeneratedWinningStrategy(SuperiorTrendSensitiveStrategy):
    def __init__(self):
        # Use winning parameters
        params = {json.dumps(strategy.parameters, indent=8)}
        
        super().__init__(
            fast_window=params.get('fast_period', 5),
            slow_window=params.get('slow_period', 20),
            crossover_threshold=params.get('crossover_threshold', 1.01),
            crossunder_threshold=params.get('crossunder_threshold', 0.99),
            min_trade_usd=500
        )
        
        self.strategy_info = {{
            'name': '{strategy.strategy_name}',
            'score': {strategy.overall_score:.3f},
            'expected_return': {strategy.total_return:.4f},
            'expected_win_rate': {strategy.win_rate:.4f}
        }}
        
        logger.info(f"🏆 WINNING STRATEGY DEPLOYED: {{self.strategy_info['name']}}")
        logger.info(f"   Expected Return: {{self.strategy_info['expected_return']:+.2%}}")
        logger.info(f"   Expected Win Rate: {{self.strategy_info['expected_win_rate']:.1%}}")
        logger.info(f"   Strategy Score: {{self.strategy_info['score']:.3f}}")

class AutoGeneratedTradingSystem(SuperiorTradingSystem):
    def __init__(self):
        self.strategy = AutoGeneratedWinningStrategy()
        self.data_provider = SafePaperTradingDataProvider(use_real_data=True)
        self.running = False
        self.last_report_time = time.time()

async def main():
    system = AutoGeneratedTradingSystem()
    try:
        await system.run()
    except KeyboardInterrupt:
        logger.info("👋 Auto-generated winning strategy stopped")
        system.stop()

if __name__ == "__main__":
    asyncio.run(main())
'''
        
        # Save to file
        filename = f'auto_generated_winner_{strategy.strategy_id}.py'
        with open(filename, 'w') as f:
            f.write(strategy_code)
        
        return filename
    
    def _stop_current_strategy(self):
        """Stop currently running strategy"""
        try:
            # Stop any running trading processes
            result = subprocess.run(['pkill', '-f', 'superior_trend_sensitive_strategy.py'], 
                                  capture_output=True)
            result = subprocess.run(['pkill', '-f', 'auto_generated_winner'], 
                                  capture_output=True)
            time.sleep(2)
            logger.info("🛑 Stopped current strategy")
        except Exception as e:
            logger.error(f"Error stopping current strategy: {e}")
    
    def _start_new_strategy(self, strategy_file: str) -> bool:
        """Start new strategy"""
        try:
            # Start new strategy in background
            process = subprocess.Popen(['python3', strategy_file], 
                                     stdout=subprocess.DEVNULL, 
                                     stderr=subprocess.DEVNULL)
            time.sleep(3)
            
            # Check if process is still running
            if process.poll() is None:
                logger.info(f"✅ Started new strategy: {strategy_file}")
                return True
            else:
                logger.error(f"❌ Strategy failed to start: {strategy_file}")
                return False
                
        except Exception as e:
            logger.error(f"Error starting new strategy: {e}")
            return False
    
    def _update_deployment_record(self, strategy: StrategyScore):
        """Update deployment record in database"""
        
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        # Update strategy deployment count
        cursor.execute('''
            UPDATE strategies 
            SET times_deployed = times_deployed + 1, status = 'deployed'
            WHERE strategy_id = ?
        ''', (strategy.strategy_id,))
        
        # Add deployment history
        cursor.execute('''
            INSERT INTO deployment_history 
            (strategy_id, deployment_time, performance_period, live_return, benchmark_return, success, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (strategy.strategy_id, datetime.now(timezone.utc).isoformat(), 
              '1h', 0.0, 0.0, True, f'Auto-deployed with score {strategy.overall_score:.3f}'))
        
        conn.commit()
        conn.close()

class ContinuousWinnerManager:
    """Continuously manage winning strategies"""
    
    def __init__(self):
        self.db = WinningStrategyDatabase()
        self.auto_deploy = AutoDeploymentSystem(self.db)
        self.running = False
        
    async def run_continuous_management(self):
        """Run continuous strategy management"""
        
        logger.info("🚀 Starting Continuous Winner Management")
        logger.info("🏆 Collecting winning strategies, scoring, and auto-deploying best performers")
        
        self.running = True
        
        while self.running:
            try:
                # 1. Collect new strategy results
                await self._collect_strategy_results()
                
                # 2. Score and update database
                await self._update_strategy_scores()
                
                # 3. Check for deployment opportunities
                await self._check_deployment_opportunities()
                
                # 4. Report status
                await self._report_status()
                
                # Wait 5 minutes before next cycle
                await asyncio.sleep(300)
                
            except Exception as e:
                logger.error(f"❌ Error in winner management: {e}")
                await asyncio.sleep(60)
    
    async def _collect_strategy_results(self):
        """Collect strategy results from various sources"""
        
        # Collect from backtest results
        result_files = glob.glob('backtest_results/*.json')
        
        for file_path in result_files:
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                
                # Process different data formats
                strategies = self._extract_strategies_from_results(data)
                
                for strategy_data in strategies:
                    if strategy_data.get('total_return', 0) > 0.05:  # Only 5%+ return strategies
                        self.db.add_or_update_strategy(strategy_data)
                
            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")
    
    def _extract_strategies_from_results(self, data: Any) -> List[Dict]:
        """Extract strategy data from various result formats"""
        
        strategies = []
        
        if isinstance(data, list):
            strategies.extend(data)
        elif isinstance(data, dict):
            # Handle different structures
            for key, value in data.items():
                if isinstance(value, list):
                    strategies.extend(value)
                elif isinstance(value, dict) and 'strategy' in value:
                    strategies.append(value)
        
        return strategies
    
    async def _update_strategy_scores(self):
        """Update strategy scores based on latest data"""
        
        # Get all strategies and recalculate scores
        top_strategies = self.db.get_top_strategies(limit=50, min_score=0.0)
        
        logger.info(f"📊 Updated scores for {len(top_strategies)} strategies")
    
    async def _check_deployment_opportunities(self):
        """Check if we should deploy a new strategy"""
        
        if self.auto_deploy.should_deploy_new_strategy():
            candidates = self.db.get_deployment_candidates()
            if candidates:
                best_candidate = candidates[0]
                logger.info(f"🎯 Deploying new winning strategy: {best_candidate.strategy_name}")
                
                success = self.auto_deploy.deploy_strategy(best_candidate)
                if success:
                    logger.info("🏆 WINNING STRATEGY DEPLOYED SUCCESSFULLY!")
                else:
                    logger.error("❌ Failed to deploy winning strategy")
    
    async def _report_status(self):
        """Report current status"""
        
        top_strategies = self.db.get_top_strategies(limit=5)
        
        logger.info("🏆 TOP 5 WINNING STRATEGIES:")
        for i, strategy in enumerate(top_strategies, 1):
            logger.info(f"{i}. {strategy.strategy_name} ({strategy.timeframe})")
            logger.info(f"   Score: {strategy.overall_score:.3f} | Return: {strategy.total_return:+.2%} | Win Rate: {strategy.win_rate:.1%}")
        
        # Check current deployment
        if self.auto_deploy.current_strategy:
            current = self.auto_deploy.current_strategy
            deployment_time = (time.time() - self.auto_deploy.deployment_start_time) / 3600
            logger.info(f"🚀 CURRENTLY DEPLOYED: {current.strategy_name} ({deployment_time:.1f}h)")

def main():
    """Main function"""
    manager = ContinuousWinnerManager()
    
    try:
        asyncio.run(manager.run_continuous_management())
    except KeyboardInterrupt:
        logger.info("👋 Continuous Winner Manager stopped")
        manager.running = False

if __name__ == "__main__":
    main()