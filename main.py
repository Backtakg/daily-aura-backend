import os
from datetime import datetime
from zoneinfo import ZoneInfo

import httpx

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# ============================================================

# DAILY AURA BACKEND

# ============================================================

APP_NAME = "Daily Aura"
TIMEZONE = ZoneInfo("Asia/Kathmandu")

# ============================================================

# APP

# ============================================================

app = FastAPI(
title="Daily Aura API",
version="4.0.0"
)

app.add_middleware(
CORSMiddleware,
allow_origins=["*"],
allow_credentials=False,
allow_methods=["*"],
allow_headers=["*"]
)

# ============================================================

# HOROSCOPE DATA

# ============================================================

HOROSCOPES = {
"Aries": {
"symbol": "♈",
"vedic": "Mesha",
"reading": (
"Today encourages initiative and confident decisions. "
"Trust your ideas, but give yourself enough time to think "
"before taking an important step."
)
},
"Taurus": {
"symbol": "♉",
"vedic": "Vrishabha",
"reading": (
"Steady progress is more valuable than rushing today. "
"Focus on one practical goal and let consistency work "
"in your favor."
)
},
"Gemini": {
"symbol": "♊",
"vedic": "Mithuna",
"reading": (
"Communication can open an unexpected door today. "
"Listen carefully and don't underestimate the value "
"of a simple conversation."
)
},
"Cancer": {
"symbol": "♋",
"vedic": "Karka",
"reading": (
"Your intuition may be especially noticeable today. "
"Give yourself some quiet space and pay attention to "
"what feels important."
)
},
"Leo": {
"symbol": "♌",
"vedic": "Simha",
"reading": (
"Confidence can help you stand out today. "
"Use your energy positively and remember that leadership "
"also means listening."
)
},
"Virgo": {
"symbol": "♍",
"vedic": "Kanya",
"reading": (
"Small improvements can make a noticeable difference. "
"Organize your priorities and avoid spending energy "
"on things that do not matter."
)
},
"Libra": {
"symbol": "♎",
"vedic": "Tula",
"reading": (
"Balance is the theme of the day. "
"Consider both your own needs and the needs of people "
"around you before making a decision."
)
},
"Scorpio": {
"symbol": "♏",
"vedic": "Vrishchika",
"reading": (
"Determination is strong today. "
"Choose one meaningful objective and put your attention "
"there instead of trying to solve everything at once."
)
},
"Sagittarius": {
"symbol": "♐",
"vedic": "Dhanu",
"reading": (
"Curiosity can lead you somewhere interesting today. "
"Explore a new idea or look at an old problem from "
"a different angle."
)
},
"Capricorn": {
"symbol": "♑",
"vedic": "Makara",
"reading": (
"Long-term thinking works in your favor today. "
"A small practical action now can support a larger "
"goal later."
)
},
"Aquarius": {
"symbol": "♒",
"vedic": "Kumbha",
"reading": (
"An unusual idea may deserve your attention today. "
"Don't immediately dismiss something simply because "
"it is different."
)
},
"Pisces": {
"symbol": "♓",
"vedic": "Meena",
"reading": (
"Creativity and reflection are highlighted today. "
"Give yourself enough quiet time to understand what "
"you really want."
)
}
}

# ============================================================

# FALLBACK QUOTES

# ============================================================

FALLBACK_QUOTES = [
{
"quote": "Small steps every day create big changes.",
"author": "Daily Aura"
},
{
"quote": "Your future is created by what you do today.",
"author": "Daily Aura"
},
{
"quote": "A calm mind can find a way forward.",
"author": "Daily Aura"
},
{
"quote": "Believe in the progress you cannot yet see.",
"author": "Daily Aura"
},
{
"quote": "Start where you are. Make today count.",
"author": "Daily Aura"
},
{
"quote": "You don't need to be perfect. Just keep moving.",
"author": "Daily Aura"
},
{
"quote": "Every morning is another chance to begin again.",
"author": "Daily Aura"
}
]

# ============================================================

# TAROT

# ============================================================

