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

def plot_progress(actual, ideal, label, unit):
    diff = round(ideal - actual, 1)
    # ideal jika selisih kecil
    if abs(diff) < 0.1:
        df = pd.DataFrame({label: ["Ideal"], "Nilai": [1]})
        box, color = st.success, [theme['success']]
        msg = f"✅ {label} sudah ideal ({ideal} {unit})."
    else:
        # split nilai untuk pie
        if diff > 0:
            df = pd.DataFrame({label: ["Actual", "Needed"], "Nilai":[actual, diff]})
        else:
            df = pd.DataFrame({label: ["Ideal", "Excess"],  "Nilai":[ideal, abs(diff)]})
        box, color = st.warning, [theme['success'], theme['warning']]
        verb = "tambah" if diff>0 else "kurangi"
        msg = f"⚠️ Perlu {verb} {abs(diff)} {unit} untuk capai ideal ({ideal} {unit})."

    box(msg)
    fig = px.pie(
        df, names=label, values="Nilai",
        color_discrete_sequence=color
    )
    
    # Mengatur ukuran pie chart
    fig.update_layout(
        height=300,  # Tinggi pie chart
        width=300,   # Lebar pie chart
        margin=dict(t=20, b=20, l=10, r=10)  # Memberikan margin untuk memperkecil chart
    )
    
    st.plotly_chart(fig, use_container_width=False)


