import xml.etree.ElementTree as ET
import urllib.request
import urllib.parse
import json
import re
import time

RSS_URL = "https://www.nasa.gov/rss/dyn/breaking_news.rss"

def translate_text(text, target_lang):
    if not text:
        return ""
    try:
        # Используем бесплатное API MyMemory (ограничение до 1000 слов в день, для анонсов хватит)
        url = f"https://api.mymemory.translated.net/get?q={urllib.parse.quote(text)}&langpair=en|{target_lang}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            translated = data.get('responseData', {}).get('translatedText', '')
            if translated:
                # Декодируем HTML-сущности, если они вернулись
                return urllib.parse.unquote(translated)
    except Exception as e:
        print(f"Ошибка перевода на {target_lang}: {e}")
    return text # Если упало, возвращаем оригинал

def get_difficulty(title, summary):
    text = f"{title} {summary}".lower()
    if re.search(r'(авар|катастроф|крушен|взрыв|fail|crash|explod)', text):
        return "accident"
    if re.search(r'(двигател|топлив|тяга|орбит|траектор|термодинам|ионн|плазм|engine|orbit|propulsion|thruster)', text):
        return "pro"
    if re.search(r'(урок|методич|учит|класс|школ|задан|проект|lesson|teacher|school|class)', text):
        return "teacher"
    return "novice"

def main():
    print("Запуск сборщика новостей из NASA...")
    try:
        req = urllib.request.Request(RSS_URL, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            xml_data = response.read()
    except Exception as e:
        print(f"Не удалось скачать RSS: {e}")
        return

    root = ET.fromstring(xml_data)
    articles = []
    
    # Берем первые 10 новостей, чтобы не перегружать бесплатный лимит перевода
    items = root.findall('.//item')[:10]
    
    for idx, item in enumerate(items):
        title_en = item.find('title').text if item.find('title') is not None else ""
        summary_en = item.find('description').text if item.find('description') is not None else ""
        link = item.find('link').text if item.find('link') is not None else ""
        pub_date = item.find('pubDate').text if item.find('pubDate') is not None else ""
        
        # Очищаем описание от HTML тегов, если они есть
        summary_en = re.sub('<[^<]+?>', '', summary_en).strip()
        
        print(f"[{idx+1}/{len(items)}] Перевод новости: {title_en[:30]}...")
        
        # Переводим
        title_ru = translate_text(title_en, "ru")
        summary_ru = translate_text(summary_en, "ru")
        
        time.sleep(1) # Пауза, чтобы API не заблокировало
        
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
    print("Успешно! Файл news.json обновлен.")

if __name__ == "__main__":
    main()