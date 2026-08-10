import os
import json
import asyncio
import hashlib
from contextlib import asynccontextmanager
from datetime import datetime
from zoneinfo import ZoneInfo

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Optional Web Push support

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

# External free content API

HOROSCOPE_API = (
"https://freehoroscopeapi.com/api/v1/get-horoscope/daily"
)

# Public quote API

QUOTE_API = "https://dummyjson.com/quotes/random"

HTTP_TIMEOUT = 10.0

# ============================================================

# TEMPORARY SUBSCRIPTION STORAGE

# ============================================================

subscriptions = {}

# ============================================================

# ZODIAC DATA

# ============================================================

HOROSCOPES = {
"Aries": {
"symbol": "♈",
"vedic": "Mesha"
},
"Taurus": {
"symbol": "♉",
"vedic": "Vrishabha"
},
"Gemini": {
"symbol": "♊",
"vedic": "Mithuna"
},
"Cancer": {
"symbol": "♋",
"vedic": "Karka"
},
"Leo": {
"symbol": "♌",
"vedic": "Simha"
},
"Virgo": {
"symbol": "♍",
"vedic": "Kanya"
},
"Libra": {
"symbol": "♎",
"vedic": "Tula"
},
"Scorpio": {
"symbol": "♏",
"vedic": "Vrishchika"
},
"Sagittarius": {
"symbol": "♐",
"vedic": "Dhanu"
},
"Capricorn": {
"symbol": "♑",
"vedic": "Makara"
},
"Aquarius": {
"symbol": "♒",
"vedic": "Kumbha"
},
"Pisces": {
"symbol": "♓",
"vedic": "Meena"
}
}

# ============================================================

# FALLBACK HOROSCOPES

# ============================================================

