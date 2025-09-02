#!/usr/bin/env python3
"""
Notion Dashboard Setup for Paper Trading Control
Creates the necessary Notion pages and databases for trading control
"""

import asyncio
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class NotionDashboardSetup:
    """Sets up Notion dashboard for paper trading control"""
    
    def __init__(self, parent_page_id: str = "26138364579a81708596caa9cd639f29"):
        self.parent_page_id = parent_page_id
        
    async def create_trading_control_database(self):
        """Create trading control database in Notion"""
        try:
            # Import Notion tools
            from mcp__notion__notion_database import notion_database
            
            # Database configuration
            database_config = {
                "payload": {
                    "action": "create_database",
                    "params": {
                        "parent": {
                            "type": "page_id",
                            "page_id": self.parent_page_id
                        },
                        "title": [{
                            "type": "text",
                            "text": {"content": "🎯 Paper Trading Control Center"}
                        }],
                        "icon": {
                            "type": "emoji",
                            "emoji": "🎯"
                        },
                        "cover": None,
                        "properties": {
                            "Action": {
                                "type": "select",
                                "select": {
                                    "options": [
                                        {"name": "START", "color": "green"},
                                        {"name": "STOP", "color": "red"},
                                        {"name": "RESTART", "color": "blue"},
                                        {"name": "STATUS", "color": "yellow"}
                                    ]
                                }
                            },
                            "Configuration": {
                                "type": "select", 
                                "select": {
                                    "options": [
                                        {"name": "default", "color": "blue"},
                                        {"name": "conservative", "color": "green"},
                                        {"name": "aggressive", "color": "red"},
                                        {"name": "learning", "color": "yellow"}
                                    ]
                                }
                            },
                            "Status": {
                                "type": "select",
                                "select": {
                                    "options": [
                                        {"name": "🟢 Running", "color": "green"},
                                        {"name": "🔴 Stopped", "color": "red"},
                                        {"name": "🟡 Starting", "color": "yellow"},
                                        {"name": "🟠 Stopping", "color": "orange"}
                                    ]
                                }
                            },
                            "Portfolio Value": {
                                "type": "number",
                                "number": {"format": "dollar"}
                            },
                            "BTC Price": {
                                "type": "number", 
                                "number": {"format": "dollar"}
                            },
                            "Total Trades": {
                                "type": "number",
                                "number": {"format": "number"}
                            },
                            "Win Rate": {
                                "type": "number",
                                "number": {"format": "percent"}
                            },
                            "P&L": {
                                "type": "number",
                                "number": {"format": "dollar"}
                            },
                            "Last Updated": {
                                "type": "date",
                                "date": {}
                            },
                            "Commands": {
                                "type": "rich_text",
                                "rich_text": {}
                            }
                        }
                    }
                }
            }
            
            result = await notion_database(database_config)
            
            if result.get('success'):
                database_id = result.get('database', {}).get('id')
                logger.info(f"✅ Trading control database created: {database_id}")
                return database_id
            else:
                logger.error(f"Failed to create database: {result}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating trading control database: {e}")
            return None
    
    async def create_status_dashboard_page(self):
        """Create main status dashboard page"""
        try:
            from mcp__notion__notion_pages import notion_pages
            
            # Create dashboard page
            page_config = {
                "payload": {
                    "action": "create_page",
                    "params": {
                        "parent": {
                            "type": "page_id",
                            "page_id": self.parent_page_id
                        },
                        "properties": {
                            "title": {
                                "title": [{
                                    "type": "text",
                                    "text": {"content": "📊 Paper Trading Dashboard"}
                                }]
                            }
                        },
                        "icon": {
                            "type": "emoji",
                            "emoji": "📊"
                        },
                        "children": [
                            {
                                "type": "heading_1",
                                "heading_1": {
                                    "rich_text": [{
                                        "type": "text",
                                        "text": {"content": "🎯 BTC Paper Trading Dashboard"}
                                    }]
                                }
                            },
                            {
                                "type": "paragraph",
                                "paragraph": {
                                    "rich_text": [{
                                        "type": "text",
                                        "text": {"content": "Real-time paper trading monitoring and control center"}
                                    }]
                                }
                            },
                            {
                                "type": "heading_2", 
                                "heading_2": {
                                    "rich_text": [{
                                        "type": "text",
                                        "text": {"content": "📱 Mobile & Desktop Control"}
                                    }]
                                }
                            },
                            {
                                "type": "callout",
                                "callout": {
                                    "icon": {"type": "emoji", "emoji": "💡"},
                                    "rich_text": [{
                                        "type": "text",
                                        "text": {"content": "Control your paper trading system from anywhere using this Notion dashboard. Updates automatically every 30 seconds."}
                                    }]
                                }
                            },
                            {
                                "type": "heading_3",
                                "heading_3": {
                                    "rich_text": [{
                                        "type": "text", 
                                        "text": {"content": "🚀 Quick Actions"}
                                    }]
                                }
                            },
                            {
                                "type": "to_do",
                                "to_do": {
                                    "rich_text": [{
                                        "type": "text",
                                        "text": {"content": "START Default Trading ($100K balance)"}
                                    }],
                                    "checked": False
                                }
                            },
                            {
                                "type": "to_do", 
                                "to_do": {
                                    "rich_text": [{
                                        "type": "text",
                                        "text": {"content": "START Conservative Trading ($200K balance)"}
                                    }],
                                    "checked": False
                                }
                            },
                            {
                                "type": "to_do",
                                "to_do": {
                                    "rich_text": [{
                                        "type": "text",
                                        "text": {"content": "START Learning Mode ($50K balance)"}
                                    }],
                                    "checked": False
                                }
                            },
                            {
                                "type": "to_do",
                                "to_do": {
                                    "rich_text": [{
                                        "type": "text",
                                        "text": {"content": "STOP All Trading"}
                                    }],
                                    "checked": False
                                }
                            },
                            {
                                "type": "divider",
                                "divider": {}
                            },
                            {
                                "type": "heading_3",
                                "heading_3": {
                                    "rich_text": [{
                                        "type": "text",
                                        "text": {"content": "📊 Live Status"}
                                    }]
                                }
                            },
                            {
                                "type": "paragraph",
                                "paragraph": {
                                    "rich_text": [{
                                        "type": "text",
                                        "text": {"content": "Status updates will appear below automatically..."}
                                    }]
                                }
                            }
                        ]
                    }
                }
            }
            
            result = await notion_pages(page_config)
            
            if result.get('success'):
                page_id = result.get('page', {}).get('id')
                logger.info(f"✅ Dashboard page created: {page_id}")
                return page_id
            else:
                logger.error(f"Failed to create page: {result}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating dashboard page: {e}")
            return None
    
    async def setup_complete_dashboard(self):
        """Set up complete Notion dashboard"""
        logger.info("🚀 Setting up Notion Paper Trading Dashboard...")
        
        # Create control database
        database_id = await self.create_trading_control_database()
        
        # Create dashboard page  
        page_id = await self.create_status_dashboard_page()
        
        if database_id and page_id:
            logger.info("✅ Notion dashboard setup complete!")
            logger.info(f"📊 Dashboard Page: {page_id}")
            logger.info(f"🎯 Control Database: {database_id}")
            
            # Create setup summary
            setup_info = {
                'dashboard_page_id': page_id,
                'control_database_id': database_id,
                'parent_page_id': self.parent_page_id,
                'created_at': datetime.now().isoformat(),
                'status': 'success'
            }
            
            # Save setup info
            with open('/tmp/notion_dashboard_setup.json', 'w') as f:
                json.dump(setup_info, f, indent=2)
            
            return setup_info
            
        else:
            logger.error("❌ Dashboard setup failed")
            return None

async def main():
    """Main setup function"""
    print("🎯 Setting up Notion Paper Trading Control Center...")
    
    setup = NotionDashboardSetup()
    result = await setup.setup_complete_dashboard()
    
    if result:
        print("\n✅ SUCCESS! Your Notion trading control center is ready!")
        print(f"📱 Access from Notion app or web: https://notion.so/{result['dashboard_page_id']}")
        print(f"🎯 Control Database: {result['control_database_id']}")
        print("\n🚀 Next steps:")
        print("1. Open your Notion app/web")
        print("2. Navigate to the Paper Trading Dashboard")
        print("3. Use the checkboxes to control your trading system")
        print("4. Status updates every 30 seconds automatically")
    else:
        print("❌ Setup failed. Check logs for details.")

if __name__ == "__main__":
    asyncio.run(main())