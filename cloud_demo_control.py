#!/usr/bin/env python3
"""
Cloud Demo Control Center - Railway Compatible
Simulates trading system with realistic demo data
"""

import json
import os
import time
import random
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

class CloudDemoController:
    def __init__(self):
        self.demo_mode = True
        self.start_time = time.time()
        self.is_running = False
        self.strategy_type = "demo"
        
    def get_demo_status(self) -> dict:
        """Generate realistic demo trading status"""
        runtime = time.time() - self.start_time
        base_portfolio = 100000
        
        # Simulate profitable performance based on Superior Strategy
        if self.is_running and self.strategy_type == "superior":
            # Simulate 120.34% returns over time
            profit_factor = min(1.2034, 1 + (runtime / 86400) * 0.001)  # Gradual growth
            portfolio_value = base_portfolio * profit_factor
            daily_pnl = (portfolio_value - base_portfolio) * 0.02 * random.uniform(0.8, 1.2)
        elif self.is_running and self.strategy_type == "proven":
            # Simulate 69.1% win rate performance
            profit_factor = min(1.15, 1 + (runtime / 86400) * 0.0008)
            portfolio_value = base_portfolio * profit_factor
            daily_pnl = (portfolio_value - base_portfolio) * 0.015 * random.uniform(0.9, 1.1)
        else:
            portfolio_value = base_portfolio
            daily_pnl = 0
            
        btc_price = 65000 + random.uniform(-500, 500)  # Realistic BTC price
        
        return {
            "portfolio_value": round(portfolio_value, 2),
            "btc_price": round(btc_price, 2),
            "usd_balance": round(portfolio_value * 0.3, 2),
            "btc_balance": round((portfolio_value * 0.7) / btc_price, 6),
            "daily_pnl": round(daily_pnl, 2),
            "daily_pnl_pct": round((daily_pnl / base_portfolio) * 100, 2),
            "total_trades": random.randint(15, 45) if self.is_running else 0,
            "win_rate": 69.1 if self.strategy_type == "proven" else (41.9 if self.strategy_type == "superior" else 0),
            "is_running": self.is_running,
            "strategy": self.strategy_type.title() + " Strategy",
            "status": "DEMO MODE - Paper Trading Active" if self.is_running else "DEMO MODE - Stopped",
            "last_update": datetime.now().strftime("%H:%M:%S")
        }
        
    def start_proven_strategy(self) -> dict:
        """Start demo proven strategy"""
        self.is_running = True
        self.strategy_type = "proven"
        return {"success": True, "message": "Demo Proven Strategy Started - 69.1% Win Rate!"}
        
    def start_superior_strategy(self) -> dict:
        """Start demo superior strategy"""
        self.is_running = True
        self.strategy_type = "superior"
        return {"success": True, "message": "Demo Superior Strategy Started - 120.34% Return!"}
        
    def stop_trading(self) -> dict:
        """Stop demo trading"""
        self.is_running = False
        return {"success": True, "message": "Demo Trading Stopped"}

# Global controller instance
controller = CloudDemoController()

class ControlRequestHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # Suppress default logging
        
    def do_GET(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        if path == '/':
            self.serve_main_page()
        elif path == '/status':
            self.serve_status()
        else:
            self.send_error(404)
            
    def do_POST(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        if path == '/start_proven':
            result = controller.start_proven_strategy()
            self.send_json_response(result)
        elif path == '/start_superior':
            result = controller.start_superior_strategy()
            self.send_json_response(result)
        elif path == '/stop':
            result = controller.stop_trading()
            self.send_json_response(result)
        else:
            self.send_error(404)
            
    def send_json_response(self, data):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
        
    def serve_status(self):
        status = controller.get_demo_status()
        self.send_json_response(status)
        
    def serve_main_page(self):
        html = """<!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>🎯 BTC Trading System - Cloud Demo</title>
            <style>
                * { margin: 0; padding: 0; box-sizing: border-box; }
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
                    color: white; min-height: 100vh; padding: 20px;
                }
                .container { max-width: 800px; margin: 0 auto; }
                .header { text-align: center; margin-bottom: 30px; }
                .status-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }
                .status-card { background: rgba(255,255,255,0.1); padding: 20px; border-radius: 15px; backdrop-filter: blur(10px); }
                .value { font-size: 2em; font-weight: bold; margin-top: 10px; }
                .positive { color: #4CAF50; }
                .negative { color: #f44336; }
                .controls { display: flex; gap: 15px; justify-content: center; flex-wrap: wrap; margin: 30px 0; }
                .btn { padding: 15px 30px; border: none; border-radius: 25px; font-size: 16px; font-weight: bold; cursor: pointer; transition: all 0.3s; }
                .btn-start { background: linear-gradient(45deg, #4CAF50, #45a049); color: white; }
                .btn-stop { background: linear-gradient(45deg, #f44336, #da190b); color: white; }
                .btn:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(0,0,0,0.3); }
                .alert { margin: 20px 0; padding: 15px; border-radius: 10px; text-align: center; display: none; }
                .alert-success { background: rgba(76, 175, 80, 0.2); border: 1px solid #4CAF50; }
                .alert-error { background: rgba(244, 67, 54, 0.2); border: 1px solid #f44336; }
                .demo-badge { background: #FF9800; padding: 5px 15px; border-radius: 20px; font-size: 12px; font-weight: bold; display: inline-block; margin-bottom: 20px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="demo-badge">🌐 CLOUD DEMO MODE</div>
                    <h1>🎯 BTC/USDT Trading System</h1>
                    <p>Professional Paper Trading - Railway Cloud Demo</p>
                </div>
                
                <div class="status-grid">
                    <div class="status-card">
                        <h3>💰 Portfolio</h3>
                        <div class="value" id="portfolioValue">$100,000</div>
                    </div>
                    <div class="status-card">
                        <h3>₿ BTC Price</h3>
                        <div class="value" id="btcPrice">$65,000</div>
                    </div>
                    <div class="status-card">
                        <h3>💵 USD Balance</h3>
                        <div class="value" id="usdBalance">$30,000</div>
                    </div>
                    <div class="status-card">
                        <h3>₿ BTC Balance</h3>
                        <div class="value" id="btcBalance">1.077</div>
                    </div>
                    <div class="status-card">
                        <h3>📈 Daily P&L</h3>
                        <div class="value" id="dailyPnl">$0</div>
                    </div>
                    <div class="status-card">
                        <h3>🎯 Win Rate</h3>
                        <div class="value" id="winRate">0%</div>
                    </div>
                </div>
                
                <div class="status-card" style="text-align: center; margin-bottom: 20px;">
                    <h3>⚡ System Status</h3>
                    <div class="value" id="systemStatus">Demo Ready</div>
                    <p id="strategyInfo">Select a strategy to begin demo trading</p>
                </div>
                
                <div class="controls">
                    <button class="btn btn-start" onclick="startProvenStrategy()">
                        🎯 Start Proven Strategy<br><small>69.1% Win Rate</small>
                    </button>
                    <button class="btn btn-start" onclick="startSuperiorStrategy()">
                        🚀 Start Superior Strategy<br><small>120.34% Return</small>
                    </button>
                    <button class="btn btn-stop" onclick="stopTrading()">
                        ⏹️ Stop Demo
                    </button>
                </div>
                
                <div id="alertBox" class="alert"></div>
                
                <div style="text-align: center; margin-top: 30px; opacity: 0.8;">
                    <p>🌐 <strong>Cloud Demo</strong> | 📊 Real-time Updates | 💯 Paper Trading</p>
                    <p><small>Demo simulates actual performance metrics - No real money at risk</small></p>
                </div>
            </div>
            
            <script>
                function updateStatus() {
                    fetch('/status')
                        .then(response => response.json())
                        .then(data => {
                            document.getElementById('portfolioValue').textContent = '$' + data.portfolio_value.toLocaleString();
                            document.getElementById('btcPrice').textContent = '$' + data.btc_price.toLocaleString();
                            document.getElementById('usdBalance').textContent = '$' + data.usd_balance.toLocaleString();
                            document.getElementById('btcBalance').textContent = data.btc_balance;
                            
                            const dailyPnlElement = document.getElementById('dailyPnl');
                            dailyPnlElement.textContent = '$' + data.daily_pnl.toLocaleString() + ' (' + data.daily_pnl_pct + '%)';
                            dailyPnlElement.className = 'value ' + (data.daily_pnl >= 0 ? 'positive' : 'negative');
                            
                            document.getElementById('winRate').textContent = data.win_rate + '%';
                            document.getElementById('systemStatus').textContent = data.status;
                            document.getElementById('strategyInfo').textContent = data.strategy + ' | Last Update: ' + data.last_update;
                        })
                        .catch(error => console.log('Status update error:', error));
                }
                
                function startProvenStrategy() {
                    fetch('/start_proven', {method: 'POST'})
                        .then(response => response.json())
                        .then(data => showAlert(data.message, data.success));
                }
                
                function startSuperiorStrategy() {
                    fetch('/start_superior', {method: 'POST'})
                        .then(response => response.json())
                        .then(data => showAlert(data.message, data.success));
                }
                
                function stopTrading() {
                    fetch('/stop', {method: 'POST'})
                        .then(response => response.json())
                        .then(data => showAlert(data.message, data.success));
                }
                
                function showAlert(message, success) {
                    const alertBox = document.getElementById('alertBox');
                    alertBox.textContent = message;
                    alertBox.className = 'alert ' + (success ? 'alert-success' : 'alert-error');
                    alertBox.style.display = 'block';
                    setTimeout(() => alertBox.style.display = 'none', 3000);
                }
                
                // Update every 3 seconds
                updateStatus();
                setInterval(updateStatus, 3000);
            </script>
        </body>
        </html>"""
        
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode())

def start_server():
    port = int(os.environ.get('PORT', 8000))
    server = HTTPServer(('0.0.0.0', port), ControlRequestHandler)
    print(f"🌐 BTC Trading System Demo running on port {port}")
    print(f"📊 Cloud demo with Superior Strategy (120.34% return)")
    server.serve_forever()

if __name__ == '__main__':
    start_server()