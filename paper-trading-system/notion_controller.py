#!/usr/bin/env python3
"""
Notion Integration for Paper Trading Control
Provides mobile and desktop control via Notion workspace
"""

import asyncio
import json
import logging
import os
import signal
import subprocess
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import psutil

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PaperTradingNotionController:
    """Notion-based control system for paper trading"""
    
    def __init__(self):
        self.trading_process = None
        self.trading_pid = None
        self.last_status_update = 0
        self.status_update_interval = 30  # Update Notion every 30 seconds
        
        # Default Notion page ID from README
        self.notion_page_id = "26138364579a81708596caa9cd639f29"
        
    async def update_notion_status(self, status_data: Dict[str, Any]) -> bool:
        """Update Notion page with current trading status"""
        try:
            # Import notion tools if available
            from mcp__notion__notion_pages import notion_pages
            from mcp__notion__notion_blocks import notion_blocks
            
            # Create status blocks for Notion page
            status_blocks = await self._create_status_blocks(status_data)
            
            # Update the Notion page
            result = await notion_blocks({
                "payload": {
                    "action": "append_block_children",
                    "params": {
                        "blockId": self.notion_page_id,
                        "children": status_blocks
                    }
                }
            })
            
            return True
            
        except ImportError:
            logger.warning("Notion integration not available - using local status file")
            await self._create_local_status_file(status_data)
            return False
            
        except Exception as e:
            logger.error(f"Failed to update Notion: {e}")
            return False
    
    async def _create_status_blocks(self, status_data: Dict[str, Any]) -> list:
        """Create Notion blocks for trading status"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        blocks = [
            {
                "type": "heading_1",
                "heading_1": {
                    "rich_text": [{
                        "type": "text",
                        "text": {"content": f"🎯 Paper Trading Status - {timestamp}"}
                    }]
                }
            },
            {
                "type": "paragraph", 
                "paragraph": {
                    "rich_text": [{
                        "type": "text",
                        "text": {"content": f"💰 Portfolio Value: ${status_data.get('portfolio_value', 0):,.2f}"}
                    }]
                }
            },
            {
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{
                        "type": "text", 
                        "text": {"content": f"₿ BTC Price: ${status_data.get('btc_price', 0):,.2f}"}
                    }]
                }
            },
            {
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{
                        "type": "text",
                        "text": {"content": f"💵 USD Balance: ${status_data.get('usd_balance', 0):,.2f}"}
                    }]
                }
            },
            {
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{
                        "type": "text",
                        "text": {"content": f"₿ BTC Balance: {status_data.get('btc_balance', 0):.6f}"}
                    }]
                }
            },
            {
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{
                        "type": "text",
                        "text": {"content": f"📊 Total Trades: {status_data.get('total_trades', 0)} | Win Rate: {status_data.get('win_rate', 0):.1f}%"}
                    }]
                }
            },
            {
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{
                        "type": "text",
                        "text": {"content": f"📈 P&L: ${status_data.get('pnl', 0):+.2f} | Return: {status_data.get('return_pct', 0):+.2f}%"}
                    }]
                }
            },
            {
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{
                        "type": "text",
                        "text": {"content": f"⚡ Status: {'🟢 RUNNING' if status_data.get('is_running') else '🔴 STOPPED'}"}
                    }]
                }
            },
            {
                "type": "divider",
                "divider": {}
            }
        ]
        
        return blocks
    
    async def _create_local_status_file(self, status_data: Dict[str, Any]):
        """Create local status file as fallback"""
        status_file = "/tmp/paper_trading_status.json"
        
        try:
            with open(status_file, 'w') as f:
                json.dump({
                    **status_data,
                    'last_update': datetime.now().isoformat(),
                    'notion_integration': False
                }, f, indent=2)
                
            logger.info(f"Status saved to {status_file}")
            
        except Exception as e:
            logger.error(f"Failed to save status file: {e}")
    
    async def get_trading_status(self) -> Dict[str, Any]:
        """Get current trading system status"""
        try:
            # Check if trading process is running
            is_running = self.is_trading_running()
            
            # Parse latest log data
            log_data = await self._parse_latest_logs()
            
            status = {
                'is_running': is_running,
                'timestamp': datetime.now().isoformat(),
                'btc_price': log_data.get('btc_price', 0),
                'portfolio_value': log_data.get('portfolio_value', 0),
                'usd_balance': log_data.get('usd_balance', 0),
                'btc_balance': log_data.get('btc_balance', 0),
                'total_trades': log_data.get('total_trades', 0),
                'win_rate': log_data.get('win_rate', 0),
                'pnl': log_data.get('pnl', 0),
                'return_pct': log_data.get('return_pct', 0),
                'decisions_per_min': log_data.get('decisions_per_min', 0),
                'data_quality': log_data.get('data_quality', 'Unknown')
            }
            
            return status
            
        except Exception as e:
            logger.error(f"Failed to get trading status: {e}")
            return {
                'is_running': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def _parse_latest_logs(self) -> Dict[str, Any]:
        """Parse latest trading logs for status data"""
        log_file = "/tmp/paper_trading.log"
        
        try:
            if not os.path.exists(log_file):
                return {}
            
            # Read last 100 lines of log file
            with open(log_file, 'r') as f:
                lines = f.readlines()[-100:]
            
            # Parse relevant data from logs
            data = {}
            
            for line in reversed(lines):
                if "Current BTC Price:" in line:
                    try:
                        price_str = line.split("$")[1].split()[0].replace(",", "")
                        data['btc_price'] = float(price_str)
                    except:
                        pass
                        
                elif "Portfolio Value:" in line:
                    try:
                        value_str = line.split("$")[1].split()[0].replace(",", "")
                        data['portfolio_value'] = float(value_str)
                    except:
                        pass
                        
                elif "USD Balance:" in line:
                    try:
                        balance_str = line.split("$")[1].split()[0].replace(",", "")
                        data['usd_balance'] = float(balance_str)
                    except:
                        pass
                        
                elif "BTC Balance:" in line:
                    try:
                        balance_str = line.split("BTC Balance:")[1].strip().split()[0]
                        data['btc_balance'] = float(balance_str)
                    except:
                        pass
                        
                elif "Total Trades:" in line:
                    try:
                        trades_str = line.split("Total Trades:")[1].strip().split()[0]
                        data['total_trades'] = int(trades_str)
                    except:
                        pass
                        
                elif "Win Rate:" in line:
                    try:
                        rate_str = line.split("Win Rate:")[1].strip().split("%")[0]
                        data['win_rate'] = float(rate_str)
                    except:
                        pass
                        
                elif "Return:" in line and "%" in line:
                    try:
                        return_str = line.split("Return:")[1].strip().split("%")[0].replace("+", "")
                        data['return_pct'] = float(return_str)
                    except:
                        pass
                        
                elif "Decisions/Min:" in line:
                    try:
                        decisions_str = line.split("Decisions/Min:")[1].strip().split(",")[0]
                        data['decisions_per_min'] = int(decisions_str)
                    except:
                        pass
                        
                elif "Data Quality:" in line:
                    try:
                        quality = line.split("Data Quality:")[1].strip()
                        data['data_quality'] = quality
                    except:
                        pass
            
            return data
            
        except Exception as e:
            logger.error(f"Failed to parse logs: {e}")
            return {}
    
    def is_trading_running(self) -> bool:
        """Check if paper trading process is running"""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = proc.info['cmdline']
                    if cmdline and any('enhanced_paper_trading' in str(cmd) for cmd in cmdline):
                        self.trading_pid = proc.info['pid']
                        return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            return False
        except Exception as e:
            logger.error(f"Error checking process: {e}")
            return False
    
    async def start_trading(self, config: str = "default") -> bool:
        """Start paper trading system"""
        try:
            if self.is_trading_running():
                logger.info("Trading system already running")
                return True
            
            # Start the trading process
            cmd = ["python3", "enhanced_paper_trading.py"]
            
            if config != "default":
                env = os.environ.copy()
                env['PAPER_TRADING_CONFIG'] = config
            else:
                env = None
            
            self.trading_process = subprocess.Popen(
                cmd,
                cwd="/home/ajdev/btcusdt-advanced-backtesting/production",
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait a moment to check if it started successfully
            await asyncio.sleep(2)
            
            if self.is_trading_running():
                logger.info(f"Trading system started with config: {config}")
                return True
            else:
                logger.error("Failed to start trading system")
                return False
                
        except Exception as e:
            logger.error(f"Failed to start trading: {e}")
            return False
    
    async def stop_trading(self) -> bool:
        """Stop paper trading system"""
        try:
            if not self.is_trading_running():
                logger.info("Trading system not running")
                return True
            
            # Send SIGTERM to the process
            if self.trading_pid:
                os.kill(self.trading_pid, signal.SIGTERM)
                
                # Wait for graceful shutdown
                for _ in range(10):
                    await asyncio.sleep(1)
                    if not self.is_trading_running():
                        logger.info("Trading system stopped gracefully")
                        return True
                
                # Force kill if needed
                try:
                    os.kill(self.trading_pid, signal.SIGKILL)
                    logger.info("Trading system force stopped")
                except:
                    pass
                    
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop trading: {e}")
            return False
    
    async def monitor_and_update(self):
        """Main monitoring loop - updates Notion with status"""
        logger.info("🎯 Starting Notion monitoring for paper trading")
        
        try:
            while True:
                current_time = time.time()
                
                # Update status every interval
                if current_time - self.last_status_update >= self.status_update_interval:
                    status = await self.get_trading_status()
                    
                    # Update Notion with current status
                    await self.update_notion_status(status)
                    
                    self.last_status_update = current_time
                    
                    logger.info(f"📊 Status updated - Running: {status.get('is_running', False)}")
                
                await asyncio.sleep(5)  # Check every 5 seconds
                
        except KeyboardInterrupt:
            logger.info("Monitoring stopped")
        except Exception as e:
            logger.error(f"Monitoring error: {e}")

async def main():
    """Main entry point"""
    controller = PaperTradingNotionController()
    
    # Start monitoring
    await controller.monitor_and_update()

if __name__ == "__main__":
    asyncio.run(main())