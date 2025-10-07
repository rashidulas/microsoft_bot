#!/usr/bin/env python3
"""
Flask web application for FAR Bot with database integration
"""

import os
import time
import uuid
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
import logging

from config import Config
from simple_chatbot import SimpleFARChatbot
from database import db_manager
from scrape_far import FARScraper

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'your-secret-key-change-this')
CORS(app)

# Initialize chatbot
chatbot = None

def get_chatbot():
    """Get or create chatbot instance"""
    global chatbot
    if chatbot is None:
        chatbot = SimpleFARChatbot()
    return chatbot

@app.route('/')
def index():
    """Main chat interface"""
    return render_template('chatbot.html')

@app.route('/admin')
def admin():
    """Admin panel for monitoring and management"""
    return render_template('admin.html')

@app.route('/api/status')
def api_status():
    """Check system status"""
    try:
        chatbot = get_chatbot()
        far_data = db_manager.get_latest_far_data()
        
        return jsonify({
            'ai_available': chatbot.openai_available,
            'far_data_available': far_data is not None,
            'latest_far_version': far_data['fac_number'] if far_data else None,
            'latest_far_date': far_data['effective_date'] if far_data else None,
            'last_scraped': far_data['scraped_at'] if far_data else None
        })
    except Exception as e:
        logger.error(f"Status check error: {e}")
        return jsonify({
            'ai_available': False,
            'far_data_available': False,
            'error': str(e)
        }), 500

@app.route('/api/chat', methods=['POST'])
def api_chat():
    """Handle chat messages"""
    try:
        data = request.get_json()
        question = data.get('question', '').strip()
        
        if not question:
            return jsonify({'error': 'Question is required'}), 400
        
        # Get or create session ID
        session_id = session.get('session_id')
        if not session_id:
            session_id = str(uuid.uuid4())
            session['session_id'] = session_id
        
        # Get user IP
        user_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        
        # Start timing
        start_time = time.time()
        
        # Get chatbot response
        chatbot = get_chatbot()
        answer = chatbot.ask_question(question)
        
        # Calculate response time
        response_time_ms = int((time.time() - start_time) * 1000)
        
        # Save to database
        db_manager.save_chat_message(
            session_id=session_id,
            question=question,
            answer=answer,
            user_ip=user_ip,
            response_time_ms=response_time_ms
        )
        
        return jsonify({
            'answer': answer,
            'response_time_ms': response_time_ms
        })
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/history')
def api_history():
    """Get chat history"""
    try:
        session_id = session.get('session_id')
        limit = request.args.get('limit', 50, type=int)
        
        history = db_manager.get_chat_history(session_id, limit)
        
        # Format for frontend
        formatted_history = []
        for entry in history:
            formatted_history.append({
                'question': entry['question'],
                'answer': entry['answer'],
                'timestamp': entry['timestamp']
            })
        
        return jsonify(formatted_history)
        
    except Exception as e:
        logger.error(f"History error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/clear', methods=['POST'])
def api_clear():
    """Clear chat history"""
    try:
        session_id = session.get('session_id')
        deleted_count = db_manager.clear_chat_history(session_id)
        
        return jsonify({
            'message': f'Cleared {deleted_count} messages',
            'deleted_count': deleted_count
        })
        
    except Exception as e:
        logger.error(f"Clear history error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/scrape', methods=['POST'])
def api_scrape():
    """Trigger manual scraping"""
    try:
        scraper = FARScraper()
        start_time = time.time()
        
        # Run scraping
        result_file = scraper.run_scrape()
        
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
        
        return jsonify({
            'message': 'Scraping completed successfully',
            'record_id': record_id,
            'execution_time_seconds': execution_time,
            'fac_number': far_data['version_info'].get('fac_number'),
            'effective_date': far_data['version_info'].get('effective_date')
        })
        
    except Exception as e:
        logger.error(f"Scraping error: {e}")
        
        # Log error
        db_manager.log_scraping_result(
            status='error',
            error_message=str(e),
            execution_time_seconds=time.time() - start_time if 'start_time' in locals() else 0
        )
        
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/stats')
def api_admin_stats():
    """Get admin statistics"""
    try:
        stats = db_manager.get_database_stats()
        scraping_logs = db_manager.get_scraping_logs(limit=10)
        
        return jsonify({
            'database_stats': stats,
            'recent_scraping_logs': scraping_logs
        })
        
    except Exception as e:
        logger.error(f"Admin stats error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/cleanup', methods=['POST'])
def api_admin_cleanup():
    """Clean up old data"""
    try:
        data = request.get_json() or {}
        days_to_keep = data.get('days_to_keep', 30)
        
        cleanup_result = db_manager.cleanup_old_data(days_to_keep)
        
        return jsonify({
            'message': 'Cleanup completed',
            'cleanup_result': cleanup_result
        })
        
    except Exception as e:
        logger.error(f"Cleanup error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/force-scrape', methods=['POST'])
def api_admin_force_scrape():
    """Force scraping even if version hasn't changed"""
    try:
        scraper = FARScraper()
        start_time = time.time()
        
        # Force scrape by temporarily removing version check
        far_data = scraper.scrape_all_far()
        
        # Save to database
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
        
        return jsonify({
            'message': 'Force scraping completed successfully',
            'record_id': record_id,
            'execution_time_seconds': execution_time,
            'fac_number': far_data['version_info'].get('fac_number'),
            'effective_date': far_data['version_info'].get('effective_date')
        })
        
    except Exception as e:
        logger.error(f"Force scraping error: {e}")
        
        # Log error
        db_manager.log_scraping_result(
            status='error',
            error_message=str(e),
            execution_time_seconds=time.time() - start_time if 'start_time' in locals() else 0
        )
        
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Check configuration
    if not Config.validate_openai_config():
        logger.warning("OpenAI configuration not found. AI features will be disabled.")
    
    # Initialize database
    logger.info("Initializing database...")
    db_manager.init_database()
    
    # Run Flask app
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Starting Flask app on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)
