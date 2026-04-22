import json
import feedparser
from datetime import datetime, timezone

NASA_RSS_URL = "https://www.nasa.gov/rss/dyn/breaking_news.rss"
OUTPUT_FILE = "news.json"


def fetch_nasa_news(limit: int = 20) -> None:
    feed = feedparser.parse(NASA_RSS_URL)

    if feed.bozo:
        print(f"Error fetching feed: {feed.bozo_exception}")
        return

    articles = []
    for entry in feed.entries[:limit]:
        published = entry.get("published", "")
        if entry.get("published_parsed"):
            try:
                dt = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                published = dt.strftime("%Y-%m-%d %H:%M UTC")
            except Exception:
                pass

        image_url = ""
        if entry.get("media_content"):
            image_url = entry.media_content[0].get("url", "")
        elif entry.get("media_thumbnail"):
            image_url = entry.media_thumbnail[0].get("url", "")
        elif entry.get("enclosures"):
            for enc in entry.enclosures:
                if enc.get("type", "").startswith("image/"):
                    image_url = enc.get("url", "")
                    break

        articles.append({
            "title": entry.get("title", "No title"),
            "link": entry.get("link", ""),
            "summary": entry.get("summary", ""),
            "published": published,
            "image": image_url,
        })

    result = {
        "source": feed.feed.get("title", "NASA News"),
        "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "articles": articles,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(articles)} articles to {OUTPUT_FILE}")


if __name__ == "__main__":
    fetch_nasa_news()
