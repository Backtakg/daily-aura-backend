import os
import json
import asyncio
import urllib.request
import urllib.parse
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
# CONFIGURATION
# ============================================================

TIMEZONE = ZoneInfo("Asia/Kathmandu")

VAPID_PRIVATE_KEY = os.getenv(
    "VAPID_PRIVATE_KEY",
    ""
)

VAPID_PUBLIC_KEY = os.getenv(
    "VAPID_PUBLIC_KEY",
    ""
)

VAPID_EMAIL = os.getenv(
    "VAPID_EMAIL",
    "mailto:admin@example.com"
)


# ============================================================
# TEMPORARY STORAGE
# ============================================================

subscriptions = {}

# Cache today's internet content in memory.
daily_cache = {}

# Remember quotes already seen during this server session.
used_quotes = set()


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
    allow_credentials=False,
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
# LOCAL FALLBACK QUOTES
# ============================================================

QUOTES = [
    "Small steps every day create big changes.",
    "Your future is created by what you do today.",
    "A calm mind can find a way forward.",
    "Believe in the progress you cannot yet see.",
    "Start where you are. Make today count.",
    "You don't need to be perfect. Just keep moving.",
    "Every morning is another chance to begin again.",
    "A new day gives you another chance to grow.",
    "Keep going. Your progress matters.",
    "Good things often begin with one small decision."
]


# ============================================================
# LOCAL FALLBACK TAROT
# ============================================================

TAROT_CARDS = [
    {
        "name": "The Fool",
        "symbol": "🌟",
        "meaning": "A new beginning is opening before you.",
        "advice": "Do not be afraid to start something new."
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
        "meaning": "Your intuition is especially strong.",
        "advice": "Slow down and listen to yourself."
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
        "meaning": "Structure and discipline can help you.",
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
        "meaning": "Positive energy and clarity surround you.",
        "advice": "Enjoy today's good moments."
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
        "advice": "Celebrate your progress and prepare for what comes next."
    }
]


# ============================================================
# REQUEST MODELS
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
# DATE HELPERS
# ============================================================

def get_today():
    return datetime.now(TIMEZONE)


def get_today_string():
    return get_today().date().isoformat()


# ============================================================
# INTERNET JSON FETCHER
# ============================================================

def fetch_json(url, timeout=8):
    try:
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": "DailyAura/3.0"
            }
        )

        with urllib.request.urlopen(
            request,
            timeout=timeout
        ) as response:

            status = response.status

            if status < 200 or status >= 300:
                print(
                    "Internet API returned status:",
                    status,
                    url
                )
                return None

            raw = response.read().decode(
                "utf-8"
            )

            return json.loads(raw)

    except Exception as error:

        print(
            "Internet API failed:",
            url,
            str(error)
        )

        return None


# ============================================================
# FRESH INTERNET QUOTE
# ============================================================

def get_internet_quote():

    url = (
        "https://api.quotable.io/"
        "quotes/random?limit=5"
    )

    data = fetch_json(url)

    if not data:
        return None

    if not isinstance(data, list):
        return None

    candidates = []

    for item in data:

        if not isinstance(item, dict):
            continue

        text = item.get("content")
        author = item.get("author")

        if not text:
            continue

        if text in used_quotes:
            continue

        candidates.append(
            {
                "text": text,
                "author": author or "Unknown",
                "source": "Quotable"
            }
        )

    if not candidates:
        return None

    selected = candidates[0]

    used_quotes.add(
        selected["text"]
    )

    return selected


# ============================================================
# FRESH QUOTE WITH FALLBACK
# ============================================================

def get_fresh_quote():

    internet_quote = get_internet_quote()

    if internet_quote:

        return internet_quote

    day = get_today().timetuple().tm_yday

    fallback = QUOTES[
        (day - 1) % len(QUOTES)
    ]

    return {
        "text": fallback,
        "author": "Daily Aura",
        "source": "Daily Aura fallback"
    }


# ============================================================
# INTERNET TAROT
# ============================================================

def get_internet_tarot():

    urls = [
        "https://tarotapi.dev/api/v1/cards/random",
        "https://tarotapi.dev/api/v1/cards"
    ]

    # First try the random card endpoint.
    data = fetch_json(urls[0])

    if data:

        card = data

        if isinstance(data, dict):

            if isinstance(
                data.get("card"),
                dict
            ):
                card = data["card"]

            elif isinstance(
                data.get("data"),
                dict
            ):
                card = data["data"]

        if isinstance(card, dict):

            name = (
                card.get("name")
                or card.get("title")
            )

            if name:

                return normalize_tarot_card(
                    card
                )

    return None


# ============================================================
# NORMALIZE TAROT DATA
# ============================================================

