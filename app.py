# app.py
import streamlit as st
import joblib
import numpy as np
import pandas as pd
import plotly.express as px
from streamlit_extras.metric_cards import style_metric_cards

#Fungsi Bantu
def compute_ideal_height(age_months: float, gender: str) -> float:
    """
    Interpolasi median tinggi badan (cm) berdasarkan usia.
    Data median untuk usia 1–5 tahun (tahun -> cm) [3]:
    {1:76, 2:88, 3:95, 4:103, 5:110}.
    Untuk <12 bulan diasumsikan linear dari 50 cm (lahir) ke 76 cm (1 tahun).
    """
    # median tiap tahun
    med = {1:76, 2:88, 3:95, 4:103, 5:110}
    if age_months < 12:
        return round(50 + (26/12)*age_months, 1)  # 50→76 cm
    else:
        yrs = age_months / 12
        y0 = int(np.floor(yrs))
        y1 = min(y0 + 1, 5)
        h0 = med.get(y0, med[1])
        h1 = med[y1]
        frac = yrs - y0
        return round(h0 + (h1 - h0) * frac, 1)

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

# mapping rekomendasi berdasarkan (Stunting, Wasting)
rekom_map = {
    ("Normal",           "Normal"):           "Anak berada dalam kondisi tumbuh kembang yang baik. Pertahankan pola makan bergizi seimbang (karbohidrat, protein hewani dan nabati, buah, sayur), ASI eksklusif hingga 6 bulan, dan pantau tumbuh kembang secara berkala di posyandu/puskesmas.",
    ("Normal",           "Wasting"):           "Anak mengalami kekurangan berat badan relatif terhadap tinggi badan. Tingkatkan asupan energi dan protein (telur, ikan, daging, susu). Berikan makanan bergizi padat energi secara lebih sering (3 kali makan utama dan 2 kali camilan sehat). Segera konsultasikan ke tenaga kesehatan.",
    ("Normal",           "Severe Wasting"):  "Kondisi gizi anak tergolong berat. Segera bawa ke fasilitas kesehatan. Butuh penanganan medis dan pemberian Pemberian Makanan Tambahan (PMT) atau makanan terapi sesuai arahan petugas gizi. Pemantauan intensif diperlukan.",
    ("Normal",           "Overweight"):       "Anak mengalami kelebihan berat badan. Kurangi konsumsi makanan tinggi gula, garam, dan lemak. Berikan buah dan sayuran lebih sering. Dorong aktivitas fisik (main aktif, jalan, lari-larian), dan pantau asupan susu dan camilan.",
    ("Stunted",          "Normal"):           "Anak mengalami pertumbuhan tinggi yang lebih rendah dari usianya. Tingkatkan kualitas dan kuantitas makanan (terutama protein hewani seperti ayam, ikan, telur), tambahkan MPASI bergizi jika >6 bulan, dan pastikan imunisasi lengkap. Konsultasikan dengan petugas kesehatan.",
    ("Stunted",          "Wasting"):           "Anak mengalami dua masalah gizi: berat badan dan tinggi badan tidak sesuai. Perlu perhatian ekstra. Tingkatkan frekuensi makan, berikan makanan tinggi kalori dan protein, dan periksa ke puskesmas untuk pemantauan dan intervensi gizi.",
    ("Stunted",          "Severe Wasting"):  "Kondisi gizi anak sangat mengkhawatirkan. Butuh penanganan medis segera. Bawa anak ke puskesmas/RS untuk intervensi gizi terapeutik dan evaluasi klinis. Pemberian makanan tinggi energi dan pemantauan harian sangat diperlukan.",
    ("Stunted",          "Overweight"):       "Anak pendek untuk usianya dan memiliki kelebihan berat badan. Evaluasi pola makan (hindari makanan olahan, manis, tinggi lemak), perbaiki aktivitas fisik harian, dan konsultasi ke ahli gizi anak untuk intervensi gizi yang seimbang.",
    ("Severely Stunted", "Normal"):           "Anak mengalami kekurangan tinggi badan yang parah. Butuh pemantauan intensif tumbuh kembang. Berikan makanan tinggi protein dan zat besi. Perlu tambahan intervensi gizi dari posyandu dan kemungkinan rujukan ke tenaga medis.",
    ("Severely Stunted", "Wasting"):           "Anak sangat pendek dan memiliki berat badan kurang. Intervensi gizi harus dilakukan sesegera mungkin. Perlu kunjungan ke fasilitas kesehatan untuk evaluasi menyeluruh, termasuk pemberian makanan terapeutik dan pemantauan ketat.",
    ("Severely Stunted", "Severe Wasting"):  "Kondisi gizi sangat berat. Risiko kematian meningkat. Harus segera dirujuk ke fasilitas kesehatan (RS/puskesmas). Dibutuhkan terapi gizi medis intensif, pemantauan klinis harian, dan kemungkinan rawat inap.",
    ("Severely Stunted", "Overweight"):       "Anak sangat pendek namun kelebihan berat badan. Pola makan kemungkinan tidak seimbang (berlebihan kalori, kurang mikronutrien). Evaluasi menyeluruh oleh ahli gizi diperlukan. Kurangi makanan manis dan olahan, tingkatkan makanan alami dan seimbang.",
    ("Tall",             "Normal"):           "Anak memiliki pertumbuhan tinggi baik. Terus pantau pertumbuhan secara berkala dan pertahankan asupan makanan bergizi seimbang serta aktivitas fisik yang rutin.",
    ("Tall",             "Wasting"):           "Anak tinggi tetapi memiliki berat badan kurang. Perlu ditingkatkan kualitas makanan, terutama dari sisi kalori dan protein. Konsultasi ke tenaga kesehatan untuk menentukan penyebab dan tindak lanjut.",
    ("Tall",             "Severe Wasting"):  "Anak tinggi dengan berat badan sangat kurang. Perlu intervensi segera untuk menghindari komplikasi gizi. Bawa anak ke puskesmas atau rumah sakit untuk penanganan gizi intensif.",
    ("Tall",             "Overweight"):       "Anak memiliki tinggi dan berat badan melebihi standar. Risiko obesitas. Perhatikan pola makan (hindari gula, lemak, makanan cepat saji) dan dorong aktivitas fisik harian. Jika perlu, konsultasi dengan petugas gizi."
}

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
    <h1 class="title">👶 GrowUp+</h1>
