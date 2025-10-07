#!/usr/bin/env python3
"""
Simple startup script for FAR Bot
"""

import os
import sys

def main():
    """Start the FAR Bot application"""
    print("🤖 Starting FAR Bot...")
    print("=" * 50)
    
    # Check if virtual environment is activated
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("⚠️  Warning: Virtual environment not detected.")
        print("   It's recommended to activate your virtual environment first:")
        print("   source venv/bin/activate")
        print()
    
    # Check for required environment variables
    if not os.getenv('OPENAI_API_KEY'):
        print("⚠️  OpenAI API key not found!")
        print("   Please set your OpenAI API key:")
        print("   1. Create a .env file with: OPENAI_API_KEY=your_key_here")
        print("   2. Or set environment variable: export OPENAI_API_KEY=your_key_here")
        print()
        print("   The application will start but AI features will be disabled.")
        print()
    
    # Start the main application
    try:
        from main import main as start_app
        start_app()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
