#!/usr/bin/env python3
"""
Simple Historical Data Downloader for BTCUSDT
Downloads 1 year of historical data from Binance using only standard library
"""

import json
import requests
import csv
from datetime import datetime, timezone, timedelta
import time
import os
import logging

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

class SimpleDataDownloader:
    """Download historical kline data from Binance using only standard library"""
    
    def __init__(self):
        self.base_url = "https://api.binance.com/api/v3/klines"
        
    def get_interval_ms(self, interval: str) -> int:
        """Convert interval string to milliseconds"""
        intervals = {
            '1m': 60 * 1000,
            '5m': 5 * 60 * 1000,
            '15m': 15 * 60 * 1000,
            '1h': 60 * 60 * 1000,
            '4h': 4 * 60 * 60 * 1000,
            '1d': 24 * 60 * 60 * 1000,
        }
        return intervals.get(interval, 60 * 1000)
    
    def download_timeframe(self, symbol: str, interval: str, 
                          start_date: str, end_date: str) -> str:
        """Download data for a single timeframe"""
        
        logger.info(f"📊 Downloading {symbol} {interval} from {start_date} to {end_date}")
        
        # Convert dates to timestamps
        start_ts = int(datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp() * 1000)
        end_ts = int(datetime.strptime(end_date, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp() * 1000)
        
        # Create output directory
        os.makedirs('historical_data', exist_ok=True)
        filename = f"historical_data/{symbol}_{interval}_{start_date}_to_{end_date}.csv"
        
        all_data = []
        current_ts = start_ts
        limit = 1000
        
        while current_ts < end_ts:
            try:
                params = {
                    'symbol': symbol,
                    'interval': interval,
                    'startTime': current_ts,
                    'endTime': min(current_ts + (limit * self.get_interval_ms(interval)), end_ts),
                    'limit': limit
                }
                
                response = requests.get(self.base_url, params=params, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                
                if not data:
                    break
                
                # Process data - keep only essential columns
                for candle in data:
                    processed_candle = {
                        'timestamp': datetime.fromtimestamp(candle[0] / 1000, tz=timezone.utc).isoformat(),
                        'open': float(candle[1]),
                        'high': float(candle[2]),
                        'low': float(candle[3]),
                        'close': float(candle[4]),
                        'volume': float(candle[5])
                    }
                    all_data.append(processed_candle)
                
                # Update current timestamp
                current_ts = data[-1][0] + self.get_interval_ms(interval)
                
                logger.info(f"📥 Downloaded {len(data)} candles. Total: {len(all_data)}")
                
                # Rate limiting
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"❌ Error downloading data: {e}")
                time.sleep(5)
                continue
        
        # Save to CSV
        if all_data:
            with open(filename, 'w', newline='') as csvfile:
                fieldnames = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(all_data)
            
            logger.info(f"💾 Saved {len(all_data)} candles to {filename}")
            return filename
        else:
            logger.error(f"❌ No data downloaded for {symbol} {interval}")
            return None
    
    def download_all_timeframes(self):
        """Download all timeframes for backtesting"""
        
        symbol = "BTCUSDT"
        timeframes = ['1m', '5m', '15m', '1h']  # Start with smaller timeframes
        start_date = "2024-01-01"
        end_date = "2025-01-01"
        
        downloaded_files = {}
        
        for timeframe in timeframes:
            try:
                logger.info(f"🔄 Starting download for {timeframe} timeframe")
                filename = self.download_timeframe(symbol, timeframe, start_date, end_date)
                
                if filename:
                    downloaded_files[timeframe] = filename
                    logger.info(f"✅ Completed {timeframe}")
                else:
                    logger.error(f"❌ Failed {timeframe}")
                    
            except Exception as e:
                logger.error(f"❌ Error with {timeframe}: {e}")
                continue
        
        # Save file list
        with open('historical_data/file_list.json', 'w') as f:
            json.dump(downloaded_files, f, indent=2)
        
        logger.info(f"🎉 Download complete! Files: {list(downloaded_files.keys())}")
        return downloaded_files

def main():
    """Main function to download historical data"""
    downloader = SimpleDataDownloader()
    
    logger.info("🚀 Starting historical data download")
    logger.info("📅 Period: 2024-01-01 to 2025-01-01")
    logger.info("⚠️  Note: This may take several minutes...")
    
    files = downloader.download_all_timeframes()
    
    if files:
        logger.info("✅ SUCCESS: Historical data downloaded")
        logger.info("📁 Files ready for backtesting:")
        for timeframe, filename in files.items():
            logger.info(f"   {timeframe}: {filename}")
    else:
        logger.error("❌ FAILED: No data downloaded")
    
    return files

if __name__ == "__main__":
    main()