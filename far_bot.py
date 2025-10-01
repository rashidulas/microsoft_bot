#!/usr/bin/env python3
"""
FAR Bot - A system to track and explain changes to the Federal Acquisition Regulation
"""

import os
import sys
import argparse
from datetime import datetime
from scrape_far import FARScraper
from far_change_analyzer import FARChangeAnalyzer

class FARBot:
    def __init__(self, data_dir: str = "data", openai_api_key: str = None):
        self.data_dir = data_dir
        self.scraper = FARScraper(data_dir)
        self.analyzer = FARChangeAnalyzer(data_dir, openai_api_key)
        
    def scrape_latest(self) -> str:
        """Scrape the latest FAR version"""
        print("🔍 Scraping latest FAR version...")
        return self.scraper.run_scrape()
    
    def analyze_changes(self, compare_with_latest: bool = True) -> str:
        """Analyze changes between versions"""
        print("📊 Analyzing FAR changes...")
        
        # Get list of available versions
        version_file = os.path.join(self.data_dir, "far_versions.json")
        if not os.path.exists(version_file):
            print("No previous versions found. Run scrape first.")
            return None
        
        import json
        with open(version_file, "r") as f:
            versions = json.load(f)
        
        if len(versions.get("versions", [])) < 2:
            print("Need at least 2 versions to compare. Run scrape again after FAR updates.")
            return None
        
        # Get the two most recent versions
        version_list = versions["versions"]
        latest_version = version_list[-1]
        previous_version = version_list[-2]
        
        latest_file = latest_version["file_path"]
        previous_file = previous_version["file_path"]
        
        # Convert JSON file paths to actual file paths
        latest_file = latest_file.replace(".json", ".json")
        previous_file = previous_file.replace(".json", ".json")
        
        if not os.path.exists(latest_file) or not os.path.exists(previous_file):
            print(f"Version files not found. Latest: {latest_file}, Previous: {previous_file}")
            return None
        
        print(f"Comparing {previous_version['fac_number']} with {latest_version['fac_number']}")
        
        # Generate change report
        report = self.analyzer.compare_versions(previous_file, latest_file)
        
        # Save report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.analyzer.save_change_report(report, f"far_changes_{timestamp}.md")
        
        return report_file
    
    def get_status(self) -> dict:
        """Get current status of FAR tracking"""
        version_file = os.path.join(self.data_dir, "far_versions.json")
        
        if not os.path.exists(version_file):
            return {
                "status": "no_data",
                "message": "No FAR data found. Run scrape first.",
                "versions": []
            }
        
        import json
        with open(version_file, "r") as f:
            versions = json.load(f)
        
        version_list = versions.get("versions", [])
        
        return {
            "status": "active",
            "total_versions": len(version_list),
            "latest_version": version_list[-1] if version_list else None,
            "versions": version_list
        }
    
    def run_full_cycle(self) -> str:
        """Run a full cycle: scrape latest and analyze changes"""
        print("🚀 Starting full FAR tracking cycle...")
        
        # Scrape latest
        latest_file = self.scrape_latest()
        
        # Analyze changes
        change_report = self.analyze_changes()
        
        if change_report:
            print(f"✅ Full cycle complete!")
            print(f"📄 Latest FAR data: {latest_file}")
            print(f"📊 Change analysis: {change_report}")
            return change_report
        else:
            print("✅ Scraping complete, but no changes to analyze yet.")
            return latest_file

def main():
    parser = argparse.ArgumentParser(description="FAR Bot - Track and analyze Federal Acquisition Regulation changes")
    parser.add_argument("command", choices=["scrape", "analyze", "status", "run"], 
                       help="Command to run")
    parser.add_argument("--data-dir", default="data", help="Data directory (default: data)")
    parser.add_argument("--openai-key", help="OpenAI API key for AI explanations")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    # Initialize bot
    bot = FARBot(args.data_dir, args.openai_key)
    
    if args.command == "scrape":
        result = bot.scrape_latest()
        print(f"Scraping complete: {result}")
        
    elif args.command == "analyze":
        result = bot.analyze_changes()
        if result:
            print(f"Analysis complete: {result}")
        else:
            print("No changes to analyze")
            
    elif args.command == "status":
        status = bot.get_status()
        print(f"FAR Bot Status: {status['status']}")
        if status['status'] == 'active':
            print(f"Total versions tracked: {status['total_versions']}")
            if status['latest_version']:
                latest = status['latest_version']
                print(f"Latest version: {latest['fac_number']} (Effective: {latest['effective_date']})")
                
    elif args.command == "run":
        result = bot.run_full_cycle()
        print(f"Full cycle complete: {result}")

if __name__ == "__main__":
    main()
