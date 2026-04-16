import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from collections import Counter

st.set_page_config(page_title="MAYA AI - Exact Shift Predictor", layout="wide")

st.title("MAYA AI: Exact Shift Prediction & Trend Tracker")

# --- 1. Independent Date & Target Controls ---
st.sidebar.header("🎯 Target Prediction")
# USER AB SELECT KAREGA KI KIS SHIFT KA RESULT CHAHIYE
target_shift_name = st.sidebar.selectbox("Predict for Which Shift?", ["Base Shift", "Shift A", "Shift B"])

st.sidebar.markdown("---")
st.sidebar.header("Shift Date Controls")
base_start = st.sidebar.date_input("Start Date (Base)", datetime(2026, 1, 1))
base_end = st.sidebar.date_input("End Date (Base)", datetime(2026, 4, 16))

other_start = st.sidebar.date_input("Start Date (Others)", datetime(2026, 1, 1))
other_end = st.sidebar.date_input("End Date (Others)", datetime(2026, 4, 16))

max_repeat_limit = st.sidebar.slider("Max Repeat Limit", 2, 5, 4)

# --- 2. Data Locking Logic ---
@st.cache_data
def load_full_data():
    np.random.seed(42)
    dates = pd.date_range(start='2025-01-01', end='2026-04-16')
    return pd.DataFrame({
        'Date': dates,
        'Base_Shift': np.random.randint(0, 100, size=len(dates)),
        'Shift_A': np.random.randint(0, 100, size=len(dates)),
        'Shift_B': np.random.randint(0, 100, size=len(dates))
    })

df = load_full_data()

# Data filtering based on selected dates
def get_shift_data(shift_name):
    if shift_name == "Base Shift":
        return df[(df['Date'].dt.date >= base_start) & (df['Date'].dt.date <= base_end)]['Base_Shift'].tolist()
    elif shift_name == "Shift A":
        return df[(df['Date'].dt.date >= other_start) & (df['Date'].dt.date <= other_end)]['Shift_A'].tolist()
    elif shift_name == "Shift B":
        return df[(df['Date'].dt.date >= other_start) & (df['Date'].dt.date <= other_end)]['Shift_B'].tolist()

# Get data for the selected target shift
target_data_list = get_shift_data(target_shift_name)

# --- 3. Core Analysis Engine ---
def analyze_sheets(shift_list, limit):
    eliminated_total = set()
    pattern_scores = Counter() 
    
    for days in range(1, 31):
        if len(shift_list) < days: continue
        sheet = shift_list[-days:]
        counts = Counter(sheet)
        
        # Zero-Repeat Rule
        if len(counts) == len(sheet) and len(sheet) > 1:
            eliminated_total.update(sheet)
        
        # Max Hit Rule
        for num, freq in counts.items():
            if freq >= limit:
                eliminated_total.add(num)
            else:
                pattern_scores[num] += 1
                
    return eliminated_total, pattern_scores

# --- 4. REAL BACKTESTING (Checking trends for the TARGET SHIFT) ---
tier_hits = {"High": 0, "Medium": 0, "Low": 0, "Failed (Eliminated)": 0}
test_days = 10 

if len(target_data_list) > test_days:
    for i in range(test_days, 0, -1):
        past_target_data = target_data_list[:-i]
        actual_result = target_data_list[-i] 
        
        elim_past, scores_past = analyze_sheets(past_target_data, max_repeat_limit)
        safe_past = [n for n in range(100) if n not in elim_past]
        
        if safe_past:
            sorted_safe_past = sorted(safe_past, key=lambda x: scores_past[x], reverse=True)
            n_past = len(sorted_safe_past)
            ht = sorted_safe_past[:int(n_past*0.33)]
            mt = sorted_safe_past[int(n_past*0.33):int(n_past*0.66)]
            lt = sorted_safe_past[int(n_past*0.66):]
            
            if actual_result in ht: tier_hits["High"] += 1
            elif actual_result in mt: tier_hits["Medium"] += 1
            elif actual_result in lt: tier_hits["Low"] += 1
            else: tier_hits["Failed (Eliminated)"] += 1

# --- 5. Today's Live Prediction ---
# We analyze the target shift for its own pattern
elim1, scores1 = analyze_sheets(target_data_list, max_repeat_limit)
final_eliminated = elim1
final_scores = scores1

safe_pool = [n for n in range(100) if n not in final_eliminated]

if safe_pool:
    sorted_safe = sorted(safe_pool, key=lambda x: final_scores[x], reverse=True)
    n = len(sorted_safe)
    high_tier = sorted_safe[:int(n*0.33)]
    med_tier = sorted_safe[int(n*0.33):int(n*0.66)]
    low_tier = sorted_safe[int(n*0.66):]
else:
    high_tier, med_tier, low_tier = [], [], []

valid_hits = {k: v for k, v in tier_hits.items() if k != "Failed (Eliminated)"}
best_tier = max(valid_hits, key=valid_hits.get) if sum(valid_hits.values()) > 0 else "None"

# --- 6. UI Display ---
# Target Date calculate karna (Base ya Other shift ke dates ke hisab se)
if target_shift_name == "Base Shift":
    target_date = base_end + timedelta(days=1)
else:
    target_date = other_end + timedelta(days=1)

# Ab screen par bada aur saaf dikhega ki prediction kis shift ki hai
st.markdown(f"### 🎯 Prediction for: **[{target_shift_name.upper()}]** on **{target_date.strftime('%d %B %Y')}**")

st.markdown("---")
st.write(f"### 🏆 AI Recommendation Engine (10-Day Trend for {target_shift_name})")

if best_tier != "None":
    st.success(f"**Agli '{target_shift_name}' ke liye aapko [{best_tier.upper()} TIER] par lagana sabse behtar rahega.**")
    st.write(f"Pichle 10 dinon ki testing mein, actual aane wale numbers is tarah ghire hain:")
    st.write(f"🔥 **High:** {tier_hits['High']} baar | ⚡ **Medium:** {tier_hits['Medium']} baar | ❄️ **Low:** {tier_hits['Low']} baar")
else:
    st.warning("Trend calculate karne ke liye data kafi nahi hai.")

st.markdown("---")
st.subheader(f"📊 Safe Numbers for {target_shift_name} (After Elimination)")

c1, c2, c3 = st.columns(3)
with c1:
    st.markdown("#### 🔥 High Tier")
    st.write(", ".join([f"{x:02d}" for x in high_tier]))
with c2:
    st.markdown("#### ⚡ Medium Tier")
    st.write(", ".join([f"{x:02d}" for x in med_tier]))
with c3:
    st.markdown("#### ❄️ Low Tier")
    st.write(", ".join([f"{x:02d}" for x in low_tier]))
          
