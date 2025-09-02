#!/usr/bin/env python3
"""
Real Market Data Integration for Paper Trading
Uses actual Binance data without external WebSocket dependencies

This provides real market data for paper trading while maintaining
complete safety (no real money at risk).
"""

import asyncio
import json
import urllib.request
import urllib.error
import time
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class RealMarketDataProvider:
    """Real market data provider using Binance REST API"""
    
    def __init__(self, symbol: str = "BTCUSDT"):
        self.symbol = symbol
        self.base_url = "https://api.binance.com/api/v3"
        self.last_price = 0.0
        self.price_cache = {}
        self.cache_timeout = 2  # Cache data for 2 seconds
        
    async def get_current_price(self) -> Optional[Dict[str, Any]]:
        """Get current market price from Binance"""
        try:
            # Check cache first
            current_time = time.time()
            cache_key = f"{self.symbol}_price"
            
            if (cache_key in self.price_cache and 
                current_time - self.price_cache[cache_key]['timestamp'] < self.cache_timeout):
                return self.price_cache[cache_key]['data']
            
            # Fetch fresh data
            url = f"{self.base_url}/ticker/price?symbol={self.symbol}"
            
            # Use asyncio to make non-blocking request
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, self._fetch_url, url)
            
            if response:
                data = json.loads(response)
                price = float(data['price'])
                
                market_data = {
                    'symbol': self.symbol,
                    'price': price,
                    'timestamp': current_time,
                    'source': 'binance_rest'
                }
                
                # Cache the result
                self.price_cache[cache_key] = {
                    'data': market_data,
                    'timestamp': current_time
                }
                
                self.last_price = price
                return market_data
                
        except Exception as e:
            logger.warning(f"Failed to fetch real market data: {e}")
            # Return simulated data as fallback
            return await self._get_simulated_data()
        
        return None
    
    async def get_ticker_24hr(self) -> Optional[Dict[str, Any]]:
        """Get 24hr ticker statistics"""
        try:
            url = f"{self.base_url}/ticker/24hr?symbol={self.symbol}"
            
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, self._fetch_url, url)
            
            if response:
                data = json.loads(response)
                return {
                    'symbol': data['symbol'],
                    'price': float(data['lastPrice']),
                    'bid': float(data['bidPrice']),
                    'ask': float(data['askPrice']),
                    'volume': float(data['volume']),
                    'high': float(data['highPrice']),
                    'low': float(data['lowPrice']),
                    'change': float(data['priceChange']),
                    'change_percent': float(data['priceChangePercent']),
                    'timestamp': time.time(),
                    'source': 'binance_rest'
                }
        except Exception as e:
            logger.warning(f"Failed to fetch 24hr ticker: {e}")
        
        return None
    
    def _fetch_url(self, url: str) -> Optional[str]:
        """Synchronous URL fetch for executor"""
        try:
            with urllib.request.urlopen(url, timeout=5) as response:
                return response.read().decode('utf-8')
        except (urllib.error.URLError, urllib.error.HTTPError) as e:
            logger.error(f"HTTP request failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Request error: {e}")
            return None
    
    async def _get_simulated_data(self) -> Dict[str, Any]:
        """Fallback simulated data when real data unavailable"""
        # Use last known price or default
        base_price = self.last_price if self.last_price > 0 else 45000.0
        
        # Add small random variation
        import random
        price_variation = random.uniform(-0.001, 0.001)  # ±0.1%
        current_price = base_price * (1 + price_variation)
        
        return {
            'symbol': self.symbol,
            'price': current_price,
            'timestamp': time.time(),
            'source': 'simulated'
        }

