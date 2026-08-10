```python
import os
import json
from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

try:
    from pywebpush import webpush, WebPushException
    PYWEBPUSH_AVAILABLE = True
except ImportError:
    webpush = None
    WebPushException = Exception
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

# Temporary memory storage.
# Subscriptions disappear when Render restarts.
subscriptions = {}


# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="Daily Aura API",
    version="3.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# HOROSCOPE DATA
# ============================================================

HOROSCOPES = {
    "Aries": {
        "symbol": "♈",
        "vedic": "Mesha",
        "reading": (
            "Today is a good day to take initiative. "
            "Trust your ideas and move forward with confidence."
        )
    },
    "Taurus": {
        "symbol": "♉",
        "vedic": "Vrishabha",
        "reading": (
            "Patience can bring better results today. "
            "Focus on steady progress."
        )
    },
    "Gemini": {
        "symbol": "♊",
        "vedic": "Mithuna",
        "reading": (
            "Communication is your strength today. "
            "A conversation may open a new opportunity."
        )
    },
    "Cancer": {
        "symbol": "♋",
        "vedic": "Karka",
        "reading": (
            "Listen to your intuition today. "
            "Spend quality time with people you care about."
        )
    },
    "Leo": {
        "symbol": "♌",
        "vedic": "Simha",
        "reading": (
            "Your confidence can attract attention today. "
            "Use your energy wisely."
        )
    },
    "Virgo": {
        "symbol": "♍",
        "vedic": "Kanya",
        "reading": (
            "Small details matter today. "
            "Organize your priorities and stay focused."
        )
    },
    "Libra": {
        "symbol": "♎",
        "vedic": "Tula",
        "reading": (
            "Balance is important today. "
            "Think carefully before making decisions."
        )
    },
    "Scorpio": {
        "symbol": "♏",
        "vedic": "Vrishchika",
        "reading": (
            "Your determination is strong today. "
            "Focus that energy on one meaningful goal."
        )
    },
    "Sagittarius": {
        "symbol": "♐",
        "vedic": "Dhanu",
        "reading": (
            "A fresh perspective can change your day. "
            "Stay curious and explore new ideas."
        )
    },
    "Capricorn": {
        "symbol": "♑",
        "vedic": "Makara",
        "reading": (
            "Consistent effort is your advantage today. "
            "Keep working toward your long-term goals."
        )
    },
    "Aquarius": {
        "symbol": "♒",
        "vedic": "Kumbha",
        "reading": (
            "An original idea may be worth pursuing today. "
            "Share your thoughts with others."
        )
    },
    "Pisces": {
        "symbol": "♓",
        "vedic": "Meena",
        "reading": (
            "Your creativity and empathy are strong today. "
            "Give yourself some quiet time."
        )
    }
}


# ============================================================
# DAILY QUOTES
# ============================================================

QUOTES = [
    "Small steps every day create big changes.",
    "Your future is created by what you do today.",
    "A calm mind can find a way forward.",
    "Believe in the progress you cannot yet see.",
    "Start where you are. Make today count.",
    "You don't need to be perfect. Just keep moving.",
    "Every morning is another chance to begin again.",
    "A peaceful mind sees possibilities others miss.",
    "Progress matters more than perfection.",
    "Today can be the beginning of something better.",
    "Trust your journey and keep moving forward.",
    "Your effort today becomes your strength tomorrow.",
    "Give yourself permission to grow slowly.",
    "Good things often begin with one small decision."
]


# ============================================================
# TAROT CARDS
# ============================================================

TAROT_CARDS = [
    {
        "name": "The Fool",
        "symbol": "🌟",
        "meaning": "A new beginning is opening before you.",
        "advice": "Don't be afraid to start something new."
    },
    {
        "name": "The Magician",
        "symbol": "✨",
        "meaning": "You have the skills and resources needed.",
        "advice": "Use what you already have and take action."
    },
    {
        "name": "The High Priestess",
        "symbol": "🌙",
        "meaning": "Your intuition is especially strong today.",
        "advice": "Slow down and listen to your intuition."
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
        "meaning": "Structure and discipline can create stability.",
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
        "meaning": "Determination can move you forward.",
        "advice": "Stay focused on your direction."
    },
    {
        "name": "Strength",
        "symbol": "🦁",
        "meaning": "Real strength comes from patience and confidence.",
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
        "meaning": "Positive energy, clarity and confidence surround you.",
        "advice": "Let yourself enjoy today's good moments."
    },
    {
        "name": "The Moon",
        "symbol": "🌙",
        "meaning": "Not everything is clear yet.",
        "advice": "Give yourself time before making decisions."
    },
    {
        "name": "The World",
        "symbol": "🌎",
        "meaning": "A cycle may be reaching completion.",
        "advice": "Celebrate your progress and prepare for what's next."
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
# DATE / DAILY CONTENT HELPERS
# ============================================================

def get_today():
    return datetime.now(TIMEZONE)


def get_daily_quote():
    day_of_year = get_today().timetuple().tm_yday

    return QUOTES[
        (day_of_year - 1) % len(QUOTES)
    ]


def get_daily_tarot():
    day_of_year = get_today().timetuple().tm_yday

    return TAROT_CARDS[
        (day_of_year - 1) % len(TAROT_CARDS)
    ]


def get_daily_content(horoscope_name):
    horoscope = HOROSCOPES.get(horoscope_name)

    if not horoscope:
        return None

    tarot = get_daily_tarot()
    quote = get_daily_quote()

    return {
        "date": get_today().date().isoformat(),

        "horoscope": {
            "name": horoscope_name,
            "symbol": horoscope["symbol"],
            "vedic": horoscope["vedic"],
            "reading": horoscope["reading"]
        },

        "tarot": tarot,

        "quote": quote
    }


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():
    return {
        "status": "healthy",
        "service": "Daily Aura",
        "version": "3.0.0",
        "timezone": "Asia/Kathmandu",
        "message": "Daily Aura backend is online."
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "Daily Aura",
        "timezone": "Asia/Kathmandu",
        "subscriptions": len(subscriptions),
        "pywebpush_available": PYWEBPUSH_AVAILABLE,
        "vapid_configured": bool(VAPID_PRIVATE_KEY)
    }


# ============================================================
# VAPID PUBLIC KEY
# ============================================================

@app.get("/vapid-public-key")
def vapid_public_key():
    if not VAPID_PUBLIC_KEY:
        raise HTTPException(
            status_code=500,
            detail="VAPID public key is not configured."
        )

    return {
        "publicKey": VAPID_PUBLIC_KEY
    }


# ============================================================
# DAILY TAROT
# ============================================================

@app.get("/daily-tarot")
def daily_tarot():
    return {
        "date": get_today().date().isoformat(),
        "tarot": get_daily_tarot()
    }


# ============================================================
# DAILY QUOTE
# ============================================================

@app.get("/daily-quote")
def daily_quote():
    return {
        "date": get_today().date().isoformat(),
        "quote": get_daily_quote()
    }


# ============================================================
# DAILY CONTENT
# ============================================================

@app.get("/daily-content/{horoscope_name}")
def daily_content(horoscope_name: str):

    name = horoscope_name.strip().capitalize()

    content = get_daily_content(name)

    if content is None:
        raise HTTPException(
            status_code=404,
            detail="Horoscope sign not found."
        )

    return content


# ============================================================
# API DAILY CONTENT
# ============================================================

@app.get("/api/daily/{horoscope_name}")
def api_daily_content(horoscope_name: str):

    name = horoscope_name.strip().capitalize()

    content = get_daily_content(name)

    if content is None:
        raise HTTPException(
            status_code=404,
            detail="Horoscope sign not found."
        )

    return content


# ============================================================
# SUBSCRIBE
# ============================================================

@app.post("/subscribe")
@app.post("/api/subscribe")
def subscribe(data: SubscribeRequest):

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
            detail="Subscription endpoint is required."
        )

    subscriptions[endpoint] = {
        "subscription": data.subscription.model_dump(),
        "horoscope": horoscope,
        "language": data.language,
        "created_at": get_today().isoformat()
    }

    return {
        "success": True,
        "message": "Subscribed successfully.",
        "horoscope": horoscope,
        "language": data.language
    }


# ============================================================
# UNSUBSCRIBE
# ============================================================

@app.post("/unsubscribe")
@app.post("/api/unsubscribe")
def unsubscribe(data: UnsubscribeRequest):

    endpoint = data.endpoint.strip()

    removed = subscriptions.pop(
        endpoint,
        None
    )

    if removed is None:
        return {
            "success": True,
            "message": "Subscription was already removed."
        }

    return {
        "success": True,
        "message": "Unsubscribed successfully."
    }


# ============================================================
# SEND PUSH NOTIFICATION
# ============================================================

def send_notification(user_data):

    if not PYWEBPUSH_AVAILABLE:
        print(
            "pywebpush is not installed. "
            "Skipping notification."
        )
        return False

    if not VAPID_PRIVATE_KEY:
        print(
            "VAPID_PRIVATE_KEY is not configured."
        )
        return False

    subscription = user_data["subscription"]

    horoscope_name = user_data["horoscope"]

    content = get_daily_content(
        horoscope_name
    )

    if not content:
        return False

    payload = {
        "title": "Daily Aura ✨",
        "body": (
            f"{content['horoscope']['symbol']} "
            f"{horoscope_name}: "
            f"{content['horoscope']['reading']} "
            f"🃏 {content['tarot']['name']} "
            f"✨ {content['quote']}"
        ),
        "url": "/",
        "tarot": content["tarot"],
        "quote": content["quote"]
    }

    try:

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

        print(
            "Push notification failed:",
            error
        )

        return False

    except Exception as error:

        print(
            "Unexpected notification error:",
            error
        )

        return False


# ============================================================
# TEST NOTIFICATION
# ============================================================

@app.post("/test-notification/{horoscope_name}")
def test_notification(horoscope_name: str):

    name = horoscope_name.strip().capitalize()

    if name not in HOROSCOPES:
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
            "horoscope": name
        }

        if send_notification(
            temporary_data
        ):
            sent += 1

    return {
        "success": True,
        "sent": sent,
        "horoscope": name
    }


# ============================================================
# MANUAL MORNING NOTIFICATION
# ============================================================

@app.post("/send-morning-now")
def send_morning_now():

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

        if send_notification(
            user_data
        ):
            sent += 1

    return {
        "success": True,
        "message": "Morning notification test completed.",
        "sent": sent
    }


# ============================================================
# STARTUP INFORMATION
# ============================================================

@app.on_event("startup")
async def startup_event():

    print(
        "========================================"
    )

    print(
        "Daily Aura backend started"
    )

    print(
        "Timezone: Asia/Kathmandu"
    )

    print(
        "Service: Healthy"
    )

    print(
        "PyWebPush:",
        PYWEBPUSH_AVAILABLE
    )

    print(
        "VAPID configured:",
        bool(VAPID_PRIVATE_KEY)
    )

    print(
        "========================================"
    )
```