TAROT_CARDS = [
{
"name": "The Fool",
"symbol": "🌟",
"meaning": (
"A new beginning is opening before you. "
"This card represents curiosity, freedom and courage."
),
"advice": "Don't be afraid to start something new.",
"image_url": (
"https://upload.wikimedia.org/wikipedia/commons/9/90/"
"RWS_Tarot_00_Fool.jpg"
)
},
{
"name": "The Magician",
"symbol": "✨",
"meaning": (
"You have useful skills and resources available to you. "
"The focus is on turning an idea into action."
),
"advice": "Use what you already have and take action.",
"image_url": (
"https://upload.wikimedia.org/wikipedia/commons/d/de/"
"RWS_Tarot_01_Magician.jpg"
)
},
{
"name": "The High Priestess",
"symbol": "🌙",
"meaning": (
"Intuition and hidden information are emphasized. "
"Not every answer needs to be discovered immediately."
),
"advice": "Slow down and listen to your intuition.",
"image_url": (
"https://upload.wikimedia.org/wikipedia/commons/8/88/"
"RWS_Tarot_02_High_Priestess.jpg"
)
},
{
"name": "The Empress",
"symbol": "🌸",
"meaning": (
"Growth, creativity and nurturing energy are highlighted."
),
"advice": "Nurture yourself and what matters to you.",
"image_url": (
"https://upload.wikimedia.org/wikipedia/commons/d/d2/"
"RWS_Tarot_03_Empress.jpg"
)
},
{
"name": "The Emperor",
"symbol": "👑",
"meaning": (
"Structure, responsibility and stability can help you."
),
"advice": "Take control of what you can.",
"image_url": (
"https://upload.wikimedia.org/wikipedia/commons/c/c3/"
"RWS_Tarot_04_Emperor.jpg"
)
},
{
"name": "The Lovers",
"symbol": "💞",
"meaning": (
"Connection, values and important choices are highlighted."
),
"advice": "Choose with honesty and intention.",
"image_url": (
"https://upload.wikimedia.org/wikipedia/commons/3/3a/"
"RWS_Tarot_06_Lovers.jpg"
)
},
{
"name": "The Chariot",
"symbol": "🏆",
"meaning": (
"Determination and direction can help you overcome "
"distractions."
),
"advice": "Stay focused on your direction.",
"image_url": (
"https://upload.wikimedia.org/wikipedia/commons/9/9b/"
"RWS_Tarot_07_Chariot.jpg"
)
},
{
"name": "Strength",
"symbol": "🦁",
"meaning": (
"Strength comes through patience, confidence and "
"self-control."
),
"advice": "Be patient with yourself and others.",
"image_url": (
"https://upload.wikimedia.org/wikipedia/commons/f/f5/"
"RWS_Tarot_08_Strength.jpg"
)
},
{
"name": "The Star",
"symbol": "⭐",
"meaning": (
"Hope, renewal and a sense of direction are emphasized."
),
"advice": "Let hope guide your next step.",
"image_url": (
"https://upload.wikimedia.org/wikipedia/commons/d/db/"
"RWS_Tarot_17_Star.jpg"
)
},
{
"name": "The Sun",
"symbol": "☀️",
"meaning": (
"Clarity, positive energy and confidence are highlighted."
),
"advice": "Allow yourself to enjoy today's good moments.",
"image_url": (
"https://upload.wikimedia.org/wikipedia/commons/1/17/"
"RWS_Tarot_19_Sun.jpg"
)
},
{
"name": "The Moon",
"symbol": "🌙",
"meaning": (
"Some situations may not be completely clear yet. "
"Avoid rushing into conclusions."
),
"advice": "Look beyond first impressions.",
"image_url": (
"https://upload.wikimedia.org/wikipedia/commons/7/72/"
"RWS_Tarot_18_Moon.jpg"
)
},
{
"name": "The World",
"symbol": "🌎",
"meaning": (
"A cycle may be approaching completion, creating room "
"for the next chapter."
),
"advice": "Recognize your progress and prepare for what's next.",
"image_url": (
"https://upload.wikimedia.org/wikipedia/commons/f/ff/"
"RWS_Tarot_21_World.jpg"
)
}
]

# ============================================================

# DATE HELPERS

# ============================================================

def get_today():
return datetime.now(TIMEZONE)

def get_daily_tarot():
day_of_year = get_today().timetuple().tm_yday

```
return TAROT_CARDS[
    (day_of_year - 1) % len(TAROT_CARDS)
]
```

def get_fallback_quote():
day_of_year = get_today().timetuple().tm_yday

```
return FALLBACK_QUOTES[
    (day_of_year - 1) % len(FALLBACK_QUOTES)
]
```

# ============================================================

# INTERNET QUOTE

# ============================================================

async def fetch_internet_quote():

```
url = "https://zenquotes.io/api/today"

try:

    timeout = httpx.Timeout(8.0)

    async with httpx.AsyncClient(
        timeout=timeout,
        follow_redirects=True
    ) as client:

        response = await client.get(url)

        if response.status_code == 200:

            data = response.json()

            if (
                isinstance(data, list)
                and len(data) > 0
            ):

                item = data[0]

                quote = item.get("q")
                author = item.get("a")

                if quote:

                    return {
                        "quote": quote,
                        "author": author or "Unknown",
                        "source": "ZenQuotes",
                        "fresh": True
                    }

except Exception as error:

    print(
        "Internet quote error:",
        error
    )

fallback = get_fallback_quote()

return {
    **fallback,
    "source": "Daily Aura fallback",
    "fresh": False
}
```

# ============================================================

