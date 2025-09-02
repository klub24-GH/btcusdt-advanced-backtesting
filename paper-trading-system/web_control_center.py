#!/usr/bin/env python3
"""
Web-based Mobile & Desktop Control Center
Alternative to Notion - works on all devices via browser
"""

import asyncio
import json
import os
import signal
import subprocess
import time
from datetime import datetime
from typing import Dict, Any
import psutil
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn

app = FastAPI(title="Paper Trading Control Center")

class TradingController:
    def __init__(self):
        self.trading_process = None
        self.trading_pid = None
        self.connected_clients = set()
        
    def is_trading_running(self) -> bool:
        """Check if paper trading is running"""
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
        except Exception:
            return False
    
    async def get_status(self) -> Dict[str, Any]:
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
    
    async def start_trading(self, config: str = "default") -> Dict[str, Any]:
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
                cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            
            await asyncio.sleep(2)
            
            if self.is_trading_running():
                return {"success": True, "message": f"Started with {config} config"}
            else:
                return {"success": False, "message": "Failed to start"}
                
        except Exception as e:
            return {"success": False, "message": f"Error: {str(e)}"}
    
    async def stop_trading(self) -> Dict[str, Any]:
        """Stop paper trading system"""
        try:
            if not self.is_trading_running():
                return {"success": True, "message": "Not running"}
            
            if self.trading_pid:
                os.kill(self.trading_pid, signal.SIGTERM)
                
                # Wait for graceful shutdown
                for _ in range(10):
                    await asyncio.sleep(1)
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

