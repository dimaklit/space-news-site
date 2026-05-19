# AstroTrack Multi-Lang Heavy Duty Scraper - v1.6.0 (2026)
import xml.etree.ElementTree as ET
import urllib.request
import urllib.parse
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

def process_batch_with_hard_retry(batch_items, max_retries=5):
    """Отправляет пачку из 4 новостей и принудительно пробивает 429 ошибку через 70 сек ожидания"""
    clean_key = GEMINI_API_KEY.strip() if GEMINI_API_KEY else ""
    if not clean_key:
        return None

    input_list = [{"id": item["id"], "title": item["title_en"], "summary": item["summary_en"]} for item in batch_items]

    prompt = f"""
You are an expert space journalist and STEM educator. Translate and adapt the following list of space news articles.
Return a raw JSON array of objects (no markdown ticks, no prose). Each object must have exactly these keys:
{{
  "id": (match the ID from input),
  "title_ru": "Точный перевод заголовка на русский",
  "summary_ru": "Точный перевод описания на русский для взрослой аудитории",
  "title_ru_kids": "Упрощенный заголовок на русском для детей 8-12 лет с эмодзи",
  "summary_ru_kids": "Адаптированный пересказ новости на русском для детей простыми словами с эмодзи",
  "title_he": "Точный перевод заголовка на иврит",
  "summary_he": "Точный перевод описания на иврит для взрослых",
  "title_he_kids": "Адаптированный заголовок на иврите для детей с эмодзи",
  "summary_he_kids": "Адаптированный пересказ новости на иврите для детей простыми словами с эмодзи"
}}

Input list:
{json.dumps(input_list, ensure_ascii=False)}
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
            conn = http.client.HTTPSConnection(host, timeout=40)
            headers = {"Content-Type": "application/json"}
            conn.request("POST", path, body=data_bytes, headers=headers)
            
            response = conn.getresponse()
            raw_data = response.read().decode("utf-8")
            conn.close()
            
            if response.status == 200:
                res_json = json.loads(raw_data)
                text_response = res_json['candidates'][0]['content']['parts'][0]['text']
                return json.loads(text_response.strip())
            
            elif response.status == 429:
                # Жесткий сброс лимитов: спим 70 секунд и пробуем эту же пачку заново
                print(f"   [!] Лимит тарифа (429). Попытка {attempt+1}/{max_retries}. Засыпаем на 70 секунд для очистки лимитов...")
                time.sleep(70.0)
            else:
                print(f"   [!] Ошибка API {response.status}. Повтор через 10 секунд...")
                time.sleep(10.0)
        except Exception as e:
            print(f"   [!] Сетевой сбой: {e}. Повтор через 10 seconds...")
            time.sleep(10.0)
            
    return None

def parse_rfc2822_date(date_str):
    try:
        date_str = date_str.split(', ')[1] if ', ' in date_str else date_str
        date_clean = re.sub(r'\s[A-Z]{3,4}$|\s\+[0-9]{4}$', '', date_str)
        return datetime.strptime(date_clean, "%d %b %Y %H:%M:%S")
    except:
        return datetime.now()

def main():
    print("=== Запуск Отказоустойчивого ИИ-Сборщика AstroTrack v1.6.0 ===")
    raw_articles = []
    global_id = 1

    # Сбор новостей
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
            items = root.findall('.//item')[:10] # По 10 штук с каждого фида
            
            for item in items:
                title_en = item.find('title').text if item.find('title') is not None else ""
                summary_en = item.find('description').text if item.find('description') is not None else ""
                link = item.find('link').text if item.find('link') is not None else ""
                pub_date = item.find('pubDate').text if item.find('pubDate') is not None else ""
                
                summary_en = re.sub('<[^<]+?>', '', summary_en).strip()
                if len(summary_en) > 300:
                    summary_en = summary_en[:297] + "..."

                raw_articles.append({
                    "id": global_id, "source": source['name'],
                    "date_parsed": parse_rfc2822_date(pub_date).isoformat(),
                    "date_display": pub_date, "link": link,
                    "title_en": title_en, "summary_en": summary_en
                })
                global_id += 1
        except Exception as parse_err:
            print(f"Ошибка XML {source['name']}: {parse_err}")

    print(f"\nВсего успешно собрано {len(raw_articles)} новостей. Начинаем пакетный ИИ-перевод...")

    final_articles = []
    batch_size = 4 # Оптимальный размер для баланса токенов
    
    for i in range(0, len(raw_articles), batch_size):
        batch = raw_articles[i:i + batch_size]
        print(f" -> Обработка пачки новостей с ID {batch[0]['id']} по {batch[-1]['id']}...")
        
        ai_responses = process_batch_with_hard_retry(batch)
        
        # Профилактическая пауза между успешными пачками
        time.sleep(10.0)

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
                "name_en": item.get('name', 'Unknown Mission'),
                "window_start": item.get('window_start'),
                "rocket": item.get('rocket', {}).get('configuration', {}).get('full_name', ''),
                "pad": item.get('pad', {}).get('name', ''),
                "location": item.get('pad', {}).get('location', {}).get('name', '')
            } for item in data.get('results', [])]
            with open("launches.json", "w", encoding="utf-8") as f:
                json.dump(launches, f, ensure_ascii=False, indent=2)
    except:
        with open("launches.json", "w", encoding="utf-8") as f: json.dump([], f)

if __name__ == "__main__":
    main()
