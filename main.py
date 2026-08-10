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

# DAILY AURA BACKEND

# ============================================================

TIMEZONE = ZoneInfo("Asia/Kathmandu")

VAPID_PRIVATE_KEY = os.getenv("VAPID_PRIVATE_KEY", "")
VAPID_PUBLIC_KEY = os.getenv("VAPID_PUBLIC_KEY", "")
VAPID_EMAIL = os.getenv(
"VAPID_EMAIL",
"mailto:admin@example.com"
)

# Temporary in-memory storage.

# Subscriptions disappear when the Render service restarts.

subscriptions = {}

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

# DAILY QUOTES

# ============================================================

QUOTES = [
"Small steps every day create big changes.",
"Your future is created by what you do today.",
"A calm mind can find a way forward.",
"Believe in the progress you cannot yet see.",
"Start where you are. Make today count.",
"You don't need to be perfect. Just keep moving.",
"Every morning is another chance to begin again."
]

# ============================================================

# DAILY TAROT

# ============================================================

TAROT_CARDS = [
{
"name": "The Fool",
"symbol": "🌟",
"meaning": "A new beginning is opening before you. Stay curious and trust yourself.",
"advice": "Don't be afraid to start something new."
},
{
"name": "The Magician",
"symbol": "✨",
"meaning": "You have the skills and resources needed to turn an idea into reality.",
"advice": "Use what you already have and take action."
},
{
"name": "The High Priestess",
"symbol": "🌙",
"meaning": "Your intuition is especially strong today. Some answers may come from within.",
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
"meaning": "Structure and discipline can help you create stability.",
"advice": "Take control of what you can."
},
{
"name": "The Lovers",
"symbol": "💞",
"meaning": "Connection and important choices are highlighted today.",
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
"meaning": "Real strength comes from patience, compassion and confidence.",
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
"meaning": "Positive energy, clarity and confidence are around you.",
"advice": "Let yourself enjoy today's good moments."
},
{
"name": "The Moon",
"symbol": "🌙",
"meaning": "Not everything is clear yet. Give yourself time before making decisions.",
"advice": "Look beyond first impressions."
},
{
"name": "The World",
"symbol": "🌎",
"meaning": "A cycle may be reaching completion.",
"advice": "Celebrate progress and prepare for what's next."
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

# HELPERS

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

```
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
```

def get_notification_content(horoscope_name, language="en"):
data = get_daily_content(horoscope_name)

```
if not data:
    return None

horoscope = data["horoscope"]
tarot = data["tarot"]
quote = data["quote"]

title = "Daily Aura ✨"

body = (
    f'{horoscope["symbol"]} {horoscope_name} Horoscope: '
    f'{horoscope["reading"]} '
    f'🃏 Tarot: {tarot["name"]} '
    f'✨ Quote: "{quote}"'
)

return {
    "title": title,
    "body": body,
    "url": "/",
    "tarot": tarot["name"],
    "quote": quote
}
```

# ============================================================

# PUSH NOTIFICATION

# ============================================================

def send_notification(user_data):
if not VAPID_PRIVATE_KEY:
print("VAPID_PRIVATE_KEY is not configured.")
return False

```
if not PYWEBPUSH_AVAILABLE:
    print("pywebpush is not installed.")
    return False

subscription = user_data["subscription"]
horoscope_name = user_data["horoscope"]
language = user_data.get("language", "en")

content = get_notification_content(
    horoscope_name,
    language
)

if not content:
    return False

payload = {
    "title": content["title"],
    "body": content["body"],
    "url": content["url"],
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
    print("Push notification failed:", error)
    return False

except Exception as error:
    print("Unexpected notification error:", error)
    return False
```

# ============================================================

# SEND MORNING NOTIFICATIONS

# ============================================================

def send_morning_notifications():
print("====================================")
print("Sending Daily Aura notifications...")
print("Time:", get_today().isoformat())
print("Subscribers:", len(subscriptions))
print("====================================")

```
sent = 0

for endpoint, user_data in list(subscriptions.items()):
    success = send_notification(user_data)

    if success:
        sent += 1
        print(
            "Notification sent:",
            user_data["horoscope"]
        )
    else:
        print(
            "Notification failed:",
            user_data["horoscope"]
        )

return sent
```

# ============================================================

# SCHEDULER

# ============================================================

async def notification_scheduler():
last_sent_date = None

```
while True:
    now = datetime.now(TIMEZONE)
    current_date = now.date()

    is_morning = (
        now.hour == 8
        and now.minute == 0
    )

    if (
        is_morning
        and last_sent_date != current_date
    ):
        try:
            send_morning_notifications()
            last_sent_date = current_date

        except Exception as error:
            print(
                "Scheduler error:",
                error
            )

    await asyncio.sleep(20)
```

# ============================================================

# FASTAPI LIFESPAN

# ============================================================

@asynccontextmanager
async def lifespan(app):
scheduler_task = asyncio.create_task(
notification_scheduler()
)

```
print("-----------------------------------")
print("Daily Aura backend started")
print("Timezone: Asia/Kathmandu")
print("Morning notification: 08:00")
print("-----------------------------------")

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

# FASTAPI APP

# ============================================================

app = FastAPI(
title="Daily Aura API",
version="2.0.0",
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
return {
"app": "Daily Aura",
"status": "online",
"timezone": "Asia/Kathmandu",
"notification_time": "08:00",
"features": [
"Horoscope",
"Daily Quote",
"Daily Tarot",
"Push Notifications"
]
}

# ============================================================

# HEALTH

# ============================================================

@app.get("/health")
async def health():
return {
"status": "healthy",
"subscriptions": len(subscriptions),
"vapid_configured": bool(VAPID_PRIVATE_KEY),
"webpush_available": PYWEBPUSH_AVAILABLE
}

# ============================================================

# VAPID PUBLIC KEY

# ============================================================

@app.get("/vapid-public-key")
async def vapid_public_key():
if not VAPID_PUBLIC_KEY:
raise HTTPException(
status_code=503,
detail="VAPID public key is not configured yet."
)

```
return {
    "publicKey": VAPID_PUBLIC_KEY
}
```

# ============================================================

# SAVE PUSH SUBSCRIPTION

# ============================================================

@app.post("/subscribe")
async def subscribe(request: SubscribeRequest):
if request.horoscope not in HOROSCOPES:
raise HTTPException(
status_code=400,
detail="Invalid horoscope sign."
)

```
if not request.subscription.endpoint:
    raise HTTPException(
        status_code=400,
        detail="Push subscription endpoint is required."
    )

endpoint = request.subscription.endpoint

subscriptions[endpoint] = {
    "subscription": request.subscription.model_dump(),
    "horoscope": request.horoscope,
    "language": request.language,
    "created_at": get_today().isoformat()
}

print(
    "Subscription saved:",
    request.horoscope
)

return {
    "success": True,
    "message": "Daily Aura notification subscription saved.",
    "horoscope": request.horoscope,
    "language": request.language
}
```

# ============================================================

# REMOVE PUSH SUBSCRIPTION

# ============================================================

@app.post("/unsubscribe")
async def unsubscribe(request: UnsubscribeRequest):
subscriptions.pop(
request.endpoint,
None
)

```
return {
    "success": True,
    "message": "Notification subscription removed."
}
```

# ============================================================

# CURRENT DAILY CONTENT

# ============================================================

@app.get("/daily-content/{horoscope}")
async def daily_content(horoscope: str):
if horoscope not in HOROSCOPES:
raise HTTPException(
status_code=404,
detail="Horoscope sign not found."
)

```
return get_daily_content(horoscope)
```

# ============================================================

# LIST HOROSCOPES

# ============================================================

@app.get("/horoscopes")
async def horoscopes():
return {
"horoscopes": [
{
"name": name,
"symbol": data["symbol"],
"vedic": data["vedic"]
}
for name, data in HOROSCOPES.items()
]
}

# ============================================================

# DAILY TAROT

# ============================================================

@app.get("/daily-tarot")
async def daily_tarot():
tarot = get_daily_tarot()

```
return {
    "date": get_today().date().isoformat(),
    "tarot": tarot,
    "free_daily_card": True,
    "three_card_spread": "premium"
}
```

# ============================================================

# DAILY QUOTE

# ============================================================

@app.get("/daily-quote")
async def daily_quote():
return {
"date": get_today().date().isoformat(),
"quote": get_daily_quote()
}

# ============================================================

# TEST ONE NOTIFICATION

# ============================================================

@app.post("/test-notification/{horoscope}")
async def test_notification(horoscope: str):
if horoscope not in HOROSCOPES:
raise HTTPException(
status_code=400,
detail="Invalid horoscope sign."
)

```
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
```

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

```
sent = send_morning_notifications()

return {
    "success": True,
    "message": "Morning notification test completed.",
    "sent": sent
}
```

### Important

Your Render **build already succeeds** now. The current failure is only because `main.py` contains formatting/code-block text instead of pure Python.

After replacing it:

**Render Build Command**

```text
pip install -r requirements.txt
```

**Render Start Command**

```text
uvicorn main:app --host 0.0.0.0 --port $PORT
```

You **do not need VAPID keys just to start the backend**. The API will run without them. Push notifications simply won't work until you generate and add:

* `VAPID_PRIVATE_KEY`
* `VAPID_PUBLIC_KEY`
* `VAPID_EMAIL`

First deploy this clean `main.py`. Once Render shows **Live**, we can set up VAPID and connect your frontend push notifications.
