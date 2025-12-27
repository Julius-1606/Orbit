import os
import json
import random
import asyncio
import sys
import time
import warnings
import google.generativeai as genai
from telegram import Bot

# --- 🔇 SUPPRESS WARNINGS ---
warnings.filterwarnings("ignore")

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
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # Priority 1: Exact High-Quota Matches
        wishlist = [
            'models/gemini-1.5-flash',
            'models/gemini-1.5-flash-001',
            'models/gemini-1.5-flash-latest',
            'models/gemini-1.5-pro'
        ]
        
        for wish in wishlist:
            if wish in models:
                print(f"✅ Locked on target: {wish}")
                return genai.GenerativeModel(wish.replace("models/", ""))
        
        # Priority 2: Any model with '1.5-flash' in the name (Smart Fallback)
        smart_fallback = next((m for m in models if '1.5-flash' in m), None)
        if smart_fallback:
             print(f"⚠️ Smart Fallback to: {smart_fallback}")
             return genai.GenerativeModel(smart_fallback.replace("models/", ""))

        # Priority 3: Any model with 'flash' (avoiding pro/ultra if possible for speed)
        flash_fallback = next((m for m in models if 'flash' in m), None)
        if flash_fallback:
             print(f"⚠️ Flash Fallback to: {flash_fallback}")
             return genai.GenerativeModel(flash_fallback.replace("models/", ""))
        
        # Priority 4: Whatever is left (Last Resort)
        first_option = next((m for m in models if 'gemini' in m), None)
        if first_option:
            print(f"⚠️ Absolute Fallback to: {first_option}")
            return genai.GenerativeModel(first_option.replace("models/", ""))
            
    except Exception as e:
        print(f"⚠️ Scan failed: {e}")
    
    print("🤞 Hard-Forcing 'gemini-1.5-flash' and praying...")
    return genai.GenerativeModel('gemini-1.5-flash')

model = get_working_model()

# 🛡️ SAFE GENERATOR: Handles 429 Rate Limits
def generate_content_safe(prompt_text):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            return model.generate_content(prompt_text)
        except Exception as e:
            if "429" in str(e):
                print(f"⏳ Hit Rate Limit. Cooling down (Attempt {attempt+1}/{max_retries})...")
                time.sleep(10) # Wait 10s and retry
            else:
                raise e # Real error, let it crash
    return None

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

    # --- CHEAT CODE CHECKER ---
    if "--quiz" in sys.argv:
        print("🫡 COMMAND RECEIVED: Forcing Quiz Protocol.")
        roll = 90
    elif "--fact" in sys.argv:
        print("🫡 COMMAND RECEIVED: Forcing Knowledge Drop.")
        roll = 60
    else:
        roll = random.randint(1, 100)
        print(f"🎲 Rolled a {roll}")

    if roll <= 50:
        print("Silence is golden. Exiting.")
        return

    # 51-85: Random Fact
    elif 51 <= roll <= 85:
        topic = random.choice(config['interests'])
        prompt = f"Tell me a mind-blowing, short random fact about {topic}. Keep it under 2 sentences."
        try:
            response = generate_content_safe(prompt)
            if response:
                msg = f"🎱 <b>Magic-∞ Fact:</b>\n\n{response.text}"
                await bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode='HTML')
        except Exception as e:
            print(f"Gemini Error: {e}")

    # 86-98: The Grind (QUIZ MODE)
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
        quote = random.choice(quotes)
        
        await bot.send_message(chat_id=CHAT_ID, text=f"🚨 <b>{quote}</b>\n\nIncoming Pop Quiz: <b>{unit}</b>", parse_mode='HTML')
        
        prompt = f"""
        Generate a multiple-choice quiz question about {unit} for a 4th Year University Student.
        
        CRITICAL: Telegram Polls have strict character limits.
        1. The 'question' MUST be under 250 characters.
        2. Each 'option' MUST be under 100 characters.
        3. The 'explanation' MUST be under 190 characters.
        
        Respond ONLY with valid JSON in this format:
        {{
            "question": "The question text?",
            "options": ["A", "B", "C", "D"],
            "correct_id": 0,
            "explanation": "Brief explanation."
        }}
        """
        try:
            response = generate_content_safe(prompt)
            if response:
                text = response.text.replace('```json', '').replace('```', '').strip()
                quiz_data = json.loads(text)
                
                # HARD LIMITS (Safety Net) ✂️
                q_text = quiz_data['question']
                if len(q_text) > 300: q_text = q_text[:297] + "..."
                
                opts = [o[:100] for o in quiz_data['options']]
                
                expl = quiz_data['explanation']
                if len(expl) > 200: expl = expl[:197] + "..."

                await bot.send_poll(
                    chat_id=CHAT_ID,
                    question=q_text,
                    options=opts,
                    type="quiz",
                    correct_option_id=quiz_data['correct_id'],
                    explanation=expl
                )
        except Exception as e:
            print(f"Quiz Generation Failed: {e}")
            await bot.send_message(chat_id=CHAT_ID, text="⚠️ AI Brain Freeze. Just go read a book.")

    # 99-100: GOD MODE
    else:
        await bot.send_message(chat_id=CHAT_ID, text="👑 <b>GOD MODE ACTIVATED</b>\n\nPrepare yourself...", parse_mode='HTML')

if __name__ == "__main__":
    asyncio.run(send_chaos())
