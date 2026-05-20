# AstroTrack Ultimate Resilient Scraper & Illustrator - v5.0.0 (2026)
import xml.etree.ElementTree as ET
import urllib.request
import urllib.parse
import json
import re
import hashlib
from datetime import datetime

# Источники новостей - возвращаем полную ленту по 8 статей!
NEWS_SOURCES = [
    {"name": "SpaceX", "url": "https://spaceflightnow.com/category/falcon-9/feed/"}, 
    {"name": "ESA", "url": "https://www.esa.int/rssfeed/Our_Activities/Space_News"},
    {"name": "Spaceflight Now", "url": "https://spaceflightnow.com/feed/"}
]

LAUNCHES_URL = "https://lldev.thespacedevs.com/2.2.0/launch/upcoming/?limit=5"

# Тематическая медиатека качественных Sci-Fi иллюстраций (Бронебойные ссылки без блокировок на ПК)
SPACE_GALLERY = {
    "starlink": "https://picsum.photos/id/967/600/400", # Орбитальный поезд спутников / космос
    "falcon": "https://picsum.photos/id/1053/600/400", # Ракета / техника
    "dragon": "https://picsum.photos/id/903/600/400", # Космический корабль / вид Земли
    "mars": "https://picsum.photos/id/1016/600/400", # Красный ландшафт / планета
    "moon": "https://picsum.photos/id/1042/600/400", # Звездное небо и лунный свет
    "earth": "https://picsum.photos/id/1023/600/400", # Облака / вид сверху
    "sun": "https://picsum.photos/id/894/600/400", # Яркий космический свет / горизонт
    "satellite": "https://picsum.photos/id/961/600/400", # Научное оборудование / орбита
    "astronaut": "https://picsum.photos/id/984/600/400", # Горы и ночные звезды
    "rocket": "https://picsum.photos/id/1050/600/400", # Старт космического корабля
    "abstract": [
        "https://picsum.photos/id/907/600/400",
        "https://picsum.photos/id/931/600/400",
        "https://picsum.photos/id/952/600/400",
        "https://picsum.photos/id/962/600/400"
    ]
}

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

def assign_smart_illustration(title):
    """Анализирует текст и выбирает лучшую тематическую иллюстрацию из базы"""
    title_lower = title.lower()
    
    # Ищем ключевые слова в заголовке
    if "starlink" in title_lower:
        return SPACE_GALLERY["starlink"]
    if "falcon" in title_lower:
        return SPACE_GALLERY["falcon"]
    if "dragon" in title_lower or "crew" in title_lower:
        return SPACE_GALLERY["dragon"]
    if "mars" in title_lower:
        return SPACE_GALLERY["mars"]
    if "moon" in title_lower or "lunar" in title_lower:
        return SPACE_GALLERY["moon"]
    if "earth" in title_lower or "climate" in title_lower:
        return SPACE_GALLERY["earth"]
    if "sun" in title_lower or "solar" in title_lower or "smile" in title_lower:
        return SPACE_GALLERY["sun"]
    if "satellite" in title_lower or "orbit" in title_lower:
        return SPACE_GALLERY["satellite"]
    if "astronaut" in title_lower or "iss" in title_lower or "station" in title_lower:
        return SPACE_GALLERY["astronaut"]
    if "rocket" in title_lower or "launch" in title_lower or "lift" in title_lower or "ula" in title_lower:
        return SPACE_GALLERY["rocket"]
        
    # Если совпадений нет, берем одну из абстрактных картинок на основе хэша заголовка
    hash_object = hashlib.md5(title.encode('utf-8'))
    hash_index = int(hash_object.hexdigest(), 16) % len(SPACE_GALLERY["abstract"])
    return SPACE_GALLERY["abstract"][hash_index]

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
    print("=== Запуск Сверхнадежного Иллюстратора AstroTrack v5.0.0 ===")
    raw_articles = []

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
            print(f" Ошибка источника {source['name']}: {e}")

    print(f"\nСобрано {len(raw_articles)} новостей. Привязка умных иллюстраций и перевод...")

    final_articles = []
    for idx, raw_item in enumerate(raw_articles):
        print(f" -> [{idx+1}/{len(raw_articles)}] Обработка: {raw_item['title_en'][:40]}...")
        
        # Шаг 1: Автоматический умный подбор тематического арта (БЕЗ API И БЕЗ ЛИМИТОВ)
        image_url = assign_smart_illustration(raw_item['title_en'])
        
        # Шаг 2: Моментальный и безотказный перевод
        title_ru = web_translate(raw_item['title_en'], 'ru')
        summary_ru = web_translate(raw_item['summary_en'], 'ru')
        title_he = web_translate(raw_item['title_en'], 'he')
        summary_he = web_translate(raw_item['summary_en'], 'he')
        
        title_ru_kids, summary_ru_kids = generate_kids_version(title_ru, summary_ru, 'ru')
        title_he_kids, summary_he_kids = generate_kids_version(title_he, summary_he, 'he')

        raw_item.update({
            "image": image_url, 
            "title_ru": title_ru, "summary_ru": summary_ru,
            "title_ru_kids": title_ru_kids, "summary_ru_kids": summary_ru_kids,
            "title_he": title_he, "summary_he": summary_he,
            "title_he_kids": title_he_kids, "summary_he_kids": summary_he_kids
        })
        final_articles.append(raw_item)

    final_articles.sort(key=lambda x: x['date_parsed'], reverse=True)
    for idx, article in enumerate(final_articles):
        article["id"] = idx + 1

    with open("news.json", "w", encoding="utf-8") as f:
        json.dump(final_articles, f, ensure_ascii=False, indent=2)
    print(f"\nУспешно сохранено {len(final_articles)} новостей с умными Sci-Fi артами!")

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
