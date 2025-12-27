import streamlit as st
import json
import os

# --- PAGE SETUP ---
st.set_page_config(
    page_title="Orbit Command Center",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- FUNCTIONS ---
def load_config():
    with open('config.json', 'r') as f:
        return json.load(f)

def save_config(config):
    with open('config.json', 'w') as f:
        json.dump(config, f, indent=4)
    st.toast("Brain Updated! 🧠", icon="💾")

# --- MAIN APP ---
st.title("🛰️ Orbit: Academic Weapon Control")
st.markdown("*Commander's Log: Semester 4 - Redemption Arc*")

# Load Data
config = load_config()

# --- SIDEBAR (Profile) ---
with st.sidebar:
    st.header("👤 Profile")
    st.text_input("Username", value=config['user_name'], disabled=True)
    st.text_input("Difficulty", value=config['difficulty'], disabled=True)
    
    st.divider()
    
    st.header("🎯 Active Loadout")
    st.info(f"Tracking {len(config['current_units'])} Units")
    for unit in config['current_units']:
        st.caption(f"• {unit}")

# --- MAIN AREA (Curriculum Manager) ---
tab1, tab2 = st.tabs(["📚 Curriculum Manager", "🎲 Chaos Settings"])

with tab1:
    st.subheader("Unit Inventory Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("### 🎒 Inventory (Storage)")
        # Create a dropdown to pick Year
        selected_year = st.selectbox("Select Year", list(config['unit_inventory'].keys()))
        selected_sem = st.selectbox("Select Semester", list(config['unit_inventory'][selected_year].keys()))
        
        # Show available units in that semester
        available_units = config['unit_inventory'][selected_year][selected_sem]
        
        # Multi-select to add to Current Loadout
        units_to_add = st.multiselect(
            f"Add from {selected_year} - {selected_sem}",
            available_units
        )
        
        if st.button("➕ Add to Active Loadout"):
            for u in units_to_add:
                if u not in config['current_units']:
                    config['current_units'].append(u)
            save_config(config)
            st.rerun()

    with col2:
        st.write("### 🔥 Active Grind (Current)")
        # Checkbox list to REMOVE units
        for unit in config['current_units']:
            if st.checkbox(f"Drop {unit}", key=unit):
                config['current_units'].remove(unit)
                save_config(config)
                st.rerun()

with tab2:
    st.subheader("Interests & Chaos")
    st.write("These topics appear in random 'Magic-∞' notifications.")
    
    current_interests = st.text_area(
        "Interests (Comma separated)", 
        ", ".join(config['interests'])
    )
    
    if st.button("Update Interests"):
        new_list = [x.strip() for x in current_interests.split(",")]
        config['interests'] = new_list
        save_config(config)
        st.success("Interests updated!")

# --- FOOTER ---
st.divider()
st.caption("Orbit System v1.0 | Connected to Local Brain")