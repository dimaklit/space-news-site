# AstroTrack AI Backend Scraper - v1.2.0 (2026)
import xml.etree.ElementTree as ET
import urllib.request
import urllib.parse
import json
import re
import time
import os
import http.client
from datetime import datetime

# Настройка источников новостей
NEWS_SOURCES = [
    {"name": "NASA", "url": "https://www.nasa.gov/rss/dyn/breaking_news.rss"},
    # ЗАМЕНИЛИ СТАРЫЙ БЛОГ NASA НА СВЕЖИЙ И СТАБИЛЬНЫЙ ФИД SPACEX
    {"name": "SpaceX", "url": "https://spaceflightnow.com/category/falcon-9/feed/"}, 
    {"name": "ESA", "url": "https://www.esa.int/rssfeed/Our_Activities/Space_News"},
    {"name": "Spaceflight Now", "url": "https://spaceflightnow.com/feed/"}
]

LAUNCHES_URL = "https://lldev.thespacedevs.com/2.2.0/launch/upcoming/?limit=5"

# Получаем API ключ из переменных окружения GitHub
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

def ask_gemini_ai(title, summary):
    """Отправляет новость в Gemini Flash через http.client для перевода и детской адаптации"""
    clean_key = GEMINI_API_KEY.strip() if GEMINI_API_KEY else ""
    
    if not clean_key:
        print("Предупреждение: API ключ GEMINI_API_KEY не найден. Возвращаем базовый текст.")
        return None

    prompt = f"""
You are an expert space journalist and STEM educator. Translate and adapt the following space news article.
Title: {title}
Summary: {summary}

You must return a raw JSON object with exactly these keys (do not include markdown block ticks ```json or any prose):
{{
  "title_ru": "Точный перевод заголовка на русский",
  "summary_ru": "Точный перевод описания на русский для взрослой аудитории",
  "title_ru_kids": "Упрощенный заголовок на русском для детей 8-12 лет с эмодзи",
  "summary_ru_kids": "Адаптированный пересказ новости на русском для детей простыми словами с эмодзи",
  "title_he": "Точный перевод заголовка на иврит",
  "summary_he": "Точный перевод описания на иврит для взрослых",
  "title_he_kids": "Адаптированный заголовок на иврите для детей",
  "summary_he_kids": "Адаптированный пересказ новости на иврите для детей простыми словами с эмодзи"
}}
"""
    
    host = "generativelanguage.googleapis.com"
    path = f"/v1beta/models/gemini-2.5-flash:generateContent?key={clean_key}"
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.3
        }
    }
    
    try:
        conn = http.client.HTTPSConnection(host, timeout=15)
        data_bytes = json.dumps(payload).encode("utf-8")
        
        headers = {"Content-Type": "application/json"}
        conn.request("POST", path, body=data_bytes, headers=headers)
        
        response = conn.getresponse()
        raw_data = response.read().decode("utf-8")
        conn.close()
        
        if response.status == 200:
            res_json = json.loads(raw_data)
            text_response = res_json['candidates'][0]['content']['parts'][0]['text']
            return json.loads(text_response.strip())
        else:
            print(f"Gemini API вернул статус {response.status}: {raw_data[:200]}")
            return None
            
    except Exception as e:
        print(f"Ошибка обращения к Gemini API через http.client: {e}")
        return None

def parse_rfc2822_date(date_str):
    try:
        date_str = date_str.split(', ')[1] if ', ' in date_str else date_str
        date_clean = re.sub(r'\s[A-Z]{3,4}$|\s\+[0-9]{4}$', '', date_str)
        return datetime.strptime(date_clean, "%d %b %Y %H:%M:%S")
    except:
        return datetime.now()

