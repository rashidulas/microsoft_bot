import requests
from bs4 import BeautifulSoup
import os
import json
import hashlib
from datetime import datetime
import re
from typing import Dict, List, Optional, Tuple

BASE_URL = "https://www.acquisition.gov"
INDEX_URL = f"{BASE_URL}/browse/index/far"

class FARScraper:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.version_file = os.path.join(data_dir, "far_versions.json")
        self.ensure_data_dir()
        
    def ensure_data_dir(self):
        """Create data directory if it doesn't exist"""
        os.makedirs(self.data_dir, exist_ok=True)
        
    def get_current_version_info(self) -> Dict:
        """Get current FAR version information from the main page"""
        print("Fetching current FAR version info...")
        res = requests.get(INDEX_URL)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")
        
        # Look for the FAC Number and Effective Date in the table
        version_info = {}
        
        # Find the table with version information
        table = soup.find("table")
        if table:
            rows = table.find_all("tr")
            for row in rows[1:]:  # Skip header row
                cells = row.find_all("td")
                if len(cells) >= 2:
                    fac_number = cells[0].get_text(strip=True)
                    effective_date = cells[1].get_text(strip=True)
                    if fac_number and effective_date:
                        version_info = {
                            "fac_number": fac_number,
                            "effective_date": effective_date,
                            "scraped_at": datetime.now().isoformat()
                        }
                        break
        
        return version_info
    
    def get_far_links(self) -> List[str]:
        """Get all FAR part links from the index page"""
        print("Fetching FAR index...")
        res = requests.get(INDEX_URL)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")
        
        # Find all links that point to FAR parts
        far_links = []
        
        # Look for links in the table that contain FAR parts
        for link in soup.find_all("a", href=True):
            href = link.get("href", "")
            if "/far/part-" in href:
                far_links.append(href)
        
        # Also check the FAR Parts menu section
        far_menu = soup.find("div", class_="far-parts-menu") or soup.find("div", id="far-parts")
        if far_menu:
            for link in far_menu.find_all("a", href=True):
                href = link.get("href", "")
                if "/far/part-" in href:
                    far_links.append(href)
        
        # Remove duplicates and return
        return list(set(far_links))
    
    def scrape_far_part(self, part_url: str) -> Dict:
        """Scrape a single FAR part"""
        full_url = BASE_URL + part_url if part_url.startswith("/") else part_url
        print(f"Fetching {full_url}")
        
        try:
            page = requests.get(full_url, timeout=30)
            page.raise_for_status()
            soup = BeautifulSoup(page.text, "html.parser")
            
            # Extract title
            title = soup.find("h1") or soup.find("title")
            title_text = title.get_text(strip=True) if title else part_url
            
            # Extract main content - try different selectors
            content_selectors = [
                "div.field-item",
                "article",
                "div.content",
                "main",
                "div.main-content"
            ]
            
            content = ""
            for selector in content_selectors:
                content_div = soup.select_one(selector)
                if content_div:
                    content = content_div.get_text(separator="\n", strip=True)
                    break
            
            # If no specific content found, get all text
            if not content:
                content = soup.get_text(separator="\n", strip=True)
            
            # Clean up content
            content = re.sub(r'\n\s*\n', '\n\n', content)  # Remove excessive newlines
            content = re.sub(r'\s+', ' ', content)  # Normalize whitespace
            
            return {
                "url": full_url,
                "title": title_text,
                "content": content,
                "scraped_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Error scraping {full_url}: {e}")
            return {
                "url": full_url,
                "title": f"Error: {part_url}",
                "content": f"Error scraping this part: {e}",
                "scraped_at": datetime.now().isoformat()
            }
    
    def scrape_all_far(self) -> Dict:
        """Scrape all FAR parts"""
        version_info = self.get_current_version_info()
        far_links = self.get_far_links()
        
        print(f"Found {len(far_links)} FAR parts to scrape")
        
        all_parts = {}
        for i, link in enumerate(far_links, 1):
            print(f"Scraping part {i}/{len(far_links)}: {link}")
            part_data = self.scrape_far_part(link)
            all_parts[link] = part_data
            
            # Add small delay to be respectful to the server
            import time
            time.sleep(1)
        
        # Combine all content
        full_text = f"# Federal Acquisition Regulation (FAR)\n"
        full_text += f"Version: {version_info.get('fac_number', 'Unknown')}\n"
        full_text += f"Effective Date: {version_info.get('effective_date', 'Unknown')}\n"
        full_text += f"Scraped: {version_info.get('scraped_at', 'Unknown')}\n\n"
        
        for part_url, part_data in all_parts.items():
            full_text += f"\n\n## {part_data['title']}\n"
            full_text += f"URL: {part_data['url']}\n\n"
            full_text += part_data['content']
        
        return {
            "version_info": version_info,
            "parts": all_parts,
            "full_text": full_text,
            "scraped_at": datetime.now().isoformat()
        }
    
    def save_far_data(self, far_data: Dict) -> str:
        """Save FAR data to files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save full text
        text_file = os.path.join(self.data_dir, f"far_{timestamp}.txt")
        with open(text_file, "w", encoding="utf-8") as f:
            f.write(far_data["full_text"])
        
        # Save structured data
        json_file = os.path.join(self.data_dir, f"far_{timestamp}.json")
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(far_data, f, indent=2, ensure_ascii=False)
        
        # Save as latest
        latest_text = os.path.join(self.data_dir, "far_latest.txt")
        latest_json = os.path.join(self.data_dir, "far_latest.json")
        
        with open(latest_text, "w", encoding="utf-8") as f:
            f.write(far_data["full_text"])
        
        with open(latest_json, "w", encoding="utf-8") as f:
            json.dump(far_data, f, indent=2, ensure_ascii=False)
        
        return text_file
    
    def load_previous_version(self) -> Optional[Dict]:
        """Load the previous version for comparison"""
        if not os.path.exists(self.version_file):
            return None
        
        try:
            with open(self.version_file, "r", encoding="utf-8") as f:
                versions = json.load(f)
            
            if versions and "latest" in versions:
                latest_file = versions["latest"]
                if os.path.exists(latest_file):
                    with open(latest_file, "r", encoding="utf-8") as f:
                        return json.load(f)
        except Exception as e:
            print(f"Error loading previous version: {e}")
        
        return None
    
    def update_version_tracking(self, new_data: Dict, file_path: str):
        """Update version tracking file"""
        versions = {}
        
        if os.path.exists(self.version_file):
            try:
                with open(self.version_file, "r", encoding="utf-8") as f:
                    versions = json.load(f)
            except:
                versions = {}
        
        version_info = new_data["version_info"]
        fac_number = version_info.get("fac_number", "unknown")
        
        if "versions" not in versions:
            versions["versions"] = []
        
        versions["versions"].append({
            "fac_number": fac_number,
            "effective_date": version_info.get("effective_date"),
            "file_path": file_path,
            "scraped_at": version_info.get("scraped_at")
        })
        
        versions["latest"] = file_path
        
        with open(self.version_file, "w", encoding="utf-8") as f:
            json.dump(versions, f, indent=2)
    
    def run_scrape(self) -> str:
        """Main method to run the scraping process"""
        print("Starting FAR scraping process...")
        
        # Check if we need to scrape (compare versions)
        current_version = self.get_current_version_info()
        previous_data = self.load_previous_version()
        
        if previous_data:
            prev_version = previous_data["version_info"]
            if (current_version.get("fac_number") == prev_version.get("fac_number") and 
                current_version.get("effective_date") == prev_version.get("effective_date")):
                print("FAR version hasn't changed. Skipping scrape.")
                return os.path.join(self.data_dir, "far_latest.txt")
        
        # Scrape new data
        far_data = self.scrape_all_far()
        
        # Save data
        file_path = self.save_far_data(far_data)
        
        # Update version tracking
        self.update_version_tracking(far_data, file_path)
        
        print(f"FAR scraping completed. Data saved to: {file_path}")
        return file_path

def main():
    scraper = FARScraper()
    result_file = scraper.run_scrape()
    print(f"FAR data saved to: {result_file}")

if __name__ == "__main__":
    main()
