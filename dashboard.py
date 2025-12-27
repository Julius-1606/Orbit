import os
import warnings

# --- 🔇 SUPPRESS WARNINGS (Must be before imports) ---
os.environ["GRPC_VERBOSITY"] = "ERROR"
os.environ["GLOG_minloglevel"] = "2"
warnings.filterwarnings("ignore")

import streamlit as st
import json
import random
import time
import google.generativeai as genai

# --- 🔐 KEYCHAIN & AI SETUP ---
GEMINI_API_KEYS = [
    "AIzaSyDRthGk2azAa8EcJYfzWfHmpuz8Z_Z5fGU",      # Primary
    "AIzaSyACCa8g1S-OuriEEPefbtE03AYASQlI3Y0",      # Backup 1
    "AIzaSyB4RQujKan7CnJLuOHMgnMf-emBX9emNW8",      # Backup 2
    "AIzaSyBYMHrr5yicq3bFo7817CFUtXQ6YUS6YSg",      # Backup 3
    "AIzaSyAVxFhE3Gxgq2jE5_QI0p_1EFdCSROfu3w",      # Backup 4
    "AIzaSyA7rpM5SFNTGKOUwy5UDdGt65EWXS1gUbM",      # Backup 5
]

# Session State for Rotation
if "key_index" not in st.session_state:
    st.session_state.key_index = 0

def configure_genai():
    try:
        current_key = GEMINI_API_KEYS[st.session_state.key_index]
        genai.configure(api_key=current_key)
        return True
    except Exception as e:
        return False

def rotate_key():
    if len(GEMINI_API_KEYS) > 1:
        st.session_state.key_index = (st.session_state.key_index + 1) % len(GEMINI_API_KEYS)
        configure_genai()
        st.toast(f"🔄 Swapping to Key #{st.session_state.key_index + 1}", icon="🔑")
        return True
    return False

# Initialize AI
configure_genai()

# 🛠️ AUTO-SELECTOR: Finds a model that actually exists (Copied from Orbit.py)
def get_working_model():
    try:
        # Get all models that support generating text
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
                print(f"✅ Dashboard locked on: {wish}")
                return genai.GenerativeModel(wish.replace("models/", ""))
        
        # Smart Fallback
        smart_fallback = next((m for m in safe_models if '1.5-flash' in m), None)
        if smart_fallback:
             return genai.GenerativeModel(smart_fallback.replace("models/", ""))

        # Flash Fallback
        flash_fallback = next((m for m in safe_models if 'flash' in m), None)
        if flash_fallback:
             return genai.GenerativeModel(flash_fallback.replace("models/", ""))
        
        # Absolute Fallback
        first_option = next((m for m in safe_models if 'gemini' in m), None)
        if first_option:
            return genai.GenerativeModel(first_option.replace("models/", ""))
            
    except Exception as e:
        print(f"⚠️ Dashboard Scan failed: {e}")
    
    return genai.GenerativeModel('gemini-1.5-flash')

# Set the model dynamically instead of hardcoding
model = get_working_model()

