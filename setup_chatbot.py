#!/usr/bin/env python3
"""
Setup script for FAR AI Chatbot
"""

import os
import sys
import subprocess

def install_requirements():
    """Install required packages"""
    print("📦 Installing required packages...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Packages installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing packages: {e}")
        return False

def check_far_data():
    """Check if FAR data exists"""
    if os.path.exists("data/far_latest.json"):
        print("✅ FAR data found!")
        return True
    else:
        print("❌ No FAR data found.")
        print("   Please run: python far_bot.py scrape")
        return False

def setup_env_file():
    """Help user set up environment file"""
    env_file = ".env"
    
    if os.path.exists(env_file):
        print(f"✅ {env_file} file already exists")
        return True
    
    print("🔧 Setting up environment file...")
    print("Please enter your OpenAI API key:")
    api_key = input("OpenAI API Key: ").strip()
    
    if not api_key:
        print("⚠️  No API key provided. You can set it later by:")
        print("   1. Creating a .env file with: OPENAI_API_KEY=your_key_here")
        print("   2. Or setting environment variable: export OPENAI_API_KEY=your_key_here")
        return False
    
    try:
        with open(env_file, "w") as f:
            f.write(f"OPENAI_API_KEY={api_key}\n")
            f.write("OPENAI_MODEL=gpt-3.5-turbo\n")
            f.write("OPENAI_TEMPERATURE=0.3\n")
        
        print(f"✅ Created {env_file} file with your API key")
        return True
    except Exception as e:
        print(f"❌ Error creating {env_file}: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 FAR AI Chatbot Setup")
    print("=" * 40)
    
    # Install requirements
    if not install_requirements():
        return
    
    # Check FAR data
    if not check_far_data():
        print("\n📋 Next steps:")
        print("1. Run: python far_bot.py scrape")
        print("2. Then run this setup again")
        return
    
    # Setup environment
    setup_env_file()
    
    print("\n🎉 Setup complete!")
    print("\n📋 Available commands:")
    print("• python simple_chatbot.py     - Command line chatbot")
    print("• python web_chatbot.py        - Web interface chatbot")
    print("• python far_bot.py scrape     - Update FAR data")
    print("• python far_bot.py status     - Check system status")
    
    print("\n🌐 To start the web chatbot:")
    print("   python web_chatbot.py")
    print("   Then open: http://localhost:5000")

if __name__ == "__main__":
    main()

