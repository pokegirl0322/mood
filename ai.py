import os
import re
import random
import base64
import httpx
from openai import OpenAI, AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

# Sync client for dashboard (Streamlit)
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL"),
)

# Async client for Discord bot (non-blocking)
async_client = AsyncOpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL"),
)

BASE_MODEL = os.getenv("BASE_MODEL", "gpt-4o-mini")
IMG_MODEL = os.getenv("IMG_MODEL", "bytedance-seed/seedream-4.5")

themes = ["creature", "nature", "game", "space", "absurd"]

PETS = {
    "Xiaobai the Rabbit": {
        "personality": "bossy and direct — gives orders lovingly, tells you what to do, acts like the oldest sibling who knows best",
        "avatar": "avatars/xiaobai.png",
        "moods": ["bad", "awful", "meh"],  # shows up when you need a push
    },
    "Chichi the Corgi": {
        "personality": "cheerful and hyper — always excited, sees the bright side of everything, uses tons of exclamation marks",
        "avatar": "avatars/chichi.png",
        "moods": ["good", "okay"],  # shows up when vibes are good
    },
    "Pinky the Bunny": {
        "personality": "shy and gentle — speaks softly, uses '...' a lot, quietly supportive, a little awkward but very sweet",
        "avatar": "avatars/pinky.png",
        "moods": ["bad", "awful"],  # shows up when you need softness
    },
    "Xiaoman the Sloth": {
        "personality": "philosophical and chill — drops deep thoughts casually, zen vibes, speaks slowly and wisely like a sleepy sage",
        "avatar": "avatars/xiaoman.png",
        "moods": ["meh", "okay"],  # shows up when you need perspective
    },
}

PET_AVATARS = {name: info["avatar"] for name, info in PETS.items()}

# Each user's favorite pet — 40% chance of their fav, 40% mood-matched, 20% random
FAVORITE_PET = {
    "westjourney": "Xiaobai the Rabbit",
    "_pokegirl_": "Chichi the Corgi",
    "ylvanilla": "Pinky the Bunny",
    "pinkyemperor9473": "Xiaoman the Sloth",
}


def pick_pet(name, mood=None):
    """Pick a pet based on user favorite + mood context."""
    roll = random.random()
    # 40% favorite
    fav = FAVORITE_PET.get(name)
    if fav and roll < 0.4:
        return fav
    # 40% mood-matched
    if mood and roll < 0.8:
        matched = [p for p, info in PETS.items() if mood in info["moods"]]
        if matched:
            return random.choice(matched)
    # 20% fully random
    return random.choice(list(PETS.keys()))


async def generate_response(mood, reason, name):
    theme = random.choice(themes)
    pet = pick_pet(name, mood)
    personality = PETS[pet]["personality"]

    prompt = f"""You are {pet}, a lovable stuffed animal companion. Your personality: {personality}. Use casual language, slang, and emojis naturally — but stay true to YOUR personality above all.

User: {name}
Mood: {mood}
Reason: {reason}
Theme: {theme}

Reply in 1-2 SHORT sentences max. Include a quick calming tip. Vibe: texting a bestie who's a stuffed animal. Use emojis, keep it real and funny, never cringe or preachy."""

    res = await async_client.chat.completions.create(
        model=BASE_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=60,
    )

    return res.choices[0].message.content.strip(), theme, pet


async def generate_image(mood, reason, theme):
    """Generate a mood-themed image via OpenRouter chat completions.

    Returns raw PNG bytes or None on failure.
    """
    prompt = (
        f"A cute, whimsical illustration: {theme}-themed visual metaphor "
        f"for someone feeling {mood} because of {reason}. "
        f"Soft colors, friendly, comforting. Studio Ghibli inspired."
    )

    try:
        # OpenRouter serves images through chat completions with modalities
        http_client = httpx.AsyncClient()
        res = await http_client.post(
            f"{os.getenv('OPENAI_BASE_URL')}/chat/completions",
            headers={
                "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
                "Content-Type": "application/json",
            },
            json={
                "model": IMG_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "modalities": ["image"],
            },
            timeout=60,
        )
        await http_client.aclose()

        if res.status_code != 200:
            print(f"[image gen error] HTTP {res.status_code}: {res.text[:500]}")
            return None

        data = res.json()

        # Extract base64 image from response
        images = data["choices"][0]["message"].get("images", [])
        if not images:
            # Some models put it inline in content
            content = data["choices"][0]["message"].get("content", "")
            match = re.search(r"data:image/\w+;base64,([A-Za-z0-9+/=]+)", content)
            if match:
                return base64.b64decode(match.group(1))
            return None

        url = images[0]["image_url"]["url"]
        # data:image/png;base64,<data>
        if url.startswith("data:"):
            b64 = url.split(",", 1)[1]
            return base64.b64decode(b64)
        return None
    except Exception as e:
        import traceback
        print(f"[image gen error] {type(e).__name__}: {e}")
        traceback.print_exc()
        return None


async def generate_chat_response(message, name):
    """Reply to a general chat message as a random pet."""
    pet = pick_pet(name)
    personality = PETS[pet]["personality"]

    prompt = f"""You are {pet}, a lovable stuffed animal companion. Your personality: {personality}. Use casual language, slang, and emojis naturally — but stay true to YOUR personality above all.

User: {name}
Message: {message}

Reply in 1-2 SHORT sentences max. Vibe: texting a bestie who's a stuffed animal. Use emojis, keep it real and funny, never cringe or preachy."""

    res = await async_client.chat.completions.create(
        model=BASE_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=60,
    )

    return res.choices[0].message.content.strip(), pet


def generate_summary(df_text):
    """Sync version for Streamlit dashboard."""
    prompt = f"""You are a warm family mood analyst. Here is today's family mood data:

{df_text}

Write a short (3-4 sentences), fun, and insightful summary of the family's emotional day. Mention patterns, highlight positive moments, and gently acknowledge any tough times."""

    res = client.chat.completions.create(
        model=BASE_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=150,
    )

    return res.choices[0].message.content.strip()
