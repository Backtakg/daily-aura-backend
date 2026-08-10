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

# ============================================================

# DAILY AURA BACKEND

# ============================================================

APP_NAME = "Daily Aura"
TIMEZONE = ZoneInfo("Asia/Kathmandu")

# ============================================================

# OPTIONAL VAPID CONFIGURATION

# ============================================================

VAPID_PRIVATE_KEY = os.getenv("VAPID_PRIVATE_KEY", "")
VAPID_PUBLIC_KEY = os.getenv("VAPID_PUBLIC_KEY", "")
VAPID_EMAIL = os.getenv(
"VAPID_EMAIL",
"mailto:admin@example.com"
)

# pywebpush is optional.

try:
from pywebpush import webpush, WebPushException
PYWEBPUSH_AVAILABLE = True
except ImportError:
PYWEBPUSH_AVAILABLE = False

# ============================================================

# TEMPORARY SUBSCRIPTION STORAGE

# ============================================================

subscriptions = {}

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
"Focus on one practical goal and let consistency work in "
"your favor."
)
},
"Gemini": {
"symbol": "♊",
"vedic": "Mithuna",
"reading": (
"Communication can open an unexpected door today. "
"Listen carefully, ask questions, and don't underestimate "
"the value of a simple conversation."
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
"also means listening to others."
)
},
"Virgo": {
"symbol": "♍",
"vedic": "Kanya",
"reading": (
"Small improvements can make a noticeable difference. "
"Organize your priorities and avoid spending energy on "
"things that do not matter."
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
"Explore a new idea, learn something useful, or look at "
"an old problem from a different angle."
)
},
"Capricorn": {
"symbol": "♑",
"vedic": "Makara",
"reading": (
"Long-term thinking works in your favor today. "
"A small practical action now can support a larger goal "
"later."
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

# TAROT DATA

# ============================================================

TAROT_CARDS = [
{
"name": "The Fool",
"symbol": "🌟",
"meaning": (
"A new beginning is opening before you. "
"This card represents curiosity, freedom and the courage "
"to take the first step."
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
"Structure, responsibility and stability can help you "
"move forward."
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
"self-control rather than force."
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

# APP

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
allow_headers=["*"]
)

# ============================================================

# TIME / DAILY HELPERS

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
"""
Fetches a daily quote from ZenQuotes.

```
If the internet service fails, Daily Aura uses
local fallback content instead.
"""

url = "https://zenquotes.io/api/today"

try:
    timeout = httpx.Timeout(8.0)

    async with httpx.AsyncClient(
        timeout=timeout,
        follow_redirects=True
    ) as client:

        response = await client.get(url)

        if response.status_code != 200:
            return get_fallback_quote()

        data = response.json()

        if isinstance(data, list) and len(data) > 0:

            item = data[0]

            quote = item.get("q")
            author = item.get("a")

            if quote:

                return {
                    "quote": quote,
                    "author": author or "Unknown",
                    "source": "ZenQuotes"
                }

except Exception as error:
    print("Quote API unavailable:", error)

fallback = get_fallback_quote()

fallback["source"] = "Daily Aura fallback"

return fallback
```

# ============================================================

# INTERNET ON THIS DAY DATA

# ============================================================

async def fetch_on_this_day():
"""
Fetches current-date historical events from
the free ZenQuotes On This Day API.

```
The result is used as an extra fresh internet-based
Daily Aura section.
"""

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

        return {
            "source": "ZenQuotes On This Day",
            "date": f"{month:02d}-{day:02d}",
            "events": data.get("data", {}).get(
                "Events",
                []
            )[:3],
            "births": data.get("data", {}).get(
                "Births",
                []
            )[:3]
        }

except Exception as error:
    print("On This Day API unavailable:", error)

return None
```

# ============================================================

# DAILY CONTENT

# ============================================================

async def build_daily_content(horoscope_name: str):

```
horoscope = HOROSCOPES.get(horoscope_name)

if not horoscope:
    return None

today = get_today()

tarot = get_daily_tarot()

quote = await fetch_internet_quote()

historical = await fetch_on_this_day()

return {
    "date": today.date().isoformat(),
    "timezone": "Asia/Kathmandu",

    "horoscope": {
        "name": horoscope_name,
        "symbol": horoscope["symbol"],
        "vedic": horoscope["vedic"],
        "reading": horoscope["reading"]
    },

    "tarot": tarot,

    "quote": quote,

    "internet": {
        "fresh": True,
        "on_this_day": historical
    }
}
```

# ============================================================

# ROOT / HEALTH

# ============================================================

@app.get("/")
async def root():

```
return {
    "status": "healthy",
    "service": APP_NAME,
    "version": "3.0.0",
    "timezone": "Asia/Kathmandu"
}
```

@app.get("/health")
async def health():

```
return {
    "status": "healthy",
    "service": APP_NAME,
    "timezone": "Asia/Kathmandu",
    "subscriptions": len(subscriptions),
    "vapid_configured": bool(VAPID_PRIVATE_KEY),
    "pywebpush_available": PYWEBPUSH_AVAILABLE
}
```

# ============================================================

# VAPID PUBLIC KEY

# ============================================================

@app.get("/vapid-public-key")
async def vapid_public_key():

```
if not VAPID_PUBLIC_KEY:

    raise HTTPException(
        status_code=404,
        detail="VAPID public key is not configured."
    )

return {
    "publicKey": VAPID_PUBLIC_KEY
}
```

# ============================================================

# DAILY CONTENT

# ============================================================

@app.get("/daily-content/{horoscope}")
async def daily_content(horoscope: str):

```
name = horoscope.strip().capitalize()

content = await build_daily_content(name)

if not content:

    raise HTTPException(
        status_code=404,
        detail="Horoscope sign not found."
    )

return content
```

# ============================================================

# COMPATIBILITY ROUTE

# ============================================================

@app.get("/api/daily/{horoscope_name}")
async def api_daily(horoscope_name: str):

```
name = horoscope_name.strip().capitalize()

content = await build_daily_content(name)

if not content:

    raise HTTPException(
        status_code=404,
        detail="Horoscope sign not found."
    )

return content
```

# ============================================================

# DAILY TAROT ONLY

# ============================================================

@app.get("/daily-tarot")
async def daily_tarot():

```
tarot = get_daily_tarot()

return {
    "date": get_today().date().isoformat(),
    "timezone": "Asia/Kathmandu",
    "tarot": tarot
}
```

# ============================================================

# DAILY QUOTE ONLY

# ============================================================

@app.get("/daily-quote")
async def daily_quote():

```
quote = await fetch_internet_quote()

return {
    "date": get_today().date().isoformat(),
    "timezone": "Asia/Kathmandu",
    "quote": quote
}
```

# ============================================================

# ON THIS DAY

# ============================================================

@app.get("/on-this-day")
async def on_this_day():

```
data = await fetch_on_this_day()

if not data:

    return {
        "date": get_today().date().isoformat(),
        "available": False,
        "message": "Internet history service unavailable."
    }

return {
    "available": True,
    "data": data
}
```

# ============================================================

# ALL SIGNS

# ============================================================

@app.get("/horoscopes")
async def all_horoscopes():

```
return {
    "date": get_today().date().isoformat(),
    "horoscopes": [
        {
            "name": name,
            "symbol": data["symbol"],
            "vedic": data["vedic"]
        }
        for name, data in HOROSCOPES.items()
    ]
}
```

# ============================================================

# SUBSCRIBE

# ============================================================

@app.post("/subscribe")
async def subscribe(data: SubscribeRequest):

```
horoscope = data.horoscope.strip().capitalize()

if horoscope not in HOROSCOPES:

    raise HTTPException(
        status_code=400,
        detail="Invalid horoscope sign."
    )

endpoint = data.subscription.endpoint

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
```

# ============================================================

# API SUBSCRIBE COMPATIBILITY

# ============================================================

@app.post("/api/subscribe")
async def api_subscribe(data: SubscribeRequest):

```
return await subscribe(data)
```

# ============================================================

# UNSUBSCRIBE

# ============================================================

@app.post("/unsubscribe")
async def unsubscribe(data: UnsubscribeRequest):

```
endpoint = data.endpoint

if endpoint in subscriptions:

    del subscriptions[endpoint]

    return {
        "success": True,
        "message": "Unsubscribed successfully."
    }

return {
    "success": True,
    "message": "Subscription was already removed."
}
```

# ============================================================

# API UNSUBSCRIBE COMPATIBILITY

# ============================================================

@app.post("/api/unsubscribe")
async def api_unsubscribe(data: UnsubscribeRequest):

```
return await unsubscribe(data)
```

# ============================================================

# OPTIONAL PUSH NOTIFICATION

# ============================================================

def send_push_notification(user_data):

```
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

    payload = {
        "title": "Daily Aura ✨",
        "body": (
            f"{horoscope['symbol']} "
            f"{horoscope_name}: "
            f"{horoscope['reading']} "
            f"🃏 Tarot: {tarot['name']}"
        ),
        "url": "/",
        "tarot": tarot["name"],
        "tarot_image": tarot["image_url"]
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

except Exception as error:

    print("Unexpected push error:", error)

return False
```

# ============================================================

# SEND TEST NOTIFICATION

# ============================================================

@app.post("/test-notification/{horoscope}")
async def test_notification(horoscope: str):

```
name = horoscope.strip().capitalize()

if name not in HOROSCOPES:

    raise HTTPException(
        status_code=400,
        detail="Invalid horoscope sign."
    )

sent = 0

for _, user_data in list(
    subscriptions.items()
):

    temporary_data = {
        **user_data,
        "horoscope": name
    }

    if send_push_notification(
        temporary_data
    ):

        sent += 1

return {
    "success": True,
    "sent": sent,
    "horoscope": name
}
```

# ============================================================

# MANUAL MORNING TEST

# ============================================================

@app.post("/send-morning-now")
async def send_morning_now():

```
if not subscriptions:

    return {
        "success": False,
        "message": "No notification subscriptions saved.",
        "sent": 0
    }

sent = 0

for _, user_data in list(
    subscriptions.items()
):

    if send_push_notification(
        user_data
    ):

        sent += 1

return {
    "success": True,
    "message": "Morning notification test completed.",
    "sent": sent
}
```

# ============================================================

# SCHEDULER

# ============================================================

async def notification_scheduler():

```
last_sent_date = None

while True:

    try:

        now = get_today()

        current_date = now.date()

        if (
            now.hour == 8
            and now.minute == 0
            and last_sent_date != current_date
        ):

            print(
                "Sending Daily Aura notifications..."
            )

            for _, user_data in list(
                subscriptions.items()
            ):

                send_push_notification(
                    user_data
                )

            last_sent_date = current_date

    except Exception as error:

        print(
            "Scheduler error:",
            error
        )

    await asyncio.sleep(20)
```

# ============================================================

# LIFESPAN

# ============================================================

@asynccontextmanager
async def lifespan(application: FastAPI):

```
scheduler_task = asyncio.create_task(
    notification_scheduler()
)

print("----------------------------------------")
print("Daily Aura backend started")
print("Timezone: Asia/Kathmandu")
print("Morning notification: 08:00")
print("Internet content: enabled")
print("----------------------------------------")

try:

    yield

finally:

    scheduler_task.cancel()

    try:

        await scheduler_task

    except asyncio.CancelledError:

        pass
```

# ============================================================

# APPLY LIFESPAN

# ============================================================

app.router.lifespan_context = lifespan
