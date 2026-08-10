import os
import json
import asyncio
import hashlib
from contextlib import asynccontextmanager
from datetime import datetime
from zoneinfo import ZoneInfo
from urllib.parse import quote
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ============================================================

# DAILY AURA BACKEND

# ============================================================

APP_NAME = "Daily Aura"
APP_VERSION = "3.0.0"
TIMEZONE = ZoneInfo("Asia/Kathmandu")

# ============================================================

# OPTIONAL PUSH NOTIFICATIONS

# ============================================================

VAPID_PRIVATE_KEY = os.getenv("VAPID_PRIVATE_KEY", "")
VAPID_PUBLIC_KEY = os.getenv("VAPID_PUBLIC_KEY", "")
VAPID_EMAIL = os.getenv(
"VAPID_EMAIL",
"mailto:admin@example.com"
)

PYWEBPUSH_AVAILABLE = False

try:
from pywebpush import webpush, WebPushException

```
PYWEBPUSH_AVAILABLE = True
```

except ImportError:
pass

# ============================================================

# OPTIONAL AI

#

# Add GEMINI_API_KEY in Render Environment Variables.

#

# The app still works without it.

# ============================================================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Use a current Gemini Flash model available to your API account.

GEMINI_MODEL = os.getenv(
"GEMINI_MODEL",
"gemini-2.5-flash"
)

GEMINI_URL = (
"https://generativelanguage.googleapis.com/v1beta/models/"
+ GEMINI_MODEL
+ ":generateContent"
)

# ============================================================

# OPTIONAL AI IMAGE GENERATION

#

# Add POLLINATIONS_API_KEY only if you want generated

# tarot artwork.

# ============================================================

POLLINATIONS_API_KEY = os.getenv(
"POLLINATIONS_API_KEY",
""
)

POLLINATIONS_MODEL = os.getenv(
"POLLINATIONS_MODEL",
"flux"
)

# ============================================================

# TEMPORARY STORAGE

#

# This survives only while the Render instance is running.

# Move to a database later for permanent history/accounts.

# ============================================================

subscriptions = {}

# Stores generated content fingerprints so the same generated

# content is not intentionally returned repeatedly while the

# current server instance is alive.

generated_history = set()

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
),
},
"Taurus": {
"symbol": "♉",
"vedic": "Vrishabha",
"reading": (
"Patience can bring better results today. "
"Focus on steady progress."
),
},
"Gemini": {
"symbol": "♊",
"vedic": "Mithuna",
"reading": (
"Communication is your strength today. "
"A conversation may open a new opportunity."
),
},
"Cancer": {
"symbol": "♋",
"vedic": "Karka",
"reading": (
"Listen to your intuition today. "
"Spend quality time with people you care about."
),
},
"Leo": {
"symbol": "♌",
"vedic": "Simha",
"reading": (
"Your confidence can attract attention today. "
"Use your energy wisely."
),
},
"Virgo": {
"symbol": "♍",
"vedic": "Kanya",
"reading": (
"Small details matter today. "
"Organize your priorities and stay focused."
),
},
"Libra": {
"symbol": "♎",
"vedic": "Tula",
"reading": (
"Balance is important today. "
"Think carefully before making decisions."
),
},
"Scorpio": {
"symbol": "♏",
"vedic": "Vrishchika",
"reading": (
"Your determination is strong today. "
"Focus that energy on one meaningful goal."
),
},
"Sagittarius": {
"symbol": "♐",
"vedic": "Dhanu",
"reading": (
"A fresh perspective can change your day. "
"Stay curious and explore new ideas."
),
},
"Capricorn": {
"symbol": "♑",
"vedic": "Makara",
"reading": (
"Consistent effort is your advantage today. "
"Keep working toward your long-term goals."
),
},
"Aquarius": {
"symbol": "♒",
"vedic": "Kumbha",
"reading": (
"An original idea may be worth pursuing today. "
"Share your thoughts with others."
),
},
"Pisces": {
"symbol": "♓",
"vedic": "Meena",
"reading": (
"Your creativity and empathy are strong today. "
"Give yourself some quiet time."
),
},
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
"Your next chapter can begin with one small decision.",
"Give yourself permission to grow at your own pace.",
"A peaceful mind can see opportunities clearly.",
"Progress matters more than perfection.",
"Today can be different from yesterday.",
]

