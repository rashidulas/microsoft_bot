#!/usr/bin/env python3
"""
Main application entry point for FAR Bot with database integration and scheduling
"""

import os
import sys
import logging
import signal
from threading import Thread
import time

from config import Config
from database import db_manager
from scheduler import start_scheduler, stop_scheduler, get_scheduler_status
from app import app

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('far_bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class FARBotApplication:
    """Main application class that manages all components"""
    
    def __init__(self):
        self.running = False
        self.flask_thread = None
        
    def initialize_database(self):
        """Initialize database and load initial data if needed"""
        logger.info("Initializing database...")
        db_manager.init_database()
        
        # Check if we have any FAR data
        latest_data = db_manager.get_latest_far_data()
        if not latest_data:
            logger.info("No FAR data found in database. Running initial scrape...")
            self.run_initial_scrape()
        else:
            logger.info(f"Found existing FAR data: {latest_data['fac_number']} ({latest_data['effective_date']})")
    
    def run_initial_scrape(self):
        """Run initial scraping to populate database"""
        try:
            from scrape_far import FARScraper
            scraper = FARScraper()
            
            logger.info("Starting initial FAR scraping...")
            result_file = scraper.run_scrape()
            
            # Load and save to database
            with open(result_file.replace('.txt', '.json'), 'r', encoding='utf-8') as f:
                import json
                far_data = json.load(f)
            
            record_id = db_manager.save_far_data(far_data)
            logger.info(f"Initial scraping completed. Saved with ID: {record_id}")
            
        except Exception as e:
            logger.error(f"Initial scraping failed: {e}")
            # Don't exit - let the app run without data for now
    
    def start_flask_app(self):
        """Start Flask application in a separate thread"""
        def run_flask():
            try:
                port = int(os.getenv('PORT', 5000))
                debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
                
                logger.info(f"Starting Flask app on port {port}")
                app.run(host='0.0.0.0', port=port, debug=debug, use_reloader=False)
            except Exception as e:
                logger.error(f"Flask app error: {e}")
        
        self.flask_thread = Thread(target=run_flask, daemon=True)
        self.flask_thread.start()
    
    def start_scheduler(self):
        """Start the automated scheduler"""
        try:
            start_scheduler()
            logger.info("Scheduler started successfully")
            
            # Log scheduler status
            status = get_scheduler_status()
            logger.info(f"Scheduler status: {status}")
            
        except Exception as e:
            logger.error(f"Failed to start scheduler: {e}")
    
    def setup_signal_handlers(self):
        """Set up signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}. Shutting down gracefully...")
            self.shutdown()
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def start(self):
        """Start the application"""
        if self.running:
            logger.warning("Application is already running")
            return
        
        logger.info("Starting FAR Bot Application...")
        
        # Check configuration
        if not Config.validate_openai_config():
            logger.warning("OpenAI configuration not found. AI features will be disabled.")
        
        # Initialize database
        self.initialize_database()
        
        # Start scheduler
        self.start_scheduler()
        
        # Start Flask app
        self.start_flask_app()
        
        # Set up signal handlers
        self.setup_signal_handlers()
        
        self.running = True
        logger.info("FAR Bot Application started successfully!")
        logger.info("Access the chat interface at: http://localhost:5000")
        logger.info("Access the admin panel at: http://localhost:5000/admin")
        
        # Keep main thread alive
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
            self.shutdown()
    
    def shutdown(self):
        """Shutdown the application gracefully"""
        if not self.running:
            return
        
        logger.info("Shutting down FAR Bot Application...")
        self.running = False
        
        # Stop scheduler
        try:
            stop_scheduler()
            logger.info("Scheduler stopped")
        except Exception as e:
            logger.error(f"Error stopping scheduler: {e}")
        
        # Note: Flask app will stop when the process exits
        logger.info("FAR Bot Application shutdown complete")

def main():
    """Main entry point"""
    try:
        app_instance = FARBotApplication()
        app_instance.start()
    except Exception as e:
        logger.error(f"Application failed to start: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
