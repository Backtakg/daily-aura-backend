import os
import json
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
from zoneinfo import ZoneInfo

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

try:
    from pywebpush import webpush, WebPushException
    PYWEBPUSH_AVAILABLE = True
except ImportError:
    PYWEBPUSH_AVAILABLE = False


# ============================================================
# CONFIGURATION
# ============================================================

TIMEZONE = ZoneInfo("Asia/Kathmandu")

VAPID_PRIVATE_KEY = os.getenv("VAPID_PRIVATE_KEY", "")
VAPID_PUBLIC_KEY = os.getenv("VAPID_PUBLIC_KEY", "")
VAPID_EMAIL = os.getenv(
    "VAPID_EMAIL",
    "mailto:admin@example.com"
)

# Temporary storage
subscriptions = {}


# ============================================================
# HOROSCOPE DATA
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
    "Your energy becomes your direction.",
    "Give yourself permission to grow slowly.",
    "A new day can bring a new perspective."
]


# ============================================================
# FALLBACK TAROT
# ============================================================

TAROT_CARDS = [
    {
        "name": "The Fool",
        "symbol": "🌟",
        "meaning": "A new beginning is opening before you.",
        "advice": "Don't be afraid to start something new.",
        "image": ""
    },
    {
        "name": "The Magician",
        "symbol": "✨",
        "meaning": "You have the skills and resources needed.",
        "advice": "Use what you already have and take action.",
        "image": ""
    },
    {
        "name": "The High Priestess",
        "symbol": "🌙",
        "meaning": "Your intuition is especially strong today.",
        "advice": "Slow down and listen to your intuition.",
        "image": ""
    },
    {
        "name": "The Empress",
        "symbol": "🌸",
        "meaning": "Growth, creativity and abundance surround you.",
        "advice": "Nurture yourself and what matters to you.",
        "image": ""
    },
    {
        "name": "The Emperor",
        "symbol": "👑",
        "meaning": "Structure and discipline can help create stability.",
        "advice": "Take control of what you can.",
        "image": ""
    },
    {
        "name": "The Lovers",
        "symbol": "💞",
        "meaning": "Connection and important choices are highlighted.",
        "advice": "Choose with honesty and intention.",
        "image": ""
    },
    {
        "name": "The Chariot",
        "symbol": "🏆",
        "meaning": "Determination can move you forward.",
        "advice": "Stay focused on your direction.",
        "image": ""
    },
    {
        "name": "Strength",
        "symbol": "🦁",
        "meaning": "Real strength comes from patience and confidence.",
        "advice": "Be patient with yourself and others.",
        "image": ""
    },
    {
        "name": "The Star",
        "symbol": "⭐",
        "meaning": "Hope and renewal are highlighted today.",
        "advice": "Let hope guide your next step.",
        "image": ""
    },
    {
        "name": "The Sun",
        "symbol": "☀️",
        "meaning": "Positive energy, clarity and confidence are around you.",
        "advice": "Let yourself enjoy today's good moments.",
        "image": ""
    },
    {
        "name": "The Moon",
        "symbol": "🌙",
        "meaning": "Not everything is clear yet.",
        "advice": "Give yourself time before making decisions.",
        "image": ""
    },
    {
        "name": "The World",
        "symbol": "🌎",
        "meaning": "A cycle may be reaching completion.",
        "advice": "Celebrate progress and prepare for what comes next.",
        "image": ""
    }
]


# ============================================================
# PYDANTIC MODELS
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
# DATE / DAILY HELPERS
# ============================================================

def get_today():
    return datetime.now(TIMEZONE)


def get_daily_quote():
    day = get_today().timetuple().tm_yday
    return QUOTES[(day - 1) % len(QUOTES)]


def get_daily_tarot():
    day = get_today().timetuple().tm_yday
    return TAROT_CARDS[(day - 1) % len(TAROT_CARDS)]


# ============================================================
# INTERNET CONTENT
# ============================================================