# ============================================================

# FALLBACK TAROT CARDS

# ============================================================

TAROT_CARDS = [
{
"name": "The Fool",
"symbol": "🌟",
"meaning": (
"A new beginning is opening before you. "
"Stay curious and trust yourself."
),
"advice": "Don't be afraid to start something new.",
},
{
"name": "The Magician",
"symbol": "✨",
"meaning": (
"You have the skills and resources needed "
"to turn an idea into reality."
),
"advice": "Use what you already have and take action.",
},
{
"name": "The High Priestess",
"symbol": "🌙",
"meaning": (
"Your intuition is especially strong today. "
"Some answers may come from within."
),
"advice": "Slow down and listen to your intuition.",
},
{
"name": "The Empress",
"symbol": "🌸",
"meaning": (
"Growth, creativity and abundance surround you."
),
"advice": "Nurture yourself and what matters to you.",
},
{
"name": "The Emperor",
"symbol": "👑",
"meaning": (
"Structure and discipline can help you create stability."
),
"advice": "Take control of what you can.",
},
{
"name": "The Lovers",
"symbol": "💞",
"meaning": (
"Connection and important choices are highlighted today."
),
"advice": "Choose with honesty and intention.",
},
{
"name": "The Chariot",
"symbol": "🏆",
"meaning": (
"Determination can move you forward."
),
"advice": "Stay focused on your direction.",
},
{
"name": "Strength",
"symbol": "🦁",
"meaning": (
"Real strength comes from patience, compassion and confidence."
),
"advice": "Be patient with yourself and others.",
},
{
"name": "The Star",
"symbol": "⭐",
"meaning": (
"Hope and renewal are highlighted today."
),
"advice": "Let hope guide your next step.",
},
{
"name": "The Sun",
"symbol": "☀️",
"meaning": (
"Positive energy, clarity and confidence are around you."
),
"advice": "Let yourself enjoy today's good moments.",
},
{
"name": "The Moon",
"symbol": "🌙",
"meaning": (
"Not everything is clear yet. "
"Give yourself time before making decisions."
),
"advice": "Look beyond first impressions.",
},
{
"name": "The World",
"symbol": "🌎",
"meaning": (
"A cycle may be reaching completion."
),
"advice": "Celebrate progress and prepare for what's next.",
},
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

class GenerateRequest(BaseModel):
horoscope: str
language: str = "en"

# ============================================================

# BASIC HELPERS

# ============================================================

def get_today():
return datetime.now(TIMEZONE)

def normalize_horoscope(name: str):
clean = str(name).strip().lower()

```
for sign in HOROSCOPES:
    if sign.lower() == clean:
        return sign

return None
```

def get_daily_quote():
day_of_year = get_today().timetuple().tm_yday
return QUOTES[(day_of_year - 1) % len(QUOTES)]

def get_daily_tarot():
day_of_year = get_today().timetuple().tm_yday
return TAROT_CARDS[(day_of_year - 1) % len(TAROT_CARDS)]

def make_fingerprint(value):
raw = json.dumps(
value,
sort_keys=True,
ensure_ascii=False,
)

```
return hashlib.sha256(
    raw.encode("utf-8")
).hexdigest()
```

# ============================================================

# GEMINI AI

# ============================================================

def call_gemini(prompt):
"""
Calls Gemini directly using Python's standard library.

```
No extra Python package is required.
"""

if not GEMINI_API_KEY:
    return None

payload = {
    "contents": [
        {
            "parts": [
                {
                    "text": prompt
                }
            ]
        }
    ],
    "generationConfig": {
        "temperature": 0.95,
        "topP": 0.95,
        "maxOutputTokens": 1200,
    },
}

url = GEMINI_URL + "?key=" + GEMINI_API_KEY

request = Request(
    url,
    data=json.dumps(payload).encode("utf-8"),
    headers={
        "Content-Type": "application/json"
    },
    method="POST",
)

try:
    with urlopen(request, timeout=25) as response:
        body = response.read().decode("utf-8")

    data = json.loads(body)

    candidates = data.get(
        "candidates",
        []
    )

    if not candidates:
        return None

    parts = (
        candidates[0]
        .get("content", {})
        .get("parts", [])
    )

    text_parts = []

    for part in parts:
        text = part.get("text")

        if text:
            text_parts.append(text)

    result = "\n".join(text_parts).strip()

    return result or None

except HTTPError as error:
    print(
        "Gemini HTTP error:",
        error.code,
    )
    return None

except URLError as error:
    print(
        "Gemini connection error:",
        error,
    )
    return None

except Exception as error:
    print(
        "Gemini error:",
        error,
    )
    return None
```

def extract_json(text):
"""
Safely extracts JSON if Gemini wraps it in markdown.
"""

````
if not text:
    return None

clean = text.strip()

if clean.startswith("```"):
    lines = clean.splitlines()

    if lines:
        lines = lines[1:]

    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]

    clean = "\n".join(lines).strip()

