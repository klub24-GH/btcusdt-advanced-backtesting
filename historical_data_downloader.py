#!/usr/bin/env python3
"""
Historical Data Downloader for BTCUSDT
Downloads 1 year of historical data from Binance for backtesting
"""

import asyncio
import json
import requests
import pandas as pd
from datetime import datetime, timezone, timedelta
import time
import os
import logging
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/data_downloader.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BinanceHistoricalDataDownloader:
    """Download historical kline data from Binance"""
    
    def __init__(self):
        self.base_url = "https://api.binance.com/api/v3/klines"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'BTC-Paper-Trading-Backtester/1.0'
        })
        
    def get_historical_data(self, symbol: str = "BTCUSDT", 
                          interval: str = "1m",
                          start_date: str = "2024-01-01",
                          end_date: str = "2025-01-01") -> pd.DataFrame:
        """
        Download historical kline data from Binance
        
        Args:
            symbol: Trading pair (default: BTCUSDT)
            interval: Timeframe (1m, 5m, 15m, 1h, 4h, 1d)
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            
        Returns:
            pandas.DataFrame with OHLCV data
        """
        logger.info(f"📊 Downloading {symbol} {interval} data from {start_date} to {end_date}")
        
        # Convert dates to timestamps
        start_ts = int(datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp() * 1000)
        end_ts = int(datetime.strptime(end_date, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp() * 1000)
        
        all_data = []
        current_ts = start_ts
        
        # Binance API limit: 1000 klines per request
        limit = 1000
        
        while current_ts < end_ts:
            try:
                params = {
                    'symbol': symbol,
                    'interval': interval,
                    'startTime': current_ts,
                    'endTime': min(current_ts + (limit * self._get_interval_ms(interval)), end_ts),
                    'limit': limit
                }
                
                response = self.session.get(self.base_url, params=params)
                response.raise_for_status()
                
                data = response.json()
                
                if not data:
                    break
                    
                all_data.extend(data)
                
                # Update current timestamp for next batch
                current_ts = data[-1][0] + self._get_interval_ms(interval)
                
                logger.info(f"📥 Downloaded {len(data)} candles. Total: {len(all_data)}")
                
                # Rate limiting: Binance allows 1200 requests per minute
                time.sleep(0.1)  # 100ms delay between requests
                
            except Exception as e:
                logger.error(f"❌ Error downloading data: {e}")
                time.sleep(5)  # Wait 5 seconds on error
                continue
        
        # Convert to DataFrame
        df = pd.DataFrame(all_data, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_volume', 'count', 'taker_buy_base_volume',
            'taker_buy_quote_volume', 'ignore'
        ])
        
        # Convert data types
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df['open'] = df['open'].astype(float)
        df['high'] = df['high'].astype(float)
        df['low'] = df['low'].astype(float)
        df['close'] = df['close'].astype(float)
        df['volume'] = df['volume'].astype(float)
        
        # Keep only essential columns
        df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']].copy()
        
        logger.info(f"✅ Downloaded {len(df)} candles for {symbol} {interval}")
        logger.info(f"   Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
        
        return df
    
    def _get_interval_ms(self, interval: str) -> int:
        """Convert interval string to milliseconds"""
        intervals = {
            '1m': 60 * 1000,
            '3m': 3 * 60 * 1000,
            '5m': 5 * 60 * 1000,
            '15m': 15 * 60 * 1000,
            '30m': 30 * 60 * 1000,
            '1h': 60 * 60 * 1000,
            '2h': 2 * 60 * 60 * 1000,
            '4h': 4 * 60 * 60 * 1000,
            '6h': 6 * 60 * 60 * 1000,
            '8h': 8 * 60 * 60 * 1000,
            '12h': 12 * 60 * 60 * 1000,
            '1d': 24 * 60 * 60 * 1000,
            '3d': 3 * 24 * 60 * 60 * 1000,
            '1w': 7 * 24 * 60 * 60 * 1000,
        }
        return intervals.get(interval, 60 * 1000)  # Default to 1 minute
    
    def save_data(self, df: pd.DataFrame, filename: str):
        """Save DataFrame to CSV file"""
        os.makedirs('historical_data', exist_ok=True)
        filepath = f"historical_data/{filename}"
        df.to_csv(filepath, index=False)
        logger.info(f"💾 Saved data to {filepath}")
        return filepath
    
    def download_multiple_timeframes(self, symbol: str = "BTCUSDT",
                                   timeframes: List[str] = None,
                                   start_date: str = "2024-01-01",
                                   end_date: str = "2025-01-01") -> Dict[str, str]:
        """Download data for multiple timeframes"""
        
        if timeframes is None:
            timeframes = ['1m', '5m', '15m', '1h', '4h', '1d']
        
        downloaded_files = {}
        
        for timeframe in timeframes:
            try:
                logger.info(f"🔄 Starting download for {timeframe} timeframe")
                
                df = self.get_historical_data(
                    symbol=symbol,
                    interval=timeframe,
                    start_date=start_date,
                    end_date=end_date
                )
                
                filename = f"{symbol}_{timeframe}_{start_date}_to_{end_date}.csv"
                filepath = self.save_data(df, filename)
                downloaded_files[timeframe] = filepath
                
                logger.info(f"✅ Completed {timeframe}: {len(df)} candles")
                
            except Exception as e:
                logger.error(f"❌ Failed to download {timeframe} data: {e}")
                continue
        
        return downloaded_files

def main():
    """Download historical data for backtesting"""
    downloader = BinanceHistoricalDataDownloader()
    
    # Download 1 year of data (2024-2025) for multiple timeframes
    logger.info("🚀 Starting historical data download for BTCUSDT")
    logger.info("📅 Period: January 1, 2024 to January 1, 2025")
    logger.info("⏱️  Timeframes: 1m, 5m, 15m, 1h, 4h, 1d")
    
    files = downloader.download_multiple_timeframes(
        symbol="BTCUSDT",
        timeframes=['1m', '5m', '15m', '1h', '4h', '1d'],
        start_date="2024-01-01",
        end_date="2025-01-01"
    )
    
    logger.info("🎉 Download complete!")
    logger.info("📁 Downloaded files:")
    for timeframe, filepath in files.items():
        logger.info(f"   {timeframe}: {filepath}")
    
    # Save file list for backtesting
    with open('historical_data/file_list.json', 'w') as f:
        json.dump(files, f, indent=2)
    
    logger.info("💾 File list saved to historical_data/file_list.json")
    return files

if __name__ == "__main__":
    main()