import os
import json
import random
import asyncio
import sys
import time
import warnings

# --- 🔇 SUPPRESS WARNINGS ---
os.environ["GRPC_VERBOSITY"] = "ERROR"
os.environ["GLOG_minloglevel"] = "2"
warnings.filterwarnings("ignore")

import google.generativeai as genai
from telegram import Bot

# --- 🔐 SECRETS MANAGEMENT ---
# Try to get secrets from Environment Variables (GitHub Actions / Local Env)
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
KEYS_STRING = os.environ.get("GEMINI_KEYS")

# Fallback: If running locally without Env Vars, try to read from a local secrets file
# (This part ensures it still works on your laptop if you haven't set Env Vars)
if not TELEGRAM_TOKEN or not KEYS_STRING:
    try:
        # Check if we can find them in .streamlit/secrets.toml (Reusing dashboard secrets)
        import toml
        script_dir = os.path.dirname(os.path.abspath(__file__))
        secrets_path = os.path.join(script_dir, ".streamlit", "secrets.toml")
        with open(secrets_path, "r") as f:
            local_secrets = toml.load(f)
            TELEGRAM_TOKEN = TELEGRAM_TOKEN or local_secrets.get("TELEGRAM_TOKEN")
            GEMINI_API_KEYS = local_secrets.get("GEMINI_KEYS") # Expecting a list in TOML
    except Exception:
        pass
else:
    # If found in Env Vars (GitHub), split the comma-separated string into a list
    GEMINI_API_KEYS = KEYS_STRING.split(",") if KEYS_STRING else []

# 🛑 SECURITY CHECK
if not TELEGRAM_TOKEN or not GEMINI_API_KEYS:
    print("❌ FATAL ERROR: Secrets not found. Set TELEGRAM_TOKEN and GEMINI_KEYS.")
    sys.exit(1)

CHAT_ID = "6882899041" # Chat ID is public info, essentially (it's just your user ID), so it's okay-ish to keep.

CURRENT_KEY_INDEX = 0

# --- CONFIGURATION & ROTATION ---
def configure_genai():
    global CURRENT_KEY_INDEX
    if not GEMINI_API_KEYS: return
    key = GEMINI_API_KEYS[CURRENT_KEY_INDEX]
    genai.configure(api_key=key)

def rotate_key():
    global CURRENT_KEY_INDEX
    if len(GEMINI_API_KEYS) > 1:
        CURRENT_KEY_INDEX = (CURRENT_KEY_INDEX + 1) % len(GEMINI_API_KEYS)
        print(f"🔄 Rotating to Backup Key #{CURRENT_KEY_INDEX + 1}...")
        configure_genai()
        return True
    else:
        print("⚠️ No backup keys found!")
        return False

# Initialize first key
configure_genai()

# 🛠️ AUTO-SELECTOR
def get_working_model():
    try:
        print("🔍 Scanning available AI models...")
        all_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # 🚫 BAN LIST
        safe_models = [m for m in all_models if "gemini-2" not in m and "experimental" not in m]
        
        wishlist = ['models/gemini-1.5-flash', 'models/gemini-1.5-flash-001', 'models/gemini-1.5-pro']
        for wish in wishlist:
            if wish in safe_models:
                print(f"✅ Locked on target: {wish}")
                return genai.GenerativeModel(wish.replace("models/", ""))
        
        # Fallbacks
        fallback = next((m for m in safe_models if '1.5-flash' in m), None)
        if fallback: return genai.GenerativeModel(fallback.replace("models/", ""))
            
    except Exception as e:
        print(f"⚠️ Scan failed: {e}")
    
    print("🤞 Hard-Forcing 'gemini-1.5-flash'...")
    return genai.GenerativeModel('gemini-1.5-flash')

model = get_working_model()

# 🛡️ SAFE GENERATOR
def generate_content_safe(prompt_text):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            return model.generate_content(prompt_text)
        except Exception as e:
            err_msg = str(e)
            if "429" in err_msg or "403" in err_msg:
                print(f"⏳ Limit Hit. (Attempt {attempt+1})")
                if rotate_key():
                    time.sleep(2)
                    continue
                else:
                    time.sleep(10)
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
        print(f"❌ CRITICAL ERROR: Could not find config.json")
        return None

async def send_chaos():
    bot = Bot(token=TELEGRAM_TOKEN)
    config = load_config()
    
    if not config: return 

    # --- LOGIC START ---
    if "--quiz" in sys.argv:
        roll = 90
    elif "--fact" in sys.argv:
        roll = 60
    else:
        roll = random.randint(1, 100)
        print(f"🎲 Rolled a {roll}")

    if roll <= 50:
        print("Silence is golden.")
        return

    # FACT
    elif 51 <= roll <= 85:
        topic = random.choice(config['interests'])
        prompt = f"Tell me a mind-blowing, short random fact about {topic}. Keep it under 2 sentences."
        response = generate_content_safe(prompt)
        if response and response.text:
            msg = f"🎱 <b>Magic-∞ Fact:</b>\n\n{response.text}"
            await bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode='HTML')

    # QUIZ
    elif 86 <= roll <= 98:
        unit = random.choice(config['current_units'])
        await bot.send_message(chat_id=CHAT_ID, text=f"🚨 <b>Incoming Pop Quiz: {unit}</b>", parse_mode='HTML')
        
        prompt = f"""
        Generate a multiple-choice quiz about {unit} for a 4th Year Student.
        Strict JSON format: {{"question": "...", "options": ["A","B","C","D"], "correct_id": 0, "explanation": "..."}}
        Limits: Question < 250 chars, Options < 100 chars.
        """
        response = generate_content_safe(prompt)
        if response and response.text:
            try:
                text = response.text.replace('```json', '').replace('```', '').strip()
                data = json.loads(text)
                await bot.send_poll(
                    chat_id=CHAT_ID,
                    question=data['question'][:297],
                    options=[o[:97] for o in data['options']],
                    type="quiz",
                    correct_option_id=data['correct_id'],
                    explanation=data['explanation'][:197]
                )
            except Exception as e:
                print(f"Quiz Error: {e}")

    else:
        await bot.send_message(chat_id=CHAT_ID, text="👑 <b>GOD MODE ACTIVATED</b>", parse_mode='HTML')

if __name__ == "__main__":
    asyncio.run(send_chaos())
