"""
Configuration file for FAR Bot
"""
import os
from typing import Optional
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration settings for FAR Bot"""
    
    # OpenAI API Configuration
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    OPENAI_TEMPERATURE: float = float(os.getenv("OPENAI_TEMPERATURE", "0.3"))
    
    @classmethod
    def get_openai_client(cls) -> Optional[OpenAI]:
        """Get OpenAI client instance"""
        if not cls.OPENAI_API_KEY:
            return None
        return OpenAI(api_key=cls.OPENAI_API_KEY)
    
    # Data directory
    DATA_DIR: str = os.getenv("DATA_DIR", "data")
    
    # Chat settings
    MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "2000"))
    CHAT_HISTORY_LIMIT: int = int(os.getenv("CHAT_HISTORY_LIMIT", "10"))
    
    @classmethod
    def validate_openai_config(cls) -> bool:
        """Validate that OpenAI configuration is properly set"""
        if not cls.OPENAI_API_KEY:
            print("⚠️  OpenAI API key not found!")
            print("Please set your OpenAI API key:")
            print("1. Create a .env file with: OPENAI_API_KEY=your_key_here")
            print("2. Or set environment variable: export OPENAI_API_KEY=your_key_here")
            print("3. Or pass it directly when creating the chatbot")
            return False
        return True
