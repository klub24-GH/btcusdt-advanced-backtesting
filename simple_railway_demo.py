#!/usr/bin/env python3
"""
Simple Railway Demo - Guaranteed to Work
Ultra-minimal demo for Railway deployment
"""

import json
import os
import time
import random
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

class SimpleHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass
        
    def do_GET(self):
        if self.path == '/':
            self.send_demo_page()
        elif self.path == '/status':
            self.send_status()
        else:
            self.send_error(404)
            
    def do_POST(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(b'{"success": true, "message": "Demo Action Completed"}')
        
    def send_status(self):
        # Generate demo data
        btc_price = 65000 + random.uniform(-1000, 1000)
        portfolio = 100000 + random.uniform(0, 20000)
        
        status = {
            "portfolio_value": round(portfolio, 2),
            "btc_price": round(btc_price, 2),
            "usd_balance": round(portfolio * 0.3, 2),
            "btc_balance": round((portfolio * 0.7) / btc_price, 6),
            "daily_pnl": round(portfolio * 0.02 * random.uniform(-1, 2), 2),
            "win_rate": 69.1,
            "total_trades": random.randint(5, 25),
            "status": "DEMO ACTIVE - 120.34% Strategy",
            "last_update": datetime.now().strftime("%H:%M:%S")
        }
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(status).encode())
        
    def send_demo_page(self):
        html = '''<!DOCTYPE html>
<html>
<head>
    <title>🎯 BTC Trading Demo</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: Arial; background: linear-gradient(135deg, #1e3c72, #2a5298); color: white; padding: 20px; }
        .container { max-width: 800px; margin: 0 auto; text-align: center; }
        .card { background: rgba(255,255,255,0.1); padding: 20px; margin: 15px; border-radius: 15px; }
        .value { font-size: 2em; font-weight: bold; margin: 10px 0; }
        .positive { color: #4CAF50; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; }
        .btn { padding: 15px 30px; background: #4CAF50; color: white; border: none; border-radius: 25px; font-size: 16px; cursor: pointer; margin: 10px; }
        .btn:hover { background: #45a049; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 BTC Trading System - Live Demo</h1>
        <p>✅ Railway Cloud Deployment Working</p>
        
        <div class="grid">
            <div class="card">
                <h3>💰 Portfolio</h3>
                <div class="value" id="portfolio">$100,000</div>
            </div>
            <div class="card">
                <h3>₿ BTC Price</h3>
                <div class="value" id="btcPrice">$65,000</div>
            </div>
            <div class="card">
                <h3>📈 Daily P&L</h3>
                <div class="value positive" id="pnl">+$1,234</div>
            </div>
            <div class="card">
                <h3>🎯 Win Rate</h3>
                <div class="value" id="winRate">69.1%</div>
            </div>
        </div>
        
        <div class="card">
            <h3>⚡ System Status</h3>
            <div class="value" id="status">DEMO ACTIVE - 120.34% Strategy</div>
        </div>
        
        <div>
            <button class="btn" onclick="showAlert()">🚀 Start Superior Strategy</button>
            <button class="btn" onclick="showAlert()">🎯 Start Proven Strategy</button>
        </div>
        
        <div style="margin-top: 30px; opacity: 0.8;">
            <p>🌐 <strong>Live Demo</strong> | Updates every 2 seconds | 💯 Paper Trading</p>
            <p><small>Simulates real trading performance - No actual money at risk</small></p>
        </div>
    </div>
    
    <script>
        function updateStatus() {
            fetch('/status')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('portfolio').textContent = '$' + data.portfolio_value.toLocaleString();
                    document.getElementById('btcPrice').textContent = '$' + data.btc_price.toLocaleString();
                    document.getElementById('pnl').textContent = '$' + data.daily_pnl.toLocaleString();
                    document.getElementById('winRate').textContent = data.win_rate + '%';
                    document.getElementById('status').textContent = data.status;
                })
                .catch(error => console.log('Update error:', error));
        }
        
        function showAlert() {
            alert('Demo Strategy Started! 🚀\\n\\nShowing simulated 120.34% performance');
        }
        
        updateStatus();
        setInterval(updateStatus, 2000);
    </script>
</body>
</html>'''
        
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode())

def main():
    port = int(os.environ.get('PORT', 8000))
    server = HTTPServer(('0.0.0.0', port), SimpleHandler)
    print(f"🌐 Simple Railway Demo running on port {port}")
    print(f"🎯 Demo URL will show live trading data")
    server.serve_forever()

if __name__ == '__main__':
    main()