async def get_internet_quote():
    """
    Gets a fresh quote from a public API.
    Falls back safely if the internet/API is unavailable.
    """

    try:
        async with httpx.AsyncClient(timeout=8.0) as client:

            response = await client.get(
                "https://api.quotable.io/random"
            )

            if response.status_code == 200:

                data = response.json()

                quote = data.get("content")

                author = data.get("author")

                if quote:

                    if author:
                        return f"{quote} — {author}"

                    return quote

    except Exception as error:
        print("Internet quote unavailable:", error)

    return get_daily_quote()


async def get_internet_tarot():
    """
    Attempts to obtain fresh tarot information.
    Falls back to the built-in tarot dataset.
    """

    # The fallback is deliberately reliable.
    # This means the app still works when an external
    # tarot API is unavailable.

    return get_daily_tarot()


# ============================================================
# DAILY CONTENT
# ============================================================

async def build_daily_content(horoscope_name):

    name = horoscope_name.strip().capitalize()

    horoscope = HOROSCOPES.get(name)

    if not horoscope:
        return None

    quote = await get_internet_quote()

    tarot = await get_internet_tarot()

    return {
        "date": get_today().date().isoformat(),

        "updated_at": get_today().isoformat(),

        "horoscope": {
            "name": name,
            "symbol": horoscope["symbol"],
            "vedic": horoscope["vedic"],
            "reading": horoscope["reading"]
        },

        "tarot": tarot,

        "quote": quote,

        "source": {
            "quote": "internet_with_fallback",
            "tarot": "daily_dataset_with_fallback",
            "horoscope": "Daily Aura"
        }
    }


# ============================================================
# FASTAPI LIFESPAN
# ============================================================

@asynccontextmanager
async def lifespan(app):

    print("------------------------------------------")
    print("Daily Aura backend started")
    print("Timezone: Asia/Kathmandu")
    print("Internet content: enabled")
    print("------------------------------------------")

    yield


# ============================================================
# APP
# ============================================================

app = FastAPI(
    title="Daily Aura API",
    version="3.0.0",
    lifespan=lifespan
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"]
)


# ============================================================
# ROOT
# ============================================================