@app.get("/", response_class=HTMLResponse)
async def get_dashboard():
    """Mobile-responsive dashboard"""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>🎯 Paper Trading Control Center</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white; min-height: 100vh; padding: 20px;
            }
            .container { max-width: 800px; margin: 0 auto; }
            .header { text-align: center; margin-bottom: 30px; }
            .status-card, .controls-card { 
                background: rgba(255,255,255,0.1); backdrop-filter: blur(10px);
                border-radius: 15px; padding: 20px; margin-bottom: 20px;
                border: 1px solid rgba(255,255,255,0.2);
            }
            .status-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; }
            .stat { text-align: center; padding: 15px; background: rgba(255,255,255,0.1); border-radius: 10px; }
            .stat-value { font-size: 1.5em; font-weight: bold; margin-bottom: 5px; }
            .stat-label { font-size: 0.9em; opacity: 0.8; }
            .controls { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; }
            .btn { 
                padding: 15px 25px; border: none; border-radius: 10px; font-size: 16px;
                cursor: pointer; transition: all 0.3s; font-weight: bold;
            }
            .btn-start { background: #4CAF50; color: white; }
            .btn-stop { background: #f44336; color: white; }
            .btn-config { background: #2196F3; color: white; }
            .btn:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(0,0,0,0.3); }
            .btn:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }
            .status-indicator { width: 12px; height: 12px; border-radius: 50%; display: inline-block; margin-right: 8px; }
            .status-running { background: #4CAF50; }
            .status-stopped { background: #f44336; }
            @media (max-width: 600px) {
                .controls { grid-template-columns: 1fr; }
                .status-grid { grid-template-columns: repeat(2, 1fr); }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🎯 Paper Trading Control Center</h1>
                <p>Mobile & Desktop Trading System Control</p>
            </div>
            
            <div class="status-card">
                <h2>📊 Live Status</h2>
                <div id="status-indicator">
                    <span class="status-indicator status-stopped"></span>
                    <span id="status-text">Loading...</span>
                </div>
                <div class="status-grid" id="status-grid">
                    <div class="stat">
                        <div class="stat-value" id="portfolio-value">$0</div>
                        <div class="stat-label">Portfolio Value</div>
                    </div>
                    <div class="stat">
                        <div class="stat-value" id="btc-price">$0</div>
                        <div class="stat-label">BTC Price</div>
                    </div>
                    <div class="stat">
                        <div class="stat-value" id="usd-balance">$0</div>
                        <div class="stat-label">USD Balance</div>
                    </div>
                    <div class="stat">
                        <div class="stat-value" id="btc-balance">0</div>
                        <div class="stat-label">BTC Balance</div>
                    </div>
                    <div class="stat">
                        <div class="stat-value" id="total-trades">0</div>
                        <div class="stat-label">Total Trades</div>
                    </div>
                </div>
            </div>
            
            <div class="controls-card">
                <h2>🎮 Controls</h2>
                <div class="controls">
                    <button class="btn btn-start" onclick="startTrading('default')">
                        🚀 START Default ($100K)
                    </button>
                    <button class="btn btn-config" onclick="startTrading('conservative')">
                        🛡️ Conservative ($200K)
                    </button>
                    <button class="btn btn-config" onclick="startTrading('aggressive')">
                        ⚡ Aggressive ($500K)
                    </button>
                    <button class="btn btn-config" onclick="startTrading('learning')">
                        📚 Learning ($50K)
                    </button>
                    <button class="btn btn-stop" onclick="stopTrading()">
                        🛑 STOP Trading
                    </button>
                </div>
            </div>
            
            <div class="status-card">
                <h2>📱 Mobile App Features</h2>
                <p>✅ Real-time monitoring • ✅ One-tap controls • ✅ Live price updates</p>
                <p>🛡️ 100% Paper Trading - NO REAL MONEY at risk</p>
            </div>
        </div>
        
        <script>
            const ws = new WebSocket(`ws://${location.host}/ws`);
            
            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                updateStatus(data);
            };
            
            function updateStatus(data) {
                const indicator = document.querySelector('.status-indicator');
                const statusText = document.getElementById('status-text');
                
                if (data.is_running) {
                    indicator.className = 'status-indicator status-running';
                    statusText.textContent = 'System Running';
                } else {
                    indicator.className = 'status-indicator status-stopped';
                    statusText.textContent = 'System Stopped';
                }
                
                document.getElementById('portfolio-value').textContent = 
                    '$' + (data.portfolio_value || 0).toLocaleString();
                document.getElementById('btc-price').textContent = 
                    '$' + (data.btc_price || 0).toLocaleString();
                document.getElementById('usd-balance').textContent = 
                    '$' + (data.usd_balance || 0).toLocaleString();
                document.getElementById('btc-balance').textContent = 
                    (data.btc_balance || 0).toFixed(6);
                document.getElementById('total-trades').textContent = 
                    data.total_trades || 0;
            }
            
            async function startTrading(config) {
                const response = await fetch('/start', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({config: config})
                });
                const result = await response.json();
                alert(result.message);
            }
            
            async function stopTrading() {
                const response = await fetch('/stop', {method: 'POST'});
                const result = await response.json();
                alert(result.message);
            }
            
            // Initial load
            fetch('/status').then(r => r.json()).then(updateStatus);
        </script>
    </body>
    </html>
    """

@app.get("/status")
async def get_status():
    """Get current status"""
    return await controller.get_status()

@app.post("/start")
async def start_trading(request: dict):
    """Start trading with config"""
    config = request.get('config', 'default')
    return await controller.start_trading(config)

@app.post("/stop")
async def stop_trading():
    """Stop trading"""
    return await controller.stop_trading()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time updates"""
    await websocket.accept()
    controller.connected_clients.add(websocket)
    
    try:
        while True:
            status = await controller.get_status()
            await websocket.send_text(json.dumps(status))
            await asyncio.sleep(5)  # Update every 5 seconds
    except WebSocketDisconnect:
        controller.connected_clients.remove(websocket)

if __name__ == "__main__":
    print("🚀 Starting Paper Trading Control Center...")
    print("📱 Access from mobile: http://your-ip:8000")
    print("💻 Access from desktop: http://localhost:8000")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)