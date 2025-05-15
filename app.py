# app.py

import streamlit as st
import joblib
import numpy as np

# ----- Load Models -----
model_stunting = joblib.load("best_model_stunting.joblib")
model_wasting  = joblib.load("best_model_wasting.joblib")

# ----- Streamlit Page Config -----
st.set_page_config(
    page_title="GrowUp+ – Prediksi Stunting & Wasting",
    layout="centered"
)
st.title("GrowUp+")
st.markdown("Pemantauan tumbuh kembang anak untuk deteksi risiko stunting dan gizi buruk.")

# ----- Input Form -----
with st.form("input_data"):
    umur   = st.number_input("Umur (bulan)", min_value=0.0, value=12.0, step=1.0)
    gender = st.selectbox("Jenis Kelamin", ["Laki-laki", "Perempuan"])
    tinggi = st.number_input("Tinggi Badan (cm)", min_value=0.0, value=75.0)
    berat  = st.number_input("Berat Badan (kg)", min_value=0.0, value=10.0)
    submitted = st.form_submit_button("Prediksi")

if submitted:
    # Encode gender
    gender_enc = 0 if gender.startswith("L") else 1

    # Siapkan array input
    X = np.array([[umur, gender_enc, tinggi, berat]])

    # Prediksi Stunting
    pred_s = model_stunting.predict(X)[0]
    labels_s = ["Normal", "Stunted", "Severely Stunted", "Tall"]
    result_s = labels_s[pred_s]

    # Prediksi Wasting
    pred_w = model_wasting.predict(X)[0]
    labels_w = ["Normal", "Mild Wasting", "Moderate Wasting", "Severe Wasting"]
    result_w = labels_w[pred_w]

    # Tampilkan hasil dalam tabs
    tab1, tab2 = st.tabs(["Stunting", "Wasting"])

    with tab1:
        st.subheader("Hasil Prediksi Stunting")
        st.write(f"**{result_s}**")
        if result_s in ["Stunted", "Severely Stunted"]:
            st.warning("Anak terindikasi stunting. Segera konsultasikan dengan tenaga medis.")
        elif result_s == "Tall":
            st.info("Tinggi anak di atas rata-rata untuk usianya.")
        else:
            st.success("Kondisi gizi anak relatif normal.")

    with tab2:
        st.subheader("Hasil Prediksi Wasting")
        st.write(f"**{result_w}**")
        if result_w in ["Moderate Wasting", "Severe Wasting"]:
            st.warning("Anak terindikasi wasting. Segera konsultasikan dengan tenaga medis.")
        else:
            st.success("Kondisi gizi anak relatif normal.")

