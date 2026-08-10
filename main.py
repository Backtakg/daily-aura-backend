```python
import os
import asyncio
from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from pywebpush import webpush, WebPushException


# =========================================================
# DAILY AURA BACKEND
# =========================================================

app = FastAPI(
    title="Daily Aura API",
    version="1.0.0"
)


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# CONFIGURATION
# =========================================================

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

TIMEZONE = ZoneInfo(
    "Asia/Kathmandu"
)


# =========================================================
# TEMPORARY SUBSCRIPTION STORAGE
#
# This works while the server is running.
# Later we can move this to a real database.
# =========================================================

subscriptions = {}


# =========================================================
# HOROSCOPE DATA
# =========================================================

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
        "reading": "Listen to your intuition today. Spend some quality time with people you care about."
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


# =========================================================
# DAILY QUOTES
# =========================================================

QUOTES = [

    "Small steps every day create big changes.",

    "Your future is created by what you do today.",

    "A calm mind can find a way forward.",

    "Believe in the progress you cannot yet see.",

    "Start where you are. Make today count.",

    "You don't need to be perfect. Just keep moving.",

    "Every morning is another chance to begin again."

]


# =========================================================
# REQUEST MODELS
# =========================================================

class PushSubscription(BaseModel):

    endpoint: str

    keys: dict


class SubscribeRequest(BaseModel):

    subscription: PushSubscription

    horoscope: str

    language: str = "en"


class UnsubscribeRequest(BaseModel):

    endpoint: str


# =========================================================
# HEALTH CHECK
# =========================================================

@app.get("/")
async def root():

    return {
        "app": "Daily Aura",
        "status": "online",
        "timezone": "Asia/Kathmandu",
        "notification_time": "08:00"
    }


@app.get("/health")
async def health():

    return {
        "status": "healthy",
        "subscriptions": len(subscriptions),
        "vapid_configured": bool(
            VAPID_PRIVATE_KEY
        )
    }


# =========================================================
# VAPID PUBLIC KEY
# =========================================================

@app.get("/vapid-public-key")
async def vapid_public_key():

    if not VAPID_PUBLIC_KEY:

        raise HTTPException(
            status_code=500,
            detail="VAPID public key is not configured."
        )

    return {
        "publicKey": VAPID_PUBLIC_KEY
    }


# =========================================================
# SAVE SUBSCRIPTION
# =========================================================

@app.post("/subscribe")
async def subscribe(
    request: SubscribeRequest
):

    if request.horoscope not in HOROSCOPES:

        raise HTTPException(
            status_code=400,
            detail="Invalid horoscope sign."
        )


    endpoint = request.subscription.endpoint


    subscriptions[endpoint] = {

        "subscription": request.subscription.model_dump(),

        "horoscope":
            request.horoscope,

        "language":
            request.language,

        "created_at":
            datetime.now(
                TIMEZONE
            ).isoformat()

    }


    return {

        "success": True,

        "message":
            "Daily Aura notification subscription saved.",

        "horoscope":
            request.horoscope

    }


# =========================================================
# REMOVE SUBSCRIPTION
# =========================================================

@app.post("/unsubscribe")
async def unsubscribe(
    request: UnsubscribeRequest
):

    subscriptions.pop(
        request.endpoint,
        None
    )


    return {

        "success": True,

        "message":
            "Notification subscription removed."

    }


# =========================================================
# DAILY CONTENT
# =========================================================

def get_daily_quote():

    day_of_year = datetime.now(
        TIMEZONE
    ).timetuple().tm_yday


    return QUOTES[
        (day_of_year - 1)
        % len(QUOTES)
    ]


def get_notification_content(
    horoscope_name
):

    horoscope =
        HOROSCOPES.get(
            horoscope_name
        )


    if not horoscope:

        return None


    quote =
        get_daily_quote()


    return {

        "title":
            "Daily Aura ✨",

        "body":
            f"{horoscope['symbol']} "
            f"{horoscope_name} Horoscope: "
            f"{horoscope['reading']} "
            f"✨ Daily Quote: "
            f"“{quote}”"

    }


# =========================================================
# SEND ONE NOTIFICATION
# =========================================================

def send_notification(
    user_data
):

    if not VAPID_PRIVATE_KEY:

        print(
            "VAPID_PRIVATE_KEY is not configured."
        )

        return False


    subscription =
        user_data["subscription"]


    horoscope_name =
        user_data["horoscope"]


    content =
        get_notification_content(
            horoscope_name
        )


    if not content:

        return False


    payload = {

        "title":
            content["title"],

        "body":
            content["body"],

        "url":
            "/"

    }


    try:

        webpush(

            subscription_info=
                subscription,

            data=
                __import__(
                    "json"
                ).dumps(
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
            "Unexpected notification error:",
            error
        )

        return False


# =========================================================
# SEND ALL MORNING NOTIFICATIONS
# =========================================================

def send_morning_notifications():

    print(
        "Sending Daily Aura morning notifications..."
    )


    removed = []


    for endpoint, user_data in list(
        subscriptions.items()
    ):

        success =
            send_notification(
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


    for endpoint in removed:

        subscriptions.pop(
            endpoint,
            None
        )


# =========================================================
# SCHEDULER
# =========================================================

async def notification_scheduler():

    last_sent_date = None


    while True:

        now =
            datetime.now(
                TIMEZONE
            )


        current_date =
            now.date()


        is_morning =
            now.hour == 8


        if (
            is_morning
            and
            last_sent_date != current_date
        ):

            try:

                send_morning_notifications()

                last_sent_date =
                    current_date

            except Exception as error:

                print(
                    "Scheduler error:",
                    error
                )


        await asyncio.sleep(
            30
        )


# =========================================================
# STARTUP
# =========================================================

@app.on_event("startup")
async def startup_event():

    asyncio.create_task(
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
        "-----------------------------------"
    )
```
