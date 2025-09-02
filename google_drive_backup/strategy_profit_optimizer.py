#!/usr/bin/env python3
"""
Strategy Profit Optimizer
Continuously scores strategies, picks winners, and maximizes profit
Uses only standard library for maximum compatibility
"""

import json
import os
import time
import logging
import csv
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Tuple, Any, Optional
import subprocess
import glob
import shutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [OPTIMIZER] %(message)s',
    handlers=[
        logging.FileHandler('/tmp/strategy_optimizer.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class StrategyProfitOptimizer:
    """Continuously optimize strategies for maximum profit"""
    
    def __init__(self):
        self.winning_strategies = []
        self.strategy_scores = {}
        self.deployment_history = []
        self.running = False
        
        # Profit optimization weights
        self.profit_weights = {
            'total_return': 0.40,      # 40% - Pure profit focus
            'risk_adjusted_return': 0.25, # 25% - Risk-adjusted gains
            'win_rate': 0.15,          # 15% - Consistency
            'trade_frequency': 0.10,    # 10% - More opportunities
            'live_performance': 0.10    # 10% - Real-world success
        }
        
        logger.info("🚀 Strategy Profit Optimizer initialized")
        logger.info("💰 Focus: MAXIMUM PROFIT with optimal risk management")
    
    def calculate_profit_score(self, strategy_data: Dict) -> float:
        """Calculate profit-optimized score"""
        
        total_return = strategy_data.get('total_return', 0)
        win_rate = strategy_data.get('win_rate', 0)
        sharpe_ratio = strategy_data.get('sharpe_ratio', 0)
        max_drawdown = strategy_data.get('max_drawdown', 0)
        total_trades = strategy_data.get('total_trades', 0)
        
        # 1. Pure return score (logarithmic to favor high returns)
        import math
        return_score = min(1.0, math.log(1 + abs(total_return * 10)) / 3)
        if total_return < 0:
            return_score = -return_score
        
        # 2. Risk-adjusted return (Sharpe with drawdown penalty)
        risk_adj_score = min(1.0, max(0, sharpe_ratio / 5.0))  # Sharpe 5.0 = perfect
        if max_drawdown > 0:
            risk_adj_score *= (1 - min(0.5, max_drawdown / 0.3))  # Penalty for high drawdown
        
        # 3. Win rate score (higher win rate = more consistent profits)
        win_score = min(1.0, win_rate / 0.8)  # 80% win rate = perfect
        
        # 4. Trade frequency score (more trades = more profit opportunities)
        trade_freq_score = min(1.0, total_trades / 200)  # 200 trades = very active
        
        # 5. Profit factor bonus
        profit_factor = strategy_data.get('profit_factor', 1)
        profit_bonus = min(0.2, (profit_factor - 1) / 5)  # Up to 0.2 bonus
        
        # Calculate weighted profit score
        profit_score = (
            return_score * self.profit_weights['total_return'] +
            risk_adj_score * self.profit_weights['risk_adjusted_return'] +
            win_score * self.profit_weights['win_rate'] +
            trade_freq_score * self.profit_weights['trade_frequency']
        ) + profit_bonus
        
        return max(0.0, min(1.0, profit_score))
    
    def collect_all_strategies(self) -> List[Dict]:
        """Collect all strategies from backtesting results"""
        
        all_strategies = []
        
        # Collect from various result files
        result_patterns = [
            'backtest_results/*.json',
            'backtest_results/*results*.json',
            'monitoring_results/*.jsonl'
        ]
        
        for pattern in result_patterns:
            files = glob.glob(pattern)
            
            for file_path in files:
                try:
                    strategies = self._load_strategies_from_file(file_path)
                    all_strategies.extend(strategies)
                    
                except Exception as e:
                    logger.error(f"Error loading {file_path}: {e}")
        
        logger.info(f"📊 Collected {len(all_strategies)} strategies from results")
        return all_strategies
    
    def _load_strategies_from_file(self, file_path: str) -> List[Dict]:
        """Load strategies from a specific file"""
        
        strategies = []
        
        if file_path.endswith('.jsonl'):
            # Line-delimited JSON
            with open(file_path, 'r') as f:
                for line in f:
                    try:
                        data = json.loads(line.strip())
                        if 'strategy_name' in data:
                            strategies.append(data)
                    except json.JSONDecodeError:
                        continue
        else:
            # Regular JSON
            with open(file_path, 'r') as f:
                data = json.load(f)
                
                if isinstance(data, list):
                    strategies.extend(data)
                elif isinstance(data, dict):
                    # Handle different JSON structures
                    strategies.extend(self._extract_strategies_from_dict(data))
        
        return strategies
    
    def _extract_strategies_from_dict(self, data: Dict) -> List[Dict]:
        """Extract strategies from nested dictionary structures"""
        
        strategies = []
        
        # Look for strategy data in various structures
        if 'strategy' in data:
            strategies.append(data)
        
        # Check for timeframe-organized data
        for key, value in data.items():
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, dict) and ('strategy' in item or 'total_return' in item):
                        strategies.append(item)
            elif isinstance(value, dict) and ('strategy' in value or 'total_return' in value):
                strategies.append(value)
        
        return strategies
    
    def score_and_rank_strategies(self, strategies: List[Dict]) -> List[Tuple[float, Dict]]:
        """Score and rank strategies by profit potential"""
        
        scored_strategies = []
        
        for strategy in strategies:
            try:
                # Calculate profit score
                profit_score = self.calculate_profit_score(strategy)
                
                # Only keep profitable strategies
                if profit_score > 0.3:  # Minimum 30% profit score
                    scored_strategies.append((profit_score, strategy))
                    
                    # Store in scores dict
                    strategy_name = strategy.get('strategy', 'Unknown')
                    self.strategy_scores[strategy_name] = profit_score
                    
            except Exception as e:
                logger.error(f"Error scoring strategy: {e}")
        
        # Sort by profit score (highest first)
        scored_strategies.sort(key=lambda x: x[0], reverse=True)
        
        logger.info(f"💰 Found {len(scored_strategies)} profitable strategies")
        return scored_strategies
    
    def identify_winning_strategies(self, scored_strategies: List[Tuple[float, Dict]], top_n: int = 10) -> List[Dict]:
        """Identify top winning strategies"""
        
        winners = []
        
        for score, strategy in scored_strategies[:top_n]:
            
            # Enhanced strategy info
            winner_info = {
                'profit_score': score,
                'strategy_name': strategy.get('strategy', 'Unknown'),
                'timeframe': strategy.get('timeframe', '1h'),
                'total_return': strategy.get('total_return', 0),
                'win_rate': strategy.get('win_rate', 0),
                'sharpe_ratio': strategy.get('sharpe_ratio', 0),
                'max_drawdown': strategy.get('max_drawdown', 0),
                'total_trades': strategy.get('total_trades', 0),
                'parameters': strategy.get('parameters', {}),
                'profit_potential': self._calculate_profit_potential(strategy),
                'risk_level': self._calculate_risk_level(strategy),
                'recommended_allocation': self._calculate_allocation(score)
            }
            
            winners.append(winner_info)
        
        self.winning_strategies = winners
        return winners
    
    def _calculate_profit_potential(self, strategy: Dict) -> str:
        """Calculate profit potential category"""
        
        total_return = strategy.get('total_return', 0)
        
        if total_return >= 1.0:    # 100%+ return
            return "EXTREMELY HIGH"
        elif total_return >= 0.5:  # 50%+ return
            return "HIGH"
        elif total_return >= 0.2:  # 20%+ return
            return "MEDIUM"
        elif total_return >= 0.1:  # 10%+ return
            return "MODERATE"
        else:
            return "LOW"
    
    def _calculate_risk_level(self, strategy: Dict) -> str:
        """Calculate risk level"""
        
        max_drawdown = strategy.get('max_drawdown', 0)
        sharpe_ratio = strategy.get('sharpe_ratio', 0)
        
        if max_drawdown > 0.3 or sharpe_ratio < 1.0:
            return "HIGH"
        elif max_drawdown > 0.15 or sharpe_ratio < 2.0:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _calculate_allocation(self, profit_score: float) -> float:
        """Calculate recommended capital allocation percentage"""
        
        # Higher scoring strategies get more allocation
        if profit_score >= 0.8:
            return 0.30  # 30% allocation for top performers
        elif profit_score >= 0.6:
            return 0.20  # 20% allocation for good performers
        elif profit_score >= 0.4:
            return 0.10  # 10% allocation for decent performers
        else:
            return 0.05  # 5% allocation for marginal strategies
    
    def save_winning_strategies(self):
        """Save winning strategies to database files"""
        
        os.makedirs('winning_strategies', exist_ok=True)
        
        # Save detailed winners database
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        
        winners_file = f'winning_strategies/winners_database_{timestamp}.json'
        with open(winners_file, 'w') as f:
            json.dump(self.winning_strategies, f, indent=2)
        
        # Save current best strategies
        with open('winning_strategies/current_winners.json', 'w') as f:
            json.dump(self.winning_strategies, f, indent=2)
        
        # Create human-readable summary
        self._create_winners_summary()
        
        logger.info(f"💾 Saved {len(self.winning_strategies)} winning strategies")
    
    def _create_winners_summary(self):
        """Create human-readable summary of winning strategies"""
        
        summary_lines = [
            "🏆 WINNING STRATEGIES DATABASE",
            f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
            f"Total Winners: {len(self.winning_strategies)}",
            "",
            "📊 TOP PERFORMERS:",
            "=" * 80
        ]
        
        for i, winner in enumerate(self.winning_strategies[:10], 1):
            summary_lines.extend([
                f"{i:2d}. {winner['strategy_name']} ({winner['timeframe']})",
                f"    💰 Profit Score: {winner['profit_score']:.3f}",
                f"    📈 Return: {winner['total_return']:+.2%}",
                f"    🎯 Win Rate: {winner['win_rate']:.1%}",
                f"    ⚡ Sharpe: {winner['sharpe_ratio']:.2f}",
                f"    🛡️  Max DD: {winner['max_drawdown']:.1%}",
                f"    💼 Risk: {winner['risk_level']} | Profit: {winner['profit_potential']}",
                f"    📊 Allocation: {winner['recommended_allocation']:.1%}",
                ""
            ])
        
        # Save summary
        with open('winning_strategies/winners_summary.txt', 'w') as f:
            f.write('\n'.join(summary_lines))
    
    def auto_deploy_best_strategy(self) -> bool:
        """Auto-deploy the best strategy if significantly better"""
        
        if not self.winning_strategies:
            logger.warning("No winning strategies to deploy")
            return False
        
        best_strategy = self.winning_strategies[0]
        
        # Deploy if score is very high
        if best_strategy['profit_score'] >= 0.75:
            
            logger.info(f"🚀 AUTO-DEPLOYING BEST STRATEGY: {best_strategy['strategy_name']}")
            logger.info(f"   💰 Profit Score: {best_strategy['profit_score']:.3f}")
            logger.info(f"   📈 Expected Return: {best_strategy['total_return']:+.2%}")
            logger.info(f"   🎯 Win Rate: {best_strategy['win_rate']:.1%}")
            logger.info(f"   💼 Risk Level: {best_strategy['risk_level']}")
            
            # Generate deployment signal
            deployment_signal = {
                'action': 'deploy_strategy',
                'strategy': best_strategy,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'reason': f"High profit score: {best_strategy['profit_score']:.3f}"
            }
            
            # Save deployment signal
            with open('winning_strategies/deployment_signal.json', 'w') as f:
                json.dump(deployment_signal, f, indent=2)
            
            logger.info("✅ Deployment signal generated")
            return True
        
        else:
            logger.info(f"⏳ Best strategy score {best_strategy['profit_score']:.3f} < 0.75, not deploying")
            return False
    
    def run_continuous_optimization(self):
        """Run continuous profit optimization"""
        
        logger.info("🚀 Starting Continuous Strategy Profit Optimization")
        logger.info("💰 Goal: MAXIMIZE PROFITS through winner selection and deployment")
        
        self.running = True
        cycle = 1
        
        while self.running:
            try:
                logger.info(f"🔄 Optimization Cycle #{cycle}")
                
                # 1. Collect all strategies
                all_strategies = self.collect_all_strategies()
                
                if not all_strategies:
                    logger.info("⏳ No strategies found, waiting for backtesting results...")
                    time.sleep(180)  # Wait 3 minutes
                    continue
                
                # 2. Score and rank by profit potential
                scored_strategies = self.score_and_rank_strategies(all_strategies)
                
                # 3. Identify winners
                winners = self.identify_winning_strategies(scored_strategies, top_n=15)
                
                # 4. Save winners database
                self.save_winning_strategies()
                
                # 5. Auto-deploy best strategy if excellent
                deployed = self.auto_deploy_best_strategy()
                
                # 6. Report results
                self._report_optimization_results(winners, deployed)
                
                cycle += 1
                
                # Wait 10 minutes before next optimization cycle
                time.sleep(600)
                
            except KeyboardInterrupt:
                logger.info("👋 Optimization stopped by user")
                break
            except Exception as e:
                logger.error(f"❌ Error in optimization cycle: {e}")
                time.sleep(300)  # Wait 5 minutes on error
        
        self.running = False
    
    def _report_optimization_results(self, winners: List[Dict], deployed: bool):
        """Report optimization results"""
        
        if not winners:
            logger.warning("⚠️  No winning strategies found")
            return
        
        logger.info("💰 PROFIT OPTIMIZATION RESULTS:")
        logger.info("🏆 TOP 5 WINNING STRATEGIES:")
        
        for i, winner in enumerate(winners[:5], 1):
            logger.info(
                f"{i}. {winner['strategy_name']:<20} ({winner['timeframe']:>3}): "
                f"Score={winner['profit_score']:.3f} | "
                f"Return={winner['total_return']:+7.2%} | "
                f"WinRate={winner['win_rate']:5.1%} | "
                f"Risk={winner['risk_level']:<6} | "
                f"Profit={winner['profit_potential']}"
            )
        
        if deployed:
            logger.info("🚀 BEST STRATEGY AUTO-DEPLOYED!")
        
        # Calculate total profit potential
        total_potential = sum(w['total_return'] * w['recommended_allocation'] for w in winners[:5])
        logger.info(f"💎 Portfolio Profit Potential: {total_potential:+.2%}")
        
        logger.info("─" * 80)

def main():
    """Main optimization function"""
    
    optimizer = StrategyProfitOptimizer()
    
    try:
        optimizer.run_continuous_optimization()
    except KeyboardInterrupt:
        logger.info("👋 Strategy Profit Optimizer stopped")
        optimizer.running = False

if __name__ == "__main__":
    main()