FALLBACK_HOROSCOPES = {
"Aries": (
"Today is a good day to take initiative. "
"Trust your ideas and move forward with confidence."
),
"Taurus": (
"Patience can bring better results today. "
"Focus on steady progress."
),
"Gemini": (
"Communication is your strength today. "
"A conversation may open a new opportunity."
),
"Cancer": (
"Listen to your intuition today. "
"Spend quality time with people you care about."
),
"Leo": (
"Your confidence can attract attention today. "
"Use your energy wisely."
),
"Virgo": (
"Small details matter today. "
"Organize your priorities and stay focused."
),
"Libra": (
"Balance is important today. "
"Think carefully before making decisions."
),
"Scorpio": (
"Your determination is strong today. "
"Focus that energy on one meaningful goal."
),
"Sagittarius": (
"A fresh perspective can change your day. "
"Stay curious and explore new ideas."
),
"Capricorn": (
"Consistent effort is your advantage today. "
"Keep working toward your long-term goals."
),
"Aquarius": (
"An original idea may be worth pursuing today. "
"Share your thoughts with others."
),
"Pisces": (
"Your creativity and empathy are strong today. "
"Give yourself some quiet time."
)
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
"quote": "You do not need to be perfect. Just keep moving.",
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
"number": 0,
"meaning": "A new beginning is opening before you.",
"advice": "Stay curious and do not be afraid to start.",
"image": "https://commons.wikimedia.org/wiki/Special:FilePath/RWS_Tarot_00_Fool.jpg"
},
{
"name": "The Magician",
"symbol": "✨",
"number": 1,
"meaning": "You have the ability to turn an idea into action.",
"advice": "Use the skills and resources already available to you.",
"image": "https://commons.wikimedia.org/wiki/Special:FilePath/RWS_Tarot_01_Magician.jpg"
},
{
"name": "The High Priestess",
"symbol": "🌙",
"number": 2,
"meaning": "Your intuition may be especially strong today.",
"advice": "Slow down and listen to your inner voice.",
"image": "https://commons.wikimedia.org/wiki/Special:FilePath/RWS_Tarot_02_High_Priestess.jpg"
},
{
"name": "The Empress",
"symbol": "🌸",
"number": 3,
"meaning": "Growth, creativity and abundance are highlighted.",
"advice": "Nurture yourself and the things that matter to you.",
"image": "https://commons.wikimedia.org/wiki/Special:FilePath/RWS_Tarot_03_Empress.jpg"
},
{
"name": "The Emperor",
"symbol": "👑",
"number": 4,
"meaning": "Structure and discipline can create stability.",
"advice": "Take control of what you can influence.",
"image": "https://commons.wikimedia.org/wiki/Special:FilePath/RWS_Tarot_04_Emperor.jpg"
},
{
"name": "The Lovers",
"symbol": "💞",
"number": 6,
"meaning": "Connection and meaningful choices are highlighted.",
"advice": "Choose with honesty and intention.",
"image": "https://commons.wikimedia.org/wiki/Special:FilePath/RWS_Tarot_06_Lovers.jpg"
},
{
"name": "The Chariot",
"symbol": "🏆",
"number": 7,
"meaning": "Determination can help you move forward.",
"advice": "Stay focused on your direction.",
"image": "https://commons.wikimedia.org/wiki/Special:FilePath/RWS_Tarot_07_Chariot.jpg"
},
{
"name": "Strength",
"symbol": "🦁",
"number": 8,
"meaning": "Real strength comes from patience and confidence.",
"advice": "Be patient with yourself and others.",
"image": "https://commons.wikimedia.org/wiki/Special:FilePath/RWS_Tarot_08_Strength.jpg"
},
{
"name": "The Star",
"symbol": "⭐",
"number": 17,
"meaning": "Hope and renewal are highlighted today.",
"advice": "Let hope guide your next step.",
"image": "https://commons.wikimedia.org/wiki/Special:FilePath/RWS_Tarot_17_Star.jpg"
},
{
"name": "The Sun",
"symbol": "☀️",
"number": 19,
"meaning": "Positive energy, clarity and confidence are present.",
"advice": "Allow yourself to enjoy today's good moments.",
"image": "https://commons.wikimedia.org/wiki/Special:FilePath/RWS_Tarot_19_Sun.jpg"
},
{
"name": "The Moon",
"symbol": "🌙",
"number": 18,
"meaning": "Not everything may be clear yet.",
"advice": "Give yourself time before making an important decision.",
"image": "https://commons.wikimedia.org/wiki/Special:FilePath/RWS_Tarot_18_Moon.jpg"
},
{
"name": "The World",
"symbol": "🌎",
"number": 21,
"meaning": "A cycle may be reaching completion.",
"advice": "Recognize your progress and prepare for what comes next.",
"image": "https://commons.wikimedia.org/wiki/Special:FilePath/RWS_Tarot_21_World.jpg"
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

# DATE HELPERS

# ============================================================

def get_today():
return datetime.now(TIMEZONE)

def get_date_string():
return get_today().date().isoformat()

# ============================================================

# DAILY TAROT

# ============================================================

def get_daily_tarot():
today = get_today()
day_number = today.timetuple().tm_yday

```
index = (day_number - 1) % len(TAROT_CARDS)

return TAROT_CARDS[index]
```

# ============================================================

# DAILY FALLBACK QUOTE

# ============================================================

def get_fallback_quote():
day_number = get_today().timetuple().tm_yday
index = (day_number - 1) % len(FALLBACK_QUOTES)

```
return FALLBACK_QUOTES[index]
```

# ============================================================

# FETCH FRESH HOROSCOPE FROM INTERNET

# ============================================================

async def fetch_online_horoscope(horoscope_name):
sign = horoscope_name.lower()

```
try:
    async with httpx.AsyncClient(
        timeout=HTTP_TIMEOUT,
        follow_redirects=True
    ) as client:

        response = await client.get(
            HOROSCOPE_API,
            params={"sign": sign}
        )

        response.raise_for_status()

        data = response.json()

        remote_data = data.get("data", {})

        reading = remote_data.get("horoscope")

        if reading:
            return {
                "reading": str(reading).strip(),
                "source": "internet"
            }

except Exception as error:
    print(
        "Online horoscope unavailable:",
        error
    )

return {
    "reading": FALLBACK_HOROSCOPES[horoscope_name],
    "source": "fallback"
}
```

# ============================================================

# FETCH FRESH QUOTE FROM INTERNET

# ============================================================

async def fetch_online_quote():
try:
async with httpx.AsyncClient(
timeout=HTTP_TIMEOUT,
follow_redirects=True
) as client:

```
        response = await client.get(
            QUOTE_API
        )

        response.raise_for_status()

        data = response.json()

        quote = data.get("quote")
        author = data.get("author")

        if quote:
            return {
                "quote": str(quote).strip(),
                "author": str(author or "Unknown").strip(),
                "source": "internet"
            }

except Exception as error:
    print(
        "Online quote unavailable:",
        error
    )

fallback = get_fallback_quote()

return {
    "quote": fallback["quote"],
    "author": fallback["author"],
    "source": "fallback"
}
```

# ============================================================

# CONTENT FINGERPRINT

# ============================================================

def create_content_id(
date,
horoscope,
reading,
tarot_name,
quote
):
raw = (
f"{date}|"
f"{horoscope}|"
f"{reading}|"
f"{tarot_name}|"
f"{quote}"
)

```
return hashlib.sha256(
    raw.encode("utf-8")
).hexdigest()[:16]
```

# ============================================================

# DAILY CONTENT

# ============================================================

async def get_daily_content(horoscope_name):

```
if horoscope_name not in HOROSCOPES:
    return None

zodiac = HOROSCOPES[horoscope_name]

horoscope_result = await fetch_online_horoscope(
    horoscope_name
)

quote_result = await fetch_online_quote()

tarot = get_daily_tarot()

date = get_date_string()

content_id = create_content_id(
    date,
    horoscope_name,
    horoscope_result["reading"],
    tarot["name"],
    quote_result["quote"]
)

return {
    "date": date,

    "content_id": content_id,

    "source": {
        "horoscope": horoscope_result["source"],
        "quote": quote_result["source"],
        "tarot": "Wikimedia Commons"
    },

    "horoscope": {
        "name": horoscope_name,
        "symbol": zodiac["symbol"],
        "vedic": zodiac["vedic"],
        "reading": horoscope_result["reading"]
    },

    "tarot": {
        "name": tarot["name"],
        "symbol": tarot["symbol"],
        "number": tarot["number"],
        "meaning": tarot["meaning"],
        "advice": tarot["advice"],
        "image": tarot["image"]
    },

    "quote": {
        "text": quote_result["quote"],
        "author": quote_result["author"]
    }
}
```

# ============================================================

# FASTAPI LIFESPAN

# ============================================================

@asynccontextmanager
async def lifespan(app):

```
print("--------------------------------------------")
print("Daily Aura backend started")
print("Timezone: Asia/Kathmandu")
print("Internet content: ENABLED")
print("Horoscope API: ENABLED")
print("Quote API: ENABLED")
print(
    "Web Push:",
    "ENABLED" if PYWEBPUSH_AVAILABLE else "DISABLED"
)
print("--------------------------------------------")

yield

print("Daily Aura backend shutting down")
```

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
allow_credentials=True,
allow_methods=["*"],
allow_headers=["*"]
)

