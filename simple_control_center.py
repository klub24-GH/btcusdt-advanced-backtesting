#!/usr/bin/env python3
"""
Simple Control Center (No External Dependencies)
Browser-based mobile & desktop control using built-in Python only
"""

import asyncio
import json
import os
import signal
import subprocess
import time
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import threading
import psutil

class TradingController:
    def __init__(self):
        self.trading_process = None
        self.trading_pid = None
        
    def is_trading_running(self) -> bool:
        """Check if paper trading is running"""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = proc.info['cmdline'] or []
                    if any('enhanced_paper_trading' in str(cmd) for cmd in cmdline):
                        self.trading_pid = proc.info['pid']
                        return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            return False
        except Exception:
            return False
    
    def get_status(self) -> dict:
        """Get current trading status"""
        try:
            # Parse latest logs
            log_data = {}
            log_file = "/tmp/paper_trading.log"
            
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    lines = f.readlines()[-50:]
                
                for line in reversed(lines):
                    if "Current BTC Price:" in line and 'btc_price' not in log_data:
                        try:
                            price_str = line.split("$")[1].split()[0].replace(",", "")
                            log_data['btc_price'] = float(price_str)
                        except:
                            pass
                    elif "Portfolio Value:" in line and 'portfolio_value' not in log_data:
                        try:
                            value_str = line.split("$")[1].split()[0].replace(",", "")
                            log_data['portfolio_value'] = float(value_str)
                        except:
                            pass
                    elif "USD Balance:" in line and 'usd_balance' not in log_data:
                        try:
                            balance_str = line.split("$")[1].split()[0].replace(",", "")
                            log_data['usd_balance'] = float(balance_str)
                        except:
                            pass
                    elif "BTC Balance:" in line and 'btc_balance' not in log_data:
                        try:
                            balance_str = line.split("BTC Balance:")[1].strip().split()[0]
                            log_data['btc_balance'] = float(balance_str)
                        except:
                            pass
                    elif "Total Trades:" in line and 'total_trades' not in log_data:
                        try:
                            trades_str = line.split("Total Trades:")[1].strip().split()[0]
                            log_data['total_trades'] = int(trades_str)
                        except:
                            pass
            
            return {
                'is_running': self.is_trading_running(),
                'timestamp': datetime.now().isoformat(),
                'btc_price': log_data.get('btc_price', 0),
                'portfolio_value': log_data.get('portfolio_value', 0),
                'usd_balance': log_data.get('usd_balance', 0),
                'btc_balance': log_data.get('btc_balance', 0),
                'total_trades': log_data.get('total_trades', 0),
                'pid': self.trading_pid
            }
            
        except Exception as e:
            return {
                'is_running': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def start_trading(self, config: str = "default") -> dict:
        """Start paper trading system"""
        try:
            if self.is_trading_running():
                return {"success": True, "message": "Already running"}
            
            cmd = ["python3", "/home/ajdev/btcusdt-advanced-backtesting/production/enhanced_paper_trading.py"]
            
            env = None
            if config != "default":
                env = os.environ.copy()
                env['PAPER_TRADING_CONFIG'] = config
            
            self.trading_process = subprocess.Popen(
                cmd, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            
            time.sleep(2)
            
            if self.is_trading_running():
                return {"success": True, "message": f"Started with {config} config"}
            else:
                return {"success": False, "message": "Failed to start"}
                
        except Exception as e:
            return {"success": False, "message": f"Error: {str(e)}"}
    
    def stop_trading(self) -> dict:
        """Stop paper trading system"""
        try:
            if not self.is_trading_running():
                return {"success": True, "message": "Not running"}
            
            if self.trading_pid:
                os.kill(self.trading_pid, signal.SIGTERM)
                
                # Wait for graceful shutdown
                for _ in range(10):
                    time.sleep(1)
                    if not self.is_trading_running():
                        return {"success": True, "message": "Stopped gracefully"}
                
                # Force kill if needed
                try:
                    os.kill(self.trading_pid, signal.SIGKILL)
                except:
                    pass
                    
            return {"success": True, "message": "Stopped"}
            
        except Exception as e:
            return {"success": False, "message": f"Error: {str(e)}"}

controller = TradingController()

class ControlRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests"""
        path = urlparse(self.path).path
        
        if path == "/":
            self.serve_dashboard()
        elif path == "/status":
            self.serve_json(controller.get_status())
        elif path == "/api/status":
            self.serve_json(controller.get_status())
        else:
            self.send_error(404)
    
    def do_POST(self):
        """Handle POST requests"""
        path = urlparse(self.path).path
        
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            
            if path == "/start":
                try:
                    data = json.loads(post_data)
                    config = data.get('config', 'default')
                except:
                    config = 'default'
                result = controller.start_trading(config)
                self.serve_json(result)
            elif path == "/stop":
                result = controller.stop_trading()
                self.serve_json(result)
            else:
                self.send_error(404)
                
        except Exception as e:
            self.serve_json({"success": False, "message": str(e)})
    
    def serve_json(self, data):
        """Send JSON response"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def serve_dashboard(self):
        """Serve mobile-responsive dashboard"""
        html = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>🎯 Paper Trading Control</title>
            <style>
                * { margin: 0; padding: 0; box-sizing: border-box; }
                body { 
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white; min-height: 100vh; padding: 15px;
                }
                .container { max-width: 800px; margin: 0 auto; }
                .header { text-align: center; margin-bottom: 25px; }
                .card { 
                    background: rgba(255,255,255,0.1); backdrop-filter: blur(10px);
                    border-radius: 15px; padding: 20px; margin-bottom: 20px;
                    border: 1px solid rgba(255,255,255,0.2);
                }
                .status-grid { 
                    display: grid; 
                    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); 
                    gap: 15px; 
                }
                .stat { 
                    text-align: center; padding: 15px; 
                    background: rgba(255,255,255,0.1); 
                    border-radius: 10px; 
                }
                .stat-value { font-size: 1.4em; font-weight: bold; margin-bottom: 5px; }
                .stat-label { font-size: 0.85em; opacity: 0.8; }
                .controls { 
                    display: grid; 
                    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); 
                    gap: 12px; 
                }
                .btn { 
                    padding: 12px 20px; border: none; border-radius: 10px; 
                    font-size: 14px; cursor: pointer; transition: all 0.3s; 
                    font-weight: bold; color: white;
                }
                .btn-start { background: #4CAF50; }
                .btn-stop { background: #f44336; }
                .btn-config { background: #2196F3; }
                .btn:hover { transform: translateY(-2px); opacity: 0.9; }
                .btn:active { transform: translateY(0); }
                .status-indicator { 
                    width: 12px; height: 12px; border-radius: 50%; 
                    display: inline-block; margin-right: 8px; 
                }
                .running { background: #4CAF50; }
                .stopped { background: #f44336; }
                @media (max-width: 600px) {
                    .controls { grid-template-columns: 1fr 1fr; }
                    .status-grid { grid-template-columns: repeat(2, 1fr); }
                }
                .footer { text-align: center; margin-top: 20px; opacity: 0.8; font-size: 0.9em; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎯 Paper Trading Control</h1>
                    <p>Mobile & Desktop Control Center</p>
                </div>
                
                <div class="card">
                    <h2>📊 Live Status</h2>
                    <div style="margin: 15px 0;">
                        <span class="status-indicator stopped" id="status-dot"></span>
                        <span id="status-text">Loading...</span>
                    </div>
                    <div class="status-grid">
                        <div class="stat">
                            <div class="stat-value" id="portfolio">$0</div>
                            <div class="stat-label">Portfolio</div>
                        </div>
                        <div class="stat">
                            <div class="stat-value" id="btc-price">$0</div>
                            <div class="stat-label">BTC Price</div>
                        </div>
                        <div class="stat">
                            <div class="stat-value" id="usd-bal">$0</div>
                            <div class="stat-label">USD Balance</div>
                        </div>
                        <div class="stat">
                            <div class="stat-value" id="btc-bal">0</div>
                            <div class="stat-label">BTC Balance</div>
                        </div>
                        <div class="stat">
                            <div class="stat-value" id="trades">0</div>
                            <div class="stat-label">Trades</div>
                        </div>
                    </div>
                </div>
                
                <div class="card">
                    <h2>🎮 Controls</h2>
                    <div class="controls">
                        <button class="btn btn-start" onclick="start('default')">
                            🚀 START Default ($100K)
                        </button>
                        <button class="btn btn-config" onclick="start('conservative')">
                            🛡️ Conservative ($200K)
                        </button>
                        <button class="btn btn-config" onclick="start('aggressive')">
                            ⚡ Aggressive ($500K)
                        </button>
                        <button class="btn btn-config" onclick="start('learning')">
                            📚 Learning ($50K)
                        </button>
                        <button class="btn btn-stop" onclick="stop()" style="grid-column: span 2;">
                            🛑 STOP Trading
                        </button>
                    </div>
                </div>
                
                <div class="footer">
                    <p>🛡️ 100% Paper Trading - NO REAL MONEY at risk</p>
                    <p>Auto-refresh every 5 seconds</p>
                </div>
            </div>
            
            <script>
                function updateStatus() {
                    fetch('/status')
                        .then(r => r.json())
                        .then(data => {
                            const dot = document.getElementById('status-dot');
                            const text = document.getElementById('status-text');
                            
                            if (data.is_running) {
                                dot.className = 'status-indicator running';
                                text.textContent = 'System Running';
                            } else {
                                dot.className = 'status-indicator stopped';
                                text.textContent = 'System Stopped';
                            }
                            
                            document.getElementById('portfolio').textContent = 
                                '$' + (data.portfolio_value || 0).toLocaleString();
                            document.getElementById('btc-price').textContent = 
                                '$' + (data.btc_price || 0).toLocaleString();
                            document.getElementById('usd-bal').textContent = 
                                '$' + (data.usd_balance || 0).toLocaleString();
                            document.getElementById('btc-bal').textContent = 
                                (data.btc_balance || 0).toFixed(6);
                            document.getElementById('trades').textContent = 
                                data.total_trades || 0;
                        })
                        .catch(e => console.log('Update failed:', e));
                }
                
                function start(config) {
                    fetch('/start', {
                        method: 'POST',
                        body: JSON.stringify({config: config})
                    })
                    .then(r => r.json())
                    .then(data => {
                        alert(data.message);
                        updateStatus();
                    })
                    .catch(e => alert('Start failed: ' + e));
                }
                
                function stop() {
                    fetch('/stop', {method: 'POST'})
                        .then(r => r.json())
                        .then(data => {
                            alert(data.message);
                            updateStatus();
                        })
                        .catch(e => alert('Stop failed: ' + e));
                }
                
                // Auto-refresh every 5 seconds
                updateStatus();
                setInterval(updateStatus, 5000);
            </script>
        </body>
        </html>
        """
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode())
    
    def log_message(self, format, *args):
        """Suppress default logging"""
        return

def start_server():
    """Start the control center server"""
    server = HTTPServer(('0.0.0.0', 8000), ControlRequestHandler)
    print("🚀 Paper Trading Control Center Started!")
    print(f"📱 Mobile Access: http://your-ip:8000")
    print(f"💻 Desktop Access: http://localhost:8000")
    print("🛑 Press Ctrl+C to stop")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n✅ Control center stopped")
        server.shutdown()

if __name__ == "__main__":
    start_server()