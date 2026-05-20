# AstroTrack Ultimate Resilient AI Scraper - v2.1.0 (2026)
import xml.etree.ElementTree as ET
import urllib.request
import json
import re
import time
import os
import http.client
from datetime import datetime

# Источники новостей
NEWS_SOURCES = [
    {"name": "NASA", "url": "https://www.nasa.gov/rss/dyn/breaking_news.rss"},
    {"name": "SpaceX", "url": "https://spaceflightnow.com/category/falcon-9/feed/"}, 
    {"name": "ESA", "url": "https://www.esa.int/rssfeed/Our_Activities/Space_News"},
    {"name": "Spaceflight Now", "url": "https://spaceflightnow.com/feed/"}
]

LAUNCHES_URL = "https://lldev.thespacedevs.com/2.2.0/launch/upcoming/?limit=5"
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

def ask_gemini_with_retry(title, summary, max_retries=3):
    """Запрашивает перевод у ИИ с автоматическим повтором при ошибках 429, 503 или таймаутах"""
    clean_key = GEMINI_API_KEY.strip() if GEMINI_API_KEY else ""
    if not clean_key:
        return None

    prompt = f"""
You are an expert space journalist and STEM educator. Translate and adapt the following space news article.
Title: {title}
Summary: {summary}

You must return a raw JSON object (NO markdown ticks, NO prose). Keys:
{{
  "title_ru": "Точный профессиональный перевод заголовка на русский",
  "summary_ru": "Точный перевод описания на русский для взрослых",
  "title_ru_kids": "Увлекательный заголовок на русском для детей 8-12 лет с эмодзи",
  "summary_ru_kids": "Простой пересказ новости на русском для детей с метафорами и эмодзи",
  "title_he": "Точный перевод заголовка на иврит",
  "summary_he": "Точный перевод описания на иврит для взрослых",
  "title_he_kids": "Адаптированный заголовок на иврите для детей с эмодзи",
  "summary_he_kids": "Простой пересказ новости на иврите для детей с эмодзи"
}}
"""
    host = "generativelanguage.googleapis.com"
    path = f"/v1beta/models/gemini-2.5-flash:generateContent?key={clean_key}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json", "temperature": 0.3}
    }
    data_bytes = json.dumps(payload).encode("utf-8")

    for attempt in range(max_retries):
        try:
            conn = http.client.HTTPSConnection(host, timeout=25)
            headers = {"Content-Type": "application/json"}
            conn.request("POST", path, body=data_bytes, headers=headers)
            
            response = conn.getresponse()
            raw_data = response.read().decode("utf-8")
            conn.close()
            
            if response.status == 200:
                res_json = json.loads(raw_data)
                return json.loads(res_json['candidates'][0]['content']['parts'][0]['text'].strip())
            elif response.status in [429, 503]:
                print(f"   [!] API вернул статус {response.status}. Попытка {attempt+1}/{max_retries}. Ожидаем 20 секунд...")
                time.sleep(20.0)
            else:
                print(f"   [!] Ошибка API {response.status}. Повтор через 5 секунд...")
                time.sleep(5.0)
        except Exception as e:
            print(f"   [!] Сбой соединения ({e}). Попытка {attempt+1}/{max_retries}. Ожидаем 15 секунд...")
            time.sleep(15.0)
            
    return None

def parse_rfc2822_date(date_str):
    try:
        date_str = date_str.split(', ')[1] if ', ' in date_str else date_str
        date_clean = re.sub(r'\s[A-Z]{3,4}$|\s\+[0-9]{4}$', '', date_str)
        return datetime.strptime(date_clean, "%d %b %Y %H:%M:%S")
    except:
        return datetime.now()

def main():
    print("=== Запуск Сверхнадежного ИИ-Сборщика AstroTrack v2.1.0 ===")
    raw_articles = []

    # Скачиваем по 3 главные новости
    for source in NEWS_SOURCES:
        print(f"Скачиваем ленту {source['name']}...")
        try:
            req = urllib.request.Request(source['url'], headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as response:
                xml_data = response.read()
            
            root = ET.fromstring(xml_data)
            items = root.findall('.//item')[:3]
            
            for item in items:
                title_en = item.find('title').text if item.find('title') is not None else ""
                summary_en = item.find('description').text if item.find('description') is not None else ""
                link = item.find('link').text if item.find('link') is not None else ""
                pub_date = item.find('pubDate').text if item.find('pubDate') is not None else ""
                
                summary_en = re.sub('<[^<]+?>', '', summary_en).strip()
                if len(summary_en) > 280:
                    summary_en = summary_en[:277] + "..."

                raw_articles.append({
                    "source": source['name'],
                    "date_parsed": parse_rfc2822_date(pub_date).isoformat(),
                    "date_display": pub_date, "link": link,
                    "title_en": title_en, "summary_en": summary_en
                })
        except Exception as e:
            print(f"Ошибка источника {source['name']}: {e}")

    print(f"\nСобрано {len(raw_articles)} главных новостей. Начинаем бронебойный ИИ-перевод...")

    final_articles = []
    for idx, raw_item in enumerate(raw_articles):
        print(f" -> [{idx+1}/{len(raw_articles)}] Перевод через ИИ: {raw_item['title_en'][:40]}...")
        
        # Запускаем функцию с автоповтором внутри
        ai_data = ask_gemini_with_retry(raw_item['title_en'], raw_item['summary_en'])
        
        # Базовая вежливая пауза между успешными статьями
        time.sleep(4.5)
        
        if ai_data:
            raw_item.update({
                "title_ru": ai_data.get("title_ru", raw_item["title_en"]),
                "summary_ru": ai_data.get("summary_ru", raw_item["summary_en"]),
                "title_ru_kids": ai_data.get("title_ru_kids", raw_item["title_en"]),
                "summary_ru_kids": ai_data.get("summary_ru_kids", raw_item["summary_en"]),
                "title_he": ai_data.get("title_he", raw_item["title_en"]),
                "summary_he": ai_data.get("summary_he", raw_item["summary_en"]),
                "title_he_kids": ai_data.get("title_he_kids", raw_item["title_en"]),
                "summary_he_kids": ai_data.get("summary_he_kids", raw_item["summary_en"])
            })
        else:
            # Жесткий fallback, если все 3 попытки сгорели
            raw_item.update({
                "title_ru": raw_item["title_en"], "summary_ru": raw_item["summary_en"],
                "title_ru_kids": raw_item["title_en"], "summary_ru_kids": raw_item["summary_en"],
                "title_he": raw_item["title_en"], "summary_he": raw_item["summary_en"],
                "title_he_kids": raw_item["title_en"], "summary_he_kids": raw_item["summary_en"]
            })
        final_articles.append(raw_item)

    # Сортировка по свежести
    final_articles.sort(key=lambda x: x['date_parsed'], reverse=True)
    for idx, article in enumerate(final_articles):
        article["id"] = idx + 1

    with open("news.json", "w", encoding="utf-8") as f:
        json.dump(final_articles, f, ensure_ascii=False, indent=2)
    print(f"\nУспешно сохранено {len(final_articles)} ИИ-новостей!")

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
