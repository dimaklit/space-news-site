# AstroTrack AI Advanced Scraper - v1.3.0 (2026)
import xml.etree.ElementTree as ET
import urllib.request
import urllib.parse
import json
import re
import time
import os
import http.client
from datetime import datetime

# Настройка стабильных источников новостей
NEWS_SOURCES = [
    {"name": "NASA", "url": "https://www.nasa.gov/rss/dyn/breaking_news.rss"},
    {"name": "SpaceX", "url": "https://spaceflightnow.com/category/falcon-9/feed/"}, 
    {"name": "ESA", "url": "https://www.esa.int/rssfeed/Our_Activities/Space_News"},
    {"name": "Spaceflight Now", "url": "https://spaceflightnow.com/feed/"}
]

LAUNCHES_URL = "https://lldev.thespacedevs.com/2.2.0/launch/upcoming/?limit=5"
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

def process_batch_with_gemini(batch_items):
    """Отправляет пачку из нескольких новостей в Gemini одним запросом для обхода лимитов 15 RPM"""
    clean_key = GEMINI_API_KEY.strip() if GEMINI_API_KEY else ""
    if not clean_key:
        print("Предупреждение: API ключ GEMINI_API_KEY не найден.")
        return None

    # Формируем компактный список для ИИ
    input_list = []
    for item in batch_items:
        input_list.append({
            "id": item["id"],
            "title": item["title_en"],
            "summary": item["summary_en"]
        })

    prompt = f"""
You are an expert space journalist and STEM educator. Translate and adapt the following list of space news articles.
For each article in the list, provide translations and adaptations.

Input list:
{json.dumps(input_list, ensure_ascii=False)}

You must return a raw JSON array of objects (do not include markdown block ticks ```json or any prose). Each object must have exactly these keys:
{{
  "id": (match the ID from input),
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
        conn = http.client.HTTPSConnection(host, timeout=30)
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
        print(f"Ошибка обращения к Gemini API в батче: {e}")
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
    print("=== Запуск ИИ-Батч-Сборщика AstroTrack v1.3.0 ===")
    raw_articles = []
    global_id = 1

    # Шаг 1: Собираем все сырые новости со всех лент
    for source in NEWS_SOURCES:
        print(f"Скачиваем ленту {source['name']}...")
        try:
            req = urllib.request.Request(source['url'], headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as response:
                xml_data = response.read()
        except Exception as e:
            print(f"Не удалось скачать ленту {source['name']}: {e}")
            continue

        try:
            root = ET.fromstring(xml_data)
            # ТЕПЕРЬ БЕРЕМ ПО 10 СВЕЖИХ НОВОСТЕЙ
            items = root.findall('.//item')[:10]
            
            for item in items:
                title_en = item.find('title').text if item.find('title') is not None else ""
                summary_en = item.find('description').text if item.find('description') is not None else ""
                link = item.find('link').text if item.find('link') is not None else ""
                pub_date = item.find('pubDate').text if item.find('pubDate') is not None else ""
                
                summary_en = re.sub('<[^<]+?>', '', summary_en).strip()
                if len(summary_en) > 350:
                    summary_en = summary_en[:347] + "..."

                raw_articles.append({
                    "id": global_id,
                    "source": source['name'],
                    "date_parsed": parse_rfc2822_date(pub_date).isoformat(),
                    "date_display": pub_date,
                    "link": link,
                    "title_en": title_en,
                    "summary_en": summary_en
                })
                global_id += 1
        except Exception as parse_err:
            print(f"Ошибка парсинга XML для {source['name']}: {parse_err}")

    print(f"\nВсего собрано {len(raw_articles)} новостей. Начинаем ИИ-обработку пачками...")

    # Шаг 2: Делим массив новостей на батчи по 4 штуки и отправляем в Gemini
    final_articles = []
    batch_size = 4
    
    for i in range(0, len(raw_articles), batch_size):
        batch = raw_articles[i:i + batch_size]
        print(f" -> Отправка в Gemini пачки новостей с ID {batch[0]['id']} по {batch[-1]['id']}...")
        
        ai_responses = process_batch_with_gemini(batch)
        
        # Безопасная пауза между пачками (всего 10-12 запросов, лимит RPM никогда не сработает)
        time.sleep(6.0)

        # Сопоставляем ответы ИИ с метаданными новостей
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
                    "title_he": ai_data.get("title_he", raw_item["title_en"]),
                    "summary_he": ai_data.get("summary_he", raw_item["summary_en"]),
                    "title_he_kids": ai_data.get("title_he_kids", raw_item["title_en"]),
                    "summary_he_kids": ai_data.get("summary_he_kids", raw_item["summary_en"])
                })
            else:
                # Если пачка упала — пишем заглушку
                raw_item.update({
                    "title_ru": raw_item["title_en"], "summary_ru": raw_item["summary_en"],
                    "title_ru_kids": raw_item["title_en"], "summary_ru_kids": raw_item["summary_en"],
                    "title_he": raw_item["title_en"], "summary_he": raw_item["summary_en"],
                    "title_he_kids": raw_item["title_en"], "summary_he_kids": raw_item["summary_en"]
                })
            final_articles.append(raw_item)

    # Сортировка по свежести
    final_articles.sort(key=lambda x: x['date_parsed'], reverse=True)

    with open("news.json", "w", encoding="utf-8") as f:
        json.dump(final_articles, f, ensure_ascii=False, indent=2)
    print(f"\nУспешно сохранено {len(final_articles)} новостей в news.json!")
    
    fetch_launches()

if __name__ == "__main__":
    main()