# mapping rekomendasi berdasarkan (Stunting, Wasting)
rekom_map = {
    ("Normal",           "Normal"):           "Anak berada dalam kondisi tumbuh kembang yang baik. Pertahankan pola makan bergizi seimbang (karbohidrat, protein hewani dan nabati, buah, sayur), ASI eksklusif hingga 6 bulan, dan pantau tumbuh kembang secara berkala di posyandu/puskesmas.",
    ("Normal",           "Wasting"):          "Anak mengalami kekurangan berat badan relatif terhadap tinggi badan. Tingkatkan asupan energi dan protein (telur, ikan, daging, susu). Berikan makanan bergizi padat energi secara lebih sering (3 kali makan utama dan 2 kali camilan sehat). Segera konsultasikan ke tenaga kesehatan.",
    ("Normal",           "Severe Wasting"):   "Kondisi gizi anak tergolong berat. Segera bawa ke fasilitas kesehatan. Butuh penanganan medis dan pemberian Pemberian Makanan Tambahan (PMT) atau makanan terapi sesuai arahan petugas gizi. Pemantauan intensif diperlukan.",
    ("Normal",           "Overweight"):       "Anak mengalami kelebihan berat badan. Kurangi konsumsi makanan tinggi gula, garam, dan lemak. Berikan buah dan sayuran lebih sering. Dorong aktivitas fisik (main aktif, jalan, lari-larian), dan pantau asupan susu dan camilan.",
    ("Stunted",          "Normal"):           "Anak mengalami pertumbuhan tinggi yang lebih rendah dari usianya. Tingkatkan kualitas dan kuantitas makanan (terutama protein hewani seperti ayam, ikan, telur), tambahkan MPASI bergizi jika >6 bulan, dan pastikan imunisasi lengkap. Konsultasikan dengan petugas kesehatan.",
    ("Stunted",          "Wasting"):          "Anak mengalami dua masalah gizi: berat badan dan tinggi badan tidak sesuai. Perlu perhatian ekstra. Tingkatkan frekuensi makan, berikan makanan tinggi kalori dan protein, dan periksa ke puskesmas untuk pemantauan dan intervensi gizi.",
    ("Stunted",          "Severe Wasting"):   "Kondisi gizi anak sangat mengkhawatirkan. Butuh penanganan medis segera. Bawa anak ke puskesmas/RS untuk intervensi gizi terapeutik dan evaluasi klinis. Pemberian makanan tinggi energi dan pemantauan harian sangat diperlukan.",
    ("Stunted",          "Overweight"):       "Anak pendek untuk usianya dan memiliki kelebihan berat badan. Evaluasi pola makan (hindari makanan olahan, manis, tinggi lemak), perbaiki aktivitas fisik harian, dan konsultasi ke ahli gizi anak untuk intervensi gizi yang seimbang.",
    ("Severely Stunted", "Normal"):           "Anak mengalami kekurangan tinggi badan yang parah. Butuh pemantauan intensif tumbuh kembang. Berikan makanan tinggi protein dan zat besi. Perlu tambahan intervensi gizi dari posyandu dan kemungkinan rujukan ke tenaga medis.",
    ("Severely Stunted", "Wasting"):          "Anak sangat pendek dan memiliki berat badan kurang. Intervensi gizi harus dilakukan sesegera mungkin. Perlu kunjungan ke fasilitas kesehatan untuk evaluasi menyeluruh, termasuk pemberian makanan terapeutik dan pemantauan ketat.",
    ("Severely Stunted", "Severe Wasting"):   "Kondisi gizi sangat berat. Risiko kematian meningkat. Harus segera dirujuk ke fasilitas kesehatan (RS/puskesmas). Dibutuhkan terapi gizi medis intensif, pemantauan klinis harian, dan kemungkinan rawat inap.",
    ("Severely Stunted", "Overweight"):       "Anak sangat pendek namun kelebihan berat badan. Pola makan kemungkinan tidak seimbang (berlebihan kalori, kurang mikronutrien). Evaluasi menyeluruh oleh ahli gizi diperlukan. Kurangi makanan manis dan olahan, tingkatkan makanan alami dan seimbang.",
    ("Tall",             "Normal"):           "Anak memiliki pertumbuhan tinggi baik. Terus pantau pertumbuhan secara berkala dan pertahankan asupan makanan bergizi seimbang serta aktivitas fisik yang rutin.",
    ("Tall",             "Wasting"):          "Anak tinggi tetapi memiliki berat badan kurang. Perlu ditingkatkan kualitas makanan, terutama dari sisi kalori dan protein. Konsultasi ke tenaga kesehatan untuk menentukan penyebab dan tindak lanjut.",
    ("Tall",             "Severe Wasting"):   "Anak tinggi dengan berat badan sangat kurang. Perlu intervensi segera untuk menghindari komplikasi gizi. Bawa anak ke puskesmas atau rumah sakit untuk penanganan gizi intensif.",
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
    <h1 class="title">👶 GrowUp+</h1>
""", unsafe_allow_html=True)

# Sidebar untuk input data
with st.sidebar:
    st.header("📋 Silakan Masukkan Data Anak")
    st.markdown("---")
    
    umur = st.number_input(
        "Umur (bulan)", 
        min_value=1, 
        max_value=60, 
        value=12,     
        step=1, 
        format="%d",
        help="Masukkan usia anak dalam bulan. (Batas: 1-60 bulan)"
    )
    
    gender = st.selectbox("Jenis Kelamin", ["Laki-laki", "Perempuan"])
    
    tinggi = st.number_input(
        "Tinggi Badan (cm)", 
        min_value=40.0, 
        max_value=150.0, 
        value=75.0, 
        step=0.1,
        format="%.1f",
        help="Masukkan tinggi badan anak dalam cm. (Batas: 40-150 cm)"
    )
    
    berat = st.number_input(
        "Berat Badan (kg)", 
        min_value=3.0, 
        max_value=50.0, 
        value=10.0, 
        step=0.1,
        format="%.1f",
        help="Masukkan berat badan anak dalam kg. (Batas: 3-50 kg)"
    )
    
    st.markdown("---")
    
    if st.button("🚀 Mulai Analisis", use_container_width=True):
        st.session_state.analyzed = True

# Konten utama
if st.session_state.get('analyzed', False):
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
            'labels': ["Normal", "Wasting", "Severe Wasting", "Overweight"],
            'color': [theme['success'], theme['warning'], theme['danger'], theme['primary']]
        }
    }

    # Tampilkan hasil dalam kolom
    col1, col2 = st.columns(2)
    tinggi_aktual = tinggi
    tinggi_ideal  = compute_ideal_height(umur, gender)
    # selisih_tg    = round(tinggi_ideal - tinggi_aktual, 1) # Tidak digunakan secara langsung di sini
    
    with col1:
        st.markdown("### 📏 Hasil Prediksi Stunting")
        stunting_category = results['stunting']['labels'][pred_s]
        st.markdown(f"**Kategori:** {stunting_category}")
        
        # Hitung progres dan persentase untuk stunting
        stunting_progress_value = (pred_s + 1) / len(results['stunting']['labels'])
        stunting_percentage = stunting_progress_value * 100
        
        # Menampilkan progres bar dan persentase
        st.progress(stunting_progress_value, text=f"Tingkat Risiko: {stunting_percentage:.0f}%")
        plot_progress(tinggi_aktual, tinggi_ideal, "Tinggi", "cm")

    with col2:
        st.markdown("### ⚖️ Hasil Prediksi Wasting")
        wasting_category = results['wasting']['labels'][pred_w]
        st.markdown(f"**Kategori:** {wasting_category}")
        
        # Hitung progres dan persentase untuk wasting
        wasting_progress_value = (pred_w + 1) / len(results['wasting']['labels'])
        wasting_percentage = wasting_progress_value * 100
        
        # Menampilkan progres bar dan persentase
        st.progress(wasting_progress_value, text=f"Tingkat Risiko: {wasting_percentage:.0f}%")
        plot_progress(berat, compute_ideal_weight(umur), "Berat", "kg")

    # Rekomendasi Medis
    st.markdown("---")
    with st.expander("📌 Rekomendasi Medis", expanded=True):
        st.markdown(f"**Stunting:** {results['stunting']['labels'][pred_s]}  \n**Wasting :** {results['wasting']['labels'][pred_w]}")
        rekom_text = rekom_map.get(
            (results['stunting']['labels'][pred_s], results['wasting']['labels'][pred_w]),
            f"Data rekomendasi tidak tersedia untuk kombinasi: Stunting ({results['stunting']['labels'][pred_s]}), Wasting ({results['wasting']['labels'][pred_w]})."
        )
        st.markdown(f"**Rekomendasi:** {rekom_text}", unsafe_allow_html=True)

        st.markdown("<div class='disclaimer'>Disclaimer: Hasil ini masih berupa rekomendasi secara general, untuk hasil terbaik tetap membutuhkan konsultasi dengan tim medis.</div>", unsafe_allow_html=True)

else:
    # Tampilan awal
    st.markdown("""
    <div style="text-align: center; padding: 2rem 1rem;">
        <h3 style="color: #2E86C1;">Platform Deteksi Dini Indikasi Stunting dan Gizi Buruk pada Anak</h3>
        <p>Untuk memulai, silakan masukkan data anak Anda pada sidebar di sebelah kiri.</p>
        <p>GrowUp+ akan membantu Anda memantau tumbuh kembang anak dengan menyediakan:</p>
        <ul style="list-style: none; padding: 0; text-align: left; display: inline-block; margin: auto;">
            <li>✅ Prediksi indikasi stunting</li>
            <li>✅ Deteksi masalah gizi (kurang/buruk/lebih)</li>
            <li>✅ Rekomendasi medis otomatis berbasis Machine Learning</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
# Footer
st.markdown("<div class='footer'>© 2025 GrowUp+ - Sistem Pemantauan Tumbuh Kembang Anak<br>Dikembangkan dengan ❤️ oleh Kelompok 22</div>", unsafe_allow_html=True)

# CSS tambahan untuk desain yang lebih menarik
st.markdown(f"""
    <style>
        .title {{
            animation: fadeIn 2s;
            color: {theme['primary']};
            text-align: center;
            padding: 1rem;
            font-size: 3rem;  /* Ukuran font yang lebih besar */
        }}
        
        .sidebar .sidebar-content {{
            background-color: {theme['secondary']};
            border-radius: 15px;
            padding: 2rem;
        }}
        
        .stButton>button {{
            background-color: {theme['primary']};
            color: white;
            border-radius: 5px;
            padding: 0.7rem 1.5rem;
            font-size: 1.2rem;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: all 0.3s;
        }}
        
        .stButton>button:hover {{
            background-color: {theme['success']};
            opacity: 0.8;
            transform: scale(1.05);
        }}
        
        .stExpander {{
            margin-bottom: 2rem;
        }}
        
        .stProgress {
            background-color: #AED6F1; /* Warna latar belakang untuk progress bar */
            border-radius: 20px;
            height: 30px;
        }
        
        .stProgress>div {
            color: #2E86C1; /* Warna teks untuk progres */
            font-weight: bold; /* Membuat teks lebih tebal */
            text-align: center; /* Menyusun teks di tengah */
            font-size: 1rem; /* Ukuran font yang nyaman dibaca */
            line-height: 30px; /* Menyesuaikan tinggi bar dengan teks */
        }
        
        .stProgress p {
            color: #2E86C1;
            font-size: 1.2rem; /* Ukuran font untuk teks status */
            font-weight: bold;
        }
        
        .stPlotlyChart {{
            border: 1px solid {theme['secondary']};
            border-radius: 15px;
            padding: 1rem;
        }}

         .footer {{
            text-align: center;
            font-size: 1rem;
            color: #666;
            padding: 1rem;
            background-color: {theme['primary']};
            border-radius: 10px;
        }}
        
        .disclaimer {{
            font-size: 1rem;
            color: #E74C3C;
            font-style: italic;
            text-align: center;
        }}
    </style>
""", unsafe_allow_html=True)
