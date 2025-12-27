import os
import json
import random
import asyncio
import google.generativeai as genai
from telegram import Bot

# --- ⚠️ HARDCODED SECRETS (PRIVATE REPO ONLY) ⚠️ ---
TELEGRAM_TOKEN = "8512814291:AAEgtDBZDzB4MKz2BdsAjXYk0YLpKzGGO20"
GEMINI_API_KEY = "AIzaSyDRthGk2azAa8EcJYfzWfHmpuz8Z_Z5fGU"
CHAT_ID = "6882899041"

# --- CONFIGURATION ---
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')

def load_config():
    # Get the directory where THIS script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Join it with the filename to get the full path
    config_path = os.path.join(script_dir, 'config.json')
    
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ CRITICAL ERROR: Could not find config.json at: {config_path}")
        print("Make sure config.json is in the exact same folder as orbit.py!")
        return None

async def send_chaos():
    bot = Bot(token=TELEGRAM_TOKEN)
    config = load_config()
    
    if not config:
        return # Exit if config failed to load

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
            "Error 404: Motivation not found? Too bad.",
            "Lock in. The patient isn't gonna save themselves. 🩺",
            "Academic Weapon status: Loading... 🔫",
            "Imagine failing. Now get back to work.",
            "Your competition is studying right now. Are you?",
            "Pain is temporary. The 'Dr.' title is forever. 🥼",
            "Stop scrolling. Start solving.",
            "This unit won't learn itself, chief.",
            "Be the main character in your own success story.",
            "Coffee in. Knowledge out. ☕",
            "Diamonds are made under pressure. So are you.",
            "The charts are moving. Why aren't you? 📉",
            "Houston, we have a problem: You aren't studying. 🚀",
            "Coding is just wizardry. Go cast a spell. 🧙‍♂️",
            "If it was easy, everyone would do it.",
            "Don't practice until you get it right. Practice until you can't get it wrong.",
            "Future you is begging you to lock in right now."
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
