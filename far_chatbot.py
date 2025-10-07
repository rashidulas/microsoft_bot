#!/usr/bin/env python3
"""
FAR Chatbot - AI-powered assistant for Federal Acquisition Regulation questions
"""

import os
import json
import re
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from config import Config

class FARChatbot:
    def __init__(self, data_dir: str = "data", openai_api_key: Optional[str] = None):
        self.data_dir = data_dir
        self.chat_history = []
        
        # Initialize OpenAI client
        if openai_api_key:
            from openai import OpenAI
            self.client = OpenAI(api_key=openai_api_key)
        else:
            self.client = Config.get_openai_client()
        
        if not self.client:
            print("⚠️  No OpenAI API key provided. Chatbot will work in limited mode.")
            self.openai_available = False
            return
        
        self.openai_available = True
        self.model = Config.OPENAI_MODEL
        self.temperature = Config.OPENAI_TEMPERATURE
        self.max_tokens = Config.MAX_TOKENS
        
    def load_far_data(self) -> Optional[Dict]:
        """Load the latest FAR data"""
        latest_file = os.path.join(self.data_dir, "far_latest.json")
        
        if not os.path.exists(latest_file):
            print("❌ No FAR data found. Please run the scraper first:")
            print("   python far_bot.py scrape")
            return None
        
        try:
            with open(latest_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Error loading FAR data: {e}")
            return None
    
    def search_far_content(self, query: str, far_data: Dict, max_results: int = 5) -> List[Dict]:
        """Search FAR content for relevant sections"""
        if not far_data or "parts" not in far_data:
            return []
        
        query_lower = query.lower()
        results = []
        
        for part_url, part_data in far_data["parts"].items():
            content = part_data.get("content", "").lower()
            title = part_data.get("title", "").lower()
            
            # Calculate relevance score
            score = 0
            
            # Title matches get higher score
            if query_lower in title:
                score += 10
            
            # Content matches
            content_matches = content.count(query_lower)
            score += content_matches
            
            # Check for related terms
            related_terms = self._get_related_terms(query_lower)
            for term in related_terms:
                if term in content:
                    score += 1
            
            if score > 0:
                results.append({
                    "part_url": part_url,
                    "title": part_data.get("title", ""),
                    "content": part_data.get("content", ""),
                    "score": score,
                    "url": part_data.get("url", "")
                })
        
        # Sort by relevance score and return top results
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:max_results]
    
    def _get_related_terms(self, query: str) -> List[str]:
        """Get related terms for better search"""
        term_mapping = {
            "contract": ["agreement", "procurement", "acquisition", "award"],
            "bid": ["proposal", "offer", "solicitation", "submission"],
            "vendor": ["contractor", "supplier", "offeror", "bidder"],
            "cost": ["price", "pricing", "budget", "expense"],
            "compliance": ["requirement", "regulation", "standard", "policy"],
            "small business": ["sba", "set-aside", "small business concern"],
            "security": ["clearance", "classified", "sensitive", "confidential"],
            "labor": ["wage", "employee", "worker", "employment"],
            "termination": ["cancellation", "default", "breach", "suspension"]
        }
        
        related = []
        for key, terms in term_mapping.items():
            if key in query:
                related.extend(terms)
        
        return related
    
    def format_context_for_ai(self, search_results: List[Dict], query: str) -> str:
        """Format search results as context for AI"""
        if not search_results:
            return "No relevant FAR sections found for this query."
        
        context = f"Based on the Federal Acquisition Regulation (FAR), here are relevant sections for the query: '{query}'\n\n"
        
        for i, result in enumerate(search_results, 1):
            context += f"**Section {i}: {result['title']}**\n"
            context += f"URL: {result['url']}\n\n"
            
            # Truncate content to avoid token limits
            content = result['content'][:2000] + "..." if len(result['content']) > 2000 else result['content']
            context += f"{content}\n\n"
            context += "---\n\n"
        
        return context
    
    def generate_ai_response(self, query: str, context: str) -> str:
        """Generate AI response based on query and context"""
        if not self.openai_available:
            return "AI features are not available. Please provide an OpenAI API key to enable AI responses."
        
        try:
            system_prompt = """You are an expert in the Federal Acquisition Regulation (FAR) and government contracting. 
            Your role is to help businesses understand FAR requirements in clear, practical language.
            
            Guidelines:
            - Provide accurate, helpful answers based on the FAR content provided
            - Explain complex regulations in business-friendly terms
            - Include relevant FAR section references when possible
            - If you're unsure about something, say so and suggest consulting official sources
            - Focus on practical implications for contractors and businesses
            - Keep responses concise but comprehensive"""
            
            user_prompt = f"""Context from FAR:
            {context}
            
            Question: {query}
            
            Please provide a helpful answer based on the FAR content above."""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            return f"Error generating AI response: {e}"
    
    def get_simple_response(self, query: str, search_results: List[Dict]) -> str:
        """Generate a simple response without AI"""
        if not search_results:
            return "I couldn't find relevant information in the FAR for your question. Please try rephrasing or ask about a different topic."
        
        response = f"I found {len(search_results)} relevant FAR section(s) for your question:\n\n"
        
        for i, result in enumerate(search_results, 1):
            response += f"{i}. **{result['title']}**\n"
            response += f"   URL: {result['url']}\n"
            
            # Extract a relevant snippet
            content = result['content']
            query_lower = query.lower()
            
            # Find the first sentence containing the query
            sentences = content.split('. ')
            relevant_sentence = None
            for sentence in sentences:
                if query_lower in sentence.lower():
                    relevant_sentence = sentence.strip()
                    break
            
            if relevant_sentence:
                response += f"   Relevant excerpt: {relevant_sentence[:200]}...\n"
            
            response += "\n"
        
        response += "\nFor detailed information, please refer to the full FAR sections above."
        return response
    
    def ask_question(self, question: str, use_ai: bool = True) -> str:
        """Main method to ask a question about the FAR"""
        print(f"🔍 Searching FAR for: '{question}'")
        
        # Load FAR data
        far_data = self.load_far_data()
        if not far_data:
            return "Unable to load FAR data. Please ensure the scraper has been run."
        
        # Search for relevant content
        search_results = self.search_far_content(question, far_data)
        
        if not search_results:
            return "I couldn't find relevant information in the FAR for your question. Please try rephrasing or ask about a different topic."
        
        # Add to chat history
        self.chat_history.append({
            "question": question,
            "timestamp": datetime.now().isoformat(),
            "results_count": len(search_results)
        })
        
        # Keep only recent history
        if len(self.chat_history) > Config.CHAT_HISTORY_LIMIT:
            self.chat_history = self.chat_history[-Config.CHAT_HISTORY_LIMIT:]
        
        # Generate response
        if use_ai and self.openai_available:
            context = self.format_context_for_ai(search_results, question)
            return self.generate_ai_response(question, context)
        else:
            return self.get_simple_response(question, search_results)
    
    def get_chat_history(self) -> List[Dict]:
        """Get chat history"""
        return self.chat_history
    
    def clear_history(self):
        """Clear chat history"""
        self.chat_history = []

def main():
    """Interactive chatbot interface"""
    print("🤖 FAR Chatbot - Ask questions about the Federal Acquisition Regulation")
    print("Type 'quit' to exit, 'history' to see chat history, 'clear' to clear history")
    print("-" * 70)
    
    # Initialize chatbot
    chatbot = FARChatbot()
    
    if not chatbot.openai_available:
        print("⚠️  AI features disabled. Install OpenAI API key for enhanced responses.")
        print("   Set OPENAI_API_KEY environment variable or pass it to FARChatbot()")
        print()
    
    while True:
        try:
            question = input("\n❓ Your question: ").strip()
            
            if question.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            if question.lower() == 'history':
                history = chatbot.get_chat_history()
                if history:
                    print("\n📜 Chat History:")
                    for i, entry in enumerate(history, 1):
                        print(f"{i}. {entry['question']} ({entry['timestamp']})")
                else:
                    print("No chat history yet.")
                continue
            
            if question.lower() == 'clear':
                chatbot.clear_history()
                print("Chat history cleared.")
                continue
            
            if not question:
                continue
            
            # Get answer
            answer = chatbot.ask_question(question)
            print(f"\n💡 Answer:\n{answer}")
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