# ============================================================

# ROOT

# ============================================================

@app.get("/")
async def root():

```
return {
    "status": "healthy",
    "service": "Daily Aura",
    "version": "3.0.0",
    "timezone": "Asia/Kathmandu",
    "internet_content": True,
    "features": [
        "Fresh Daily Horoscope",
        "Fresh Daily Quote",
        "Daily Tarot",
        "Tarot Image",
        "Push Notifications"
    ]
}
```

# ============================================================

# HEALTH

# ============================================================

@app.get("/health")
async def health():

```
return {
    "status": "healthy",
    "service": "Daily Aura",
    "internet_content": True,
    "subscriptions": len(subscriptions),
    "vapid_configured": bool(VAPID_PRIVATE_KEY),
    "webpush_available": PYWEBPUSH_AVAILABLE
}
```

# ============================================================

# STATUS

# ============================================================

@app.get("/api/status")
async def api_status():

```
return {
    "status": "online",
    "internet": True,
    "horoscope_api": HOROSCOPE_API,
    "quote_api": QUOTE_API,
    "timezone": "Asia/Kathmandu",
    "date": get_date_string(),
    "vapid_configured": bool(VAPID_PRIVATE_KEY),
    "webpush_available": PYWEBPUSH_AVAILABLE
}
```

