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
    st.subheader("⚖️ Prediksi Wasting")
    st.markdown(f"**{labs_w[pw]}**")
    st.progress((pw + 1) / 4, text="Tingkat Risiko")

    # Hitung Berat Ideal menurut Burger’s formula
    berat_ideal = compute_ideal_weight(umur)
    df2 = pd.DataFrame({
        "Kategori": ["Berat Ideal", "Berat Aktual"],
        "Nilai":    [berat_ideal, berat]
    })
    fig2 = px.pie(
        df2,
        names="Kategori",
        values="Nilai",
        color_discrete_map={
            "Berat Ideal": theme['success'],
            "Berat Aktual": theme['danger']
        },
        title="Perbandingan Berat Ideal vs Aktual"
    )
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

    # Data historis (contoh)
    st.markdown("---")
    st.markdown("### 📈 Riwayat Pertumbuhan")
    with st.container(height=300):
        # Contoh data historis
        df_history = pd.DataFrame({
            'Bulan': [umur-2, umur-1, umur],
            'Tinggi': [tinggi-5, tinggi-2, tinggi],
            'Berat': [berat-1, berat-0.5, berat]
        })
        
        tab1, tab2 = st.tabs(["Tinggi Badan", "Berat Badan"])
        
        with tab1:
            fig = px.line(df_history, x='Bulan', y='Tinggi', 
                         markers=True, title="Perkembangan Tinggi Badan",
                         color_discrete_sequence=[theme['primary']])
            st.plotly_chart(fig, use_container_width=True)
            
        with tab2:
            fig = px.line(df_history, x='Bulan', y='Berat',
                         markers=True, title="Perkembangan Berat Badan",
                         color_discrete_sequence=[theme['warning']])
            st.plotly_chart(fig, use_container_width=True)

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
            <li>✅ Rekomendasi medis berbasis Machine</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; padding: 1rem; color: #666;'>
    <p>© 2024 GrowUp+ - Sistem Pemantauan Tumbuh Kembang Anak</p>
    <p>Dikembangkan dengan ❤️ oleh Kelompok 22</p>
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
