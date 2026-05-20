# AstroTrack Perfect Global Kids Scraper - v12.0.0 (2026)
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

def build_dynamic_kids_content(title, summary, source, lang):
    """Полностью динамический интернациональный генератор детского режима"""
    t_lower = title.lower()
    
    # Конфигурация вступлений (Заменили проблемный флаг EU на стабильный эмодзи)
    intros = {
        "ru": {
            "SpaceX": "⚡ Команда Илона Маска снова зажигает!",
            "ESA": "✨🔬 Европейские ученые отправили секретное донесение!",
            "mars": "🔴 Новости с Красной Планеты!",
            "sat": "🛰️ Внимание, на связи космический радар!",
            "def": "🌟 Смотри, что произошло!"
        },
        "he": {
            "SpaceX": "⚡ הצוות של אילון מאסק שוב מפציץ!",
            "ESA": "✨🔬 המדענים מאירופה שלחו דיווח מרתק!",
            "mars": "🔴 חדשות מרעישות מכוכב המאדים!",
            "sat": "🛰️ שימו לב, מכשיר הלוויין מעדכן!",
            "def": "🌟 תראו מה קרה!"
        },
        "en": {
            "SpaceX": "⚡ Elon Musk's team strikes again!",
            "ESA": "✨🔬 European scientists just sent an amazing report!",
            "mars": "🔴 Fresh updates from the Red Planet!",
            "sat": "🛰️ Space radar intercept successfully decoded!",
            "def": "🌟 Check out this cosmic event!"
        }
    }

    # Конфигурация концовок
    outros = {
        "ru": {
            "launch": "🚀 Обратный отсчет окончен, полетели! Хотел бы стать командиром экипажа? ☄️",
            "earth": "🌍 Наша планета из космоса выглядит волшебно. Поделись этой красотой! 📸",
            "sun": "☀️ Ого, Солнце сегодня очень горячее! Защитные экраны корабля на максимуме! 🛡️",
            "def": "🪐 Как тебе такое космическое путешествие?"
        },
        "he": {
            "launch": "🚀 הספירה לאחור הסתיימה, טסים! היית רוצה להיות המפקד של החללית הזו? ☄️",
            "earth": "🌍 כדור הארץ נראה פשוט קסום מהחלל. תראה איזה יופי! 📸",
            "sun": "☀️ וואו, השמש ממש לוהטת היום! מגיני החללית עובדים בעוצמה מלאה! 🛡️",
            "def": "🪐 מה דעתך על המסע הזה?"
        },
        "en": {
            "launch": "🚀 Liftoff confirmed! Would you like to be the commander of this spaceship? ☄️",
            "earth": "🌍 Our planet looks absolutely magical from orbit. Truly breathtaking! 📸",
            "sun": "☀️ Wow, the Sun is hyperactive today! Spaceship radiation shields at 100%! 🛡️",
            "def": "🪐 What do you think about this awesome space journey?"
        }
    }

    # Факты-клики
    facts = {
        "ru": [" Космос на древнегреческом означает 'порядок'!", " В космосе абсолютная, полная тишина!", " Скафандр весит как большой пес!"],
        "he": [" המילה 'קוסמוס' ביוונית עתיקה משמעותה 'סדר'!", " דרך אгב, בחלל יש שקט מוחלט לחלוטין!", " חליפת חלל שוקלת כמו כלב ענקי!"],
        "en": [" 'Cosmos' in ancient Greek actually means 'order'!", " Fun fact: space is completely, absolutely silent!", " A real space suit weighs as much as a huge dog!"]
    }

    # Выбираем ветку языка
    ln = lang if lang in intros else "en"
    
    # Определяем категорию вступления
    if source == "SpaceX": intro = intros[ln]["SpaceX"]
    elif source == "Esa" or source == "ESA": intro = intros[ln]["ESA"]
    elif "марс" in t_lower or "mars" in t_lower: intro = intros[ln]["mars"]
    elif "спутник" in t_lower or "satell" in t_lower or "starlink" in t_lower: intro = intros[ln]["sat"]
    else: intro = intros[ln]["def"]

    # Определяем категорию концовки
    if "запуск" in t_lower or "ракета" in t_lower or "launch" in t_lower or "falcon" in t_lower: outro = outros[ln]["launch"]
    elif "земл" in t_lower or "earth" in t_lower or "фото" in t_lower or "view" in t_lower: outro = outros[ln]["earth"]
    elif "солн" in t_lower or "sun" in t_lower or "solar" in t_lower: outro = outros[ln]["sun"]
    else: outro = outros[ln]["def"]

    # Вычисляем уникальный факт по хэшу строки
    hash_val = int(hashlib.md5(title.encode('utf-8')).hexdigest(), 16)
    fact = facts[ln][hash_val % len(facts[ln])]

    return f"🚀 {title} ✨", f"{intro} {summary} {outro}{fact}"

def parse_rfc2822_date(date_str):
    try:
        date_str = date_str.split(', ')[1] if ', ' in date_str else date_str
        date_clean = re.sub(r'\s[A-Z]{3,4}$|\s\+[0-9]{4}$', '', date_str)
        return datetime.strptime(date_clean, "%d %b %Y %H:%M:%S")
    except:
        return datetime.now()

def main():
    print("=== Запуск Исправленного Робота Космического Контента v12.0.0 ===")
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

    final_articles = []
    for idx, raw_item in enumerate(raw_articles):
        # Переводы
        title_ru = web_translate(raw_item['title_en'], 'ru')
        summary_ru = web_translate(raw_item['summary_en'], 'ru')
        title_he = web_translate(raw_item['title_en'], 'he')
        summary_he = web_translate(raw_item['summary_en'], 'he')
        
        # Сборка уникального Kids Mode на трех языках
        title_ru_kids, summary_ru_kids = build_dynamic_kids_content(title_ru, summary_ru, raw_item['source'], 'ru')
        title_he_kids, summary_he_kids = build_dynamic_kids_content(title_he, summary_he, raw_item['source'], 'he')
        title_en_kids, summary_en_kids = build_dynamic_kids_content(raw_item['title_en'], raw_item['summary_en'], raw_item['source'], 'en')

        raw_item.update({
            "image": "",
            "title_ru": title_ru, "summary_ru": summary_ru,
            "title_ru_kids": title_ru_kids, "summary_ru_kids": summary_ru_kids,
            "title_he": title_he, "summary_he": summary_he,
            "title_he_kids": title_he_kids, "summary_he_kids": summary_he_kids,
            "title_en_kids": title_en_kids, "summary_en_kids": summary_en_kids
        })
        final_articles.append(raw_item)

    final_articles.sort(key=lambda x: x['date_parsed'], reverse=True)
    for idx, article in enumerate(final_articles):
        article["id"] = idx + 1

    with open("news.json", "w", encoding="utf-8") as f:
        json.dump(final_articles, f, ensure_ascii=False, indent=2)
    print("\nnews.json успешно обновлен!")

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
