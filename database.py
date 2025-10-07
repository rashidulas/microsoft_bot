#!/usr/bin/env python3
"""
Database models and connection management for FAR Bot
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from contextlib import contextmanager
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages database connections and operations"""
    
    def __init__(self, db_path: str = "far_bot.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database tables"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Create FAR data table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS far_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fac_number TEXT NOT NULL,
                    effective_date TEXT NOT NULL,
                    full_text TEXT NOT NULL,
                    parts_data TEXT NOT NULL,  -- JSON string
                    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    file_hash TEXT,
                    is_latest BOOLEAN DEFAULT FALSE
                )
            """)
            
            # Create chat history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    user_ip TEXT,
                    response_time_ms INTEGER
                )
            """)
            
            # Create scraping logs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scraping_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    status TEXT NOT NULL,  -- 'success', 'error', 'skipped'
                    fac_number TEXT,
                    effective_date TEXT,
                    error_message TEXT,
                    records_scraped INTEGER,
                    execution_time_seconds REAL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for better performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_far_latest ON far_data(is_latest)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_far_scraped_at ON far_data(scraped_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_chat_timestamp ON chat_history(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_chat_session ON chat_history(session_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_scraping_timestamp ON scraping_logs(timestamp)")
            
            conn.commit()
            logger.info("Database initialized successfully")
    
    @contextmanager
    def get_connection(self):
        """Get database connection with proper error handling"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Enable column access by name
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def save_far_data(self, far_data: Dict) -> int:
        """Save FAR data to database"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Mark all existing records as not latest
            cursor.execute("UPDATE far_data SET is_latest = FALSE")
            
            # Calculate file hash for deduplication
            file_hash = self._calculate_hash(far_data)
            
            # Check if this data already exists
            cursor.execute("SELECT id FROM far_data WHERE file_hash = ?", (file_hash,))
            existing = cursor.fetchone()
            
            if existing:
                # Update existing record to be latest
                cursor.execute("UPDATE far_data SET is_latest = TRUE WHERE id = ?", (existing['id'],))
                conn.commit()
                logger.info(f"Updated existing FAR data record {existing['id']} as latest")
                return existing['id']
            
            # Insert new record
            cursor.execute("""
                INSERT INTO far_data (fac_number, effective_date, full_text, parts_data, file_hash, is_latest)
                VALUES (?, ?, ?, ?, ?, TRUE)
            """, (
                far_data['version_info'].get('fac_number', ''),
                far_data['version_info'].get('effective_date', ''),
                far_data['full_text'],
                json.dumps(far_data['parts']),
                file_hash
            ))
            
            record_id = cursor.lastrowid
            conn.commit()
            logger.info(f"Saved new FAR data with ID {record_id}")
            return record_id
    
    def get_latest_far_data(self) -> Optional[Dict]:
        """Get the latest FAR data from database"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM far_data 
                WHERE is_latest = TRUE 
                ORDER BY scraped_at DESC 
                LIMIT 1
            """)
            
            row = cursor.fetchone()
            if row:
                return {
                    'id': row['id'],
                    'fac_number': row['fac_number'],
                    'effective_date': row['effective_date'],
                    'full_text': row['full_text'],
                    'parts': json.loads(row['parts_data']),
                    'scraped_at': row['scraped_at'],
                    'version_info': {
                        'fac_number': row['fac_number'],
                        'effective_date': row['effective_date'],
                        'scraped_at': row['scraped_at']
                    }
                }
            return None
    
    def save_chat_message(self, session_id: str, question: str, answer: str, 
                         user_ip: str = None, response_time_ms: int = None) -> int:
        """Save chat message to database"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO chat_history (session_id, question, answer, user_ip, response_time_ms)
                VALUES (?, ?, ?, ?, ?)
            """, (session_id, question, answer, user_ip, response_time_ms))
            
            record_id = cursor.lastrowid
            conn.commit()
            return record_id
    
    def get_chat_history(self, session_id: str = None, limit: int = 50) -> List[Dict]:
        """Get chat history from database"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if session_id:
                cursor.execute("""
                    SELECT * FROM chat_history 
                    WHERE session_id = ? 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                """, (session_id, limit))
            else:
                cursor.execute("""
                    SELECT * FROM chat_history 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                """, (limit,))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def clear_chat_history(self, session_id: str = None) -> int:
        """Clear chat history"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if session_id:
                cursor.execute("DELETE FROM chat_history WHERE session_id = ?", (session_id,))
            else:
                cursor.execute("DELETE FROM chat_history")
            
            deleted_count = cursor.rowcount
            conn.commit()
            return deleted_count
    
    def log_scraping_result(self, status: str, fac_number: str = None, 
                           effective_date: str = None, error_message: str = None,
                           records_scraped: int = None, execution_time_seconds: float = None):
        """Log scraping operation result"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO scraping_logs (status, fac_number, effective_date, error_message, 
                                         records_scraped, execution_time_seconds)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (status, fac_number, effective_date, error_message, 
                  records_scraped, execution_time_seconds))
            conn.commit()
    
    def get_scraping_logs(self, limit: int = 100) -> List[Dict]:
        """Get scraping logs from database"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM scraping_logs 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (limit,))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def get_database_stats(self) -> Dict:
        """Get database statistics"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Count records in each table
            cursor.execute("SELECT COUNT(*) as count FROM far_data")
            far_data_count = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM chat_history")
            chat_count = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM scraping_logs")
            logs_count = cursor.fetchone()['count']
            
            # Get latest scraping info
            cursor.execute("""
                SELECT fac_number, effective_date, scraped_at 
                FROM far_data 
                WHERE is_latest = TRUE 
                LIMIT 1
            """)
            latest_far = cursor.fetchone()
            
            # Get recent scraping success rate
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful
                FROM scraping_logs 
                WHERE timestamp > datetime('now', '-7 days')
            """)
            recent_stats = cursor.fetchone()
            
            return {
                'far_data_records': far_data_count,
                'chat_messages': chat_count,
                'scraping_logs': logs_count,
                'latest_far': dict(latest_far) if latest_far else None,
                'recent_scraping_success_rate': (
                    recent_stats['successful'] / recent_stats['total'] * 100 
                    if recent_stats['total'] > 0 else 0
                )
            }
    
    def _calculate_hash(self, data: Dict) -> str:
        """Calculate hash for data deduplication"""
        import hashlib
        content = json.dumps(data, sort_keys=True)
        return hashlib.md5(content.encode()).hexdigest()
    
    def cleanup_old_data(self, days_to_keep: int = 30):
        """Clean up old data to prevent database bloat"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Keep only latest FAR data and data from last N days
            cursor.execute("""
                DELETE FROM far_data 
                WHERE is_latest = FALSE 
                AND scraped_at < datetime('now', '-{} days')
            """.format(days_to_keep))
            
            far_deleted = cursor.rowcount
            
            # Clean up old chat history
            cursor.execute("""
                DELETE FROM chat_history 
                WHERE timestamp < datetime('now', '-{} days')
            """.format(days_to_keep))
            
            chat_deleted = cursor.rowcount
            
            # Clean up old scraping logs
            cursor.execute("""
                DELETE FROM scraping_logs 
                WHERE timestamp < datetime('now', '-{} days')
            """.format(days_to_keep))
            
            logs_deleted = cursor.rowcount
            
            conn.commit()
            
            logger.info(f"Cleaned up {far_deleted} old FAR records, {chat_deleted} chat messages, {logs_deleted} scraping logs")
            
            return {
                'far_deleted': far_deleted,
                'chat_deleted': chat_deleted,
                'logs_deleted': logs_deleted
            }

# Global database manager instance
db_manager = DatabaseManager()
