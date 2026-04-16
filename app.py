import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from collections import Counter

st.set_page_config(page_title="MAYA AI - Historical Analyzer", layout="wide")

st.title("MAYA AI: Manual Date Control & Pattern Engine")

# --- 1. Sidebar Controls ---
st.sidebar.header("📁 Data & Date Settings")
uploaded_file = st.sidebar.file_uploader("Upload CSV/Excel File", type=['csv', 'xlsx'])

# Date Selection Control (Isse aap pichle kisi bhi din ka analysis kar sakte hain)
selected_end_date = st.sidebar.date_input("Calculation End Date", datetime(2026, 4, 16))

st.sidebar.markdown("---")
st.sidebar.header("🎯 Target Selection")
shift_names = ["DS", "FD", "GD", "GL", "DB", "SG", "ZA"]
target_shift_name = st.sidebar.selectbox("Predict for Which Shift?", shift_names)

max_repeat_limit = st.sidebar.slider("Max Repeat Limit", 2, 5, 4)

if uploaded_file is not None:
    try:
        # --- 2. Data Cleaning ---
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
            
        df['DATE'] = pd.to_datetime(df['DATE'], errors='coerce')
        
        # User ki selected date tak ka data filter karna
        filtered_df = df[df['DATE'].dt.date <= selected_end_date].copy()
        
        # Shift data clean karna
        filtered_df[target_shift_name] = pd.to_numeric(filtered_df[target_shift_name], errors='coerce')
        filtered_df = filtered_df.dropna(subset=['DATE', target_shift_name])
        filtered_df[target_shift_name] = filtered_df[target_shift_name].astype(int)
        
        # Sorting for accurate history
        filtered_df = filtered_df.sort_values(by='DATE').reset_index(drop=True)
        target_data_list = filtered_df[target_shift_name].tolist()
        
        if not target_data_list:
            st.warning(f"Selected date ({selected_end_date}) tak koi data nahi mila.")
            st.stop()

        # --- 3. Last 10 Days History (Based on Selected Date) ---
        st.markdown("---")
        st.write(f"### 📅 History: Last 10 Days up to {selected_end_date.strftime('%d %b %Y')}")
        
        history_df = filtered_df.tail(10).copy()
        history_df['DATE'] = history_df['DATE'].dt.strftime('%d %B %Y')
        st.table(history_df[['DATE', target_shift_name]].set_index('DATE'))

        # --- 4. Core Elimination Engine (1-30 Days Analysis) ---
        def run_elimination(shift_list, limit):
            eliminated = set()
            scores = Counter()
            for days in range(1, 31):
                if len(shift_list) < days: continue
                sheet = shift_list[-days:]
                counts = Counter(sheet)
                # Zero-Repeat Elimination
                if len(counts) == len(sheet) and len(sheet) > 1:
                    eliminated.update(sheet)
                # Max Hit Elimination
                for num, freq in counts.items():
                    if freq >= limit: eliminated.add(num)
                    else: scores[num] += 1
            return eliminated, scores

        # --- 5. Backtesting Trend (10 Days) ---
        tier_hits = {"High": 0, "Medium": 0, "Low": 0, "Eliminated": 0}
        if len(target_data_list) > 10:
            for i in range(10, 0, -1):
                past = target_data_list[:-i]
                actual = target_data_list[-i]
                elim_p, scores_p = run_elimination(past, max_repeat_limit)
                safe_p = sorted([n for n in range(100) if n not in elim_p], key=lambda x: scores_p[x], reverse=True)
                if safe_p:
                    n_p = len(safe_p)
                    if actual in safe_p[:int(n_p*0.33)]: tier_hits["High"] += 1
                    elif actual in safe_p[int(n_p*0.33):int(n_p*0.66)]: tier_hits["Medium"] += 1
                    elif actual in safe_p[int(n_p*0.66):]: tier_hits["Low"] += 1
                    else: tier_hits["Eliminated"] += 1

        # --- 6. Live Result for Target Date ---
        elim_final, scores_final = run_elimination(target_data_list, max_repeat_limit)
        safe_pool = sorted([n for n in range(100) if n not in elim_final], key=lambda x: scores_final[x], reverse=True)
        
        if safe_pool:
            n_s = len(safe_pool)
            high_tier = safe_pool[:int(n_s*0.33)]
            med_tier = safe_pool[int(n_s*0.33):int(n_s*0.66)]
            low_tier = safe_pool[int(n_s*0.66):]
            
            target_prediction_date = selected_end_date + timedelta(days=1)
            st.markdown("---")
            st.header(f"🎯 Prediction for: {target_prediction_date.strftime('%d %B %Y')}")
            
            # Recommendation
            best_tier = max({"High": tier_hits["High"], "Medium": tier_hits["Medium"], "Low": tier_hits["Low"]}, key=lambda k: tier_hits[k])
            st.success(f"**Recommendation: Agli shift ke liye [{best_tier.upper()}] Tier sabse majboot hai.**")
            st.write(f"Recent Hits: High({tier_hits['High']}), Medium({tier_hits['Medium']}), Low({tier_hits['Low']})")

            # Tier Display
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
        
        st.info(f"Total Eliminated: {len(elim_final)} | Safe Numbers: {len(safe_pool)}")

    except Exception as e:
        st.error(f"Error: {e}")
else:
    st.info("👈 Please upload your Excel/CSV file to begin.")
                