def normalize_tarot_card(card):

    name = (
        card.get("name")
        or card.get("title")
        or "Tarot Card"
    )

    meaning = (
        card.get("meaning")
        or card.get("description")
        or card.get("desc")
        or "Reflect on the symbolism of this card."
    )

    advice = (
        card.get("advice")
        or card.get("interpretation")
        or card.get("meaning")
        or "Take a moment to reflect before acting."
    )

    symbol = (
        card.get("symbol")
        or "🃏"
    )

    image = (
        card.get("image")
        or card.get("image_url")
        or card.get("imageUrl")
        or card.get("img")
        or None
    )

    return {
        "name": name,
        "symbol": symbol,
        "meaning": meaning,
        "advice": advice,
        "image": image,
        "source": "Tarot API"
    }


# ============================================================
# DAILY TAROT
# ============================================================

def get_daily_tarot():

    today = get_today()

    date_key = today.date().isoformat()

    cache_key = (
        "tarot",
        date_key
    )

    if cache_key in daily_cache:
        return daily_cache[cache_key]

    # Try internet.
    internet_tarot = get_internet_tarot()

    if internet_tarot:

        daily_cache[cache_key] = internet_tarot

        return internet_tarot

    # Local fallback.
    day = today.timetuple().tm_yday

    tarot = TAROT_CARDS[
        (day - 1) % len(TAROT_CARDS)
    ].copy()

    tarot["image"] = None
    tarot["source"] = "Daily Aura fallback"

    daily_cache[cache_key] = tarot

    return tarot


# ============================================================
# DAILY HOROSCOPE
# ============================================================

def get_daily_horoscope(
    horoscope_name
):

    horoscope = HOROSCOPES.get(
        horoscope_name
    )

    if not horoscope:
        return None

    # Local daily variation.
    day = get_today().timetuple().tm_yday

    variations = [
        "Focus on what you can control today.",
        "A thoughtful decision may open a useful opportunity.",
        "Give yourself time to think before reacting.",
        "Stay open to a small change that could improve your day.",
        "Your consistency can matter more than speed today.",
        "A calm approach can help you handle today's challenges.",
        "Trust your experience while remaining open to new ideas."
    ]

    variation = variations[
        (day - 1) % len(variations)
    ]

    return {
        "name": horoscope_name,
        "symbol": horoscope["symbol"],
        "vedic": horoscope["vedic"],
        "reading": (
            horoscope["reading"]
            + " "
            + variation
        ),
        "source": "Daily Aura"
    }


# ============================================================
# COMPLETE DAILY CONTENT
# ============================================================

def get_daily_content(
    horoscope_name
):

    horoscope_name = horoscope_name.capitalize()

    if horoscope_name not in HOROSCOPES:
        return None

    today = get_today_string()

    cache_key = (
        "content",
        today,
        horoscope_name
    )

    if cache_key in daily_cache:
        return daily_cache[cache_key]

    horoscope = get_daily_horoscope(
        horoscope_name
    )

    tarot = get_daily_tarot()

    quote = get_fresh_quote()

    result = {

        "date": today,

        "timezone":
            "Asia/Kathmandu",

        "horoscope":
            horoscope,

        "tarot":
            tarot,

        "quote":
            quote,

        "fresh":
            True

    }

    daily_cache[cache_key] = result

    return result


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
        "internet_content": True
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health():

    return {
        "status": "healthy",
        "service": "Daily Aura",
        "version": "3.0.0",
        "timezone": "Asia/Kathmandu",
        "date": get_today_string(),
        "internet_content": True,
        "push_notifications":
            PYWEBPUSH_AVAILABLE,
        "vapid_configured":
            bool(VAPID_PRIVATE_KEY)
    }


# ============================================================
# DAILY CONTENT
# ============================================================

@app.get(
    "/daily-content/{horoscope_name}"
)
def daily_content(
    horoscope_name: str
):

    content = get_daily_content(
        horoscope_name
    )

    if not content:

        raise HTTPException(
            status_code=404,
            detail="Horoscope sign not found"
        )

    return content


# ============================================================
# API DAILY CONTENT
# ============================================================

@app.get(
    "/api/daily/{horoscope_name}"
)
def api_daily_content(
    horoscope_name: str
):

    content = get_daily_content(
        horoscope_name
    )

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
def daily_tarot():

    return {
        "date": get_today_string(),
        "tarot": get_daily_tarot()
    }


# ============================================================
# DAILY QUOTE
# ============================================================

@app.get("/daily-quote")
def daily_quote():

    return {
        "date": get_today_string(),
        "quote": get_fresh_quote()
    }


# ============================================================
# VAPID PUBLIC KEY
# ============================================================

