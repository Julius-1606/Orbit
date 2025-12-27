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

# 🛠️ AUTO-SELECTOR: Finds a model that actually exists so we stop guessing
def get_working_model():
    try:
        print("🔍 Scanning available AI models...")
        # Get all models that support generating text
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # The Wishlist (Best to Worst)
        wishlist = [
            'models/gemini-1.5-flash',
            'models/gemini-1.5-flash-001',
            'models/gemini-1.5-flash-latest',
            'models/gemini-1.5-pro',
            'models/gemini-pro'
        ]
        
        for wish in wishlist:
            if wish in models:
                print(f"✅ Locked on target: {wish}")
                # We strip 'models/' prefix because GenerativeModel() sometimes prefers just the name
                return genai.GenerativeModel(wish.replace("models/", ""))
        
        # If all else fails, pick the first valid Gemini model
        first_option = next((m for m in models if 'gemini' in m), None)
        if first_option:
            print(f"⚠️ Fallback to: {first_option}")
            return genai.GenerativeModel(first_option.replace("models/", ""))
            
    except Exception as e:
        print(f"⚠️ Scan failed: {e}")
    
    # Absolute Hail Mary
    print("🤞 Forcing 'gemini-1.5-flash' and praying...")
    return genai.GenerativeModel('gemini-1.5-flash')

model = get_working_model()

def load_config():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, 'config.json')
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ CRITICAL ERROR: Could not find config.json at: {config_path}")
        return None

async def send_chaos():
    bot = Bot(token=TELEGRAM_TOKEN)
    config = load_config()
    
    if not config:
        return 

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
        prompt = f"Tell me a mind-blowing, short random fact about {topic}. Keep it under 2 sentences."
        try:
            response = model.generate_content(prompt)
            # We use HTML parsing for bold text
            msg = f"🎱 <b>Magic-∞ Fact:</b>\n\n{response.text}"
            await bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode='HTML')
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
        # Using <b> tags and parse_mode='HTML' to fix the bolding issue
        msg = f"🚨 <b>{random.choice(quotes)}</b>\n\nOpen the app. We are doing {unit} NOW."
        await bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode='HTML')

    # 99-100: GOD MODE
    else:
        await bot.send_message(chat_id=CHAT_ID, text="👑 <b>GOD MODE ACTIVATED</b>\n\nPrepare yourself...", parse_mode='HTML')

if __name__ == "__main__":
    asyncio.run(send_chaos())
