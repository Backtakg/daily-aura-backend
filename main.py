import os
import json
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

try:
    from pywebpush import webpush, WebPushException
    PYWEBPUSH_AVAILABLE = True
except ImportError:
    PYWEBPUSH_AVAILABLE = False

# ============================================================
# CONFIGURATION & STORAGE
# ============================================================

TIMEZONE = ZoneInfo("Asia/Kathmandu")

VAPID_PRIVATE_KEY = os.getenv("VAPID_PRIVATE_KEY", "")
VAPID_PUBLIC_KEY = os.getenv("VAPID_PUBLIC_KEY", "")
VAPID_EMAIL = os.getenv("VAPID_EMAIL", "mailto:admin@example.com")

# Temporary in-memory storage for subscriptions
subscriptions = {}

# ============================================================
# APP INITIALIZATION
# ============================================================

app = FastAPI(title="Daily Aura API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# APP DATASETS
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

QUOTES = [
    "Small steps every day create big changes.",
    "Your future is created by what you do today.",
    "A calm mind can find a way forward.",
    "Believe in the progress you cannot yet see.",
    "Start where you are. Make today count.",
    "You don't need to be perfect. Just keep moving.",
    "Every morning is another chance to begin again."
]

TAROT_CARDS = [
    {"name": "The Fool", "symbol": "🌟", "meaning": "A new beginning is opening before you.", "advice": "Don't be afraid to start something new."},
    {"name": "The Magician", "symbol": "✨", "meaning": "You have the skills and resources needed.", "advice": "Use what you already have."},
    {"name": "The High Priestess", "symbol": "🌙", "meaning": "Your intuition is especially strong.", "advice": "Slow down and listen."},
    {"name": "The Empress", "symbol": "🌸", "meaning": "Growth, creativity and abundance surround you.", "advice": "Nurture yourself."},
    {"name": "The Emperor", "symbol": "👑", "meaning": "Structure and discipline can help you.", "advice": "Take control of what you can."},
    {"name": "The Lovers", "symbol": "💞", "meaning": "Connection and important choices are highlighted.", "advice": "Choose with honesty."},
    {"name": "The Chariot", "symbol": "🏆", "meaning": "Determination can move you forward.", "advice": "Stay focused on your direction."},
    {"name": "Strength", "symbol": "🦁", "meaning": "Real strength comes from patience.", "advice": "Be patient with yourself."},
    {"name": "The Star", "symbol": "⭐", "meaning": "Hope and renewal are highlighted today.", "advice": "Let hope guide your next step."},
    {"name": "The Sun", "symbol": "☀️", "meaning": "Positive energy, clarity and confidence abound.", "advice": "Enjoy today's good moments."},
    {"name": "The Moon", "symbol": "🌙", "meaning": "Not everything is clear yet.", "advice": "Give yourself time before choosing."},
    {"name": "The World", "symbol": "🌎", "meaning": "A cycle may be reaching completion.", "advice": "Celebrate progress."}
]

# ============================================================
# PYDANTIC PARSING MODELS
# ============================================================

class PushSubscription(BaseModel):
    endpoint: str
    keys: dict

class SubscribeRequest(BaseModel):
    subscription: PushSubscription
    horoscope: str
    language: str = "en"

class UnsubscribeRequest(BaseModel):
    endpoint: str

# ============================================================
# INTERNAL ALGORITHMS
# ============================================================

def get_today():
    return datetime.now(TIMEZONE)

def get_daily_quote():
    day_of_year = get_today().timetuple().tm_yday
    return QUOTES[(day_of_year - 1) % len(QUOTES)]

def get_daily_tarot():
    day_of_year = get_today().timetuple().tm_yday
    return TAROT_CARDS[(day_of_year - 1) % len(TAROT_CARDS)]

def get_daily_content(horoscope_name):
    horoscope = HOROSCOPES.get(horoscope_name)
    if not horoscope:
        return None

    return {
        "date": get_today().date().isoformat(),
        "horoscope": {
            "name": horoscope_name,
            "symbol": horoscope["symbol"],
            "vedic": horoscope["vedic"],
            "reading": horoscope["reading"]
        },
        "tarot": get_daily_tarot(),
        "quote": get_daily_quote()
    }

# ============================================================
# INTERACTIVE API ROUTE PATHS
# ============================================================

@app.get("/")
def health_check():
    return {"status": "healthy", "service": "Daily Aura"}

@app.get("/api/daily/{horoscope_name}")
def get_daily_dashboard(horoscope_name: str):
    name = horoscope_name.capitalize()
    content = get_daily_content(name)
    if not content:
        raise HTTPException(status_code=404, detail="Horoscope sign not found")
    return content

@app.post("/api/subscribe")
def subscribe(data: SubscribeRequest):
    endpoint = data.subscription.endpoint
    subscriptions[endpoint] = {
        "subscription": data.subscription.model_dump(),
        "horoscope": data.horoscope.capitalize(),
        "language": data.language
    }
    return {"message": "Subscribed successfully"}

@app.post("/api/unsubscribe")
def unsubscribe(data: UnsubscribeRequest):
    if data.endpoint in subscriptions:
        del subscriptions[data.endpoint]
        return {"message": "Unsubscribed successfully"}
    raise HTTPException(status_code=404, detail="Endpoint not found")
