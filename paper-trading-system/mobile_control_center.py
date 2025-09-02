#!/usr/bin/env python3
"""
Mobile & Desktop Control Center (Zero Dependencies)
Browser-based control using only Python standard library
"""

import json
import os
import signal
import subprocess
import time
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import threading

class TradingController:
    def __init__(self):
        self.trading_process = None
        self.trading_pid = None
        
    def is_trading_running(self) -> bool:
        """Check if paper trading is running using process check"""
        try:
            # Check if process file exists
            pid_file = "/tmp/paper_trading.pid"
            if os.path.exists(pid_file):
                with open(pid_file, 'r') as f:
                    pid = int(f.read().strip())
                try:
                    # Check if process is still running
                    os.kill(pid, 0)  # Signal 0 just checks if process exists
                    self.trading_pid = pid
                    return True
                except OSError:
                    # Process not running, remove stale pid file
                    os.remove(pid_file)
                    return False
            
            # Alternative: check using ps command
            result = subprocess.run(['pgrep', '-f', 'enhanced_paper_trading'], 
                                  capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                self.trading_pid = int(result.stdout.strip().split('\n')[0])
                # Save PID for future reference
                with open(pid_file, 'w') as f:
                    f.write(str(self.trading_pid))
                return True
                
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
                # Read last 100 lines for better data extraction
                with open(log_file, 'r') as f:
                    lines = f.readlines()[-100:]
                
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
                    elif "Win Rate:" in line and 'win_rate' not in log_data:
                        try:
                            rate_str = line.split("Win Rate:")[1].strip().split("%")[0]
                            log_data['win_rate'] = float(rate_str)
                        except:
                            pass
                    elif "Total P&L:" in line and 'pnl' not in log_data:
                        try:
                            pnl_str = line.split("Total P&L: $")[1].split()[0].replace("+", "")
                            log_data['pnl'] = float(pnl_str)
                        except:
                            pass
                    elif "Decisions/Min:" in line and 'decisions_per_min' not in log_data:
                        try:
                            decisions_str = line.split("Decisions/Min:")[1].strip().split(",")[0]
                            log_data['decisions_per_min'] = int(decisions_str)
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
                'win_rate': log_data.get('win_rate', 0),
                'pnl': log_data.get('pnl', 0),
                'decisions_per_min': log_data.get('decisions_per_min', 0),
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
            
            env = os.environ.copy()
            if config != "default":
                env['PAPER_TRADING_CONFIG'] = config
            
            # Start in background and save PID
            self.trading_process = subprocess.Popen(
                cmd, env=env, 
                stdout=subprocess.DEVNULL, 
                stderr=subprocess.DEVNULL,
                preexec_fn=os.setsid  # Create new process group
            )
            
            # Save PID to file
            pid_file = "/tmp/paper_trading.pid"
            with open(pid_file, 'w') as f:
                f.write(str(self.trading_process.pid))
            
            time.sleep(3)  # Wait a bit longer for startup
            
            if self.is_trading_running():
                return {"success": True, "message": f"Started with {config} config"}
            else:
                return {"success": False, "message": "Failed to start - check logs"}
                
        except Exception as e:
            return {"success": False, "message": f"Error: {str(e)}"}
    
    def stop_trading(self) -> dict:
        """Stop paper trading system"""
        try:
            if not self.is_trading_running():
                return {"success": True, "message": "Not running"}
            
            if self.trading_pid:
                try:
                    # Try graceful shutdown first
                    os.kill(self.trading_pid, signal.SIGTERM)
                    
                    # Wait for graceful shutdown
                    for _ in range(10):
                        time.sleep(1)
                        if not self.is_trading_running():
                            # Clean up PID file
                            pid_file = "/tmp/paper_trading.pid"
                            if os.path.exists(pid_file):
                                os.remove(pid_file)
                            return {"success": True, "message": "Stopped gracefully"}
                    
                    # Force kill if needed
                    os.kill(self.trading_pid, signal.SIGKILL)
                    
                except OSError:
                    pass  # Process already dead
                    
                # Clean up PID file
                pid_file = "/tmp/paper_trading.pid"
                if os.path.exists(pid_file):
                    os.remove(pid_file)
                    
            return {"success": True, "message": "Stopped"}
            
        except Exception as e:
            return {"success": False, "message": f"Error: {str(e)}"}
    
    def start_proven_strategy(self) -> dict:
        """Start proven mean reversion strategy (69.1% win rate)"""
        try:
            if self.is_trading_running():
                # Stop current system first
                self.stop_trading()
                time.sleep(2)
            
            cmd = ["python3", "/home/ajdev/btcusdt-advanced-backtesting/production/proven_mean_reversion_strategy.py"]
            
            # Start proven strategy in background
            self.trading_process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL, 
                stderr=subprocess.DEVNULL,
                preexec_fn=os.setsid
            )
            
            # Save PID to file
            pid_file = "/tmp/paper_trading.pid"
            with open(pid_file, 'w') as f:
                f.write(str(self.trading_process.pid))
            
            time.sleep(3)
            
            if self.is_trading_running():
                return {"success": True, "message": "Proven Strategy Started - 69.1% Win Rate!"}
            else:
                return {"success": False, "message": "Failed to start proven strategy"}
                
        except Exception as e:
            return {"success": False, "message": f"Error starting proven strategy: {str(e)}"}
    
    def start_superior_strategy(self) -> dict:
        """Start superior trend sensitive strategy (120.34% return, 41.9% win rate)"""
        try:
            if self.is_trading_running():
                # Stop current system first
                self.stop_trading()
                time.sleep(2)
            
            cmd = ["python3", "/home/ajdev/btcusdt-advanced-backtesting/production/superior_trend_sensitive_strategy.py"]
            
            # Start superior strategy in background
            self.trading_process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL, 
                stderr=subprocess.DEVNULL,
                preexec_fn=os.setsid
            )
            
            # Save PID to file
            pid_file = "/tmp/paper_trading.pid"
            with open(pid_file, 'w') as f:
                f.write(str(self.trading_process.pid))
            
            time.sleep(3)
            
            if self.is_trading_running():
                return {"success": True, "message": "SUPERIOR Strategy Started - 120.34% Return!"}
            else:
                return {"success": False, "message": "Failed to start superior strategy"}
                
        except Exception as e:
            return {"success": False, "message": f"Error starting superior strategy: {str(e)}"}

