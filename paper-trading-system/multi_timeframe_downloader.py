#!/usr/bin/env python3
"""
Multi-Timeframe Historical Data Downloader
Downloads multiple timeframes for comprehensive backtesting
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
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MultiTimeframeDownloader:
    """Download multiple timeframes efficiently"""
    
    def __init__(self):
        self.base_url = "https://api.binance.com/api/v3/klines"
        self.session = requests.Session()
        
    def download_timeframe_data(self, symbol="BTCUSDT", interval="1h", days=90):
        """Download data for a specific timeframe"""
        
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(days=days)
        
        start_ts = int(start_time.timestamp() * 1000)
        end_ts = int(end_time.timestamp() * 1000)
        
        logger.info(f"📊 Downloading {days} days of {symbol} {interval} data")
        
        all_data = []
        params = {
            'symbol': symbol,
            'interval': interval,
            'startTime': start_ts,
            'endTime': end_ts,
            'limit': 1000
        }
        
        try:
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # Process data
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
            
            # Save data
            os.makedirs('historical_data', exist_ok=True)
            filename = f"historical_data/{symbol}_{interval}_{days}days.csv"
            
            with open(filename, 'w', newline='') as csvfile:
                fieldnames = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(all_data)
            
            logger.info(f"✅ Downloaded {len(all_data)} candles to {filename}")
            return filename, len(all_data)
            
        except Exception as e:
            logger.error(f"❌ Error downloading {interval} data: {e}")
            return None, 0
    
    def download_all_timeframes(self):
        """Download all important timeframes for backtesting"""
        
        # Timeframe configurations (interval: days_of_data)
        timeframe_configs = {
            '5m': 30,    # 30 days of 5-minute data (8,640 candles)
            '15m': 60,   # 60 days of 15-minute data (5,760 candles)
            '1h': 180,   # 180 days of hourly data (4,320 candles)
            '4h': 365,   # 365 days of 4-hour data (2,190 candles)
            '1d': 730,   # 2 years of daily data (730 candles)
        }
        
        results = {}
        total_candles = 0
        
        for interval, days in timeframe_configs.items():
            try:
                filename, candle_count = self.download_timeframe_data(
                    symbol="BTCUSDT",
                    interval=interval,
                    days=days
                )
                
                if filename:
                    results[interval] = {
                        'file': filename,
                        'candles': candle_count,
                        'days': days
                    }
                    total_candles += candle_count
                    
                # Rate limiting
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"❌ Failed to download {interval}: {e}")
        
        # Save summary
        summary = {
            'download_time': datetime.now(timezone.utc).isoformat(),
            'total_candles': total_candles,
            'timeframes': results
        }
        
        with open('historical_data/download_summary.json', 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"🎉 Download complete! Total candles: {total_candles:,}")
        return results

def main():
    """Main function"""
    downloader = MultiTimeframeDownloader()
    
    logger.info("🚀 Starting multi-timeframe data download")
    logger.info("📅 Downloading: 5m, 15m, 1h, 4h, 1d timeframes")
    
    results = downloader.download_all_timeframes()
    
    if results:
        logger.info("\n📊 DOWNLOAD SUMMARY:")
        for interval, info in results.items():
            logger.info(f"   {interval:4s}: {info['candles']:,} candles ({info['days']} days)")
        
        logger.info("\n✅ All data ready for advanced backtesting!")
    else:
        logger.error("❌ Download failed")

if __name__ == "__main__":
    main()