def ask_orbit(prompt):
    """Safe generator with rotation"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            return model.generate_content(prompt)
        except Exception as e:
            err_msg = str(e)
            if "429" in err_msg or "403" in err_msg:
                if rotate_key():
                    time.sleep(1)
                    continue
            # If it's a real error, print it to console for debugging
            print(f"❌ Chat Error: {err_msg}")
            return None
    return None

# --- PAGE SETUP ---
st.set_page_config(
    page_title="Orbit Command Center",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CONFIG FUNCTIONS ---
def get_config_path():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(script_dir, 'config.json')

def load_config():
    try:
        with open(get_config_path(), 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        st.error("❌ config.json not found!")
        return None

def save_config(config):
    with open(get_config_path(), 'w') as f:
        json.dump(config, f, indent=4)
    st.toast("Settings Saved! 💾", icon="✅")

# --- MAIN APP ---
st.title("🛰️ Orbit: Academic Weapon Control")
st.markdown("*Commander's Log: Semester 4 - Redemption Arc*")

# Load Data
config = load_config()

if config:
    # --- SIDEBAR (Settings) ---
    with st.sidebar:
        st.header("👤 Commander Profile")
        st.text_input("Username", value=config.get('user_name', 'Commander'), disabled=True)
        
        st.divider()
        st.header("⚙️ Game Settings")
        
        # 🎚️ DIFFICULTY ADJUSTMENT
        difficulty_levels = [
            "Easy (Review)", 
            "Medium (Standard)", 
            "Hard (Exam Prep)", 
            "Asian Parent Expectations (Extreme)"
        ]
        
        # Find current index or default to Extreme
        current_diff = config.get('difficulty', "Asian Parent Expectations (Extreme)")
        try:
            diff_index = difficulty_levels.index(current_diff)
        except ValueError:
            diff_index = 3
            
        new_difficulty = st.selectbox("Difficulty Level", difficulty_levels, index=diff_index)
        
        if new_difficulty != current_diff:
            config['difficulty'] = new_difficulty
            save_config(config)
        
        st.divider()
        st.header("🎯 Active Loadout")
        for unit in config['current_units']:
            st.caption(f"• {unit}")

    # --- MAIN TABS ---
    tab1, tab2, tab3 = st.tabs(["💬 Orbit Chat", "📚 Curriculum Manager", "🎲 Chaos Settings"])

    # --- TAB 1: CHAT SESSION ---
    with tab1:
        st.subheader("🧠 Neural Link")
        st.caption("Ask questions about your active units. Orbit has access to your Difficulty setting.")
        
        # Initialize chat history
        if "messages" not in st.session_state:
            st.session_state.messages = []

        # Display chat messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Chat Input
        if prompt := st.chat_input("Explain the mechanism of action for..."):
            # Add user message to history
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            # Generate response
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    # Context Injection
                    context = f"""
                    You are Orbit, an intense but helpful academic AI tutor.
                    The user is studying: {', '.join(config['current_units'])}.
                    Current Difficulty: {config['difficulty']}.
                    User Question: {prompt}
                    
                    If the difficulty is Extreme, be strict and detailed.
                    If the difficulty is Easy, be encouraging and simple.
                    Keep it Gen-Z/Modern in tone.
                    """
                    
                    response = ask_orbit(context)
                    
                    if response and response.text:
                        st.markdown(response.text)
                        st.session_state.messages.append({"role": "assistant", "content": response.text})
                    else:
                        st.error("⚠️ Connection Interrupted. Check terminal for details.")

    # --- TAB 2: CURRICULUM ---
    with tab2:
        st.subheader("Unit Inventory Management")
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("### 🎒 Inventory")
            years = list(config['unit_inventory'].keys())
            if years:
                selected_year = st.selectbox("Select Year", years)
                if isinstance(config['unit_inventory'][selected_year], dict):
                    semesters = list(config['unit_inventory'][selected_year].keys())
                    selected_sem = st.selectbox("Select Semester", semesters)
                    available_units = config['unit_inventory'][selected_year][selected_sem]
                else:
                    available_units = config['unit_inventory'][selected_year]
                    selected_sem = "General"
                
                units_to_add = st.multiselect(f"Add from {selected_year} - {selected_sem}", available_units)
                if st.button("➕ Add to Active Loadout"):
                    for u in units_to_add:
                        if u not in config['current_units']:
                            config['current_units'].append(u)
                    save_config(config)
                    st.rerun()

        with col2:
            st.write("### 🔥 Active Grind")
            if not config['current_units']:
                st.info("No active units.")
            else:
                for unit in config['current_units']:
                    if st.checkbox(f"Drop {unit}", key=unit):
                        config['current_units'].remove(unit)
                        save_config(config)
                        st.rerun()

    # --- TAB 3: CHAOS ---
    with tab3:
        st.subheader("Interests & Chaos")
        current_interests = st.text_area("Interests (Comma separated)", ", ".join(config['interests']))
        if st.button("Update Interests"):
            new_list = [x.strip() for x in current_interests.split(",")]
            config['interests'] = new_list
            save_config(config)
            st.success("Interests updated!")

    st.divider()
    st.caption("Orbit System v2.0 | Local Command Center")
