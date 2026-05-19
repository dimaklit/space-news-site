# AstroTrack Optimized Multi-Lang Scraper - v1.7.0 (2026)
import xml.etree.ElementTree as ET
import urllib.request
import urllib.parse
import json
import re
import time
import os
import http.client
from datetime import datetime

# Источники новостей (по 10 статей)
NEWS_SOURCES = [
    {"name": "NASA", "url": "https://www.nasa.gov/rss/dyn/breaking_news.rss"},
    {"name": "SpaceX", "url": "https://spaceflightnow.com/category/falcon-9/feed/"}, 
    {"name": "ESA", "url": "https://www.esa.int/rssfeed/Our_Activities/Space_News"},
    {"name": "Spaceflight Now", "url": "https://spaceflightnow.com/feed/"}
]

LAUNCHES_URL = "https://lldev.thespacedevs.com/2.2.0/launch/upcoming/?limit=5"
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

def process_batch_optimized(batch_items):
    """Переводит пачку новостей. Объем токенов урезан в 3 раза для стабильности Free Tier"""
    clean_key = GEMINI_API_KEY.strip() if GEMINI_API_KEY else ""
    if not clean_key:
        return None

    input_list = [{"id": item["id"], "title": item["title_en"], "summary": item["summary_en"]} for item in batch_items]

    prompt = f"""
You are a space journalist. Translate and adapt these space news articles.
Return a raw JSON array of objects (NO markdown, NO prose). Keys:
- "id" (must match input ID)
- "title_ru" (professional Russian translation)
- "summary_ru" (professional Russian summary)
- "title_ru_kids" (engaging Russian title with emojis for kids)
- "summary_ru_kids" (simple Russian summary with metaphors and emojis for kids)
- "title_he" (professional Hebrew translation)
- "summary_he" (professional Hebrew summary)

Input list:
{json.dumps(input_list, ensure_ascii=False)}
"""
    
    host = "generativelanguage.googleapis.com"
    path = f"/v1beta/models/gemini-2.5-flash:generateContent?key={clean_key}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json", "temperature": 0.2}
    }
    
    try:
        conn = http.client.HTTPSConnection(host, timeout=30)
        data_bytes = json.dumps(payload).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        conn.request("POST", path, body=data_bytes, headers=headers)
        
        response = conn.getresponse()
        raw_data = response.read().decode("utf-8")
        conn.close()
        
        if response.status == 200:
            res_json = json.loads(raw_data)
            return json.loads(res_json['candidates'][0]['content']['parts'][0]['text'].strip())
        elif response.status == 429:
            print("   [!] Ограничение лимита токенов (429). Засыпаем на 45 секунд...")
            time.sleep(45.0)
            return None
        else:
            return None
    except:
        return None

def parse_rfc2822_date(date_str):
    try:
        date_str = date_str.split(', ')[1] if ', ' in date_str else date_str
        date_clean = re.sub(r'\s[A-Z]{3,4}$|\s\+[0-9]{4}$', '', date_str)
        return datetime.strptime(date_clean, "%d %b %Y %H:%M:%S")
    except:
        return datetime.now()

def main():
    print("=== Запуск Оптимизированного Сборщика AstroTrack v1.7.0 ===")
    raw_articles = []
    global_id = 1

    for source in NEWS_SOURCES:
        print(f"Скачиваем ленту {source['name']}...")
        try:
            req = urllib.request.Request(source['url'], headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as response:
                xml_data = response.read()
        except:
            continue

        try:
            root = ET.fromstring(xml_data)
            items = root.findall('.//item')[:10]
            
            for item in items:
                title_en = item.find('title').text if item.find('title') is not None else ""
                summary_en = item.find('description').text if item.find('description') is not None else ""
                link = item.find('link').text if item.find('link') is not None else ""
                pub_date = item.find('pubDate').text if item.find('pubDate') is not None else ""
                
                summary_en = re.sub('<[^<]+?>', '', summary_en).strip()
                if len(summary_en) > 280:
                    summary_en = summary_en[:277] + "..."

                raw_articles.append({
                    "id": global_id, "source": source['name'],
                    "date_parsed": parse_rfc2822_date(pub_date).isoformat(),
                    "date_display": pub_date, "link": link,
                    "title_en": title_en, "summary_en": summary_en
                })
                global_id += 1
        except:
            pass

    print(f"\nСобрано {len(raw_articles)} новостей. Запуск ИИ-обработки оптимальными пачками...")

    final_articles = []
    batch_size = 4
    
    for i in range(0, len(raw_articles), batch_size):
        batch = raw_articles[i:i + batch_size]
        print(f" -> Обработка пачки новостей с ID {batch[0]['id']} по {batch[-1]['id']}...")
        
        ai_responses = process_batch_optimized(batch)
        
        # Если пачка упала из-за лимита токенов, пробуем еще один раз после паузы
        if ai_responses is None:
            print("   [!] Повторная отправка пачки...")
            ai_responses = process_batch_optimized(batch)
            
        time.sleep(6.0)

        for raw_item in batch:
            ai_data = None
            if ai_responses and isinstance(ai_responses, list):
                ai_data = next((res for res in ai_responses if res.get("id") == raw_item["id"]), None)
            
            if ai_data:
                raw_item.update({
                    "title_ru": ai_data.get("title_ru", raw_item["title_en"]),
                    "summary_ru": ai_data.get("summary_ru", raw_item["summary_en"]),
                    "title_ru_kids": ai_data.get("title_ru_kids", raw_item["title_en"]),
                    "summary_ru_kids": ai_data.get("summary_ru_kids", raw_item["summary_en"]),
                    # На иврите используем один качественный перевод для обеих версий сайта
                    "title_he": ai_data.get("title_he", raw_item["title_en"]),
                    "summary_he": ai_data.get("summary_he", raw_item["summary_en"]),
                    "title_he_kids": ai_data.get("title_he", raw_item["title_en"]),
                    "summary_he_kids": ai_data.get("summary_he", raw_item["summary_en"])
                })
            else:
                raw_item.update({
                    "title_ru": raw_item["title_en"], "summary_ru": raw_item["summary_en"],
                    "title_ru_kids": raw_item["title_en"], "summary_ru_kids": raw_item["summary_en"],
                    "title_he": raw_item["title_en"], "summary_he": raw_item["summary_en"],
                    "title_he_kids": raw_item["title_en"], "summary_he_kids": raw_item["summary_en"]
                })
            final_articles.append(raw_item)

    final_articles.sort(key=lambda x: x['date_parsed'], reverse=True)

    with open("news.json", "w", encoding="utf-8") as f:
        json.dump(final_articles, f, ensure_ascii=False, indent=2)
    print(f"\nУспешно сохранено {len(final_articles)} новостей в news.json!")
    
    # Сбор пусков
    try:
        req = urllib.request.Request(LAUNCHES_URL, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            launches = [{
                "name_en": item.get('name', 'Unknown Mission'), "window_start": item.get('window_start'),
                "rocket": item.get('rocket', {}).get('configuration', {}).get('full_name', ''),
                "pad": item.get('pad', {}).get('name', ''), "location": item.get('pad', {}).get('location', {}).get('name', '')
            } for item in data.get('results', [])]
            with open("launches.json", "w", encoding="utf-8") as f: json.dump(launches, f, ensure_ascii=False, indent=2)
    except:
        with open("launches.json", "w", encoding="utf-8") as f: json.dump([], f)

if __name__ == "__main__":
    main()
