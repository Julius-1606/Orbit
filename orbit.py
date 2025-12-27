import os
import json
import random
import asyncio
import sys
import time
import warnings

# --- 🔇 SUPPRESS WARNINGS (Must be before imports) ---
os.environ["GRPC_VERBOSITY"] = "ERROR"
os.environ["GLOG_minloglevel"] = "2"
warnings.filterwarnings("ignore")

import google.generativeai as genai
from telegram import Bot

# --- ⚠️ HARDCODED SECRETS (PRIVATE REPO ONLY) ⚠️ ---
TELEGRAM_TOKEN = "8512814291:AAEgtDBZDzB4MKz2BdsAjXYk0YLpKzGGO20"
CHAT_ID = "6882899041"

# 🔑 KEYCHAIN: Add as many backups as you want
GEMINI_API_KEYS = [
    "AIzaSyDRthGk2azAa8EcJYfzWfHmpuz8Z_Z5fGU",     # Primary
    "AIzaSyACCa8g1S-OuriEEPefbtE03AYASQlI3Y0",     # Backup 1
    "AIzaSyB4RQujKan7CnJLuOHMgnMf-emBX9emNW8",     # Backup 2
    "AIzaSyBYMHrr5yicq3bFo7817CFUtXQ6YUS6YSg",     # Backup 3
    "AIzaSyAVxFhE3Gxgq2jE5_QI0p_1EFdCSROfu3w",     # Backup 4
    "AIzaSyA7rpM5SFNTGKOUwy5UDdGt65EWXS1gUbM",     # Backup 5
]

CURRENT_KEY_INDEX = 0

# --- CONFIGURATION & ROTATION ---
def configure_genai():
    global CURRENT_KEY_INDEX
    key = GEMINI_API_KEYS[CURRENT_KEY_INDEX]
    genai.configure(api_key=key)
    # print(f"🔌 Connected with Key #{CURRENT_KEY_INDEX + 1}")

def rotate_key():
    global CURRENT_KEY_INDEX
    if len(GEMINI_API_KEYS) > 1:
        CURRENT_KEY_INDEX = (CURRENT_KEY_INDEX + 1) % len(GEMINI_API_KEYS)
        print(f"🔄 Rotating to Backup Key #{CURRENT_KEY_INDEX + 1}...")
        configure_genai()
        return True
    else:
        print("⚠️ No backup keys found! Add more to GEMINI_API_KEYS list.")
        return False

# Initialize first key
configure_genai()

# 🛠️ AUTO-SELECTOR: Finds a model that actually exists so we stop guessing
def get_working_model():
    try:
        print("🔍 Scanning available AI models...")
        all_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # 🚫 BAN LIST: No previews, no experimentals
        safe_models = [m for m in all_models if "gemini-2" not in m and "experimental" not in m]
        
        wishlist = [
            'models/gemini-1.5-flash',
            'models/gemini-1.5-flash-001',
            'models/gemini-1.5-flash-002',
            'models/gemini-1.5-pro'
        ]
        
        for wish in wishlist:
            if wish in safe_models:
                print(f"✅ Locked on target: {wish}")
                return genai.GenerativeModel(wish.replace("models/", ""))
        
        # Smart Fallback
        smart_fallback = next((m for m in safe_models if '1.5-flash' in m), None)
        if smart_fallback:
             print(f"⚠️ Smart Fallback to: {smart_fallback}")
             return genai.GenerativeModel(smart_fallback.replace("models/", ""))

        # Flash Fallback
        flash_fallback = next((m for m in safe_models if 'flash' in m), None)
        if flash_fallback:
             print(f"⚠️ Flash Fallback to: {flash_fallback}")
             return genai.GenerativeModel(flash_fallback.replace("models/", ""))
        
        # Absolute Fallback
        first_option = next((m for m in safe_models if 'gemini' in m), None)
        if first_option:
            print(f"⚠️ Absolute Fallback to: {first_option}")
            return genai.GenerativeModel(first_option.replace("models/", ""))
            
    except Exception as e:
        print(f"⚠️ Scan failed: {e}")
    
    print("🤞 Hard-Forcing 'gemini-1.5-flash' and praying...")
    return genai.GenerativeModel('gemini-1.5-flash')

model = get_working_model()

# 🛡️ SAFE GENERATOR: Handles 429 Rate Limits + Key Rotation
def generate_content_safe(prompt_text):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            return model.generate_content(prompt_text)
        except Exception as e:
            err_msg = str(e)
            if "429" in err_msg or "403" in err_msg:
                print(f"⏳ Key Exhausted/Limit Hit. (Attempt {attempt+1}/{max_retries})")
                if rotate_key():
                    time.sleep(2) # Short pause for swap
                    continue # Retry immediately with new key
                else:
                    time.sleep(10) # No backups? Wait it out.
            else:
                print(f"❌ API Error: {err_msg}")
                return None
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
        
        response = generate_content_safe(prompt)
        if response and response.text:
            msg = f"🎱 <b>Magic-∞ Fact:</b>\n\n{response.text}"
            await bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode='HTML')
        else:
            print("⚠️ AI returned empty response for Fact.")

    # 86-98: The Grind (QUIZ MODE)
    elif 86 <= roll <= 98:
        quotes = [
            "Sleep is for the weak. Grind is for the eternal.",
            "Lock in. The patient isn't gonna save themselves. 🩺",
            "Academic Weapon status: Loading... 🔫",
            "Pain is temporary. The 'Dr.' title is forever. 🥼",
            "Stop scrolling. Start solving.",
            "Coffee in. Knowledge out. ☕",
            "The charts are moving. Why aren't you? 📉",
            "Coding is just wizardry. Go cast a spell. 🧙‍♂️"
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
        
        response = generate_content_safe(prompt)
        if response and response.text:
            try:
                # Cleaning the response to prevent JSON crashes
                text = response.text.replace('```json', '').replace('```', '').strip()
                quiz_data = json.loads(text)
                
                # Safety Truncation ✂️
                q_text = quiz_data['question'][:297] + ("..." if len(quiz_data['question']) > 297 else "")
                opts = [o[:97] + "..." if len(o) > 100 else o for o in quiz_data['options']]
                expl = quiz_data['explanation'][:197] + ("..." if len(quiz_data['explanation']) > 197 else "")

                await bot.send_poll(
                    chat_id=CHAT_ID,
                    question=q_text,
                    options=opts,
                    type="quiz",
                    correct_option_id=quiz_data['correct_id'],
                    explanation=expl
                )
            except json.JSONDecodeError:
                print(f"⚠️ JSON Parse Error. Raw AI Text: {response.text}")
                await bot.send_message(chat_id=CHAT_ID, text="⚠️ AI Brain Malfunction. Try again.")
            except Exception as e:
                print(f"Quiz Error: {e}")
        else:
            print("⚠️ AI returned empty response for Quiz.")

    # 99-100: GOD MODE
    else:
        await bot.send_message(chat_id=CHAT_ID, text="👑 <b>GOD MODE ACTIVATED</b>\n\nPrepare yourself...", parse_mode='HTML')

if __name__ == "__main__":
    asyncio.run(send_chaos())
