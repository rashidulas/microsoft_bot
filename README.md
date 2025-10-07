# FAR Bot - Federal Acquisition Regulation Change Tracker

A comprehensive system to scrape, track, and analyze changes to the Federal Acquisition Regulation (FAR) from [acquisition.gov](https://www.acquisition.gov/browse/index/far).

## Features

- **Automated Scraping**: Scrapes all 53 FAR parts from the official government website
- **Version Tracking**: Tracks FAR versions by FAC number and effective date
- **Change Detection**: Automatically detects when new versions are available
- **Change Analysis**: Compares versions and identifies what changed
- **Plain English Explanations**: Uses AI to explain changes in business-friendly language
- **Historical Tracking**: Maintains a complete history of all FAR versions

## Quick Start

### 1. Setup Environment
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Setup AI Chatbot
```bash
# Run the setup script (will prompt for OpenAI API key)
python setup_chatbot.py

# Or manually set your OpenAI API key
export OPENAI_API_KEY=your_openai_api_key_here
```

### 3. Basic Usage

**Scrape the latest FAR:**
```bash
python far_bot.py scrape
```

**Start AI Chatbot (Command Line):**
```bash
python simple_chatbot.py
```

**Start AI Chatbot (Web Interface):**
```bash
python web_chatbot.py
# Then open: http://localhost:5000
```

**Check system status:**
```bash
python far_bot.py status
```

**Run full cycle (scrape + analyze changes):**
```bash
python far_bot.py run
```

**Analyze changes between versions:**
```bash
python far_bot.py analyze
```

## AI Chatbot Features

The AI chatbot can answer questions about the FAR in plain English:

**Example Questions:**
- "What are the small business requirements?"
- "How do I submit a bid for a government contract?"
- "What are the security requirements for contractors?"
- "Tell me about contract termination procedures"
- "What is the simplified acquisition threshold?"
- "How do I become a government contractor?"

**Two Interfaces Available:**
1. **Command Line**: `python simple_chatbot.py`
2. **Web Interface**: `python web_chatbot.py` (then open http://localhost:5000)

### Advanced Usage with AI Explanations

To get AI-powered plain English explanations of changes, set your OpenAI API key:

```bash
python far_bot.py run --openai-key YOUR_OPENAI_API_KEY
```

## Files Created

- `data/far_latest.txt` - Latest FAR in text format
- `data/far_latest.json` - Latest FAR in structured JSON format
- `data/far_versions.json` - Version tracking metadata
- `data/far_changes_YYYYMMDD_HHMMSS.md` - Change analysis reports

## How It Works

1. **Version Detection**: Checks the acquisition.gov website for the current FAC number and effective date
2. **Smart Scraping**: Only scrapes if a new version is detected
3. **Content Extraction**: Extracts all FAR parts and their content
4. **Change Analysis**: Compares new version with previous version
5. **Report Generation**: Creates detailed change reports with AI explanations

## Example Output

The system successfully scraped **53 FAR parts** and created:
- **6.5MB** of FAR text data
- **13MB** of structured JSON data
- Version tracking for **FAC 2025-05** (Effective: 08/07/2025)

## Automation

You can set up automated monitoring by running the bot periodically:

```bash
# Add to crontab for daily checks
0 9 * * * cd /path/to/far_bot && python far_bot.py run
```

## API Integration

The system can be integrated with other applications through the Python classes:

```python
from far_bot import FARBot

bot = FARBot()
latest_file = bot.scrape_latest()
change_report = bot.analyze_changes()
```

## Requirements

- Python 3.7+
- requests
- beautifulsoup4
- openai (optional, for AI explanations)
- faiss-cpu (for future similarity search features)

## Legal Notice

This tool scrapes publicly available government data from acquisition.gov. Always verify important regulatory information with official sources.
