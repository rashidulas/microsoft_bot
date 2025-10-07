# 🤖 FAR Bot - Federal Acquisition Regulation AI Assistant

A comprehensive AI-powered chatbot that helps users understand the Federal Acquisition Regulation (FAR) with automated scraping, database integration, and a modern web interface.

## ✨ Features

- **🤖 AI-Powered Chat**: OpenAI GPT integration for intelligent FAR responses
- **🗄️ Database Integration**: SQLite database for persistent data storage
- **⏰ Automated Scraping**: Daily automated scraping with APScheduler
- **🌐 Modern Web UI**: Beautiful, responsive web interface
- **📊 Admin Panel**: Comprehensive monitoring and management
- **📱 Mobile Friendly**: Responsive design works on all devices

## 🚀 Quick Start

### 1. Setup Environment
```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies (if needed)
pip install -r requirements.txt
```

### 2. Configure API Key
Edit the `.env` file and add your OpenAI API key:
```bash
nano .env
# Change: OPENAI_API_KEY=your_actual_api_key_here
```

### 3. Start the Application
```bash
# Start the complete application
python start.py

# Or use the startup script
./run.sh
```

### 4. Access the Interface
- **Chat Interface**: http://localhost:5001
- **Admin Panel**: http://localhost:5001/admin

## 📁 Project Structure

```
microsoft_bot/
├── main.py                  # Main application entry point
├── start.py                 # Simple startup script
├── app.py                   # Flask web application
├── database.py              # Database models and operations
├── scheduler.py             # Automated scheduling
├── scrape_far.py            # FAR web scraping
├── config.py                # Configuration management
├── run.sh                   # Startup script
├── templates/
│   ├── chatbot.html         # Chat interface
│   └── admin.html           # Admin panel
├── data/
│   ├── far_latest.json      # Latest FAR data
│   ├── far_latest.txt       # Latest FAR text
│   └── far_versions.json    # Version tracking
├── far_bot.db              # SQLite database
├── requirements.txt         # Python dependencies
├── .env                     # Environment variables
└── README.md               # This file
```

## 🗄️ Database

The application uses SQLite with three main tables:
- **far_data**: Stores scraped FAR content and versions
- **chat_history**: Stores all chat conversations
- **scraping_logs**: Logs all scraping operations

## ⚙️ Configuration

### Environment Variables (.env file)
```env
OPENAI_API_KEY=your_openai_api_key_here
FLASK_SECRET_KEY=your-secret-key-change-this
FLASK_DEBUG=False
PORT=5001
```

### Automated Scheduling
- **Daily Scraping**: 2:00 AM every day
- **Weekly Cleanup**: 3:00 AM every Sunday
- **Smart Detection**: Only scrapes when FAR version changes

## 📊 Admin Panel Features

Access the admin panel at `/admin` to:
- Monitor system statistics
- Trigger manual scraping
- View scraping operation logs
- Manage data cleanup
- Force scraping operations

## 🔧 Troubleshooting

### Common Issues
1. **Port in use**: Change `PORT=5001` in `.env`
2. **API key errors**: Verify your OpenAI API key in `.env`
3. **Database issues**: Delete `far_bot.db` and restart

### Logs
- Application logs: `far_bot.log`
- Console output: Real-time status
- Admin panel: Scraping operation logs

## 🚀 Usage

### Chat Interface
Ask questions about the FAR like:
- "What are the small business requirements?"
- "How do I submit a bid for a government contract?"
- "What are the security requirements for contractors?"
- "Tell me about contract termination procedures"

### API Endpoints
- `GET /api/status` - System status
- `POST /api/chat` - Send chat message
- `GET /api/history` - Chat history
- `POST /api/clear` - Clear chat history
- `GET /api/admin/stats` - System statistics
- `POST /api/scrape` - Manual scraping

## 📄 License

This project is licensed under the MIT License.

## ⚠️ Disclaimer

This tool is for informational purposes only. Always consult official sources and legal professionals for authoritative FAR guidance.