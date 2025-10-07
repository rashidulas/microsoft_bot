import json
import os
import difflib
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

@dataclass
class Change:
    """Represents a change between two FAR versions"""
    type: str  # 'added', 'removed', 'modified'
    section: str
    old_content: str
    new_content: str
    summary: str

class FARChangeAnalyzer:
    def __init__(self, data_dir: str = "data", openai_api_key: Optional[str] = None):
        self.data_dir = data_dir
        self.openai_client = None
        
        if openai_api_key:
            from openai import OpenAI
            self.openai_client = OpenAI(api_key=openai_api_key)
        else:
            from config import Config
            self.openai_client = Config.get_openai_client()
        
    def load_far_data(self, file_path: str) -> Optional[Dict]:
        """Load FAR data from JSON file"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading FAR data from {file_path}: {e}")
            return None
    
    def extract_sections(self, far_data: Dict) -> Dict[str, str]:
        """Extract sections from FAR data for comparison"""
        sections = {}
        
        if "parts" in far_data:
            for part_url, part_data in far_data["parts"].items():
                # Use part URL as section identifier
                sections[part_url] = part_data.get("content", "")
        
        return sections
    
    def compare_sections(self, old_sections: Dict[str, str], new_sections: Dict[str, str]) -> List[Change]:
        """Compare sections between two FAR versions"""
        changes = []
        
        # Find added sections
        for section in new_sections:
            if section not in old_sections:
                changes.append(Change(
                    type="added",
                    section=section,
                    old_content="",
                    new_content=new_sections[section],
                    summary=f"New section added: {section}"
                ))
        
        # Find removed sections
        for section in old_sections:
            if section not in new_sections:
                changes.append(Change(
                    type="removed",
                    section=section,
                    old_content=old_sections[section],
                    new_content="",
                    summary=f"Section removed: {section}"
                ))
        
        # Find modified sections
        for section in old_sections:
            if section in new_sections:
                old_content = old_sections[section]
                new_content = new_sections[section]
                
                if old_content != new_content:
                    # Calculate similarity
                    similarity = difflib.SequenceMatcher(None, old_content, new_content).ratio()
                    
                    if similarity < 0.95:  # Significant change threshold
                        changes.append(Change(
                            type="modified",
                            section=section,
                            old_content=old_content,
                            new_content=new_content,
                            summary=f"Section modified: {section} (similarity: {similarity:.2f})"
                        ))
        
        return changes
    
    def generate_plain_english_summary(self, changes: List[Change]) -> str:
        """Generate a plain English summary of changes"""
        if not changes:
            return "No significant changes detected between versions."
        
        summary = f"# FAR Changes Summary\n\n"
        summary += f"Total changes detected: {len(changes)}\n\n"
        
        # Group changes by type
        added = [c for c in changes if c.type == "added"]
        removed = [c for c in changes if c.type == "removed"]
        modified = [c for c in changes if c.type == "modified"]
        
        if added:
            summary += f"## New Sections Added ({len(added)})\n"
            for change in added:
                summary += f"- {change.section}\n"
            summary += "\n"
        
        if removed:
            summary += f"## Sections Removed ({len(removed)})\n"
            for change in removed:
                summary += f"- {change.section}\n"
            summary += "\n"
        
        if modified:
            summary += f"## Sections Modified ({len(modified)})\n"
            for change in modified:
                summary += f"- {change.section}\n"
            summary += "\n"
        
        return summary
    
    def explain_change_with_ai(self, change: Change) -> str:
        """Use OpenAI to explain a specific change in plain English"""
        if not self.openai_client:
            return f"Change in {change.section}: {change.summary}"
        
        try:
            prompt = f"""
            Explain this change to the Federal Acquisition Regulation (FAR) in simple, plain English that a business owner could understand:
            
            Section: {change.section}
            Change Type: {change.type}
            
            Old Content:
            {change.old_content[:1000]}...
            
            New Content:
            {change.new_content[:1000]}...
            
            Please provide:
            1. A brief summary of what changed
            2. Why this change might matter to contractors
            3. Any action items or considerations for businesses
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert in government contracting and the Federal Acquisition Regulation. Explain changes in simple, business-friendly language."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.3
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Error generating AI explanation: {e}")
            return f"Change in {change.section}: {change.summary}"
    
    def generate_detailed_change_report(self, changes: List[Change]) -> str:
        """Generate a detailed change report with AI explanations"""
        report = self.generate_plain_english_summary(changes)
        report += "\n## Detailed Change Analysis\n\n"
        
        for i, change in enumerate(changes, 1):
            report += f"### Change {i}: {change.section}\n\n"
            report += f"**Type:** {change.type.title()}\n\n"
            
            # Get AI explanation if available
            ai_explanation = self.explain_change_with_ai(change)
            report += f"**Explanation:**\n{ai_explanation}\n\n"
            
            # Show diff for modified sections
            if change.type == "modified":
                report += "**Key Differences:**\n"
                diff = difflib.unified_diff(
                    change.old_content.splitlines(keepends=True),
                    change.new_content.splitlines(keepends=True),
                    fromfile="Old Version",
                    tofile="New Version",
                    lineterm=""
                )
                
                diff_lines = list(diff)[:20]  # Limit to first 20 lines
                report += "```\n" + "".join(diff_lines) + "\n```\n\n"
            
            report += "---\n\n"
        
        return report
    
    def compare_versions(self, old_file: str, new_file: str) -> str:
        """Compare two FAR versions and generate a change report"""
        print(f"Loading old version: {old_file}")
        old_data = self.load_far_data(old_file)
        
        print(f"Loading new version: {new_file}")
        new_data = self.load_far_data(new_file)
        
        if not old_data or not new_data:
            return "Error: Could not load one or both FAR versions for comparison."
        
        print("Extracting sections for comparison...")
        old_sections = self.extract_sections(old_data)
        new_sections = self.extract_sections(new_data)
        
        print("Comparing sections...")
        changes = self.compare_sections(old_sections, new_sections)
        
        print(f"Found {len(changes)} changes")
        
        if not changes:
            return "No significant changes detected between the two FAR versions."
        
        print("Generating change report...")
        report = self.generate_detailed_change_report(changes)
        
        return report
    
    def save_change_report(self, report: str, filename: Optional[str] = None) -> str:
        """Save change report to file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"far_changes_{timestamp}.md"
        
        filepath = os.path.join(self.data_dir, filename)
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(report)
        
        print(f"Change report saved to: {filepath}")
        return filepath

def main():
    """Example usage of the change analyzer"""
    analyzer = FARChangeAnalyzer()
    
    # You would typically set your OpenAI API key here
    # analyzer = FARChangeAnalyzer(openai_api_key="your-api-key-here")
    
    # Example: Compare two versions
    old_file = "data/far_20240101_120000.json"  # Replace with actual file
    new_file = "data/far_latest.json"
    
    if os.path.exists(old_file) and os.path.exists(new_file):
        report = analyzer.compare_versions(old_file, new_file)
        report_file = analyzer.save_change_report(report)
        print(f"Change analysis complete. Report saved to: {report_file}")
    else:
        print("Please ensure you have at least two FAR versions to compare.")
        print("Run the scraper first to collect FAR data.")

if __name__ == "__main__":
    main()
