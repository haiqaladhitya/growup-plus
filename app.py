# app.py
import streamlit as st
import joblib
import numpy as np
import pandas as pd
import plotly.express as px
from streamlit_extras.metric_cards import style_metric_cards

#Fungsi Bantu
def compute_ideal_weight(age_months: float) -> float:
    """
    Hitung Berat Badan Ideal (BBI) berdasarkan umur anak (bulan),
    menggunakan Burger’s formula:
    - <12 bulan: (bulan/2) + 4
    - 12–60 bulan: (tahun*2) + 8
    """
    if age_months < 12:
        bbi = (age_months / 2) + 4
    else:
        age_years = age_months / 12
        bbi = (age_years * 2) + 8
    return round(bbi, 1)

# Konfigurasi halaman
st.set_page_config(
    page_title="GrowUp+",
    page_icon="👶",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load model
@st.cache_resource
def load_models():
    return {
        'stunting': joblib.load("best_model_stunting.joblib"),
        'wasting': joblib.load("best_model_wasting.joblib")
    }

models = load_models()

# Tema warna
theme = {
    'primary': '#2E86C1',
    'secondary': '#AED6F1',
    'success': '#28B463',
    'warning': '#F1C40F',
    'danger': '#E74C3C'
}

# Header dengan animasi
st.markdown(f"""
    <style>
        @keyframes fadeIn {{
            0% {{ opacity: 0; }}
            100% {{ opacity: 1; }}
        }}
        .title {{
            animation: fadeIn 2s;
            color: {theme['primary']};
            text-align: center;
            padding: 1rem;
        }}
    </style>
    <h1 class="title">👶 GrowUp+ - Pemantauan Tumbuh Kembang Anak</h1>
""", unsafe_allow_html=True)

# Sidebar untuk input data
with st.sidebar:
    st.header("📋 Masukkan Data Anak")
    st.markdown("---")
    umur = st.slider("Umur (bulan)", 0, 60, 12,
                    help="Usia anak dalam bulan")
    gender = st.selectbox("Jenis Kelamin", ["Laki-laki", "Perempuan"])
    tinggi = st.number_input("Tinggi Badan (cm)", 40.0, 150.0, 75.0, step=0.1,
                           format="%.1f")
    berat = st.number_input("Berat Badan (kg)", 3.0, 50.0, 10.0, step=0.1,
                          format="%.1f")
    st.markdown("---")
    
    if st.button("🚀 Mulai Analisis", use_container_width=True):
        st.session_state.analyzed = True
    else:
        st.session_state.analyzed = False

# Konten utama
if st.session_state.get('analyzed'):
    # Preprocessing
    gender_enc = 0 if gender.startswith("L") else 1
    X = np.array([[umur, gender_enc, tinggi, berat]])
    
    # Prediksi
    pred_s = models['stunting'].predict(X)[0]
    pred_w = models['wasting'].predict(X)[0]
    
    # Mapping hasil
    results = {
        'stunting': {
            'labels': ["Normal", "Stunted", "Severely Stunted", "Tall"],
            'color': [theme['success'], theme['warning'], theme['danger'], theme['primary']]
        },
        'wasting': {
            'labels': ["Normal", "Mild Wasting", "Moderate Wasting", "Severe Wasting"],
            'color': [theme['success'], theme['warning'], theme['danger'], theme['primary']]
        }
    }
    
    # Tampilkan hasil dalam kolom
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📏 Hasil Prediksi Stunting")
        with st.container(border=True):
            st.markdown(f"**Kategori:** {results['stunting']['labels'][pred_s]}")
            st.progress((pred_s + 1)/4, text="Tingkat Risiko")
            
            # Grafik pertumbuhan
            df_growth = pd.DataFrame({
                'Parameter': ['Umur', 'Tinggi', 'Berat'],
                'Nilai': [umur, tinggi, berat]
            })
            
            fig = px.bar(df_growth, x='Parameter', y='Nilai', 
                        color='Parameter', color_discrete_sequence=[theme['primary'], theme['secondary'], theme['warning']])
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("### ⚖️ Hasil Prediksi Wasting")
        with st.container(border=True):
            st.markdown(f"**Kategori:** {results['wasting']['labels'][pred_w]}")
            st.progress((pred_w + 1)/4, text="Tingkat Risiko")
            
            # Grafik perbandingan
            # Hitung Berat Ideal sesuai umur
            berat_ideal = compute_ideal_weight(umur)
            selisih = round(berat_ideal - berat, 1)

            # Kasus 1: berat hampir ideal
            if abs(selisih) < 0.1:
                df2 = pd.DataFrame({
                    "Kategori": ["Berat Ideal Terpenuhi"],
                    "Nilai":    [1]
                })
                fig2 = px.pie(
                    df2, names="Kategori", values="Nilai",
                    color_discrete_sequence=[theme['success']],
                    title="Berat Aktual Sesuai Ideal"
                )
                st.success("✅ Berat aktual sudah sesuai dengan berat ideal.")
        
            # Kasus 2: berat di bawah ideal
            elif selisih > 0:
                df2 = pd.DataFrame({
                    "Kategori": ["Berat Aktual", "Menuju Berat Ideal"],
                    "Nilai":    [berat, selisih]
                })
                fig2 = px.pie(
                    df2, names="Kategori", values="Nilai",
                    color_discrete_map={
                        "Berat Aktual": theme['warning'],
                        "Menuju Berat Ideal": theme['secondary']
                    },
                    title="Progres Menuju Berat Ideal"
                )
                st.info(f"⚠️ Anak perlu menambah {selisih} kg lagi untuk mencapai berat ideal ({berat_ideal} kg).")
        
            # Kasus 3: berat di atas ideal (kelebihan)
            else:
                kelebihan = abs(selisih)
                df2 = pd.DataFrame({
                    "Kategori": ["Berat Ideal", "Kelebihan Berat"],
                    "Nilai":    [berat_ideal, kelebihan]
                })
                fig2 = px.pie(
                    df2, names="Kategori", values="Nilai",
                    color_discrete_map={
                        "Berat Ideal": theme['success'],
                        "Kelebihan Berat": theme['danger']
                    },
                    title="Perbandingan Berat Ideal vs Kelebihan"
                )
                st.warning(f"⚠️ Anak memiliki kelebihan berat {kelebihan} kg dari ideal ({berat_ideal} kg).")
        
            st.plotly_chart(fig2, use_container_width=True)
    # Rekomendasi
    st.markdown("---")
    with st.expander("📌 Rekomendasi Medis", expanded=True):
        if pred_s >= 1 or pred_w >= 1:
            st.error("""
            ⚠️ **Perhatian!**  
            Hasil analisis menunjukkan adanya potensi masalah pertumbuhan. 
            Segera konsultasikan dengan tenaga medis untuk:
            - Pemeriksaan lebih lanjut
            - Rencana intervensi gizi
            - Pemantauan berkala
            """)
        else:
            st.success("""
            ✅ **Hasil Normal**  
            Pertumbuhan anak dalam kisaran normal. Tetap lakukan:
            - Pemantauan rutin tiap bulan
            - Pemberian gizi seimbang
            - Stimulasi fisik sesuai usia
            """)

else:
    # Tampilan awal
    st.markdown("""
    <div style='text-align: center; padding: 5rem;'>
        <h3 style='color: #2E86C1;'>Selamat Datang di GrowUp+</h3>
        <p>Masukkan data anak di sidebar kiri untuk mulai analisis</p>
        <p>🩺 Aplikasi ini membantu memantau perkembangan anak dengan:</p>
        <ul style='list-style: none; padding: 0;'>
            <li>✅ Prediksi risiko stunting</li>
            <li>✅ Deteksi masalah gizi (wasting)</li>
            <li>✅ Rekomendasi medis berbasis AI</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; padding: 1rem; color: #666;'>
    <p>© 2024 GrowUp+ - Sistem Pemantauan Tumbuh Kembang Anak</p>
    <p>Dikembangkan dengan ❤️ oleh Tim Medis</p>
</div>
""", unsafe_allow_html=True)

# CSS tambahan
st.markdown(f"""
    <style>
        .st-emotion-cache-1v0mbdj img {{
            border-radius: 10px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        .stPlotlyChart {{
            border: 1px solid {theme['secondary']};
            border-radius: 10px;
            padding: 1rem;
        }}
        .stButton>button {{
            background-color: {theme['primary']};
            color: white;
            transition: all 0.3s;
        }}
        .stButton>button:hover {{
            opacity: 0.8;
            transform: scale(1.05);
        }}
    </style>
""", unsafe_allow_html=True)
