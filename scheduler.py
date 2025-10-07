#!/usr/bin/env python3
"""
Automated scheduler for daily FAR scraping
"""

import os
import time
import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
import atexit

from scrape_far import FARScraper
from database import db_manager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FARScheduler:
    """Manages automated FAR scraping schedule"""
    
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.scraper = FARScraper()
        self.setup_event_listeners()
    
    def setup_event_listeners(self):
        """Set up scheduler event listeners"""
        self.scheduler.add_listener(self.job_executed, EVENT_JOB_EXECUTED)
        self.scheduler.add_listener(self.job_error, EVENT_JOB_ERROR)
    
    def job_executed(self, event):
        """Handle successful job execution"""
        logger.info(f"Job {event.job_id} executed successfully")
    
    def job_error(self, event):
        """Handle job execution errors"""
        logger.error(f"Job {event.job_id} failed: {event.exception}")
        
        # Log error to database
        db_manager.log_scraping_result(
            status='error',
            error_message=str(event.exception)
        )
    
    def scrape_job(self):
        """Main scraping job"""
        logger.info("Starting scheduled FAR scraping...")
        start_time = time.time()
        
        try:
            # Run scraping
            result_file = self.scraper.run_scrape()
            
            # Load and save to database
            with open(result_file.replace('.txt', '.json'), 'r', encoding='utf-8') as f:
                import json
                far_data = json.load(f)
            
            record_id = db_manager.save_far_data(far_data)
            execution_time = time.time() - start_time
            
            # Log success
            db_manager.log_scraping_result(
                status='success',
                fac_number=far_data['version_info'].get('fac_number'),
                effective_date=far_data['version_info'].get('effective_date'),
                records_scraped=len(far_data.get('parts', {})),
                execution_time_seconds=execution_time
            )
            
            logger.info(f"Scheduled scraping completed successfully. Record ID: {record_id}")
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Scheduled scraping failed: {e}")
            
            # Log error
            db_manager.log_scraping_result(
                status='error',
                error_message=str(e),
                execution_time_seconds=execution_time
            )
    
    def cleanup_job(self):
        """Cleanup old data job"""
        logger.info("Starting scheduled cleanup...")
        
        try:
            cleanup_result = db_manager.cleanup_old_data(days_to_keep=30)
            logger.info(f"Scheduled cleanup completed: {cleanup_result}")
            
        except Exception as e:
            logger.error(f"Scheduled cleanup failed: {e}")
    
    def start_scheduler(self):
        """Start the scheduler with jobs"""
        if self.scheduler.running:
            logger.warning("Scheduler is already running")
            return
        
        # Add daily scraping job at 2 AM
        self.scheduler.add_job(
            func=self.scrape_job,
            trigger=CronTrigger(hour=2, minute=0),
            id='daily_far_scrape',
            name='Daily FAR Scraping',
            replace_existing=True
        )
        
        # Add weekly cleanup job on Sundays at 3 AM
        self.scheduler.add_job(
            func=self.cleanup_job,
            trigger=CronTrigger(day_of_week=6, hour=3, minute=0),  # Sunday
            id='weekly_cleanup',
            name='Weekly Data Cleanup',
            replace_existing=True
        )
        
        # Start scheduler
        self.scheduler.start()
        logger.info("Scheduler started successfully")
        
        # Register shutdown handler
        atexit.register(self.shutdown_scheduler)
    
    def stop_scheduler(self):
        """Stop the scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Scheduler stopped")
    
    def shutdown_scheduler(self):
        """Shutdown scheduler on exit"""
        self.stop_scheduler()
    
    def get_next_run_times(self):
        """Get next run times for all jobs"""
        jobs = self.scheduler.get_jobs()
        next_runs = {}
        
        for job in jobs:
            next_runs[job.id] = {
                'name': job.name,
                'next_run': job.next_run_time.isoformat() if job.next_run_time else None
            }
        
        return next_runs
    
    def trigger_job(self, job_id: str):
        """Manually trigger a job"""
        try:
            job = self.scheduler.get_job(job_id)
            if job:
                job.modify(next_run_time=datetime.now())
                logger.info(f"Triggered job: {job_id}")
                return True
            else:
                logger.error(f"Job not found: {job_id}")
                return False
        except Exception as e:
            logger.error(f"Failed to trigger job {job_id}: {e}")
            return False

# Global scheduler instance
scheduler = FARScheduler()

def start_scheduler():
    """Start the global scheduler"""
    scheduler.start_scheduler()

def stop_scheduler():
    """Stop the global scheduler"""
    scheduler.stop_scheduler()

def get_scheduler_status():
    """Get scheduler status"""
    return {
        'running': scheduler.scheduler.running,
        'next_runs': scheduler.get_next_run_times()
    }

if __name__ == '__main__':
    # Test the scheduler
    logger.info("Testing scheduler...")
    
    # Start scheduler
    start_scheduler()
    
    # Get status
    status = get_scheduler_status()
    logger.info(f"Scheduler status: {status}")
    
    # Keep running for a bit to test
    try:
        time.sleep(10)
    except KeyboardInterrupt:
        logger.info("Stopping scheduler...")
        stop_scheduler()
