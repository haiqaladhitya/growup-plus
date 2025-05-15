import streamlit as st
import joblib
import numpy as np
import pandas as pd
import plotly.express as px

# ─── 1. Konfigurasi halaman ──────────────────────────────────────────────────
st.set_page_config(
    page_title="GrowUp+",
    page_icon="👶",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── 2. Load model sekali saja ───────────────────────────────────────────────
@st.cache_resource
def load_models():
    return {
        'stunting': joblib.load("best_model_stunting.joblib"),
        'wasting':  joblib.load("best_model_wasting.joblib")
    }

models = load_models()

# ─── 3. Tema warna ───────────────────────────────────────────────────────────
theme = {
    'primary':   '#2E86C1',
    'secondary': '#AED6F1',
    'success':   '#28B463',
    'warning':   '#F1C40F',
    'danger':    '#E74C3C'
}

# ─── 4. Header ────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
  .title {{ color: {theme['primary']}; text-align: center; padding: 1rem; }}
</style>
<h1 class="title">👶 GrowUp+ – Pemantauan Tumbuh Kembang Anak</h1>
""", unsafe_allow_html=True)

# ─── 5. Sidebar: Form Input ──────────────────────────────────────────────────
with st.sidebar.form("input_form"):
    st.header("📋 Data Anak")
    umur   = st.slider("Umur (bulan)", 0, 60, 12)
    gender = st.selectbox("Jenis Kelamin", ["Laki-laki", "Perempuan"])
    tinggi = st.number_input("Tinggi Badan (cm)", 40.0, 150.0, 75.0)
    berat  = st.number_input("Berat Badan (kg)", 3.0, 50.0, 10.0)
    submitted = st.form_submit_button("🚀 Mulai Analisis")

# ─── 6. Logika Prediksi & Visualisasi ────────────────────────────────────────
if submitted:
    # Encode gender dan siapkan array input
    g_enc = 0 if gender.startswith("L") else 1
    X = np.array([[umur, g_enc, tinggi, berat]])

    # Jalankan prediksi
    ps = models['stunting'].predict(X)[0]
    pw = models['wasting'].predict(X)[0]

    # Label hasil
    labs_s = ["Normal", "Stunted", "Severely Stunted", "Tall"]
    labs_w = ["Normal", "Mild Wasting", "Moderate Wasting", "Severe Wasting"]

    # Tampilkan dalam dua kolom
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📏 Prediksi Stunting")
        st.markdown(f"**{labs_s[ps]}**")
        st.progress((ps + 1) / 4, text="Tingkat Risiko")
        df1 = pd.DataFrame({
            "Parameter": ["Umur", "Tinggi", "Berat"],
            "Nilai":     [umur, tinggi, berat]
        })
        fig1 = px.bar(
            df1, x="Parameter", y="Nilai",
            color="Parameter",
            color_discrete_map={
                "Umur": theme['primary'],
                "Tinggi": theme['secondary'],
                "Berat": theme['warning']
            },
            title="Parameter Anak"
        )
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        st.subheader("⚖️ Prediksi Wasting")
        st.markdown(f"**{labs_w[pw]}**")
        st.progress((pw + 1) / 4, text="Tingkat Risiko")
        # Pie chart Berat Ideal vs Aktual (selalu diperbarui)
        berat_ideal = berat * 1.1
        df2 = pd.DataFrame({
            "Kategori": ["Berat Ideal", "Berat Aktual"],
            "Nilai":    [berat_ideal, berat]
        })
        fig2 = px.pie(
            df2, names="Kategori", values="Nilai",
            color_discrete_map={
                "Berat Ideal": theme['success'],
                "Berat Aktual": theme['danger']
            },
            title="Perbandingan Berat Ideal vs Aktual"
        )
        st.plotly_chart(fig2, use_container_width=True)

    # Rekomendasi singkat
    st.markdown("---")
    if ps >= 1 or pw >= 1:
        st.error("⚠️ Potensi masalah pertumbuhan terdeteksi. Segera konsultasi ke tenaga medis.")
    else:
        st.success("✅ Kondisi tumbuh kembang normal. Pertahankan gaya hidup sehat!")

else:
    st.info("Isi data anak di sidebar, lalu klik **Mulai Analisis** untuk melihat hasil.")

# ─── 7. Footer ───────────────────────────────────────────────────────────────
st.markdown("---")
st.write("© 2025 GrowUp+ – Sistem Pemantauan Tumbuh Kembang Anak")
