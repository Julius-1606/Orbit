import os
import warnings
os.environ["GRPC_VERBOSITY"] = "ERROR"
os.environ["GLOG_minloglevel"] = "2"
warnings.filterwarnings("ignore")

import streamlit as st
import json
import time
import google.generativeai as genai

# --- 🔐 SECURE KEYCHAIN ---
GEMINI_API_KEYS = []
try:
    raw_keys = st.secrets.get("GEMINI_KEYS")
    if raw_keys:
        if isinstance(raw_keys, list):
            GEMINI_API_KEYS = raw_keys
        else:
            GEMINI_API_KEYS = [k.strip() for k in raw_keys.split(",")]
except Exception:
    pass

if not GEMINI_API_KEYS:
    try:
        keys_str = os.environ.get("GEMINI_KEYS")
        if keys_str:
            GEMINI_API_KEYS = [k.strip() for k in keys_str.split(",")]
    except Exception:
        pass

if not GEMINI_API_KEYS:
    st.error("❌ NO API KEYS FOUND! Please configure secrets.")
    st.stop()

if "key_index" not in st.session_state: st.session_state.key_index = 0

def configure_genai():
    try:
        current_key = GEMINI_API_KEYS[st.session_state.key_index]
        genai.configure(api_key=current_key)
        return True
    except Exception: return False

def rotate_key():
    if len(GEMINI_API_KEYS) > 1:
        st.session_state.key_index = (st.session_state.key_index + 1) % len(GEMINI_API_KEYS)
        configure_genai()
        st.toast(f"🔄 Swapping to Key #{st.session_state.key_index + 1}", icon="🔑")
        global model
        model = get_valid_model()
        return True
    return False

configure_genai()

# 📡 SONAR (Copied from Orbit.py)
def get_valid_model():
    try:
        models = list(genai.list_models())
        valid_models = [m.name for m in models if 'generateContent' in m.supported_generation_methods]
        
        for m in valid_models:
            if 'gemini-1.5-flash' in m and 'latest' not in m and 'exp' not in m:
                return genai.GenerativeModel(m.replace("models/", ""))
        
        for m in valid_models:
             if 'flash' in m and 'gemini-2' not in m and 'exp' not in m:
                return genai.GenerativeModel(m.replace("models/", ""))

        if valid_models:
            return genai.GenerativeModel(valid_models[0].replace("models/", ""))
    except Exception:
        pass
    return genai.GenerativeModel('gemini-1.5-flash')

model = get_valid_model()

def ask_orbit(prompt):
    global model
    max_retries = 3
    for attempt in range(max_retries):
        try:
            return model.generate_content(prompt)
        except Exception as e:
            err_msg = str(e)
            if "leaked" in err_msg.lower() or "403" in err_msg:
                 st.toast(f"⚠️ Key #{st.session_state.key_index+1} Leaked. Rotating...", icon="🔥")
                 if rotate_key():
                    time.sleep(1)
                    continue
            elif "429" in err_msg:
                if rotate_key():
                    time.sleep(1)
                    continue
            
            print(f"❌ Chat Error: {err_msg}")
            return None
    return None

# --- PAGE SETUP ---
st.set_page_config(page_title="Orbit Command Center", page_icon="🛰️", layout="wide")

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

st.title("🛰️ Orbit: Academic Weapon Control")
st.markdown("*Commander's Log: Semester 4 - Redemption Arc*")
config = load_config()

if config:
    with st.sidebar:
        st.header("👤 Commander Profile")
        st.text_input("Username", value=config.get('user_name', 'Commander'), disabled=True)
        st.divider()
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
                        st.error("⚠️ Connection Interrupted. Check Keys.")

    with tab2:
        col1, col2 = st.columns(2)
        with col1:
            years = list(config['unit_inventory'].keys())
            if years:
                y = st.selectbox("Year", years)
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

    with tab3:
        curr = st.text_area("Interests", ", ".join(config['interests']))
        if st.button("Update Interests"):
            config['interests'] = [x.strip() for x in curr.split(",")]
            save_config(config)
            st.success("Updated!")
