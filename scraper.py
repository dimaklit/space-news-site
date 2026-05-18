import xml.etree.ElementTree as ET
import urllib.request
import urllib.parse
import json
import re
import time

RSS_URL = "https://www.nasa.gov/rss/dyn/breaking_news.rss"
LAUNCHES_URL = "https://lldev.thespacedevs.com/2.2.0/launch/upcoming/?limit=5"

def translate_text(text, target_lang):
    if not text:
        return ""
    try:
        # Безлимитный Google Translate API
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl={target_lang}&dt=t&q={urllib.parse.quote(text)}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            translated_parts = [part[0] for part in data[0] if part[0]]
            return "".join(translated_parts)
    except Exception as e:
        print(f"Ошибка перевода на {target_lang}: {e}")
    return text

def get_difficulty(title, summary):
    text = f"{title} {summary}".lower()
    if re.search(r'(авар|катастроф|крушен|взрыв|fail|crash|explod)', text):
        return "accident"
    if re.search(r'(двигател|топлив|тяга|орбит|траектор|термодинам|ионн|плазм|engine|orbit|propulsion|thruster)', text):
        return "pro"
    if re.search(r'(урок|методич|учит|класс|школ|задан|проект|lesson|teacher|school|class)', text):
        return "teacher"
    return "novice"

def fetch_launches():
    print("Сбор расписания космических пусков...")
    try:
        req = urllib.request.Request(LAUNCHES_URL, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode('utf-8'))
            launches = []
            for item in data.get('results', []):
                name_en = item.get('name', 'Unknown Mission')
                launches.append({
                    "name_en": name_en,
                    "name_ru": translate_text(name_en, "ru"),
                    "name_he": translate_text(name_en, "he"),
                    "window_start": item.get('window_start'),
                    "rocket": item.get('rocket', {}).get('configuration', {}).get('full_name', ''),
                    "pad": item.get('pad', {}).get('name', ''),
                    "location": item.get('pad', {}).get('location', {}).get('name', '')
                })
                time.sleep(1)
            
            with open("launches.json", "w", encoding="utf-8") as f:
                json.dump(launches, f, ensure_ascii=False, indent=2)
            print("Расписание пусков успешно сохранено в launches.json")
    except Exception as e:
        print(f"Ошибка сбора пусков: {e}")
        with open("launches.json", "w", encoding="utf-8") as f:
            json.dump([], f)

def main():
    print("Запуск сборщика данных для портала AstroTrack...")
    try:
        req = urllib.request.Request(RSS_URL, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            xml_data = response.read()
    except Exception as e:
        print(f"Не удалось скачать RSS: {e}")
        return

    root = ET.fromstring(xml_data)
    articles = []
    items = root.findall('.//item')[:10]
    
    for idx, item in enumerate(items):
        title_en = item.find('title').text if item.find('title') is not None else ""
        summary_en = item.find('description').text if item.find('description') is not None else ""
        link = item.find('link').text if item.find('link') is not None else ""
        pub_date = item.find('pubDate').text if item.find('pubDate') is not None else ""
        
        summary_en = re.sub('<[^<]+?>', '', summary_en).strip()
        print(f"[{idx+1}/{len(items)}] Перевод новости: {title_en[:30]}...")
        
        title_ru = translate_text(title_en, "ru")
        summary_ru = translate_text(summary_en, "ru")
        time.sleep(1)
        
        title_he = translate_text(title_en, "he")
        summary_he = translate_text(summary_en, "he")
        
        difficulty = get_difficulty(title_ru, summary_ru)
        
        articles.append({
            "id": idx + 1,
            "date": pub_date,
            "link": link,
            "difficulty": difficulty,
            "title_en": title_en,
            "summary_en": summary_en,
            "title_ru": title_ru,
            "summary_ru": summary_ru,
            "title_he": title_he,
            "summary_he": summary_he
        })
        time.sleep(1)

    with open("news.json", "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)
    print("Лента новостей успешно сохранена в news.json")
    
    fetch_launches()

if __name__ == "__main__":
    main()