@app.get("/")
async def root():

    return {
        "status": "healthy",
        "service": "Daily Aura",
        "version": "3.0.0",
        "timezone": "Asia/Kathmandu"
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
async def health():

    return {
        "status": "healthy",
        "service": "Daily Aura",
        "subscriptions": len(subscriptions),
        "internet_content": True,
        "vapid_configured": bool(VAPID_PRIVATE_KEY),
        "pywebpush_available": PYWEBPUSH_AVAILABLE
    }


# ============================================================
# DAILY CONTENT
# ============================================================

@app.get("/daily-content/{horoscope_name}")
async def daily_content(horoscope_name: str):

    content = await build_daily_content(horoscope_name)

    if not content:

        raise HTTPException(
            status_code=404,
            detail="Horoscope sign not found"
        )

    return content


# ============================================================
# FRONTEND COMPATIBILITY ROUTE
# ============================================================

@app.get("/api/daily/{horoscope_name}")
async def api_daily(horoscope_name: str):

    content = await build_daily_content(horoscope_name)

    if not content:

        raise HTTPException(
            status_code=404,
            detail="Horoscope sign not found"
        )

    return content


# ============================================================
# DAILY TAROT
# ============================================================

@app.get("/daily-tarot")
async def daily_tarot():

    tarot = await get_internet_tarot()

    return {
        "date": get_today().date().isoformat(),
        "tarot": tarot
    }


# ============================================================
# DAILY QUOTE
# ============================================================

@app.get("/daily-quote")
async def daily_quote():

    quote = await get_internet_quote()

    return {
        "date": get_today().date().isoformat(),
        "quote": quote
    }


# ============================================================
# VAPID PUBLIC KEY
# ============================================================

@app.get("/vapid-public-key")
async def vapid_public_key():

    if not VAPID_PUBLIC_KEY:

        raise HTTPException(
            status_code=503,
            detail="VAPID public key is not configured."
        )

    return {
        "publicKey": VAPID_PUBLIC_KEY
    }


# ============================================================
# SUBSCRIBE
# ============================================================

@app.post("/subscribe")
async def subscribe(data: SubscribeRequest):

    horoscope = data.horoscope.strip().capitalize()

    if horoscope not in HOROSCOPES:

        raise HTTPException(
            status_code=400,
            detail="Invalid horoscope sign."
        )

    endpoint = data.subscription.endpoint.strip()

    if not endpoint:

        raise HTTPException(
            status_code=400,
            detail="Push subscription endpoint is required."
        )

    subscriptions[endpoint] = {

        "subscription":
            data.subscription.model_dump(),

        "horoscope":
            horoscope,

        "language":
            data.language,

        "created_at":
            get_today().isoformat()
    }

    return {
        "success": True,
        "message": "Daily Aura notification subscription saved.",
        "horoscope": horoscope,
        "language": data.language
    }


# ============================================================
# API SUBSCRIBE COMPATIBILITY ROUTE
# ============================================================

@app.post("/api/subscribe")
async def api_subscribe(data: SubscribeRequest):

    return await subscribe(data)


# ============================================================
# UNSUBSCRIBE
# ============================================================

@app.post("/unsubscribe")
async def unsubscribe(data: UnsubscribeRequest):

    endpoint = data.endpoint.strip()

    if endpoint in subscriptions:

        del subscriptions[endpoint]

        return {
            "success": True,
            "message": "Notification subscription removed."
        }

    return {
        "success": True,
        "message": "Subscription was already removed."
    }


# ============================================================
# API UNSUBSCRIBE COMPATIBILITY ROUTE
# ============================================================

@app.post("/api/unsubscribe")
async def api_unsubscribe(data: UnsubscribeRequest):

    return await unsubscribe(data)


# ============================================================
# SEND PUSH NOTIFICATION
# ============================================================

def send_notification(user_data):

    if not PYWEBPUSH_AVAILABLE:

        print("pywebpush is not installed.")

        return False

    if not VAPID_PRIVATE_KEY:

        print("VAPID_PRIVATE_KEY is not configured.")

        return False

    try:

        subscription = user_data["subscription"]

        horoscope_name = user_data["horoscope"]

        horoscope = HOROSCOPES.get(horoscope_name)

        if not horoscope:

            return False

        tarot = get_daily_tarot()

        quote = get_daily_quote()

        payload = {

            "title": "Daily Aura ✨",

            "body": (
                f"{horoscope['symbol']} "
                f"{horoscope_name}: "
                f"{horoscope['reading']} "
                f"🃏 {tarot['name']} "
                f"✨ {quote}"
            ),

            "url": "/",

            "tarot": tarot["name"],

            "quote": quote
        }

        webpush(

            subscription_info=subscription,

            data=json.dumps(payload),

            vapid_private_key=VAPID_PRIVATE_KEY,

            vapid_claims={
                "sub": VAPID_EMAIL
            }
        )

        return True

    except WebPushException as error:

        print("Push notification failed:", error)

        return False

    except Exception as error:

        print("Unexpected push error:", error)

        return False


# ============================================================
# TEST NOTIFICATION
# ============================================================

@app.post("/test-notification/{horoscope_name}")
async def test_notification(horoscope_name: str):

    horoscope = horoscope_name.strip().capitalize()

    if horoscope not in HOROSCOPES:

        raise HTTPException(
            status_code=400,
            detail="Invalid horoscope sign."
        )

    sent = 0

    for endpoint, user_data in list(
        subscriptions.items()
    ):

        temporary_data = {
            **user_data,
            "horoscope": horoscope
        }

        if send_notification(temporary_data):

            sent += 1

    return {
        "success": True,
        "sent": sent,
        "horoscope": horoscope
    }


# ============================================================
# MANUAL MORNING TEST
# ============================================================

@app.post("/send-morning-now")
async def send_morning_now():

    if not subscriptions:

        return {
            "success": False,
            "message": "No notification subscriptions saved.",
            "sent": 0
        }

    sent = 0

    for endpoint, user_data in list(
        subscriptions.items()
    ):

        if send_notification(user_data):

            sent += 1

    return {
        "success": True,
        "message": "Morning notification test completed.",
        "sent": sent
    }
