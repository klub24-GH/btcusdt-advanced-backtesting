#!/usr/bin/env python3
"""
Live vs Historical Performance Monitor
Compares live trading performance with historical backtesting predictions
Uses only standard library for maximum compatibility
"""

import json
import csv
import os
import time
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass, asdict
import threading
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [MONITOR] %(message)s',
    handlers=[
        logging.FileHandler('/tmp/performance_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class LivePerformanceSnapshot:
    """Snapshot of live trading performance"""
    timestamp: str
    strategy_name: str
    portfolio_value: float
    total_return: float
    trades_count: int
    win_rate: float
    current_position: str
    btc_price: float
    trend: str

@dataclass
class PerformanceComparison:
    """Comparison between live and historical performance"""
    timestamp: str
    strategy_name: str
    live_return: float
    historical_return: float
    deviation_pct: float
    live_win_rate: float
    historical_win_rate: float
    accuracy_score: float
    confidence_level: str

class LivePerformanceTracker:
    """Track live trading performance from log files"""
    
    def __init__(self):
        self.live_snapshots = []
        self.log_files = [
            '/tmp/superior_strategy.log',
            '/tmp/proven_strategy.log',
            '/tmp/paper_trading.log',
            '/tmp/continuous_backtesting.log'
        ]
    
    def extract_live_metrics(self) -> Optional[LivePerformanceSnapshot]:
        """Extract current live performance metrics from log files"""
        
        for log_file in self.log_files:
            if not os.path.exists(log_file):
                continue
            
            try:
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                
                # Parse most recent status line
                for line in reversed(lines[-100:]):  # Check last 100 lines
                    if 'STATUS:' in line and 'Value=' in line:
                        return self._parse_status_line(line, log_file)
                
            except Exception as e:
                logger.error(f"Error reading {log_file}: {e}")
        
        return None
    
    def _parse_status_line(self, line: str, log_file: str) -> LivePerformanceSnapshot:
        """Parse a status log line to extract performance data"""
        
        # Extract strategy name from log file
        strategy_name = "Unknown"
        if 'superior' in log_file:
            strategy_name = "Superior_Trend_Sensitive"
        elif 'proven' in log_file:
            strategy_name = "Proven_Mean_Reversion"
        elif 'paper_trading' in log_file:
            strategy_name = "Enhanced_Paper_Trading"
        
        # Parse values using regex
        portfolio_value = self._extract_float(line, r'Value=\$([0-9,]+(?:\.[0-9]+)?)')
        total_return = self._extract_float(line, r'\(([+-]?[0-9]+\.[0-9]+)%\)')
        trades_count = self._extract_int(line, r'Trades=([0-9]+)')
        win_rate = self._extract_float(line, r'Win Rate=([0-9]+\.[0-9]+)%')
        current_position = self._extract_string(line, r'Position=([A-Za-z]+)')
        trend = self._extract_string(line, r'Trend=([A-Za-z]+)')
        
        # Extract BTC price (might be in different format)
        btc_price = 0.0
        if 'BTC' in line:
            btc_price = self._extract_float(line, r'\$([0-9,]+(?:\.[0-9]+)?)')
        
        return LivePerformanceSnapshot(
            timestamp=datetime.now(timezone.utc).isoformat(),
            strategy_name=strategy_name,
            portfolio_value=portfolio_value or 100000.0,
            total_return=(total_return or 0.0) / 100.0,  # Convert percentage
            trades_count=trades_count or 0,
            win_rate=(win_rate or 0.0) / 100.0,  # Convert percentage
            current_position=current_position or "None",
            btc_price=btc_price or 0.0,
            trend=trend or "UNKNOWN"
        )
    
    def _extract_float(self, text: str, pattern: str) -> Optional[float]:
        """Extract float value using regex pattern"""
        match = re.search(pattern, text)
        if match:
            try:
                # Remove commas and convert
                value_str = match.group(1).replace(',', '')
                return float(value_str)
            except ValueError:
                pass
        return None
    
    def _extract_int(self, text: str, pattern: str) -> Optional[int]:
        """Extract integer value using regex pattern"""
        match = re.search(pattern, text)
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                pass
        return None
    
    def _extract_string(self, text: str, pattern: str) -> Optional[str]:
        """Extract string value using regex pattern"""
        match = re.search(pattern, text)
        if match:
            return match.group(1)
        return None

class HistoricalPerformanceAnalyzer:
    """Analyze historical backtesting results"""
    
    def __init__(self):
        self.results_dir = 'backtest_results'
    
    def get_historical_performance(self, strategy_name: str, timeframe: str = None) -> Optional[Dict]:
        """Get historical performance for a strategy"""
        
        # Load latest backtesting results
        result_files = [
            'multi_timeframe_results.json',
            'continuous_master_results.json',
            'vectorbt_summary_*.json'
        ]
        
        for result_file in result_files:
            file_path = os.path.join(self.results_dir, result_file)
            
            if '*' in result_file:
                # Handle wildcard files
                import glob
                matching_files = glob.glob(file_path)
                if matching_files:
                    file_path = max(matching_files)  # Get latest
                else:
                    continue
            
            if not os.path.exists(file_path):
                continue
            
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                
                # Find matching strategy
                historical_data = self._find_matching_strategy(data, strategy_name, timeframe)
                if historical_data:
                    return historical_data
                
            except Exception as e:
                logger.error(f"Error loading {file_path}: {e}")
        
        return None
    
    def _find_matching_strategy(self, data: Any, strategy_name: str, timeframe: str = None) -> Optional[Dict]:
        """Find matching strategy in historical data"""
        
        # Handle different data formats
        if isinstance(data, list):
            # Array of results
            for result in data:
                if self._strategy_matches(result, strategy_name, timeframe):
                    return result
        
        elif isinstance(data, dict):
            # Check if it's a timeframe-organized structure
            if timeframe and timeframe in data:
                timeframe_data = data[timeframe]
                if isinstance(timeframe_data, list):
                    for result in timeframe_data:
                        if self._strategy_matches(result, strategy_name):
                            return result
            
            # Check direct match
            if self._strategy_matches(data, strategy_name, timeframe):
                return data
            
            # Search in nested structures
            for key, value in data.items():
                if isinstance(value, (list, dict)):
                    nested_result = self._find_matching_strategy(value, strategy_name, timeframe)
                    if nested_result:
                        return nested_result
        
        return None
    
    def _strategy_matches(self, result: Dict, strategy_name: str, timeframe: str = None) -> bool:
        """Check if a result matches the strategy criteria"""
        
        # Normalize strategy names for comparison
        result_strategy = result.get('strategy', '').lower().replace('_', ' ')
        target_strategy = strategy_name.lower().replace('_', ' ')
        
        # Check strategy name match
        strategy_match = (
            target_strategy in result_strategy or
            result_strategy in target_strategy or
            any(word in result_strategy for word in target_strategy.split())
        )
        
        # Check timeframe match if specified
        timeframe_match = True
        if timeframe:
            result_timeframe = result.get('timeframe', '')
            timeframe_match = timeframe == result_timeframe
        
        return strategy_match and timeframe_match

class PerformanceComparisonEngine:
    """Compare live performance with historical predictions"""
    
    def __init__(self):
        self.live_tracker = LivePerformanceTracker()
        self.historical_analyzer = HistoricalPerformanceAnalyzer()
        self.comparison_history = []
    
    def generate_comparison(self) -> Optional[PerformanceComparison]:
        """Generate current performance comparison"""
        
        # Get live performance
        live_snapshot = self.live_tracker.extract_live_metrics()
        if not live_snapshot:
            return None
        
        # Get historical performance
        historical_data = self.historical_analyzer.get_historical_performance(
            live_snapshot.strategy_name
        )
        if not historical_data:
            logger.warning(f"No historical data found for {live_snapshot.strategy_name}")
            return None
        
        # Extract historical metrics
        historical_return = historical_data.get('total_return', 0)
        historical_win_rate = historical_data.get('win_rate', 0)
        
        # Calculate comparison metrics
        deviation_pct = 0
        if historical_return != 0:
            deviation_pct = ((live_snapshot.total_return - historical_return) / abs(historical_return)) * 100
        
        # Calculate accuracy score
        return_accuracy = 1 - min(1, abs(deviation_pct) / 100)
        win_rate_accuracy = 1 - abs(live_snapshot.win_rate - historical_win_rate)
        accuracy_score = (return_accuracy + win_rate_accuracy) / 2
        
        # Determine confidence level
        confidence_level = "HIGH"
        if accuracy_score < 0.5:
            confidence_level = "LOW"
        elif accuracy_score < 0.7:
            confidence_level = "MEDIUM"
        
        comparison = PerformanceComparison(
            timestamp=live_snapshot.timestamp,
            strategy_name=live_snapshot.strategy_name,
            live_return=live_snapshot.total_return,
            historical_return=historical_return,
            deviation_pct=deviation_pct,
            live_win_rate=live_snapshot.win_rate,
            historical_win_rate=historical_win_rate,
            accuracy_score=accuracy_score,
            confidence_level=confidence_level
        )
        
        self.comparison_history.append(comparison)
        return comparison

class RealTimeMonitoringDashboard:
    """Real-time monitoring dashboard for live vs historical performance"""
    
    def __init__(self):
        self.comparison_engine = PerformanceComparisonEngine()
        self.running = False
        
    def start_monitoring(self, update_interval: int = 60):
        """Start real-time monitoring"""
        
        logger.info("🚀 Starting Real-Time Performance Monitoring")
        logger.info(f"📊 Update interval: {update_interval} seconds")
        
        self.running = True
        
        while self.running:
            try:
                comparison = self.comparison_engine.generate_comparison()
                
                if comparison:
                    self._display_comparison(comparison)
                    self._save_comparison_data(comparison)
                else:
                    logger.info("⏳ Waiting for live trading data...")
                
                time.sleep(update_interval)
                
            except KeyboardInterrupt:
                logger.info("👋 Monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"❌ Error in monitoring: {e}")
                time.sleep(30)  # Wait before retrying
        
        self.running = False
    
    def _display_comparison(self, comparison: PerformanceComparison):
        """Display performance comparison"""
        
        logger.info("📊 LIVE vs HISTORICAL PERFORMANCE COMPARISON")
        logger.info(f"   Strategy: {comparison.strategy_name}")
        logger.info(f"   Live Return: {comparison.live_return:+.2%}")
        logger.info(f"   Historical Return: {comparison.historical_return:+.2%}")
        logger.info(f"   Deviation: {comparison.deviation_pct:+.1f}%")
        logger.info(f"   Live Win Rate: {comparison.live_win_rate:.1%}")
        logger.info(f"   Historical Win Rate: {comparison.historical_win_rate:.1%}")
        logger.info(f"   Accuracy Score: {comparison.accuracy_score:.2f}")
        logger.info(f"   Confidence Level: {comparison.confidence_level}")
        
        # Determine status
        if comparison.accuracy_score > 0.8:
            logger.info("✅ EXCELLENT: Live performance matches historical predictions")
        elif comparison.accuracy_score > 0.6:
            logger.info("🟡 GOOD: Live performance reasonably close to predictions")
        else:
            logger.info("🔴 WARNING: Live performance significantly deviates from predictions")
        
        logger.info("-" * 60)
    
    def _save_comparison_data(self, comparison: PerformanceComparison):
        """Save comparison data to file"""
        
        os.makedirs('monitoring_results', exist_ok=True)
        
        # Append to daily log
        today = datetime.now().strftime('%Y%m%d')
        log_file = f'monitoring_results/performance_comparison_{today}.jsonl'
        
        with open(log_file, 'a') as f:
            f.write(json.dumps(asdict(comparison)) + '\n')
    
    def stop(self):
        """Stop monitoring"""
        self.running = False

def main():
    """Main monitoring function"""
    dashboard = RealTimeMonitoringDashboard()
    
    try:
        dashboard.start_monitoring(update_interval=30)  # Update every 30 seconds
    except KeyboardInterrupt:
        logger.info("👋 Performance monitoring stopped")
        dashboard.stop()

if __name__ == "__main__":
    main()