# INTERNET ON THIS DAY

# ============================================================

async def fetch_on_this_day():

```
now = get_today()

month = now.month
day = now.day

url = (
    f"https://today.zenquotes.io/api/"
    f"{month}/{day}"
)

try:

    timeout = httpx.Timeout(8.0)

    async with httpx.AsyncClient(
        timeout=timeout,
        follow_redirects=True
    ) as client:

        response = await client.get(url)

        if response.status_code != 200:
            return None

        data = response.json()

        source_data = data.get(
            "data",
            {}
        )

        return {
            "source": "ZenQuotes On This Day",
            "date": f"{month:02d}-{day:02d}",
            "events": source_data.get(
                "Events",
                []
            )[:3],
            "births": source_data.get(
                "Births",
                []
            )[:3]
        }

except Exception as error:

    print(
        "On This Day error:",
        error
    )

return None
```

# ============================================================

# BUILD DAILY CONTENT

# ============================================================

async def build_daily_content(
horoscope_name: str
):

```
horoscope = HOROSCOPES.get(
    horoscope_name
)

if not horoscope:
    return None

quote = await fetch_internet_quote()

historical = await fetch_on_this_day()

tarot = get_daily_tarot()

today = get_today()

return {

    "success": True,

    "date":
        today.date().isoformat(),

    "timezone":
        "Asia/Kathmandu",

    "horoscope": {

        "name":
            horoscope_name,

        "symbol":
            horoscope["symbol"],

        "vedic":
            horoscope["vedic"],

        "reading":
            horoscope["reading"]
    },

    "tarot":
        tarot,

    "quote":
        quote,

    "internet": {

        "enabled":
            True,

        "on_this_day":
            historical
    }
}
```

# ============================================================

# ROOT

# ============================================================

@app.get("/")
async def root():

```
return {

    "status":
        "healthy",

    "service":
        APP_NAME,

    "version":
        "4.0.0",

    "timezone":
        "Asia/Kathmandu",

    "notifications":
        False,

    "internet_content":
        True
}
```

# ============================================================

# HEALTH

# ============================================================

@app.get("/health")
async def health():

```
return {

    "status":
        "healthy",

    "service":
        APP_NAME,

    "version":
        "4.0.0",

    "timezone":
        "Asia/Kathmandu",

    "notifications":
        False,

    "internet_content":
        True
}
```

# ============================================================

# DAILY CONTENT

# ============================================================

@app.get("/daily-content/{horoscope}")
async def daily_content(
horoscope: str
):

```
name = horoscope.strip().capitalize()

content = await build_daily_content(
    name
)

if not content:

    raise HTTPException(
        status_code=404,
        detail="Horoscope sign not found."
    )

return content
```

# ============================================================

# COMPATIBILITY DAILY ROUTE

# ============================================================

@app.get("/api/daily/{horoscope_name}")
async def api_daily(
horoscope_name: str
):

```
name = (
    horoscope_name
    .strip()
    .capitalize()
)

content = await build_daily_content(
    name
)

if not content:

    raise HTTPException(
        status_code=404,
        detail="Horoscope sign not found."
    )

return content
```

# ============================================================

# TAROT

# ============================================================

@app.get("/daily-tarot")
async def daily_tarot():

```
return {

    "success":
        True,

    "date":
        get_today().date().isoformat(),

    "timezone":
        "Asia/Kathmandu",

    "tarot":
        get_daily_tarot()
}
```

# ============================================================

# QUOTE

# ============================================================

@app.get("/daily-quote")
async def daily_quote():

```
return {

    "success":
        True,

    "date":
        get_today().date().isoformat(),

    "timezone":
        "Asia/Kathmandu",

    "quote":
        await fetch_internet_quote()
}
```

# ============================================================

# ON THIS DAY

# ============================================================

@app.get("/on-this-day")
async def on_this_day():

```
data = await fetch_on_this_day()

return {

    "success":
        True,

    "available":
        data is not None,

    "data":
        data
}
```

# ============================================================

# ALL HOROSCOPES

# ============================================================

@app.get("/horoscopes")
async def all_horoscopes():

```
return {

    "success":
        True,

    "date":
        get_today().date().isoformat(),

    "horoscopes": [

        {

            "name":
                name,

            "symbol":
                data["symbol"],

            "vedic":
                data["vedic"]

        }

        for name, data
        in HOROSCOPES.items()
    ]
}
```

# ============================================================

# 404 HANDLER

# ============================================================

@app.exception_handler(404)
async def not_found_handler(
request,
exc
):

```
return {

    "success":
        False,

    "error":
        "Not Found",

    "path":
        str(request.url.path),

    "available_routes": [

        "/",

        "/health",

        "/daily-content/Aries",

        "/daily-tarot",

        "/daily-quote",

        "/on-this-day",

        "/horoscopes"

    ]
}
```
