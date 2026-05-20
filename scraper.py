# AstroTrack Light Speed No-Limit Scraper - v3.0.0 (2026)
import xml.etree.ElementTree as ET
import urllib.request
import urllib.parse
import json
import re
import os
from datetime import datetime

# Источники новостей - возвращаем по 10 статей, система выдержит любую нагрузку!
NEWS_SOURCES = [
    {"name": "SpaceX", "url": "https://spaceflightnow.com/category/falcon-9/feed/"}, 
    {"name": "ESA", "url": "https://www.esa.int/rssfeed/Our_Activities/Space_News"},
    {"name": "Spaceflight Now", "url": "https://spaceflightnow.com/feed/"}
]

LAUNCHES_URL = "https://lldev.thespacedevs.com/2.2.0/launch/upcoming/?limit=5"

def web_translate(text, target_lang):
    """Бесплатный и быстрый перевод через веб-интерфейс Google Translate БЕЗ лимитов и ключей"""
    if not text.strip():
        return text
    try:
        # Формируем безопасный URL для веб-запроса
        encoded_text = urllib.parse.quote(text)
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl={target_lang}&dt=t&q={encoded_text}"
        
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            res_json = json.loads(response.read().decode('utf-8'))
            
            # Собираем переведенные части текста воедино
            translated_parts = [part[0] for part in res_json[0] if part[0]]
            return "".join(translated_parts).strip()
    except Exception as e:
        print(f"   [!] Ошибка веб-перевода на {target_lang}: {e}")
        return text

def generate_kids_version(title, summary, lang):
    """Локальный генератор детской версии (Kids Edition) на основе базового перевода с эмодзи"""
    if lang == "ru":
        kids_title = f"🚀 Космические новости: {title} ✨"
        kids_summary = f"🌟 Привет, юный космонавт! Смотри, что произошло: {summary} 🪐 Как тебе такое путешествие? Это просто фантастика! 🔭🛰️"
    else:  # иврит
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
    print("=== Запуск Бесперебойного Скоростного Сборщика AstroTrack v3.0.0 ===")
    raw_articles = []

    # Скачиваем по 8 свежих новостей с каждого стабильного источника
    for source in NEWS_SOURCES:
        print(f"Скачиваем ленту {source['name']}...")
        try:
            req = urllib.request.Request(source['url'], headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as response:
                xml_data = response.read()
            
            root = ET.fromstring(xml_data)
            items = root.findall('.//item')[:8]
            
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
            print(f" Ошибка скачивания {source['name']}: {e}")

    print(f"\nСобрано {len(raw_articles)} новостей. Запуск мгновенного веб-перевода БЕЗ лимитов...")

    final_articles = []
    for idx, raw_item in enumerate(raw_articles):
        print(f" -> [{idx+1}/{len(raw_articles)}] Перевод: {raw_item['title_en'][:40]}...")
        
        # Переводим на русский язык
        title_ru = web_translate(raw_item['title_en'], 'ru')
        summary_ru = web_translate(raw_item['summary_en'], 'ru')
        
        # Переводим на иврит
        title_he = web_translate(raw_item['title_en'], 'he')
        summary_he = web_translate(raw_item['summary_en'], 'he')
        
        # Генерируем детские версии локально
        title_ru_kids, summary_ru_kids = generate_kids_version(title_ru, summary_ru, 'ru')
        title_he_kids, summary_he_kids = generate_kids_version(title_he, summary_he, 'he')

        raw_item.update({
            "title_ru": title_ru, "summary_ru": summary_ru,
            "title_ru_kids": title_ru_kids, "summary_ru_kids": summary_ru_kids,
            "title_he": title_he, "summary_he": summary_he,
            "title_he_kids": title_he_kids, "summary_he_kids": summary_he_kids
        })
        final_articles.append(raw_item)

    # Сортировка по свежести
    final_articles.sort(key=lambda x: x['date_parsed'], reverse=True)
    for idx, article in enumerate(final_articles):
        article["id"] = idx + 1

    with open("news.json", "w", encoding="utf-8") as f:
        json.dump(final_articles, f, ensure_ascii=False, indent=2)
    print(f"\nУспешно сохранено {len(final_articles)} полностью переведенных новостей в news.json!")

    # Сбор пусков
    print("\nСбор расписания космических пусков...")
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
            print("Расписание пусков сохранено.")
    except Exception as e:
        print(f"Ошибка пусков: {e}")
        with open("launches.json", "w", encoding="utf-8") as f: json.dump([], f)

if __name__ == "__main__":
    main()