""", unsafe_allow_html=True)

# Sidebar untuk input data
with st.sidebar:
    st.header("📋 Silahkan masukkan data anak")
    st.markdown("---")
    umur = st.number_input(
        "Umur (bulan)", 
        min_value=1, 
        max_value=60, 
        value=12,      # nilai default
        step=1, 
        format="%d",
        help="Masukkan usia anak dalam bulan"
    )
    
    gender = st.selectbox("Jenis Kelamin", ["Laki-laki", "Perempuan"])
    
    tinggi = st.number_input(
        "Tinggi Badan (cm)", 
        min_value=40.0, 
        max_value=150.0, 
        value=75.0, 
        step=0.1,
        format="%.1f"
    )
    
    berat = st.number_input(
        "Berat Badan (kg)", 
        min_value=3.0, 
        max_value=50.0, 
        value=10.0, 
        step=0.1,
        format="%.1f"
    )
    
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
    tinggi_aktual = tinggi
    tinggi_ideal  = compute_ideal_height(umur, gender)
    selisih_tg    = round(tinggi_ideal - tinggi_aktual, 1)
    
    with col1:
        st.markdown("### 📏 Hasil Prediksi Stunting")
        with st.container(border=True):
            st.markdown(f"**Kategori:** {results['stunting']['labels'][pred_s]}")
            st.progress((pred_s + 1)/4, text="Tingkat Risiko")
            
            # Grafik pertumbuhan
            # Kasus: hampir ideal
        if abs(selisih_tg) < 0.1:
            df_tg = pd.DataFrame({"Kategori":["Tinggi Ideal Terpenuhi"], "Nilai":[1]})
            fig_t = px.pie(df_tg, names="Kategori", values="Nilai",
                           color_discrete_sequence=[theme['success']],
                           title="Tinggi Aktual Sesuai Ideal")
            st.success("✅ Tinggi badan sudah sesuai dengan ideal.")
        
        # Kasus: di bawah ideal
        elif selisih_tg > 0:
            df_tg = pd.DataFrame({
                "Kategori":["Tinggi Aktual","Menuju Tinggi Ideal"],
                "Nilai":[tinggi_aktual, selisih_tg]
            })
            fig_t = px.pie(df_tg, names="Kategori", values="Nilai",
                           color_discrete_map={
                             "Tinggi Aktual": theme['success'],
                             "Menuju Tinggi Ideal": theme['warning']
                           },
                           title="Progres Menuju Tinggi Ideal")
            st.info(f"⚠️ Perlu tambah tinggi {selisih_tg} cm untuk mencapai ideal ({tinggi_ideal} cm).")
        
        # Kasus: di atas ideal
        else:
            kelebihan = abs(selisih_tg)
            df_tg = pd.DataFrame({
                "Kategori":["Tinggi Ideal","Kelebihan Tinggi"],
                "Nilai":[tinggi_ideal, kelebihan]
            })
            fig_t = px.pie(df_tg, names="Kategori", values="Nilai",
                           color_discrete_map={
                             "Tinggi Ideal": theme['success'],
                             "Kelebihan Tinggi": theme['warning']
                           },
                           title="Perbandingan Tinggi Ideal vs Kelebihan")
            st.warning(f"⚠️ Anak memiliki kelebihan tinggi {kelebihan} cm dari ideal ({tinggi_ideal} cm).")
        
        st.plotly_chart(fig_t, use_container_width=True)

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
                        "Berat Aktual": theme['success'],
                        "Menuju Berat Ideal": theme['warning']
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
                        "Kelebihan Berat": theme['warning']
                    },
                    title="Perbandingan Berat Ideal vs Kelebihan"
                )
                st.warning(f"⚠️ Anak memiliki kelebihan berat {kelebihan} kg dari ideal ({berat_ideal} kg).")
        
            st.plotly_chart(fig2, use_container_width=True)
    # setelah Anda menghitung pred_s dan pred_w serta memiliki:
    stunting_label = results['stunting']['labels'][pred_s]
    wasting_label  = results['wasting']['labels'][pred_w]
    #Rekomendasi
    st.markdown("---")
    with st.expander("📌 Rekomendasi Medis", expanded=True):
        # cari teks rekomendasi
        rekom_text = rekom_map.get(
            (stunting_label, wasting_label),
            "Data rekomendasi tidak tersedia."
        )
        # tampilkan kategori dan rekomendasi
        st.markdown(f"**Stunting:** {stunting_label}  \n"
                    f"**Wasting :** {wasting_label}")
        # gunakan styling sesuai level
        if "berat" in rekom_text.lower() or "segera" in rekom_text.lower():
            st.error(rekom_text)
        else:
            st.info(rekom_text)

else:
    # Tampilan awal
    st.markdown("""
    <div style="text-align: center; padding: 5rem;">
        <h3 style="color: #2E86C1;">
          Platform Deteksi Dini Indikasi Stunting dan Gizi Buruk pada Anak
        </h3>
        <p>
          Untuk memulai, silakan masukkan data anak Anda pada sidebar di sebelah kiri.
        </p>
        <p>
          GrowUp+ akan membantu Anda memantau tumbuh kembang anak dengan menyediakan:
        </p>
        <ul style="
            list-style: none;
            padding: 0;
            text-align: left;
            display: inline-block;
            margin: auto;
        ">
            <li>✅ Prediksi indikasi stunting</li>
            <li>✅ Deteksi masalah gizi (kurang/buruk)</li>
            <li>✅ Rekomendasi medis otomatis berbasis Machine Learning</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; padding: 1rem; color: #666;'>
    <p>© 2025 GrowUp+ - Sistem Pemantauan Tumbuh Kembang Anak</p>
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
