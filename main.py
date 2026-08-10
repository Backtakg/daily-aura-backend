```python
import os
from datetime import datetime
from zoneinfo import ZoneInfo

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware


# ============================================================
# DAILY AURA BACKEND
# ============================================================

TIMEZONE = ZoneInfo("Asia/Kathmandu")

app = FastAPI(
    title="Daily Aura API",
    version="3.0.0"
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# HOROSCOPES
# ============================================================

HOROSCOPES = {
    "Aries": {
        "symbol": "♈",
        "vedic": "Mesha",
        "reading": "Today is a good day to take initiative. Trust your ideas and move forward with confidence."
    },
    "Taurus": {
        "symbol": "♉",
        "vedic": "Vrishabha",
        "reading": "Patience can bring better results today. Focus on steady progress."
    },
    "Gemini": {
        "symbol": "♊",
        "vedic": "Mithuna",
        "reading": "Communication is your strength today. A conversation may open a new opportunity."
    },
    "Cancer": {
        "symbol": "♋",
        "vedic": "Karka",
        "reading": "Listen to your intuition today. Spend quality time with people you care about."
    },
    "Leo": {
        "symbol": "♌",
        "vedic": "Simha",
        "reading": "Your confidence can attract attention today. Use your energy wisely."
    },
    "Virgo": {
        "symbol": "♍",
        "vedic": "Kanya",
        "reading": "Small details matter today. Organize your priorities and stay focused."
    },
    "Libra": {
        "symbol": "♎",
        "vedic": "Tula",
        "reading": "Balance is important today. Think carefully before making decisions."
    },
    "Scorpio": {
        "symbol": "♏",
        "vedic": "Vrishchika",
        "reading": "Your determination is strong today. Focus that energy on one meaningful goal."
    },
    "Sagittarius": {
        "symbol": "♐",
        "vedic": "Dhanu",
        "reading": "A fresh perspective can change your day. Stay curious and explore new ideas."
    },
    "Capricorn": {
        "symbol": "♑",
        "vedic": "Makara",
        "reading": "Consistent effort is your advantage today. Keep working toward your long-term goals."
    },
    "Aquarius": {
        "symbol": "♒",
        "vedic": "Kumbha",
        "reading": "An original idea may be worth pursuing today. Share your thoughts with others."
    },
    "Pisces": {
        "symbol": "♓",
        "vedic": "Meena",
        "reading": "Your creativity and empathy are strong today. Give yourself some quiet time."
    }
}


# ============================================================
# FALLBACK QUOTES
# ============================================================

QUOTES = [
    "Small steps every day create big changes.",
    "Your future is created by what you do today.",
    "A calm mind can find a way forward.",
    "Believe in the progress you cannot yet see.",
    "Start where you are. Make today count.",
    "You don't need to be perfect. Just keep moving.",
    "Every morning is another chance to begin again.",
    "Growth begins when you choose to keep going.",
    "A new day brings a new opportunity.",
    "Trust the process and take the next step."
]


# ============================================================
# TAROT
# ============================================================

TAROT_CARDS = [
    {
        "name": "The Fool",
        "symbol": "🌟",
        "meaning": "A new beginning is opening before you. Stay curious and trust yourself.",
        "advice": "Do not be afraid to start something new."
    },
    {
        "name": "The Magician",
        "symbol": "✨",
        "meaning": "You have useful skills and resources available to you.",
        "advice": "Use what you already have and take action."
    },
    {
        "name": "The High Priestess",
        "symbol": "🌙",
        "meaning": "Your intuition may be especially strong today.",
        "advice": "Slow down and listen to your inner voice."
    },
    {
        "name": "The Empress",
        "symbol": "🌸",
        "meaning": "Growth, creativity and abundance surround you.",
        "advice": "Nurture yourself and what matters to you."
    },
    {
        "name": "The Emperor",
        "symbol": "👑",
        "meaning": "Structure and discipline can help create stability.",
        "advice": "Take control of what you can."
    },
    {
        "name": "The Lovers",
        "symbol": "💞",
        "meaning": "Connection and important choices are highlighted.",
        "advice": "Choose with honesty and intention."
    },
    {
        "name": "The Chariot",
        "symbol": "🏆",
        "meaning": "Determination can help you move forward.",
        "advice": "Stay focused on your direction."
    },
    {
        "name": "Strength",
        "symbol": "🦁",
        "meaning": "Real strength comes from patience and compassion.",
        "advice": "Be patient with yourself and others."
    },
    {
        "name": "The Star",
        "symbol": "⭐",
        "meaning": "Hope and renewal are highlighted today.",
        "advice": "Let hope guide your next step."
    },
    {
        "name": "The Sun",
        "symbol": "☀️",
        "meaning": "Positive energy, clarity and confidence are highlighted.",
        "advice": "Allow yourself to enjoy today's good moments."
    },
    {
        "name": "The Moon",
        "symbol": "🌙",
        "meaning": "Not everything is clear yet.",
        "advice": "Give yourself time before making important decisions."
    },
    {
        "name": "The World",
        "symbol": "🌎",
        "meaning": "A cycle may be reaching completion.",
        "advice": "Celebrate your progress and prepare for what comes next."
    }
]


# ============================================================
# DAILY HELPERS
# ============================================================

def get_today():
    return datetime.now(TIMEZONE)


def get_daily_quote():
    day_of_year = get_today().timetuple().tm_yday

    quote = QUOTES[
        (day_of_year - 1) % len(QUOTES)
    ]

    return str(quote)


def get_daily_tarot():
    day_of_year = get_today().timetuple().tm_yday

    return TAROT_CARDS[
        (day_of_year - 1) % len(TAROT_CARDS)
    ]


# ============================================================
# FRESH INTERNET CONTENT
# ============================================================

async def get_internet_quote():
    """
    Attempts to retrieve a fresh quote from a public
    internet API.

    If the internet API is unavailable, the local
    fallback quote is returned.
    """

    url = "https://api.quotable.io/random"

    try:
        async with httpx.AsyncClient(
            timeout=8.0,
            follow_redirects=True
        ) as client:

            response = await client.get(url)

            if response.status_code == 200:

                data = response.json()

                quote = data.get("content")

                if quote:
                    return str(quote)

    except Exception as error:
        print(
            "Internet quote unavailable:",
            error
        )

    return get_daily_quote()


# ============================================================
# DAILY CONTENT
# ============================================================

async def build_daily_content(
    horoscope_name: str
):
    horoscope = HOROSCOPES.get(
        horoscope_name
    )

    if not horoscope:
        return None

    tarot = get_daily_tarot()

    internet_quote = await get_internet_quote()

    return {
        "date": get_today().date().isoformat(),

        "timezone": "Asia/Kathmandu",

        "horoscope": {
            "name": horoscope_name,
            "symbol": horoscope["symbol"],
            "vedic": horoscope["vedic"],
            "reading": horoscope["reading"]
        },

        "tarot": {
            "name": tarot["name"],
            "symbol": tarot["symbol"],
            "meaning": tarot["meaning"],
            "advice": tarot["advice"]
        },

        "quote": internet_quote
    }


# ============================================================
# ROOT
# ============================================================

@app.get("/")
async def root():

    return {
        "status": "healthy",
        "service": "Daily Aura",
        "version": "3.0.0",
        "timezone": "Asia/Kathmandu",
        "features": [
            "Daily Horoscope",
            "Daily Tarot",
            "Daily Quote",
            "Fresh Internet Quote",
            "Fallback Content"
        ]
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
async def health():

    return {
        "status": "healthy",
        "service": "Daily Aura",
        "timezone": "Asia/Kathmandu"
    }


# ============================================================
# DAILY CONTENT
# ============================================================

@app.get("/api/daily/{horoscope_name}")
async def daily_content(
    horoscope_name: str
):

    name = horoscope_name.strip().capitalize()

    if name not in HOROSCOPES:

        raise HTTPException(
            status_code=404,
            detail="Horoscope sign not found"
        )

    content = await build_daily_content(
        name
    )

    return content


# ============================================================
# COMPATIBILITY ROUTE
# ============================================================

@app.get("/daily-content/{horoscope_name}")
async def daily_content_legacy(
    horoscope_name: str
):

    name = horoscope_name.strip().capitalize()

    if name not in HOROSCOPES:

        raise HTTPException(
            status_code=404,
            detail="Horoscope sign not found"
        )

    return await build_daily_content(
        name
    )


# ============================================================
# QUOTE ONLY
# ============================================================

@app.get("/daily-quote")
async def daily_quote():

    quote = await get_internet_quote()

    return {
        "quote": str(quote),
        "date": get_today().date().isoformat()
    }


# ============================================================
# TAROT ONLY
# ============================================================

@app.get("/daily-tarot")
async def daily_tarot():

    return {
        "date": get_today().date().isoformat(),
        "tarot": get_daily_tarot()
    }


# ============================================================
# HOROSCOPE LIST
# ============================================================

@app.get("/horoscopes")
async def horoscopes():

    return {
        "signs": list(HOROSCOPES.keys())
    }


# ============================================================
# REMOVE OLD NOTIFICATION SYSTEM
# ============================================================

@app.get("/notifications")
async def notifications_removed():

    return {
        "enabled": False,
        "message": "Notifications have been removed from Daily Aura."
    }
```
