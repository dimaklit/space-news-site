# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Космонавигатор** — a Russian-language space education portal for teachers and students. Static site with no build system.

## Commands

**Update news data:**
```bash
pip install -r requirements.txt
python scraper.py
```

**Serve locally** (any static server works):
```bash
python -m http.server 8000
# then open http://localhost:8000
```

No linting, testing, or build steps exist.

## Architecture

**4 files total:**
- `index.html` — entire frontend: HTML + embedded CSS + embedded JS (~887 lines, single SPA)
- `scraper.py` — fetches NASA RSS feed via `feedparser`, writes `news.json`
- `news.json` — generated data file; loaded client-side at runtime
- `requirements.txt` — `feedparser==6.0.11` only

**External APIs used at runtime (client-side JS):**
- ISS position: `https://api.wheretheiss.at/v1/satellites/25544` — polled every 5s
- Launch calendar: `https://ll.thespacedevs.com/2.2.0/launch/upcoming/` — polled every 30s
- News: `news.json` (local file, populated by scraper which pulls `https://www.nasa.gov/rss/dyn/breaking_news.rss`)

## Frontend Structure (`index.html`)

Six sections toggled by `data-sec` attributes on nav buttons:
1. `home` — hero + live ISS stats + news preview
2. `news` — filterable news feed from `news.json`
3. `launches` — upcoming launches with countdown timers
4. `explainers` — 6 static educational cards (hardcoded)
5. `workshop` — 6 static experiment/project templates (hardcoded)
6. `apps` — 8 curated space apps (hardcoded)

**News difficulty tagging** — auto-detected by regex on title/summary:
- `accident`: авар|катастроф|крушен|взрыв|fail|crash|explod
- `pro`: двигател|топлив|тяга|орбит|траектор|термодинам|ионн|плазм
- `teacher`: урок|методич|учит|класс|школ|задан|проект
- `novice`: default fallback

**CSS variables** (dark sci-fi theme): teal `#00d4ff`, purple `#a855f7`, orange `#ff6b2b`, green `#22d3a5`.

## Data Flow

```
NASA RSS → scraper.py → news.json → index.html (fetch on load)
wheretheiss.at API → index.html (live, every 5s)
thespacedevs.com API → index.html (live, every 30s)
```

The scraper writes at most 20 articles (configurable via `fetch_nasa_news(limit)`). Run it manually to refresh news.