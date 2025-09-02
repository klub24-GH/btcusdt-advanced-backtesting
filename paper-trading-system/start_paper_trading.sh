#!/bin/bash
# Paper Trading System Deployment Script
# Safe deployment for live paper trading with real market data

set -e

echo "📊 BTCUSDT Paper Trading System - Live Deployment"
echo "💰 Real market data, virtual portfolio - NO REAL MONEY AT RISK"
echo "================================================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PAPER_TRADING_DIR="/home/ajdev/btcusdt-advanced-backtesting/production"
LOG_DIR="/tmp/paper_trading"

echo -e "${BLUE}🔒 Paper Trading Safety Verification${NC}"
echo "================================================================================"

# Create log directory
mkdir -p "$LOG_DIR"

# Safety checks
echo -e "${YELLOW}🛡️ Running safety verification...${NC}"
cd "$PAPER_TRADING_DIR"

# Test paper trading configuration
python3 paper_trading_config.py
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Paper trading configuration: SAFE${NC}"
else
    echo -e "${RED}❌ Paper trading configuration failed safety checks${NC}"
    exit 1
fi

echo -e "${BLUE}📡 Market Data Integration Test${NC}"
echo "================================================================================"

echo -e "${YELLOW}🌐 Testing real market data connection...${NC}"
python3 real_market_data_integration.py
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Market data integration: OPERATIONAL${NC}"
else
    echo -e "${YELLOW}⚠️ Real market data unavailable - will use simulation${NC}"
fi

echo -e "${BLUE}💰 Virtual Portfolio Setup${NC}"
echo "================================================================================"

echo -e "${YELLOW}📋 Paper Trading Configuration:${NC}"
echo "   • Starting Balance: \$10,000 (VIRTUAL)"
echo "   • Trading Pair: BTCUSDT"
echo "   • Market Data: Live Binance feeds"
echo "   • Paper Trading Mode: ✅ ENABLED"
echo "   • Real Money Trading: ❌ DISABLED"
echo "   • Maximum Position Size: 20% of portfolio"
echo "   • Safety Checks: ✅ ACTIVE"

echo -e "${BLUE}🎯 System Capabilities${NC}"
echo "================================================================================"

echo -e "${YELLOW}📈 Paper Trading Features:${NC}"
echo "   • Real-time decision making (1 decision/second)"
echo "   • Live market data integration"
echo "   • Virtual portfolio tracking"
echo "   • Risk management simulation"
echo "   • Performance analytics"
echo "   • Trade history logging"
echo "   • P&L calculation"
echo "   • Win rate tracking"

echo -e "${BLUE}⚠️ IMPORTANT SAFETY NOTICES${NC}"
echo "================================================================================"
echo -e "${GREEN}✅ PAPER TRADING MODE: This system uses virtual money only${NC}"
echo -e "${GREEN}✅ NO FINANCIAL RISK: No real cryptocurrency or USD at risk${NC}"
echo -e "${GREEN}✅ REAL MARKET DATA: Uses actual Binance price feeds${NC}"
echo -e "${GREEN}✅ EDUCATIONAL PURPOSE: Perfect for learning and testing strategies${NC}"
echo -e "${GREEN}✅ SAFE ENVIRONMENT: All trades are simulated${NC}"

echo ""
echo -e "${BLUE}🚀 Ready to Start Paper Trading${NC}"
echo "================================================================================"
echo -e "${YELLOW}Choose your paper trading configuration:${NC}"
echo "  1) Default - Balanced approach (recommended for most users)"
echo "  2) Conservative - Lower risk, fewer trades"
echo "  3) Aggressive - Higher risk, more trades (still 100% safe)"
echo "  4) Learning - Educational mode with detailed logging"
echo ""

read -p "Enter your choice (1-4) or press Enter for default: " choice

case $choice in
    1|"")
        CONFIG_TYPE="default"
        echo -e "${GREEN}Selected: Default Configuration${NC}"
        ;;
    2)
        CONFIG_TYPE="conservative"
        echo -e "${GREEN}Selected: Conservative Configuration${NC}"
        ;;
    3)
        CONFIG_TYPE="aggressive"
        echo -e "${GREEN}Selected: Aggressive Configuration${NC}"
        ;;
    4)
        CONFIG_TYPE="learning"
        echo -e "${GREEN}Selected: Learning Configuration${NC}"
        ;;
    *)
        echo -e "${YELLOW}Invalid choice, using default${NC}"
        CONFIG_TYPE="default"
        ;;
esac

echo ""
echo -e "${BLUE}🎬 Starting Paper Trading System${NC}"
echo "================================================================================"
echo -e "${YELLOW}Configuration:${NC} $CONFIG_TYPE"
echo -e "${YELLOW}Market Data:${NC} Live Binance BTCUSDT"
echo -e "${YELLOW}Virtual Portfolio:${NC} \$10,000 starting balance"
echo -e "${YELLOW}Safety Mode:${NC} Paper trading (NO real money)"
echo ""
echo -e "${GREEN}Press Ctrl+C to stop paper trading at any time${NC}"
echo ""

# Wait a moment for user to read
sleep 3

echo -e "${GREEN}🚀 LAUNCHING PAPER TRADING SYSTEM...${NC}"
echo "================================================================================"

# Launch paper trading system
export PAPER_TRADING_CONFIG="$CONFIG_TYPE"
python3 paper_trading_system.py

echo ""
echo -e "${BLUE}🛑 Paper Trading Session Ended${NC}"
echo "================================================================================"
echo -e "${GREEN}✅ Session completed safely${NC}"
echo -e "${YELLOW}📊 Check logs at: $LOG_DIR/paper_trading.log${NC}"
echo -e "${YELLOW}💰 No real money was involved in this session${NC}"
echo ""
echo -e "${GREEN}Thank you for using the BTCUSDT Paper Trading System!${NC}"
echo "================================================================================"