controller = TradingController()

class ControlRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests"""
        path = urlparse(self.path).path
        
        if path == "/":
            self.serve_dashboard()
        elif path == "/status":
            self.serve_json(controller.get_status())
        else:
            self.send_error(404)
    
    def do_POST(self):
        """Handle POST requests"""
        path = urlparse(self.path).path
        
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length).decode('utf-8')
            
            if path == "/start":
                try:
                    data = json.loads(post_data) if post_data else {}
                    config = data.get('config', 'default')
                except:
                    config = 'default'
                result = controller.start_trading(config)
                self.serve_json(result)
            elif path == "/stop":
                result = controller.stop_trading()
                self.serve_json(result)
            elif path == "/start-proven":
                result = controller.start_proven_strategy()
                self.serve_json(result)
            elif path == "/start-superior":
                result = controller.start_superior_strategy()
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
        html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>🎯 Paper Trading Control</title>
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                body {{ 
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white; min-height: 100vh; padding: 15px;
                }}
                .container {{ max-width: 900px; margin: 0 auto; }}
                .header {{ text-align: center; margin-bottom: 25px; }}
                .card {{ 
                    background: rgba(255,255,255,0.1); backdrop-filter: blur(10px);
                    border-radius: 15px; padding: 20px; margin-bottom: 20px;
                    border: 1px solid rgba(255,255,255,0.2);
                }}
                .status-grid {{ 
                    display: grid; 
                    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); 
                    gap: 15px; 
                }}
                .stat {{ 
                    text-align: center; padding: 15px; 
                    background: rgba(255,255,255,0.1); 
                    border-radius: 10px; 
                }}
                .stat-value {{ font-size: 1.4em; font-weight: bold; margin-bottom: 5px; }}
                .stat-label {{ font-size: 0.85em; opacity: 0.8; }}
                .controls {{ 
                    display: grid; 
                    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); 
                    gap: 12px; 
                }}
                .btn {{ 
                    padding: 12px 20px; border: none; border-radius: 10px; 
                    font-size: 14px; cursor: pointer; transition: all 0.3s; 
                    font-weight: bold; color: white;
                }}
                .btn-start {{ background: #4CAF50; }}
                .btn-stop {{ background: #f44336; }}
                .btn-config {{ background: #2196F3; }}
                .btn:hover {{ transform: translateY(-2px); opacity: 0.9; }}
                .btn:active {{ transform: translateY(0); }}
                .btn:disabled {{ opacity: 0.5; cursor: not-allowed; transform: none; }}
                .status-indicator {{ 
                    width: 12px; height: 12px; border-radius: 50%; 
                    display: inline-block; margin-right: 8px; 
                }}
                .running {{ background: #4CAF50; animation: pulse 2s infinite; }}
                .stopped {{ background: #f44336; }}
                @keyframes pulse {{
                    0% {{ opacity: 1; }}
                    50% {{ opacity: 0.5; }}
                    100% {{ opacity: 1; }}
                }}
                
                @keyframes glow {{
                    0% {{ box-shadow: 0 0 20px rgba(255, 159, 243, 0.6), 0 0 30px rgba(255, 159, 243, 0.4); }}
                    50% {{ box-shadow: 0 0 30px rgba(255, 159, 243, 0.8), 0 0 40px rgba(255, 159, 243, 0.6); }}
                    100% {{ box-shadow: 0 0 20px rgba(255, 159, 243, 0.6), 0 0 30px rgba(255, 159, 243, 0.4); }}
                }}
                @media (max-width: 600px) {{
                    .controls {{ grid-template-columns: 1fr 1fr; }}
                    .status-grid {{ grid-template-columns: repeat(2, 1fr); }}
                }}
                .footer {{ text-align: center; margin-top: 20px; opacity: 0.8; font-size: 0.9em; }}
                .alert {{ 
                    padding: 10px; margin: 10px 0; border-radius: 5px; 
                    background: rgba(0,0,0,0.3); display: none;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎯 Paper Trading Control Center</h1>
                    <p>Mobile & Desktop Control • Real-time Updates</p>
                </div>
                
                <div class="card">
                    <h2>📊 Live System Status</h2>
                    <div style="margin: 15px 0;">
                        <span class="status-indicator stopped" id="status-dot"></span>
                        <span id="status-text">Loading...</span>
                        <span style="float: right; font-size: 0.9em;" id="last-update">--</span>
                    </div>
                    <div class="status-grid">
                        <div class="stat">
                            <div class="stat-value" id="portfolio">$0</div>
                            <div class="stat-label">Portfolio Value</div>
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
                            <div class="stat-value" id="btc-bal">0.000000</div>
                            <div class="stat-label">BTC Balance</div>
                        </div>
                        <div class="stat">
                            <div class="stat-value" id="trades">0</div>
                            <div class="stat-label">Total Trades</div>
                        </div>
                        <div class="stat">
                            <div class="stat-value" id="win-rate">0%</div>
                            <div class="stat-label">Win Rate</div>
                        </div>
                        <div class="stat">
                            <div class="stat-value" id="pnl">$0</div>
                            <div class="stat-label">P&L</div>
                        </div>
                        <div class="stat">
                            <div class="stat-value" id="decisions">0</div>
                            <div class="stat-label">Decisions/Min</div>
                        </div>
                    </div>
                </div>
                
                <div class="card">
                    <h2>🎮 Trading Controls</h2>
                    <div id="alert" class="alert"></div>
                    <div class="controls">
                        <button class="btn btn-start" onclick="start('default')" id="btn-default">
                            🚀 START Default<br><small>$100K Balance</small>
                        </button>
                        <button class="btn btn-config" onclick="start('conservative')" id="btn-conservative">
                            🛡️ Conservative<br><small>$200K Balance</small>
                        </button>
                        <button class="btn btn-config" onclick="start('aggressive')" id="btn-aggressive">
                            ⚡ Aggressive<br><small>$500K Balance</small>
                        </button>
                        <button class="btn btn-config" onclick="start('learning')" id="btn-learning" style="background: linear-gradient(135deg, #a55eea, #26de81); color: white; font-weight: bold;">
                            🧠 ADAPTIVE AI<br><small>$100K - LEARNS & IMPROVES!</small>
                        </button>
                        <button class="btn btn-config" onclick="start('high_activity')" id="btn-high-activity" style="background: linear-gradient(135deg, #ff6b6b, #ee5a24); color: white; font-weight: bold;">
                            🔥 HIGH ACTIVITY<br><small>$100K - GUARANTEED TRADES!</small>
                        </button>
                        <button class="btn btn-config" onclick="start('profit_max')" id="btn-profit-max" style="background: linear-gradient(135deg, #2ed573, #1e90ff); color: white; font-weight: bold;">
                            💰 PROFIT MAX<br><small>$100K - OPTIMIZED GAINS!</small>
                        </button>
                        <button class="btn btn-config" onclick="start('ultra_profit')" id="btn-ultra-profit" style="background: linear-gradient(135deg, #ffd700, #ff6b6b); color: white; font-weight: bold; border: 2px solid #ffd700; animation: pulse 2s infinite;">
                            🚀 ULTRA PROFIT<br><small>$100K - MAXIMUM GAINS!</small>
                        </button>
                        <button class="btn btn-config" onclick="start('winner')" id="btn-winner" style="background: linear-gradient(135deg, #00d2d3, #54a0ff); color: white; font-weight: bold; border: 2px solid #00d2d3;">
                            🏆 WINNER<br><small>$100K - HIGH WIN RATE!</small>
                        </button>
                        <button class="btn btn-config" onclick="start('scalping')" id="btn-scalping" style="background: linear-gradient(135deg, #1dd1a1, #10ac84); color: white; font-weight: bold; border: 3px solid #1dd1a1; animation: pulse 2s infinite;">
                            ⚡ SCALPING MASTER<br><small>$100K - QUICK PROFITS!</small>
                        </button>
                        <button class="btn btn-config" onclick="startProven()" id="btn-proven" style="background: linear-gradient(135deg, #ff9ff3, #f368e0); color: white; font-weight: bold; border: 4px solid #ff9ff3; animation: glow 3s ease-in-out infinite; box-shadow: 0 0 20px rgba(255, 159, 243, 0.6);">
                            🎯 PROVEN WINNER<br><small>69.1% WIN RATE - BACKTESTED!</small>
                        </button>
                        <button class="btn btn-config" onclick="startSuperior()" id="btn-superior" style="background: linear-gradient(135deg, #ffd700, #ff4757); color: white; font-weight: bold; border: 5px solid #ffd700; animation: glow 2s ease-in-out infinite; box-shadow: 0 0 30px rgba(255, 215, 0, 0.8); transform: scale(1.05);">
                            🚀 SUPERIOR STRATEGY<br><small>120.34% RETURN - ULTIMATE!</small>
                        </button>
                        <button class="btn btn-stop" onclick="stop()" id="btn-stop" style="grid-column: span 2;">
                            🛑 STOP Trading
                        </button>
                    </div>
                </div>
                
                <div class="footer">
                    <p>🛡️ 100% Paper Trading - NO REAL MONEY at risk</p>
                    <p>Updates every 5 seconds • {datetime.now().strftime('%H:%M:%S')}</p>
                </div>
            </div>
            
            <script>
                let isUpdating = false;
                
                function updateStatus() {{
                    if (isUpdating) return;
                    isUpdating = true;
                    
                    fetch('/status')
                        .then(r => r.json())
                        .then(data => {{
                            const dot = document.getElementById('status-dot');
                            const text = document.getElementById('status-text');
                            const buttons = document.querySelectorAll('.btn');
                            
                            if (data.is_running) {{
                                dot.className = 'status-indicator running';
                                text.textContent = 'System Running (PID: ' + (data.pid || '?') + ')';
                                // Disable start buttons, enable stop
                                buttons.forEach(btn => {{
                                    if (btn.id === 'btn-stop') {{
                                        btn.disabled = false;
                                    }} else {{
                                        btn.disabled = true;
                                    }}
                                }});
                            }} else {{
                                dot.className = 'status-indicator stopped';
                                text.textContent = 'System Stopped';
                                // Enable start buttons, disable stop
                                buttons.forEach(btn => {{
                                    if (btn.id === 'btn-stop') {{
                                        btn.disabled = true;
                                    }} else {{
                                        btn.disabled = false;
                                    }}
                                }});
                            }}
                            
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
                            document.getElementById('win-rate').textContent = 
                                (data.win_rate || 0).toFixed(1) + '%';
                            document.getElementById('pnl').textContent = 
                                '$' + (data.pnl || 0).toFixed(2);
                            document.getElementById('decisions').textContent = 
                                data.decisions_per_min || 0;
                            
                            document.getElementById('last-update').textContent = 
                                new Date().toLocaleTimeString();
                        }})
                        .catch(e => {{
                            console.log('Update failed:', e);
                            document.getElementById('status-text').textContent = 'Connection Error';
                        }})
                        .finally(() => {{
                            isUpdating = false;
                        }});
                }}
                
                function showAlert(message, success = true) {{
                    const alert = document.getElementById('alert');
                    alert.textContent = message;
                    alert.style.display = 'block';
                    alert.style.background = success ? 'rgba(76, 175, 80, 0.3)' : 'rgba(244, 67, 54, 0.3)';
                    setTimeout(() => {{
                        alert.style.display = 'none';
                    }}, 3000);
                }}
                
                function start(config) {{
                    showAlert('Starting ' + config + ' configuration...', true);
                    fetch('/start', {{
                        method: 'POST',
                        headers: {{'Content-Type': 'application/json'}},
                        body: JSON.stringify({{config: config}})
                    }})
                    .then(r => r.json())
                    .then(data => {{
                        showAlert(data.message, data.success);
                        if (data.success) {{
                            setTimeout(updateStatus, 2000); // Update status after 2 seconds
                        }}
                    }})
                    .catch(e => showAlert('Start failed: ' + e, false));
                }}
                
                function startProven() {{
                    showAlert('Starting PROVEN Mean Reversion Strategy (69.1% Win Rate)...', true);
                    fetch('/start-proven', {{method: 'POST'}})
                        .then(r => r.json())
                        .then(data => {{
                            showAlert(data.message, data.success);
                            if (data.success) {{
                                setTimeout(updateStatus, 2000);
                            }}
                        }})
                        .catch(e => showAlert('Start PROVEN strategy failed: ' + e, false));
                }}
                
                function startSuperior() {{
                    showAlert('Starting SUPERIOR Trend Sensitive Strategy (120.34% Return)...', true);
                    fetch('/start-superior', {{method: 'POST'}})
                        .then(r => r.json())
                        .then(data => {{
                            showAlert(data.message, data.success);
                            if (data.success) {{
                                setTimeout(updateStatus, 2000);
                            }}
                        }})
                        .catch(e => showAlert('Start SUPERIOR strategy failed: ' + e, false));
                }}
                
                function stop() {{
                    showAlert('Stopping trading system...', true);
                    fetch('/stop', {{method: 'POST'}})
                        .then(r => r.json())
                        .then(data => {{
                            showAlert(data.message, data.success);
                            setTimeout(updateStatus, 2000);
                        }})
                        .catch(e => showAlert('Stop failed: ' + e, false));
                }}
                
                // Auto-refresh every 5 seconds
                updateStatus();
                setInterval(updateStatus, 5000);
                
                // Initial button states
                setTimeout(updateStatus, 1000);
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
    server = HTTPServer(('0.0.0.0', 8001), ControlRequestHandler)
    print("🚀 Paper Trading Control Center Started!")
    print(f"📱 Mobile Access: http://your-phone-ip:8001")
    print(f"💻 Desktop Access: http://localhost:8001")
    print(f"🌐 Network Access: http://your-network-ip:8001")
    print("🛑 Press Ctrl+C to stop")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n✅ Control center stopped")
        server.shutdown()

if __name__ == "__main__":
    start_server()