def fetch_launches():
    print("\nСбор расписания космических пусков...")
    try:
        req = urllib.request.Request(LAUNCHES_URL, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode('utf-8'))
            launches = []
            for item in data.get('results', []):
                launches.append({
                    "name_en": item.get('name', 'Unknown Mission'),
                    "window_start": item.get('window_start'),
                    "rocket": item.get('rocket', {}).get('configuration', {}).get('full_name', ''),
                    "pad": item.get('pad', {}).get('name', ''),
                    "location": item.get('pad', {}).get('location', {}).get('name', '')
                })
            
            with open("launches.json", "w", encoding="utf-8") as f:
                json.dump(launches, f, ensure_ascii=False, indent=2)
            print("Расписание пусков сохранено.")
    except Exception as e:
        print(f"Ошибка сбора пусков: {e}")
        with open("launches.json", "w", encoding="utf-8") as f:
            json.dump([], f)

def main():
    print("=== Запуск ИИ-сборщика AstroTrack Core v1.2.0 ===")
    all_articles = []

    for source in NEWS_SOURCES:
        print(f"\nСкачиваем ленту {source['name']}...")
        try:
            req = urllib.request.Request(source['url'], headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as response:
                xml_data = response.read()
        except Exception as e:
            print(f"Не удалось скачать ленту {source['name']}: {e}")
            continue

        try:
            root = ET.fromstring(xml_data)
            # Берем по 3 свежие новости из каждого источника
            items = root.findall('.//item')[:3]
            
            for item in items:
                title_en = item.find('title').text if item.find('title') is not None else ""
                summary_en = item.find('description').text if item.find('description') is not None else ""
                link = item.find('link').text if item.find('link') is not None else ""
                pub_date = item.find('pubDate').text if item.find('pubDate') is not None else ""
                
                summary_en = re.sub('<[^<]+?>', '', summary_en).strip()
                if len(summary_en) > 400:
                    summary_en = summary_en[:397] + "..."

                print(f" -> Обработка через ИИ Gemini: {title_en[:40]}...")
                
                # Запрос к нейросети
                ai_data = ask_gemini_ai(title_en, summary_en)
                
                # Делаем паузу в 4.5 секунды для обхода лимитов бесплатного API
                time.sleep(4.5)
                
                if ai_data:
                    article = {
                        "source": source['name'],
                        "date_parsed": parse_rfc2822_date(pub_date).isoformat(),
                        "date_display": pub_date,
                        "link": link,
                        "title_en": title_en,
                        "summary_en": summary_en,
                        "title_ru": ai_data.get("title_ru", title_en),
                        "summary_ru": ai_data.get("summary_ru", summary_en),
                        "title_ru_kids": ai_data.get("title_ru_kids", title_en),
                        "summary_ru_kids": ai_data.get("summary_ru_kids", summary_en),
                        "title_he": ai_data.get("title_he", title_en),
                        "summary_he": ai_data.get("summary_he", summary_en),
                        "title_he_kids": ai_data.get("title_he_kids", title_en),
                        "summary_he_kids": ai_data.get("summary_he_kids", summary_en)
                    }
                else:
                    article = {
                        "source": source['name'],
                        "date_parsed": parse_rfc2822_date(pub_date).isoformat(),
                        "date_display": pub_date,
                        "link": link,
                        "title_en": title_en, "summary_en": summary_en,
                        "title_ru": title_en, "summary_ru": summary_en,
                        "title_ru_kids": title_en, "summary_ru_kids": summary_en,
                        "title_he": title_en, "summary_he": summary_en,
                        "title_he_kids": title_en, "summary_he_kids": summary_en
                    }
                
                all_articles.append(article)
                
        except Exception as parse_err:
            print(f"Ошибка парсинга XML для {source['name']}: {parse_err}")

    # Сортировка по времени
    all_articles.sort(key=lambda x: x['date_parsed'], reverse=True)

    for idx, article in enumerate(all_articles):
        article["id"] = idx + 1

    with open("news.json", "w", encoding="utf-8") as f:
        json.dump(all_articles, f, ensure_ascii=False, indent=2)
    print(f"\nУспешно сохранено {len(all_articles)} ИИ-новостей в news.json")
    
    fetch_launches()

if __name__ == "__main__":
    main()
