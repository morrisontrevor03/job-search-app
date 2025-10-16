import asyncio
import schedule
import time
import threading
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_
import hashlib
import smtplib
try:
    from email.mime.text import MimeText
    from email.mime.multipart import MimeMultipart
except ImportError:
    # Fallback for Python 3.13+ or other import issues
    import email.mime.text as mime_text
    import email.mime.multipart as mime_multipart
    MimeText = mime_text.MIMEText
    MimeMultipart = mime_multipart.MIMEMultipart
import os
import logging

from db import SessionLocal
from models import SavedSearch, SearchResult
import scan

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SearchScheduler:
    def __init__(self):
        self.running = False
        self.thread = None

    def get_db(self):
        """Get database session"""
        db = SessionLocal()
        try:
            return db
        finally:
            pass  # Don't close here, close in the calling function

    def run_all_active_searches(self):
        """Run all active saved searches"""
        db = self.get_db()
        try:
            logger.info("Starting scheduled search run...")
            
            # Get all active saved searches
            active_searches = db.query(SavedSearch).filter(
                SavedSearch.is_active == True
            ).all()
            
            logger.info(f"Found {len(active_searches)} active saved searches")
            
            for saved_search in active_searches:
                try:
                    self.run_single_search(db, saved_search)
                except Exception as e:
                    logger.error(f"Error running search {saved_search.id}: {str(e)}")
                    continue
            
            logger.info("Completed scheduled search run")
            
        except Exception as e:
            logger.error(f"Error in run_all_active_searches: {str(e)}")
        finally:
            db.close()

    def run_single_search(self, db: Session, saved_search: SavedSearch):
        """Run a single saved search and store results"""
        try:
            # Check if API keys are configured
            if not scan.key or not scan.id:
                logger.warning(f"Search service not configured for search {saved_search.id}")
                return
            
            logger.info(f"Running search: {saved_search.name} (ID: {saved_search.id})")
            
            # Build and run the search
            query = scan.buildQuery(saved_search.job_title, saved_search.experience_level)
            results = scan.search(query, scan.key, scan.id, saved_search.count)
            
            if results:
                new_results_count = 0
                new_result_urls = []
                
                for result_url in results:
                    # Create hash for deduplication
                    result_hash = hashlib.sha256(result_url.encode()).hexdigest()
                    
                    # Check if this result already exists
                    existing = db.query(SearchResult).filter(
                        and_(
                            SearchResult.saved_search_id == saved_search.id,
                            SearchResult.result_hash == result_hash
                        )
                    ).first()
                    
                    if not existing:
                        new_result = SearchResult(
                            saved_search_id=saved_search.id,
                            result_url=result_url,
                            result_hash=result_hash,
                            is_new=True
                        )
                        db.add(new_result)
                        new_results_count += 1
                        new_result_urls.append(result_url)
                
                # Update last run time
                saved_search.last_run_at = datetime.utcnow()
                db.commit()
                
                logger.info(f"Search {saved_search.id} completed: {len(results)} total, {new_results_count} new")
                
                # Send notification if there are new results and email is configured
                if new_results_count > 0 and saved_search.notification_email:
                    self.send_notification(saved_search, new_results_count, new_result_urls)
                    
            else:
                # Update last run time even if no results
                saved_search.last_run_at = datetime.utcnow()
                db.commit()
                logger.info(f"Search {saved_search.id} completed: 0 results")
                
        except Exception as e:
            logger.error(f"Error running search {saved_search.id}: {str(e)}")
            # Still update last run time to avoid repeated failures
            saved_search.last_run_at = datetime.utcnow()
            db.commit()

    def send_notification(self, saved_search: SavedSearch, new_count: int, new_urls: list):
        """Send email notification for new results"""
        try:
            # Email configuration from environment variables
            smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
            smtp_port = int(os.getenv("SMTP_PORT", "587"))
            smtp_username = os.getenv("SMTP_USERNAME")
            smtp_password = os.getenv("SMTP_PASSWORD")
            from_email = os.getenv("FROM_EMAIL", smtp_username)
            
            if not smtp_username or not smtp_password:
                logger.warning("SMTP credentials not configured, skipping email notification")
                return
            
            # Create email content
            subject = f"New Job Results: {saved_search.name}"
            
            # Create HTML email body
            html_body = f"""
            <html>
            <body>
                <h2>New Job Search Results</h2>
                <p>Your saved search "<strong>{saved_search.name}</strong>" found {new_count} new job posting(s):</p>
                
                <h3>Search Details:</h3>
                <ul>
                    <li><strong>Job Title:</strong> {saved_search.job_title}</li>
                    <li><strong>Experience Level:</strong> {saved_search.experience_level}</li>
                    <li><strong>Results Count:</strong> {saved_search.count}</li>
                </ul>
                
                <h3>New Results:</h3>
                <ul>
            """
            
            # Add up to 10 new URLs to the email
            for url in new_urls[:10]:
                html_body += f'<li><a href="{url}" target="_blank">{url}</a></li>'
            
            if len(new_urls) > 10:
                html_body += f"<li><em>...and {len(new_urls) - 10} more results</em></li>"
            
            html_body += """
                </ul>
                
                <p>
                    <a href="https://your-app-url.netlify.app" target="_blank">View all results in your dashboard</a>
                </p>
                
                <hr>
                <p><small>This is an automated notification from your Job Search App. 
                To stop receiving these notifications, update your saved search settings.</small></p>
            </body>
            </html>
            """
            
            # Create email message
            msg = MimeMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = from_email
            msg['To'] = saved_search.notification_email
            
            # Add HTML part
            html_part = MimeText(html_body, 'html')
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_username, smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email notification sent to {saved_search.notification_email} for search {saved_search.id}")
            
        except Exception as e:
            logger.error(f"Failed to send email notification: {str(e)}")

    def start_scheduler(self):
        """Start the background scheduler"""
        if self.running:
            logger.warning("Scheduler is already running")
            return
        
        logger.info("Starting search scheduler...")
        
        # Schedule the job to run every 30 minutes
        schedule.every(30).minutes.do(self.run_all_active_searches)
        
        # Also run once immediately for testing (optional)
        # schedule.every().minute.do(self.run_all_active_searches)  # For testing
        
        self.running = True
        
        def run_scheduler():
            while self.running:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        
        self.thread = threading.Thread(target=run_scheduler, daemon=True)
        self.thread.start()
        
        logger.info("Search scheduler started successfully")

    def stop_scheduler(self):
        """Stop the background scheduler"""
        if not self.running:
            return
        
        logger.info("Stopping search scheduler...")
        self.running = False
        schedule.clear()
        
        if self.thread:
            self.thread.join(timeout=5)
        
        logger.info("Search scheduler stopped")

    def get_status(self):
        """Get scheduler status"""
        return {
            "running": self.running,
            "next_run": str(schedule.next_run()) if schedule.jobs else None,
            "jobs_count": len(schedule.jobs)
        }

# Global scheduler instance
scheduler = SearchScheduler()

# Functions to be used by the main app
def start_background_scheduler():
    """Start the background job scheduler"""
    scheduler.start_scheduler()

def stop_background_scheduler():
    """Stop the background job scheduler"""
    scheduler.stop_scheduler()

def get_scheduler_status():
    """Get current scheduler status"""
    return scheduler.get_status()

def run_searches_now():
    """Manually trigger all searches (for testing)"""
    scheduler.run_all_active_searches()
