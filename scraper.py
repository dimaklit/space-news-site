# AstroTrack Unique AI Illustration Scraper - v4.0.0 (2026)
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
    {"name": "SpaceX", "url": "https://spaceflightnow.com/category/falcon-9/feed/"}, 
    {"name": "ESA", "url": "https://www.esa.int/rssfeed/Our_Activities/Space_News"},
    {"name": "Spaceflight Now", "url": "https://spaceflightnow.com/feed/"}
]

LAUNCHES_URL = "https://lldev.thespacedevs.com/2.2.0/launch/upcoming/?limit=5"
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# Космическая заглушка, если генерация упадет
DEFAULT_IMAGE = "https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=600&auto=format&fit=crop"

def web_translate(text, target_lang):
    if not text.strip():
        return text
    try:
        encoded_text = urllib.parse.quote(text)
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl={target_lang}&dt=t&q={encoded_text}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            res_json = json.loads(response.read().decode('utf-8'))
            translated_parts = [part[0] for part in res_json[0] if part[0]]
            return "".join(translated_parts).strip()
    except:
        return text

def ask_gemini_for_image_prompt(title, summary):
    """Использует Gemini для генерации короткого английского промта для рисования"""
    clean_key = GEMINI_API_KEY.strip() if GEMINI_API_KEY else ""
    if not clean_key:
        return None

    # Промт для Gemini: сделай короткое, стилизованное описание для рисования
    prompt = f"""
Create a short, detailed, stylised artistic image generation prompt in English based on this space news:
Title: {title}
Summary: {summary}

Style: Sci-fi digital illustration, vibrant colors, cinematic lighting, epic composition.

Return only the prompt text, no quotes, no markdown, no prose. Be descriptive. Max 30 words.
"""
    host = "generativelanguage.googleapis.com"
    path = f"/v1beta/models/gemini-2.5-flash:generateContent?key={clean_key}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.5}
    }
    
    try:
        conn = http.client.HTTPSConnection(host, timeout=20)
        data_bytes = json.dumps(payload).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        conn.request("POST", path, body=data_bytes, headers=headers)
        
        response = conn.getresponse()
        raw_data = response.read().decode("utf-8")
        conn.close()
        
        if response.status == 200:
            res_json = json.loads(raw_data)
            text_response = res_json['candidates'][0]['content']['parts'][0]['text']
            return text_response.strip()
        else:
            print(f"   [!] Gemini API Error {response.status} during prompt generation")
            return None
    except Exception as e:
        print(f"   [!] Gemini Prompt Network Error: {e}")
        return None

def generate_unique_illustration(ai_prompt):
    """Использует бесплатный провайдер Stable Diffusion для генерации уникальной картинки"""
    if not ai_prompt:
        return DEFAULT_IMAGE
    
    # Стилизуем промт под единый арт-стиль
    stylized_prompt = f"{ai_prompt}. sci-fi art, digital illustration, vibrant, cosmic, highly detailed, sharp focus, artstation."
    
    try:
        # Используем бесплатный провайдер (пример: Pollinations, работает без ключа на Гитхабе)
        # Он отдает готовую картинку по URL
        encoded_prompt = urllib.parse.quote(stylized_prompt)
        image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}"
        
        # Pollinations отдает URL сразу, но картинка генерируется при первом запросе.
        # Чтобы GitHub Pages закэшировал картинку, мы её просто "трогаем"
        req = urllib.request.Request(image_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=30) as response:
            pass # Просто убедились, что запрос прошел
            
        return image_url
    except Exception as e:
        print(f"   [!] Ошибка генерации иллюстрации: {e}")
        return DEFAULT_IMAGE

def generate_kids_version(title, summary, lang):
    if lang == "ru":
        kids_title = f"🚀 Космические новости: {title} ✨"
        kids_summary = f"🌟 Привет, юный космонавт! Смотри, что произошло: {summary} 🪐 Как тебе такое путешествие? Это просто фантастика! 🔭🛰️"
    else:
        kids_title = f"🚀 חדשות החלל: {title} ✨"
        kids_summary = f"🌟 שלום אסטרונאוט צעיר! תראה מה קרה בחלל: {summary} 🪐 מדהים, נכון? 🔭🛰️"
    return kids_title, kids_summary

def parse_rfc2822_date(date_str):
    try:
        date_str = date_str.split(', ')[1] if ', ' in date_str else date_str
        date_clean = re.sub(r'\s[A-Z]{3,4}$|\s\+[0-9]{4}$', '', date_str)
        return datetime.strptime(date_clean, "%d %b %Y %H:%M:%S")
    except:
        return datetime.now()

def main():
    print("=== Запуск ИИ-Иллюстратора AstroTrack v4.0.0 ===")
    raw_articles = []

    # Собираем строго по 3 свежие новости, чтобы генерация не заняла вечность
    for source in NEWS_SOURCES:
        print(f"Скачиваем ленту {source['name']}...")
        try:
            req = urllib.request.Request(source['url'], headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as response:
                xml_data = response.read()
            
            root = ET.fromstring(xml_data)
            items = root.findall('.//item')[:3] # По 3 штуки!
            
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
        except:
            continue

    print(f"\nСобрано {len(raw_articles)} новостей. Запуск ИИ-Иллюстрирования (это займет время)...")

    final_articles = []
    for idx, raw_item in enumerate(raw_articles):
        print(f" -> [{idx+1}/{len(raw_articles)}] Обработка и генерация арта: {raw_item['title_en'][:40]}...")
        
        # Шаг 1: Gemini делает стилизованный промт для рисования
        ai_drawing_prompt = ask_gemini_for_image_prompt(raw_item['title_en'], raw_item['summary_en'])
        
        # Шаг 2: Бесплатный ИИ рисует уникальную иллюстрацию
        image_url = generate_unique_illustration(ai_drawing_prompt)
        
        # Шаг 3: Веб-перевод (наш быстрый и стабильный метод)
        title_ru = web_translate(raw_item['title_en'], 'ru')
        summary_ru = web_translate(raw_item['summary_en'], 'ru')
        title_he = web_translate(raw_item['title_en'], 'he')
        summary_he = web_translate(raw_item['summary_en'], 'he')
        
        title_ru_kids, summary_ru_kids = generate_kids_version(title_ru, summary_ru, 'ru')
        title_he_kids, summary_he_kids = generate_kids_version(title_he, summary_he, 'he')

        raw_item.update({
            "image": image_url, # Новое поле с уникальным URL картинки!
            "title_ru": title_ru, "summary_ru": summary_ru,
            "title_ru_kids": title_ru_kids, "summary_ru_kids": summary_ru_kids,
            "title_he": title_he, "summary_he": summary_he,
            "title_he_kids": title_he_kids, "summary_he_kids": summary_he_kids
        })
        final_articles.append(raw_item)
        
        # Пауза для стабильности
        time.sleep(12.0)

    final_articles.sort(key=lambda x: x['date_parsed'], reverse=True)
    for idx, article in enumerate(final_articles):
        article["id"] = idx + 1

    with open("news.json", "w", encoding="utf-8") as f:
        json.dump(final_articles, f, ensure_ascii=False, indent=2)
    print(f"\nУспешно сохранено {len(final_articles)} новостей с уникальным ИИ-артом!")

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
