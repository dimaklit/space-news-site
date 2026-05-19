import xml.etree.ElementTree as ET
import urllib.request
import urllib.parse
import json
import re
import time
from datetime import datetime

# News source configurations for AstroTrack
NEWS_SOURCES = [
    {"name": "NASA", "url": "https://www.nasa.gov/rss/dyn/breaking_news.rss"},
    {"name": "SpaceX", "url": "https://blogs.nasa.gov/spacex/feed/"},
    {"name": "ESA", "url": "https://www.esa.int/rssfeed/Our_Activities/Space_News"},
    {"name": "Spaceflight Now", "url": "https://spaceflightnow.com/feed/"}
]

LAUNCHES_URL = "https://lldev.thespacedevs.com/2.2.0/launch/upcoming/?limit=5"

def translate_text(text, target_lang):
    if not text:
        return ""
    try:
        # Unlimited Google Translate Web API endpoint
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl={target_lang}&dt=t&q={urllib.parse.quote(text)}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            translated_parts = [part[0] for part in data[0] if part[0]]
            return "".join(translated_parts)
    except Exception as e:
        print(f"Translation error to {target_lang}: {e}")
    return text

def get_difficulty(title, summary):
    text = f"{title} {summary}".lower()
    if re.search(r'(авар|катастроф|крушен|взрыв|fail|crash|explod)', text):
        return "accident"
    if re.search(r'(двигател|топлив|тяга|орбит|траектор|термодинам|ионн|плазм|engine|orbit|propulsion|thruster)', text):
        return "pro"
    if re.search(r'(урок|методич|учит|класс|школ|задан|проект|lesson|teacher|school|class)', text):
        return "teacher"
    return "novice"

def parse_rfc2822_date(date_str):
    try:
        # Clean standard RSS format strings for datetime sorting
        date_str = date_str.split(', ')[1] if ', ' in date_str else date_str
        date_clean = re.sub(r'\s[A-Z]{3,4}$|\s\+[0-9]{4}$', '', date_str)
        return datetime.strptime(date_clean, "%d %b %Y %H:%M:%S")
    except:
        return datetime.now()

def fetch_launches():
    print("\nFetching upcoming space launches...")
    try:
        req = urllib.request.Request(LAUNCHES_URL, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode('utf-8'))
            launches = []
            for item in data.get('results', []):
                name_en = item.get('name', 'Unknown Mission')
                launches.append({
                    "name_en": name_en,
                    "name_ru": translate_text(name_en, "ru"),
                    "name_he": translate_text(name_en, "he"),
                    "window_start": item.get('window_start'),
                    "rocket": item.get('rocket', {}).get('configuration', {}).get('full_name', ''),
                    "pad": item.get('pad', {}).get('name', ''),
                    "location": item.get('pad', {}).get('location', {}).get('name', '')
                })
                time.sleep(0.5)
            
            with open("launches.json", "w", encoding="utf-8") as f:
                json.dump(launches, f, ensure_ascii=False, indent=2)
            print("Launch calendar successfully saved to launches.json")
    except Exception as e:
        print(f"Error fetching launch schedules: {e}")
        with open("launches.json", "w", encoding="utf-8") as f:
            json.dump([], f)

def main():
    print("=== Starting AstroTrack Global Scraper Core ===")
    all_articles = []

    for source in NEWS_SOURCES:
        print(f"\nPulling latest feed from {source['name']}...")
        try:
            req = urllib.request.Request(source['url'], headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as response:
                xml_data = response.read()
        except Exception as e:
            print(f"Failed to fetch {source['name']} feed: {e}")
            continue

        try:
            root = ET.fromstring(xml_data)
            # Retrieve 3 recent news articles from each source
            items = root.findall('.//item')[:3]
            
            for item in items:
                title_en = item.find('title').text if item.find('title') is not None else ""
                summary_en = item.find('description').text if item.find('description') is not None else ""
                link = item.find('link').text if item.find('link') is not None else ""
                pub_date = item.find('pubDate').text if item.find('pubDate') is not None else ""
                
                # Strip raw HTML blocks from description strings
                summary_en = re.sub('<[^<]+?>', '', summary_en).strip()
                if len(summary_en) > 300:
                    summary_en = summary_en[:297] + "..."

                print(f" -> Translating [{source['name']}]: {title_en[:30]}...")
                
                title_ru = translate_text(title_en, "ru")
                summary_ru = translate_text(summary_en, "ru")
                time.sleep(0.5)
                
                title_he = translate_text(title_en, "he")
                summary_he = translate_text(summary_en, "he")
                time.sleep(0.5)
                
                difficulty = get_difficulty(title_ru, summary_ru)
                parsed_date = parse_rfc2822_date(pub_date)
                
                all_articles.append({
                    "source": source['name'],
                    "date_parsed": parsed_date.isoformat(),
                    "date_display": pub_date,
                    "link": link,
                    "difficulty": difficulty,
                    "title_en": title_en,
                    "summary_en": summary_en,
                    "title_ru": title_ru,
                    "summary_ru": summary_ru,
                    "title_he": title_he,
                    "summary_he": summary_he
                })
        except Exception as parse_err:
            print(f"XML Parsing structural failure for {source['name']}: {parse_err}")

    # Sort comprehensively by time parameters (newest first)
    all_articles.sort(key=lambda x: x['date_parsed'], reverse=True)

    # Re-index unique identifiers for clean mapping
    for idx, article in enumerate(all_articles):
        article["id"] = idx + 1

    with open("news.json", "w", encoding="utf-8") as f:
        json.dump(all_articles, f, ensure_ascii=False, indent=2)
    print(f"\nSuccess! Sorted and structured {len(all_articles)} total items in news.json")
    
    # Cascade directly into live launcher data pull
    fetch_launches()

if __name__ == "__main__":
    main()