try:
    return json.loads(clean)
except Exception:
    pass

start = clean.find("{")
end = clean.rfind("}")

if start >= 0 and end > start:
    try:
        return json.loads(
            clean[start:end + 1]
        )
    except Exception:
        return None

return None
````

# ============================================================

# AI CONTENT GENERATOR

# ============================================================

def generate_ai_content(
horoscope_name,
language="en",
):
horoscope = HOROSCOPES.get(
horoscope_name
)

```
if not horoscope:
    return None

today = get_today().date().isoformat()

previous_hashes = list(
    generated_history
)[-50:]

prompt = f"""
```

You are the creative content engine for Daily Aura.

Date: {today}
Horoscope sign: {horoscope_name}
Vedic sign: {horoscope["vedic"]}
Requested language: {language}

Create a completely fresh daily experience.

IMPORTANT:

* Do not copy common horoscope templates.
* Do not repeat wording from previous generations.
* Make the horoscope specific to the sign but do not claim certainty.
* Tarot content is for entertainment and reflection.
* Do not make medical, financial, legal or guaranteed predictions.
* Keep the writing warm, modern and easy to understand.
* Create a new tarot interpretation.
* Create a new short motivational quote.
* Create a unique visual prompt for a tarot card.
* The image prompt must NOT contain text, letters, numbers, logos or watermarks.
* The tarot artwork should look like a premium mystical card.
* Return ONLY valid JSON.

Previous content fingerprints to avoid:
{json.dumps(previous_hashes)}

Return exactly:

{{
"reading": "2 short paragraphs or 3-5 sentences",
"love": "1-2 sentences",
"career": "1-2 sentences",
"wellness": "1-2 sentences",
"tarot": {{
"name": "a tarot card name",
"symbol": "one suitable emoji",
"meaning": "2-3 sentences",
"advice": "one practical reflective sentence",
"image_prompt": "detailed unique tarot artwork prompt"
}},
"quote": "one original motivational quote"
}}

Language requirement:
Write all natural-language content in the requested language.
If the requested language is "en", use English.
"""

```
result = call_gemini(prompt)

if not result:
    return None

parsed = extract_json(result)

if not isinstance(parsed, dict):
    return None

if not parsed.get("reading"):
    return None

if not isinstance(
    parsed.get("tarot"),
    dict,
):
    return None

if not parsed.get("quote"):
    return None

fingerprint = make_fingerprint(parsed)

if fingerprint in generated_history:
    return None

generated_history.add(fingerprint)

return parsed
```

# ============================================================

# FALLBACK CONTENT

# ============================================================

def get_fallback_content(
horoscope_name,
):
horoscope = HOROSCOPES[
horoscope_name
]

```
tarot = get_daily_tarot()

return {
    "reading": horoscope["reading"],
    "love": (
        "Stay open to honest communication "
        "and meaningful connections."
    ),
    "career": (
        "Focus on one useful step instead "
        "of trying to solve everything at once."
    ),
    "wellness": (
        "Give yourself a little quiet time "
        "to reset and recharge."
    ),
    "tarot": {
        "name": tarot["name"],
        "symbol": tarot["symbol"],
        "meaning": tarot["meaning"],
        "advice": tarot["advice"],
        "image_prompt": (
            "Premium mystical tarot card artwork, "
            + tarot["name"]
            + ", elegant celestial symbolism, "
            "deep cosmic atmosphere, ornate border, "
            "dreamlike lighting, highly detailed, "
            "vertical card composition, no text, "
            "no letters, no numbers, no logo, "
            "no watermark"
        ),
    },
    "quote": get_daily_quote(),
}
```

# ============================================================

# TAROT IMAGE URL

# ============================================================

def create_tarot_image_url(
image_prompt,
):
"""
Returns a generated Pollinations image URL when an API
key is configured.

