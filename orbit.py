import os
import json
import random
import asyncio
import google.generativeai as genai
from telegram import Bot

# --- ⚠️ HARDCODED SECRETS (PRIVATE REPO ONLY) ⚠️ ---
# Paste your actual keys inside the quotes below.
TELEGRAM_TOKEN = "8512814291:AAEgtDBZDzB4MKz2BdsAjXYk0YLpKzGGO20"
GEMINI_API_KEY = "AIzaSyDRthGk2azAa8EcJYfzWfHmpuz8Z_Z5fGU"
CHAT_ID = "6882899041"

# --- CONFIGURATION ---
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')

def load_config():
    # Ensure config.json exists in the same directory
    with open('config.json', 'r') as f:
        return json.load(f)

async def send_chaos():
    bot = Bot(token=TELEGRAM_TOKEN)
    config = load_config()
    
    # 🎲 THE ROLL OF DESTINY (1-100)
    roll = random.randint(1, 100)
    print(f"🎲 Rolled a {roll}")

    # 1-50: Silence
    if roll <= 50:
        print("Silence is golden. Exiting.")
        return

    # 51-85: Random Fact
    elif 51 <= roll <= 85:
        topic = random.choice(config['interests'])
        prompt = f"Tell me a mind-blowing, short random fact about {topic}. Make it sound like a 'Did you know?' text."
        try:
            response = model.generate_content(prompt)
            await bot.send_message(chat_id=CHAT_ID, text=f"🎱 **Magic-∞ Fact:**\n\n{response.text}")
        except Exception as e:
            print(f"Gemini Error: {e}")

    # 86-98: The Grind
    elif 86 <= roll <= 98:
        quotes = [
            "Sleep is for the weak. Grind is for the eternal.",
            "You didn't come this far to only come this far.",
            "Surprise! Your brain looks bored.",
            "Error 404: Motivation not found? Too bad."
        ]
        unit = random.choice(config['current_units'])
        await bot.send_message(chat_id=CHAT_ID, text=f"🚨 **{random.choice(quotes)}**\n\nOpen the app. We are doing {unit} NOW.")

    # 99-100: GOD MODE
    else:
        await bot.send_message(chat_id=CHAT_ID, text="👑 **GOD MODE ACTIVATED**\n\nPrepare yourself for a riddle that combines History and Physics...")

if __name__ == "__main__":
    if "PASTE_YOUR" in TELEGRAM_TOKEN or "PASTE_YOUR" in GEMINI_API_KEY:
        print("❌ Error: You forgot to paste your API keys in orbit.py!")
    else:
        asyncio.run(send_chaos())