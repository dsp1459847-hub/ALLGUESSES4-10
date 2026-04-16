import streamlit as st
import pandas as pd
import numpy as np
from datetime import timedelta
from collections import Counter

st.set_page_config(page_title="MAYA AI - Live Data Engine", layout="wide")

st.title("MAYA AI: Live Shift Predictor & History Tracker")

# --- 1. File Uploader & Setup ---
st.sidebar.header("📁 Upload Your Data")
uploaded_file = st.sidebar.file_uploader("Apni CSV ya Excel file yahan upload karein", type=['csv', 'xlsx'])

# Asli shift names from your data
shift_names = ["DS", "FD", "GD", "GL", "DB", "SG", "ZA"]

st.sidebar.markdown("---")
st.sidebar.header("🎯 Target Prediction")
target_shift_name = st.sidebar.selectbox("Predict for Which Shift?", shift_names)

st.sidebar.markdown("---")
st.sidebar.header("Filter Controls")
max_repeat_limit = st.sidebar.slider("Max Repeat Limit", 2, 5, 4)

if uploaded_file is not None:
    # --- 2. Data Loading & Cleaning ---
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
            
        # Date column ko sahi format me lana
        df['DATE'] = pd.to_datetime(df['DATE'], errors='coerce')
        
        # Sirf Date aur Target Shift ka data alag karna
        shift_df = df[['DATE', target_shift_name]].copy()
        
        # Data Cleaning: "XX" ya blank values ko hata kar sirf numbers rakhna
        shift_df[target_shift_name] = pd.to_numeric(shift_df[target_shift_name], errors='coerce')
        shift_df = shift_df.dropna(subset=['DATE', target_shift_name])
        shift_df[target_shift_name] = shift_df[target_shift_name].astype(int)
        
        # Sort by Date just in case
        shift_df = shift_df.sort_values(by='DATE').reset_index(drop=True)
        
        target_data_list = shift_df[target_shift_name].tolist()
        
        if len(target_data_list) == 0:
            st.error(f"{target_shift_name} mein koi valid number nahi mila. Kripya data check karein.")
            st.stop()
            
        # Target Date (Aakhri date + 1 din)
        last_date = shift_df['DATE'].iloc[-1]
        target_date = last_date + timedelta(days=1)

        # --- 3. SHOW LAST 10 DAYS HISTORY ---
        st.markdown("---")
        st.write(f"### 📅 Last 10 Days Result for **{target_shift_name}**")
        
        if len(shift_df) >= 10:
            last_10_df = shift_df.tail(10).copy()
            last_10_df['DATE'] = last_10_df['DATE'].dt.strftime('%d %B %Y')
            last_10_df = last_10_df.reset_index(drop=True)
            last_10_df.index += 1 
            st.table(last_10_df.style.format({target_shift_name: "{:02d}"}))
        else:
            st.warning("10 din ka history dikhane ke liye data kafi nahi hai.")

        # --- 4. Core Analysis Engine (1-30 Days Analysis) ---
        def analyze_sheets(shift_list, limit):
            eliminated_total = set()
            pattern_scores = Counter() 
            
            for days in range(1, 31):
                if len(shift_list) < days: continue
                sheet = shift_list[-days:]
                counts = Counter(sheet)
                
                # Rule 1: Zero-Repeat (Puri sheet alag hai toh sab reject)
                if len(counts) == len(sheet) and len(sheet) > 1:
                    eliminated_total.update(sheet)
                
                # Rule 2: Max Hit Elimination
                for num, freq in counts.items():
                    if freq >= limit:
                        eliminated_total.add(num)
                    else:
                        pattern_scores[num] += 1
                        
            return eliminated_total, pattern_scores

        # --- 5. REAL BACKTESTING (Trend Calculation for Target Shift) ---
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

        # --- 6. Today's Live Prediction ---
        elim_final, scores_final = analyze_sheets(target_data_list, max_repeat_limit)
        safe_pool = [n for n in range(100) if n not in elim_final]

        if safe_pool:
            sorted_safe = sorted(safe_pool, key=lambda x: scores_final[x], reverse=True)
            n_safe = len(sorted_safe)
            high_tier = sorted_safe[:int(n_safe*0.33)]
            med_tier = sorted_safe[int(n_safe*0.33):int(n_safe*0.66)]
            low_tier = sorted_safe[int(n_safe*0.66):]
        else:
            high_tier, med_tier, low_tier = [], [], []

        valid_hits = {k: v for k, v in tier_hits.items() if k != "Failed (Eliminated)"}
        best_tier = max(valid_hits, key=valid_hits.get) if sum(valid_hits.values()) > 0 else "None"

        # --- 7. Final Output Display ---
        st.markdown("---")
        st.markdown(f"### 🎯 Prediction for: **[{target_shift_name}]** on **{target_date.strftime('%d %B %Y')}**")

        if best_tier != "None":
            st.success(f"**AI Recommendation: Agli '{target_shift_name}' ke liye aapko [{best_tier.upper()} TIER] par focus karna chahiye.**")
            st.write(f"*(Kyonki pichle 10 din mein sabse zyada actual results aayen hain: High -> {tier_hits['High']}, Medium -> {tier_hits['Medium']}, Low -> {tier_hits['Low']})*")

        st.markdown("---")
        st.subheader(f"📊 Safe Numbers for {target_shift_name} (After 70-80% Elimination)")

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

    except Exception as e:
        st.error(f"File process karne mein error aaya. Kripya check karein ki file ka format sahi hai. Error: {e}")
        
else:
    st.info("👈 Kripya sidebar se apni CSV ya Excel file upload karein taaki data processing shuru ho sake.")
        