class SafePaperTradingDataProvider:
    """Safe data provider combining real and simulated data"""
    
    def __init__(self, symbol: str = "BTCUSDT", use_real_data: bool = True):
        self.symbol = symbol
        self.use_real_data = use_real_data
        self.real_provider = RealMarketDataProvider(symbol) if use_real_data else None
        self.simulation_price = 45000.0
        self.last_real_data_time = 0
        
        logger.info(f"📡 Market Data Provider: {'Real + Simulated' if use_real_data else 'Simulation Only'}")
    
    async def get_market_data(self) -> Dict[str, Any]:
        """Get market data (real or simulated)"""
        try:
            if self.use_real_data and self.real_provider:
                # Try to get real data first
                real_data = await self.real_provider.get_current_price()
                if real_data:
                    self.last_real_data_time = time.time()
                    self.simulation_price = real_data['price']  # Update simulation baseline
                    
                    # Enhance real data with additional fields
                    ticker_data = await self.real_provider.get_ticker_24hr()
                    if ticker_data:
                        real_data.update({
                            'bid': ticker_data['bid'],
                            'ask': ticker_data['ask'],
                            'volume': ticker_data['volume'],
                            'change_24h': ticker_data['change_percent']
                        })
                    else:
                        # Add simulated bid/ask/volume
                        real_data.update({
                            'bid': real_data['price'] - 0.5,
                            'ask': real_data['price'] + 0.5,
                            'volume': 1000,
                            'change_24h': 0.0
                        })
                    
                    logger.debug(f"📊 Real market data: ${real_data['price']:,.2f}")
                    return real_data
            
            # Fallback to simulation
            return await self._get_enhanced_simulation()
            
        except Exception as e:
            logger.error(f"Market data error: {e}")
            return await self._get_enhanced_simulation()
    
    async def _get_enhanced_simulation(self) -> Dict[str, Any]:
        """Enhanced simulation with realistic patterns"""
        import random
        import math
        
        current_time = time.time()
        
        # Create realistic price movement
        time_factor = current_time * 0.01
        trend = 100 * math.sin(time_factor * 0.1)  # Long-term trend
        noise = 20 * random.gauss(0, 1)  # Random noise
        micro_moves = 5 * math.sin(time_factor)  # Short-term moves
        
        price = self.simulation_price + trend + noise + micro_moves
        price = max(price, 1000)  # Ensure reasonable minimum price
        
        # Generate realistic bid/ask spread
        spread = random.uniform(0.5, 2.0)
        bid = price - spread / 2
        ask = price + spread / 2
        
        # Generate volume
        volume = random.uniform(500, 1500)
        
        data_source = "simulation"
        if (self.last_real_data_time > 0 and 
            current_time - self.last_real_data_time < 300):  # Real data within 5 minutes
            data_source = "hybrid"
        
        market_data = {
            'symbol': self.symbol,
            'price': price,
            'bid': bid,
            'ask': ask,
            'volume': volume,
            'change_24h': random.uniform(-5.0, 5.0),
            'timestamp': current_time,
            'source': data_source
        }
        
        if random.randint(1, 100) == 1:  # Log occasionally
            logger.info(f"📊 Market data: ${price:,.2f} ({data_source})")
        
        return market_data
    
    def get_connection_status(self) -> Dict[str, Any]:
        """Get connection and data quality status"""
        current_time = time.time()
        real_data_age = current_time - self.last_real_data_time
        
        return {
            'real_data_enabled': self.use_real_data,
            'last_real_data': self.last_real_data_time,
            'real_data_age_seconds': real_data_age,
            'data_quality': 'excellent' if real_data_age < 60 else 'simulated',
            'provider_status': 'connected' if real_data_age < 300 else 'offline'
        }

# Test function to validate real market data
async def test_real_market_data():
    """Test real market data integration"""
    logger.info("🧪 Testing Real Market Data Integration")
    logger.info("=" * 50)
    
    provider = SafePaperTradingDataProvider(use_real_data=True)
    
    for i in range(5):
        data = await provider.get_market_data()
        status = provider.get_connection_status()
        
        logger.info(f"Test {i+1}: ${data['price']:,.2f} "
                   f"(Source: {data['source']}, "
                   f"Status: {status['data_quality']})")
        
        await asyncio.sleep(2)
    
    logger.info("✅ Market data test complete")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(test_real_market_data())