```
Without a Pollinations key, returns None and the frontend
can use its own fallback tarot artwork.
"""

if not POLLINATIONS_API_KEY:
    return None

if not image_prompt:
    return None

prompt = (
    image_prompt
    + ", vertical 2:3 tarot card, "
    "premium fantasy illustration"
)

encoded_prompt = quote(
    prompt,
    safe="",
)

url = (
    "https://gen.pollinations.ai/image/"
    + encoded_prompt
    + "?model="
    + quote(
        POLLINATIONS_MODEL,
        safe="",
    )
    + "&width=768"
    + "&height=1152"
    + "&nologo=true"
    + "&key="
    + quote(
        POLLINATIONS_API_KEY,
        safe="",
    )
)

return url
```

# ============================================================

# COMPLETE DAILY CONTENT

# ============================================================

def build_daily_content(
horoscope_name,
language="en",
force_ai=True,
):
normalized = normalize_horoscope(
horoscope_name
)

```
if not normalized:
    return None

ai_content = None

if force_ai and GEMINI_API_KEY:
    ai_content = generate_ai_content(
        normalized,
        language,
    )

if ai_content:
    content = ai_content
    ai_enabled = True
else:
    content = get_fallback_content(
        normalized
    )
    ai_enabled = False

image_url = create_tarot_image_url(
    content["tarot"].get(
        "image_prompt",
        "",
    )
)

result = {
    "success": True,
    "date": get_today().date().isoformat(),
    "timezone": "Asia/Kathmandu",

    "ai": {
        "enabled": ai_enabled,
        "provider": (
            "gemini"
            if ai_enabled
            else "fallback"
        ),
    },

    "horoscope": {
        "name": normalized,
        "symbol": HOROSCOPES[
            normalized
        ]["symbol"],
        "vedic": HOROSCOPES[
            normalized
        ]["vedic"],
        "reading": content[
            "reading"
        ],
        "love": content.get(
            "love",
            "",
        ),
        "career": content.get(
            "career",
            "",
        ),
        "wellness": content.get(
            "wellness",
            "",
        ),
    },

    "tarot": {
        "name": content[
            "tarot"
        ]["name"],
        "symbol": content[
            "tarot"
        ].get(
            "symbol",
            "🃏",
        ),
        "meaning": content[
            "tarot"
        ]["meaning"],
        "advice": content[
            "tarot"
        ]["advice"],
        "image_prompt": content[
            "tarot"
        ].get(
            "image_prompt",
            "",
        ),
        "image_url": image_url,
    },

    "quote": content[
        "quote"
    ],
}

return result
```

# ============================================================

# FASTAPI LIFESPAN

# ============================================================

@asynccontextmanager
async def lifespan(app):
print(
"=========================================="
)
print(
"Daily Aura backend started"
)
print(
"Version:",
APP_VERSION,
)
print(
"Timezone: Asia/Kathmandu"
)
print(
"Gemini AI:",
bool(GEMINI_API_KEY),
)
print(
"Pollinations images:",
bool(POLLINATIONS_API_KEY),
)
print(
"Push notifications:",
PYWEBPUSH_AVAILABLE,
)
print(
"=========================================="
)

