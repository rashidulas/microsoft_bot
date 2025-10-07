#!/usr/bin/env python3
"""
Simple FAR Chatbot - AI-powered assistant for Federal Acquisition Regulation questions
"""

import os
import json
from typing import List, Dict, Optional
from config import Config

class SimpleFARChatbot:
    def __init__(self, openai_api_key: Optional[str] = None):
        self.data_dir = "data"
        
        # Initialize OpenAI client
        if openai_api_key:
            from openai import OpenAI
            self.client = OpenAI(api_key=openai_api_key)
        else:
            self.client = Config.get_openai_client()
        
        if not self.client:
            print("⚠️  No OpenAI API key provided. Please set OPENAI_API_KEY environment variable.")
            self.openai_available = False
            return
        
        self.openai_available = True
        self.model = Config.OPENAI_MODEL
        self.temperature = Config.OPENAI_TEMPERATURE
        
    def load_far_data(self) -> Optional[Dict]:
        """Load the latest FAR data"""
        latest_file = os.path.join(self.data_dir, "far_latest.json")
        
        if not os.path.exists(latest_file):
            print("❌ No FAR data found. Please run: python far_bot.py scrape")
            return None
        
        try:
            with open(latest_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Error loading FAR data: {e}")
            return None
    
    def get_far_summary(self, far_data: Dict) -> str:
        """Get a summary of the FAR data for context"""
        if not far_data:
            return "No FAR data available."
        
        version_info = far_data.get("version_info", {})
        parts = far_data.get("parts", {})
        
        summary = f"Federal Acquisition Regulation (FAR) - Version {version_info.get('fac_number', 'Unknown')}\n"
        summary += f"Effective Date: {version_info.get('effective_date', 'Unknown')}\n"
        summary += f"Total Parts: {len(parts)}\n\n"
        
        # List all parts
        summary += "Available FAR Parts:\n"
        for part_url, part_data in parts.items():
            title = part_data.get("title", part_url)
            summary += f"- {title}\n"
        
        return summary
    
    def ask_question(self, question: str) -> str:
        """Ask a question about the FAR"""
        if not self.openai_available:
            return "AI features are not available. Please set your OpenAI API key."
        
        # Load FAR data
        far_data = self.load_far_data()
        if not far_data:
            return "Unable to load FAR data. Please run the scraper first."
        
        # Get FAR summary for context
        far_summary = self.get_far_summary(far_data)
        
        # Get relevant FAR content (first 8000 characters to stay within token limits)
        far_content = far_data.get("full_text", "")[:8000]
        
        try:
            system_prompt = """You are an expert in the Federal Acquisition Regulation (FAR) and government contracting. 
            You help businesses understand FAR requirements in clear, practical language.
            
            Guidelines:
            - Provide accurate, helpful answers based on the FAR content provided
            - Explain complex regulations in business-friendly terms
            - Include relevant FAR section references when possible
            - If you're unsure about something, say so and suggest consulting official sources
            - Focus on practical implications for contractors and businesses
            - Keep responses concise but comprehensive
            - Always cite the specific FAR part or section when referencing regulations"""
            
            user_prompt = f"""FAR Information:
            {far_summary}
            
            Relevant FAR Content:
            {far_content}
            
            Question: {question}
            
            Please provide a helpful answer based on the FAR content above. Include specific FAR part references when relevant."""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=1000,
                temperature=self.temperature
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            return f"Error generating AI response: {e}"

def main():
    """Simple chatbot interface"""
    print("🤖 FAR AI Chatbot")
    print("=" * 50)
    
    # Check for API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️  Please set your OpenAI API key:")
        print("   export OPENAI_API_KEY=your_key_here")
        print("   or create a .env file with: OPENAI_API_KEY=your_key_here")
        return
    
    # Initialize chatbot
    chatbot = SimpleFARChatbot()
    
    if not chatbot.openai_available:
        return
    
    print("✅ AI Chatbot ready! Ask questions about the FAR.")
    print("Type 'quit' to exit\n")
    
    while True:
        try:
            question = input("❓ Your question: ").strip()
            
            if question.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            if not question:
                continue
            
            print("🤔 Thinking...")
            answer = chatbot.ask_question(question)
            print(f"\n💡 Answer:\n{answer}\n")
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()



