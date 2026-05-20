# AstroTrack Dynamic Kids Content Scraper - v11.0.0 (2026)
import xml.etree.ElementTree as ET
import urllib.request
import urllib.parse
import json
import re
import hashlib
from datetime import datetime

NEWS_SOURCES = [
    {"name": "SpaceX", "url": "https://spaceflightnow.com/category/falcon-9/feed/"}, 
    {"name": "ESA", "url": "https://www.esa.int/rssfeed/Our_Activities/Space_News"},
    {"name": "Spaceflight Now", "url": "https://spaceflightnow.com/feed/"}
]

LAUNCHES_URL = "https://lldev.thespacedevs.com/2.2.0/launch/upcoming/?limit=5"

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

def build_dynamic_kids_content(title_translated, summary_translated, source, lang):
    """Локальный генератор: создает живой, разнообразный детский контент без повторов"""
    title_lower = title_translated.lower()
    
    # 1. Варианты динамических вступлений по источникам и темам
    intro_ru = "🌟 Смотри, что произошло!"
    intro_he = "🌟 תראו מה קרה!"
    
    if source == "SpaceX":
        intro_ru = "⚡ Команда Илона Маска снова зажигает!"
        intro_he = "⚡ הצוות של אילון מאסק שוב מפציץ!"
    elif source == "ESA":
        intro_ru = "🇪🇺 Европейские ученые отправили секретное донесение!"
        intro_he = "🇪🇺 המדענים מאירופה שלחו דיווח מרתק!"
    elif "марс" in title_lower or "mars" in title_lower:
        intro_ru = "🔴 Новости с Красной Планеты!"
        intro_he = "🔴 חדשות מרעישות מכוכב המאדים!"
    elif "спутник" in title_lower or "satellite" in title_lower or "starlink" in title_lower:
        intro_ru = "🛰️ Внимание, на связи космический радар!"
        intro_he = "🛰️ שימו לב, מכשיר הלוויין מעדכן!"

    # 2. Варианты интерактивных концовок-вопросов по контексту
    outro_ru = "🪐 Как тебе такое путешествие?"
    outro_he = "🪐 מה דעתך על המסע הזה?"
    
    if "запуск" in title_lower or "ракета" in title_lower or "falcon" in title_lower or "launch" in title_lower:
        outro_ru = "🚀 Обратный отсчет окончен, полетели! Хотел бы стать командиром такого экипажа? ☄️"
        outro_he = "🚀 הספירה לאחור הסתיימה, טסים! היית רוצה להיות המפקד של החללית הזו? ☄️"
    elif "земл" in title_lower or "earth" in title_lower or "фото" in title_lower:
        outro_ru = "🌍 Наша планета из иллюминатора выглядит просто волшебно. Поделись этой красотой с друзьями! 📸"
        outro_he = "🌍 כדור הארץ נראה פשוט קסום מהחלון של החללית. תראה איזה יופי! 📸"
    elif "солн" in title_lower or "solar" in title_lower:
        outro_ru = "☀️ Ого, Солнце сегодня очень горячее! Защитные экраны корабля работают на полную мощность! 🛡️"
        outro_he = "☀️ וואו, השמש ממש לוהטת היום! מגיני החללית עובדים בעוצמה מלאה! 🛡️"

    # Добавляем игровой элемент (забавный факт-клик для ребенка) в зависимости от хэша
    hash_val = int(hashlib.md5(title_translated.encode('utf-8')).hexdigest(), 16)
    fun_facts_ru = [
        " Слово 'космос' на древнегреческом означает 'порядок'!",
        " Кстати, в космосе абсолютная, полная тишина!",
        " Знаешь ли ты, что скафандр космонавта весит как большой пес?"
    ]
    fun_facts_he = [
        " המילה 'קוסמוס' ביוונית עתיקה משמעותה 'סדר'!",
        " דרך אגב, בחלל יש שקט מוחלט לחלוטיн!",
        " הידעת שחליפת חלל שוקלת כמו כלב ענקי?"
    ]
    
    extra_fact_ru = fun_facts_ru[hash_val % len(fun_facts_ru)]
    extra_fact_he = fun_facts_he[hash_val % len(fun_facts_he)]

    # Собираем финальные строки
    if lang == "ru":
        kids_title = f"🚀 {title_translated} ✨"
        kids_summary = f"{intro_ru} {summary_translated} {outro_ru}{extra_fact_ru}"
    else: # иврит
        kids_title = f"🚀 {title_translated} ✨"
        kids_summary = f"{intro_he} {summary_translated} {outro_he}{extra_fact_he}"
        
    return kids_title, kids_summary

def parse_rfc2822_date(date_str):
    try:
        date_str = date_str.split(', ')[1] if ', ' in date_str else date_str
        date_clean = re.sub(r'\s[A-Z]{3,4}$|\s\+[0-9]{4}$', '', date_str)
        return datetime.strptime(date_clean, "%d %b %Y %H:%M:%S")
    except:
        return datetime.now()

def main():
    print("=== Запуск Генератора Динамического Детского Контента AstroTrack v11.0.0 ===")
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

    print(f"\nСобрано {len(raw_articles)} новостей. Запуск перевода и адаптации контента...")

    final_articles = []
    for idx, raw_item in enumerate(raw_articles):
        print(f" -> [{idx+1}/{len(raw_articles)}] Сборка: {raw_item['title_en'][:40]}...")
        
        # Базовые переводы
        title_ru = web_translate(raw_item['title_en'], 'ru')
        summary_ru = web_translate(raw_item['summary_en'], 'ru')
        title_he = web_translate(raw_item['title_en'], 'he')
        summary_he = web_translate(raw_item['summary_en'], 'he')
        
        # Генерируем по-настоящему динамические детские версии (УНИКАЛЬНЫЕ ДЛЯ КАЖДОЙ СТАТЬИ)
        title_ru_kids, summary_ru_kids = build_dynamic_kids_content(title_ru, summary_ru, raw_item['source'], 'ru')
        title_he_kids, summary_he_kids = build_dynamic_kids_content(title_he, summary_he, raw_item['source'], 'he')

        raw_item.update({
            "image": "", # Изображения теперь полностью на стороне фронтенда через минималистичные эмодзи
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
    print(f"\nУспешно сохранено {len(final_articles)} динамических детских историй в news.json!")

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