```
yield
```

# ============================================================

# FASTAPI APP

# ============================================================

app = FastAPI(
title="Daily Aura API",
version=APP_VERSION,
lifespan=lifespan,
)

# ============================================================

# CORS

# ============================================================

app.add_middleware(
CORSMiddleware,
allow_origins=["*"],
allow_credentials=True,
allow_methods=["*"],
allow_headers=["*"],
)

# ============================================================

# ROOT / HEALTH

# ============================================================

@app.get("/")
def health_check():
return {
"status": "healthy",
"service": APP_NAME,
"version": APP_VERSION,
"timezone": "Asia/Kathmandu",
"ai_configured": bool(
GEMINI_API_KEY
),
"image_ai_configured": bool(
POLLINATIONS_API_KEY
),
"push_available": (
PYWEBPUSH_AVAILABLE
),
}

@app.get("/health")
def health():
return {
"status": "healthy",
"service": APP_NAME,
"version": APP_VERSION,
"ai": bool(
GEMINI_API_KEY
),
"tarot_images": bool(
POLLINATIONS_API_KEY
),
"subscriptions": len(
subscriptions
),
}

# ============================================================

# AI STATUS

# ============================================================

@app.get("/api/ai/status")
def ai_status():
return {
"success": True,
"provider": (
"Gemini"
if GEMINI_API_KEY
else "fallback"
),
"configured": bool(
GEMINI_API_KEY
),
"unique_content_protection": True,
"image_provider": (
"Pollinations"
if POLLINATIONS_API_KEY
else "frontend-fallback"
),
}

# ============================================================

# DAILY CONTENT

# ============================================================

@app.get("/api/daily/{horoscope_name}")
def get_daily_dashboard(
horoscope_name: str,
language: str = "en",
):
content = build_daily_content(
horoscope_name,
language,
force_ai=True,
)

```
if not content:
    raise HTTPException(
        status_code=404,
        detail="Horoscope sign not found",
    )

return content
```

# Compatibility route for your older frontend

@app.get("/daily-content/{horoscope}")
def daily_content(
horoscope: str,
language: str = "en",
):
content = build_daily_content(
horoscope,
language,
force_ai=True,
)

```
if not content:
    raise HTTPException(
        status_code=404,
        detail="Horoscope sign not found",
    )

return content
```

# ============================================================

# FORCE NEW AI CONTENT

#

# Frontend can call:

#

# GET /api/generate/Aries

#

# ============================================================

@app.get("/api/generate/{horoscope_name}")
def generate_new_content(
horoscope_name: str,
language: str = "en",
):
normalized = normalize_horoscope(
horoscope_name
)

```
if not normalized:
    raise HTTPException(
        status_code=404,
        detail="Horoscope sign not found",
    )

if not GEMINI_API_KEY:
    return {
        "success": True,
        "ai": {
            "enabled": False,
            "message": (
                "GEMINI_API_KEY is not configured. "
                "Using fallback content."
            ),
        },
        "content": build_daily_content(
            normalized,
            language,
            force_ai=False,
        ),
    }

# Try several times to avoid accidental duplicate
# generations.
for _ in range(3):
    content = build_daily_content(
        normalized,
        language,
        force_ai=True,
    )

    if content:
        return content

return build_daily_content(
    normalized,
    language,
    force_ai=False,
)
```

# ============================================================

# SUBSCRIBE

# ============================================================

@app.post("/api/subscribe")
def subscribe(
data: SubscribeRequest,
):
horoscope = normalize_horoscope(
data.horoscope
)

```
if not horoscope:
    raise HTTPException(
        status_code=400,
        detail="Invalid horoscope sign",
    )

endpoint = (
    data.subscription.endpoint
)

if not endpoint:
    raise HTTPException(
        status_code=400,
        detail="Push endpoint is required",
    )

subscriptions[endpoint] = {
    "subscription":
        data.subscription.model_dump(),

    "horoscope":
        horoscope,

    "language":
        data.language,

    "created_at":
        get_today().isoformat(),
}

return {
    "success": True,
    "message": (
        "Daily Aura notification subscription saved."
    ),
    "horoscope": horoscope,
    "language": data.language,
}
```