# ============================================================

# DAILY CONTENT

# ============================================================

@app.get("/api/daily/{horoscope_name}")
async def get_daily_dashboard(
horoscope_name: str
):

```
name = horoscope_name.strip().title()

if name not in HOROSCOPES:
    raise HTTPException(
        status_code=404,
        detail="Horoscope sign not found."
    )

return await get_daily_content(name)
```

# ============================================================

# OLD / COMPATIBILITY ROUTE

# ============================================================

@app.get("/daily-content/{horoscope}")
async def daily_content(
horoscope: str
):

```
name = horoscope.strip().title()

if name not in HOROSCOPES:
    raise HTTPException(
        status_code=404,
        detail="Horoscope sign not found."
    )

return await get_daily_content(name)
```

# ============================================================

# VAPID PUBLIC KEY

# ============================================================

@app.get("/vapid-public-key")
async def get_vapid_public_key():

```
if not VAPID_PUBLIC_KEY:
    raise HTTPException(
        status_code=503,
        detail="VAPID public key is not configured."
    )

return {
    "publicKey": VAPID_PUBLIC_KEY
}
```

# ============================================================

# SUBSCRIBE

# ============================================================

@app.post("/api/subscribe")
async def subscribe(
data: SubscribeRequest
):

```
horoscope = data.horoscope.strip().title()

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

# COMPATIBILITY SUBSCRIBE ROUTE

# ============================================================

@app.post("/subscribe")
async def subscribe_compat(
data: SubscribeRequest
):

```
return await subscribe(data)
```

# ============================================================

# UNSUBSCRIBE

# ============================================================

@app.post("/api/unsubscribe")
async def unsubscribe(
data: UnsubscribeRequest
):

```
endpoint = data.endpoint.strip()

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

# COMPATIBILITY UNSUBSCRIBE ROUTE

# ============================================================

@app.post("/unsubscribe")
async def unsubscribe_compat(
data: UnsubscribeRequest
):

```
return await unsubscribe(data)
```

# ============================================================

# PUSH NOTIFICATION

# ============================================================

def send_notification(user_data):

```
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

subscription = user_data.get(
    "subscription"
)

horoscope_name = user_data.get(
    "horoscope"
)

if not subscription or not horoscope_name:
    return False

try:

    payload = {
        "title": "Daily Aura ✨",
        "body": (
            f"Your {horoscope_name} "
            "daily reading is ready."
        ),
        "url": "/"
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

    print(
        "Web Push failed:",
        error
    )

    return False

except Exception as error:

    print(
        "Notification error:",
        error
    )

    return False
```

# ============================================================

# TEST NOTIFICATION

# ============================================================

@app.post(
"/test-notification/{horoscope}"
)
async def test_notification(
horoscope: str
):

```
name = horoscope.strip().title()

if name not in HOROSCOPES:
    raise HTTPException(
        status_code=400,
        detail="Invalid horoscope sign."
    )

if not subscriptions:
    return {
        "success": False,
        "sent": 0,
        "message": "No subscriptions saved."
    }

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
        "sent": 0,
        "message": "No notification subscriptions saved."
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
    "sent": sent,
    "message": "Morning notification test completed."
}
```

# ============================================================

# RUN DIRECTLY

# ============================================================

if **name** == "**main**":

```
import uvicorn

port = int(
    os.getenv("PORT", "8000")
)

uvicorn.run(
    "main:app",
    host="0.0.0.0",
    port=port
)
```
