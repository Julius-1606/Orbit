import os
import warnings
os.environ["GRPC_VERBOSITY"] = "ERROR"
os.environ["GLOG_minloglevel"] = "2"
warnings.filterwarnings("ignore")

import streamlit as st
import json
import random
import time
import google.generativeai as genai

# --- 🔐 SECURE KEYCHAIN ---
# The code checks Streamlit Secrets first (Cloud), then Environment Vars (Local/GitHub)
try:
    # 1. Try Streamlit Secrets (Cloud/Local TOML)
    GEMINI_API_KEYS = st.secrets["GEMINI_KEYS"]
except Exception:
    try:
        # 2. Try Environment Variables (Fallback)
        keys_str = os.environ.get("GEMINI_KEYS")
        GEMINI_API_KEYS = keys_str.split(",") if keys_str else []
    except Exception:
        GEMINI_API_KEYS = []

if not GEMINI_API_KEYS:
    st.error("❌ NO API KEYS FOUND! Please configure secrets.")
    st.stop()

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

configure_genai()

# 🛠️ AUTO-SELECTOR
def get_working_model():
    try:
        all_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        safe_models = [m for m in all_models if "gemini-2" not in m and "experimental" not in m]
        
        wishlist = ['models/gemini-1.5-flash', 'models/gemini-1.5-flash-001', 'models/gemini-1.5-pro']
        for wish in wishlist:
            if wish in safe_models: return genai.GenerativeModel(wish.replace("models/", ""))
        
        fallback = next((m for m in safe_models if '1.5-flash' in m), None)
        if fallback: return genai.GenerativeModel(fallback.replace("models/", ""))
            
    except Exception:
        pass
    return genai.GenerativeModel('gemini-1.5-flash')

model = get_working_model()

def ask_orbit(prompt):
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
            print(f"❌ Chat Error: {err_msg}")
            return None
    return None

# --- PAGE SETUP ---
st.set_page_config(page_title="Orbit Command Center", page_icon="🛰️", layout="wide")

# --- CONFIG FUNCTIONS ---
def get_config_path():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(script_dir, 'config.json')

def load_config():
    try:
        with open(get_config_path(), 'r') as f: return json.load(f)
    except FileNotFoundError: return None

def save_config(config):
    with open(get_config_path(), 'w') as f: json.dump(config, f, indent=4)
    st.toast("Settings Saved! 💾", icon="✅")

# --- MAIN APP ---
st.title("🛰️ Orbit: Academic Weapon Control")
st.markdown("*Commander's Log: Semester 4 - Redemption Arc*")
config = load_config()

if config:
    with st.sidebar:
        st.header("👤 Commander Profile")
        st.text_input("Username", value=config.get('user_name', 'Commander'), disabled=True)
        st.divider()
        
        # Difficulty
        diffs = ["Easy (Review)", "Medium (Standard)", "Hard (Exam Prep)", "Asian Parent Expectations (Extreme)"]
        curr_diff = config.get('difficulty', "Asian Parent Expectations (Extreme)")
        idx = diffs.index(curr_diff) if curr_diff in diffs else 3
        new_diff = st.selectbox("Difficulty Level", diffs, index=idx)
        if new_diff != curr_diff:
            config['difficulty'] = new_diff
            save_config(config)
            
        st.divider()
        st.header("🎯 Active Loadout")
        for unit in config['current_units']: st.caption(f"• {unit}")

    tab1, tab2, tab3 = st.tabs(["💬 Orbit Chat", "📚 Curriculum Manager", "🎲 Chaos Settings"])

    # CHAT
    with tab1:
        st.subheader("🧠 Neural Link")
        if "messages" not in st.session_state: st.session_state.messages = []
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]): st.markdown(msg["content"])
            
        if prompt := st.chat_input("Ask Orbit..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.markdown(prompt)
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    ctx = f"You are Orbit. User studies: {', '.join(config['current_units'])}. Difficulty: {config['difficulty']}. Question: {prompt}"
                    response = ask_orbit(ctx)
                    if response and response.text:
                        st.markdown(response.text)
                        st.session_state.messages.append({"role": "assistant", "content": response.text})
                    else:
                        st.error("⚠️ Connection Interrupted.")

    # CURRICULUM
    with tab2:
        col1, col2 = st.columns(2)
        with col1:
            years = list(config['unit_inventory'].keys())
            if years:
                y = st.selectbox("Year", years)
                # Handle old/new structure
                if isinstance(config['unit_inventory'][y], dict):
                    sems = list(config['unit_inventory'][y].keys())
                    s = st.selectbox("Semester", sems)
                    avail = config['unit_inventory'][y][s]
                else:
                    avail = config['unit_inventory'][y]
                    s = "General"
                
                adds = st.multiselect(f"Add from {y}-{s}", avail)
                if st.button("➕ Add"):
                    for u in adds:
                        if u not in config['current_units']: config['current_units'].append(u)
                    save_config(config)
                    st.rerun()
        with col2:
            for unit in config['current_units']:
                if st.checkbox(f"Drop {unit}", key=unit):
                    config['current_units'].remove(unit)
                    save_config(config)
                    st.rerun()

    # CHAOS
    with tab3:
        curr = st.text_area("Interests", ", ".join(config['interests']))
        if st.button("Update Interests"):
            config['interests'] = [x.strip() for x in curr.split(",")]
            save_config(config)
            st.success("Updated!")