@app.get("/vapid-public-key")
def vapid_public_key():

    if not VAPID_PUBLIC_KEY:

        raise HTTPException(
            status_code=500,
            detail=(
                "VAPID public key is not configured."
            )
        )

    return {
        "publicKey":
            VAPID_PUBLIC_KEY
    }


# ============================================================
# SUBSCRIBE
# ============================================================

@app.post("/subscribe")
def subscribe(
    data: SubscribeRequest
):

    horoscope = data.horoscope.capitalize()

    if horoscope not in HOROSCOPES:

        raise HTTPException(
            status_code=400,
            detail="Invalid horoscope sign."
        )

    endpoint = (
        data.subscription.endpoint
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
        "message":
            "Subscribed successfully.",
        "horoscope":
            horoscope,
        "language":
            data.language
    }


# ============================================================
# API SUBSCRIBE
# ============================================================

@app.post("/api/subscribe")
def api_subscribe(
    data: SubscribeRequest
):

    return subscribe(data)


# ============================================================
# UNSUBSCRIBE
# ============================================================

@app.post("/unsubscribe")
def unsubscribe(
    data: UnsubscribeRequest
):

    if data.endpoint in subscriptions:

        del subscriptions[
            data.endpoint
        ]

        return {
            "success": True,
            "message":
                "Unsubscribed successfully."
        }

    return {
        "success": True,
        "message":
            "Subscription was already removed."
    }


# ============================================================
# API UNSUBSCRIBE
# ============================================================

@app.post("/api/unsubscribe")
def api_unsubscribe(
    data: UnsubscribeRequest
):

    return unsubscribe(data)


# ============================================================
# SEND PUSH NOTIFICATION
# ============================================================

def send_notification(
    user_data
):

    if not PYWEBPUSH_AVAILABLE:

        print(
            "pywebpush is not installed."
        )

        return False

    if not VAPID_PRIVATE_KEY:

        print(
            "VAPID_PRIVATE_KEY is not configured."
        )

        return False

    content = get_daily_content(
        user_data["horoscope"]
    )

    if not content:
        return False

    subscription = (
        user_data["subscription"]
    )

    payload = {

        "title":
            "Daily Aura ✨",

        "body":
            (
                content["horoscope"]["symbol"]
                + " "
                + content["horoscope"]["name"]
                + ": "
                + content["horoscope"]["reading"]
                + " 🃏 "
                + content["tarot"]["name"]
                + " ✨ "
                + content["quote"]["text"]
            ),

        "url": "/",

        "tarot":
            content["tarot"],

        "quote":
            content["quote"],

        "horoscope":
            content["horoscope"]

    }

    try:

        webpush(

            subscription_info=
                subscription,

            data=json.dumps(
                payload
            ),

            vapid_private_key=
                VAPID_PRIVATE_KEY,

            vapid_claims={
                "sub":
                    VAPID_EMAIL
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
            "Notification error:",
            error
        )

        return False


# ============================================================
# SEND MORNING NOTIFICATIONS
# ============================================================

def send_morning_notifications():

    print(
        "===================================="
    )

    print(
        "Daily Aura morning notifications"
    )

    print(
        "Time:",
        get_today().isoformat()
    )

    print(
        "Subscribers:",
        len(subscriptions)
    )

    print(
        "===================================="
    )

    for endpoint, user_data in list(
        subscriptions.items()
    ):

        success = send_notification(
            user_data
        )

        if success:

            print(
                "Notification sent:",
                user_data["horoscope"]
            )

        else:

            print(
                "Notification failed:",
                user_data["horoscope"]
            )


# ============================================================
# SCHEDULER
# ============================================================

async def notification_scheduler():

    last_sent_date = None

    while True:

        now = datetime.now(
            TIMEZONE
        )

        current_date = now.date()

        if (
            now.hour == 8
            and now.minute == 0
            and last_sent_date != current_date
        ):

            try:

                send_morning_notifications()

                last_sent_date = (
                    current_date
                )

            except Exception as error:

                print(
                    "Scheduler error:",
                    error
                )

        await asyncio.sleep(20)


# ============================================================
# FASTAPI LIFESPAN
# ============================================================

@asynccontextmanager
async def lifespan(app):

    scheduler_task = asyncio.create_task(
        notification_scheduler()
    )

    print(
        "-----------------------------------"
    )

    print(
        "Daily Aura backend started"
    )

    print(
        "Timezone: Asia/Kathmandu"
    )

    print(
        "Morning notification: 08:00"
    )

    print(
        "Internet content: ENABLED"
    )

    print(
        "-----------------------------------"
    )

    try:

        yield

    finally:

        scheduler_task.cancel()

        try:

            await scheduler_task

        except asyncio.CancelledError:

            pass


app.router.lifespan_context = lifespan