# Compatibility route

@app.post("/subscribe")
def subscribe_compat(
data: SubscribeRequest,
):
return subscribe(data)

# ============================================================

# UNSUBSCRIBE

# ============================================================

@app.post("/api/unsubscribe")
def unsubscribe(
data: UnsubscribeRequest,
):
endpoint = data.endpoint

```
if endpoint in subscriptions:
    del subscriptions[endpoint]

    return {
        "success": True,
        "message": (
            "Unsubscribed successfully"
        ),
    }

return {
    "success": True,
    "message": (
        "Subscription was already removed."
    ),
}
```

# Compatibility route

@app.post("/unsubscribe")
def unsubscribe_compat(
data: UnsubscribeRequest,
):
return unsubscribe(data)

# ============================================================

# VAPID PUBLIC KEY

# ============================================================

@app.get("/api/vapid-public-key")
def vapid_public_key():
if not VAPID_PUBLIC_KEY:
return {
"configured": False,
"publicKey": None,
}

```
return {
    "configured": True,
    "publicKey": VAPID_PUBLIC_KEY,
}
```

@app.get("/vapid-public-key")
def vapid_public_key_compat():
return vapid_public_key()

# ============================================================

# SEND PUSH NOTIFICATION

# ============================================================

def send_notification(user_data):
if not PYWEBPUSH_AVAILABLE:
return False

```
if not VAPID_PRIVATE_KEY:
    return False

subscription = user_data[
    "subscription"
]

horoscope_name = user_data[
    "horoscope"
]

language = user_data.get(
    "language",
    "en",
)

content = build_daily_content(
    horoscope_name,
    language,
    force_ai=True,
)

if not content:
    return False

payload = {
    "title": "Daily Aura ✨",

    "body": (
        content["horoscope"]["reading"]
    ),

    "url": "/",

    "date": content["date"],

    "horoscope": content[
        "horoscope"
    ],

    "tarot": content[
        "tarot"
    ],

    "quote": content[
        "quote"
    ],
}

try:
    webpush(
        subscription_info=subscription,
        data=json.dumps(
            payload,
            ensure_ascii=False,
        ),
        vapid_private_key=(
            VAPID_PRIVATE_KEY
        ),
        vapid_claims={
            "sub": VAPID_EMAIL
        },
    )

    return True

except Exception as error:
    print(
        "Push notification error:",
        error,
    )
    return False
```

# ============================================================

# TEST PUSH

# ============================================================

@app.post(
"/api/test-notification/{horoscope}"
)
def test_notification(
horoscope: str,
):
normalized = normalize_horoscope(
horoscope
)

```
if not normalized:
    raise HTTPException(
        status_code=400,
        detail="Invalid horoscope sign",
    )

sent = 0

for user_data in list(
    subscriptions.values()
):
    temporary = {
        **user_data,
        "horoscope": normalized,
    }

    if send_notification(
        temporary
    ):
        sent += 1

return {
    "success": True,
    "sent": sent,
    "horoscope": normalized,
}
```

# ============================================================

# SEND MORNING NOTIFICATION NOW

# ============================================================

@app.post("/api/send-morning-now")
def send_morning_now():
if not subscriptions:
return {
"success": False,
"sent": 0,
"message": (
"No notification subscriptions saved."
),
}

```
sent = 0

for user_data in list(
    subscriptions.values()
):
    if send_notification(
        user_data
    ):
        sent += 1

return {
    "success": True,
    "sent": sent,
    "message": (
        "Morning notification test completed."
    ),
}
```

# ============================================================

# DEBUG / CONTENT TEST

# ============================================================

@app.get("/api/test/{horoscope_name}")
def test_content(
horoscope_name: str,
):
normalized = normalize_horoscope(
horoscope_name
)

```
if not normalized:
    raise HTTPException(
        status_code=404,
        detail="Horoscope sign not found",
    )

return build_daily_content(
    normalized,
    "en",
    force_ai=True,
)
```
