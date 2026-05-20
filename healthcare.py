import sqlite3
from matplotlib.pyplot import show
import streamlit as st
import pandas as pd 
import plotly.express as px
import numpy as np
import base64


# Konfigurasi Halaman
st.set_page_config(page_title="Always Healthy Hospital", layout="wide")

st.markdown(
    """
    <style>
    /* Mengubah warna background utama (Warna soft medical blue/gray) */
    .stApp {
        background-color: #F0F4F8; 
    }
    
    /* Sedikit merapikan warna teks agar kontras dan profesional */
    h1, h2, h3, p, div {
        color: #1E293B; 
    }

    /* Membuat background kartu metrik (Executive Summary) agak putih biar menonjol */
    [data-testid="stMetric"] {
        background-color: #FFFFFF;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    </style>
    """,
    unsafe_allow_html = True
)

# BACKGROUND DASHBOARD (ubah gambar jadi base64)
# =========================================================
@st.cache_data
def get_base64_image(image_path):
    with open(image_path, "rb") as f:
        data = f.read()
        return base64.b64encode(data).decode()
    
# GUNAKAN BACKGROUND DENGAN CSS 
try:
    image_path = r"D:\coba_streamlit\DC\gambar2.jpg" 
    bin_str = get_base64_image(image_path)

    # Gabungan semua pengaturan CSS (Background + Metrik + Grafik + Tabel)
    st.markdown(
        f"""
        <style>
        /* Mengatur Background Utama Aplikasi */
        .stApp {{
            background-color: #F8FAFC; /* Putih tulang yang bersih */
        }}

        /* Mengatur Gambar Header yang bisa di-scroll */
        [data-testid="stMain"] {{
            background-color: transparent; 
            background-image: url("data:image/jpeg;base64,{bin_str}");
            background-repeat: no-repeat;
            background-position: top center;
            background-size: 100% 450px; 
            background-attachment: local; 
        }}

        /* Mengatur Kartu Metrik (Executive Summary) Atas */
        [data-testid="stMetric"] {{
            background-color: rgba(255, 255, 255, 0.90) !important;
            padding: 15px;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        }}
        
        /* 🏥 KARTU GRAFIK: Soft Medical Blue Card */
        [data-testid="stPlotlyChart"] {{
            background-color: #E2E8F0 !important; /* Abu-abu biru lembut */
            padding: 12px;
            border-radius: 12px; /* Sudut melengkung halus */
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
            overflow: hidden; !important; /* Mencegah elemen grafik keluar dari kartu */
        }}
        
       /* Latar kotak utama jadi biru medis gelap */
        div[data-baseweb="select"] > div {{
            background-color: #0F4C75 !important; 
            border-radius: 8px !important;
            border: none !important;
        }}
        
        /* Mengubah kotak pilihan (yang aslinya merah) jadi biru navy gelap */
        span[data-baseweb="tag"] {{
            background-color: #1E293B !important; 
            color: #FFFFFF !important;
        }}
        
        /* Teks tulisan "NPS, CSI" di dalam tag agar jadi putih */
        span[data-baseweb="tag"] span {{
            color: #FFFFFF !important;
        }}
        
        /* Warna teks panah dropdown (v) dan tombol hapus (x) jadi putih */
        div[data-baseweb="select"] svg {{
            color: #FFFFFF !important;
        }}
        </style>
        """,
        unsafe_allow_html = True
    )
except FileNotFoundError:
    st.error("⚠️ File gambar background tidak ditemukan. Cek kembali path foldernya.")

# =========================================================
# PREPROCESSING DATASET
def load_data():
# Load Data 
    file_path = r"D:\Semester 6\DC\Deka\health care dataset.csv"
    df = pd.read_csv(file_path, sep=None, engine='python')

    # Standarisasi Nama Kolom 
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    # Preprocessing Datetime
    if 'datetime' in df.columns:
        df['datetime'] = df['datetime'].astype(str).str.replace('.', ':', regex=False)
        df['date_dt'] = pd.to_datetime(df['datetime'], dayfirst=True, errors='coerce')

        # Ekstraksi Fitur Tambahan (permudah filter/agregasi)
        df['tanggal'] = df['date_dt'].dt.date
        df['bulan'] = df['date_dt'].dt.to_period('M').astype(str) # Diubah ke string untuk grafik
       
    # Preprocessing Teks (branch)
    if 'branch' in df.columns:
        df['branch'] = df['branch'].str.replace('Always Healthy Hospital ', '', case=False, regex=False)
        df['branch'] = df['branch'].str.strip().str.title()
    if 'gender' in df.columns:
        df['gender'] = df['gender'].str.strip().str.title()

    # Mengecek Missing Values
    missing_values = df.isnull().sum()
    if missing_values.sum() == 0:
        print("✅ Tidak ada Missing Values! Data aman.")
    else:
        print("⚠️ Ditemukan Missing Values pada kolom berikut:")
        print(missing_values[missing_values > 0])

    # Cek Data
    print(df.head())
    print(df.info())

    return df  

# Simpan Hasil return ke df
df = load_data() 

###########################################################################

# DASHBOARD STREAMLIT
# =========================================================

st.markdown("<h1 style='color: #FFFFFF;'>Always Healthy Hospital</h1>", unsafe_allow_html = True)
st.markdown("<p style='color: #FFFFFF; font-size: 18px;'>Rekapitulasi Pelayanan Always Healthy Hospital</p>", unsafe_allow_html = True)
st.markdown("<h3 style='color: #FFFFFF;'>Executive Summary</h3>", unsafe_allow_html = True)

# A. Metrik Utama 
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

# Standarisasi KPI jadi numerik
kpi_cols = ['nps', 'csi', 'loyalty', 'ces']
for col in kpi_cols:
    df[col] = pd.to_numeric(df[col], errors = 'coerce') 

kpi1.metric("NPS (Net Promoter Score)", f"{df['nps'].mean():.2f}")
kpi2.metric("CSI (Customer Satisfaction)", f"{df['csi'].mean():.2f}")
kpi3.metric("Customer Loyalty", f"{df['loyalty'].mean():.2f}")
kpi4.metric("Customer Effort Score", f"{df['ces'].mean():.2f}")
st.markdown("---")

# =========================================================
col_rank, col_line, col_bar = st.columns([1.09, 1, 0.8])
# B. Peringkat Cabang 
with col_rank: 
    st.subheader("Kinerja Cabang")

    # Nilai Rataan KPI 
    df_rank = df.groupby('branch')[kpi_cols].mean().reset_index()
    df_rank['total_score'] = df_rank[kpi_cols].sum(axis = 1)

    # Urutan Peringkat 
    df_rank = df_rank.sort_values('total_score', ascending = False).reset_index(drop = True)

    # Dataframe untuk ditampilkan 
    df_tabel = df_rank[['branch', 'total_score', 'nps', 'csi', 'loyalty', 'ces']]
    df_tabel.columns = ["Nama Cabang", "Rataan KPI", "NPS", "CSI", "Loyalty", "CES"]

    # Warna Background 
    df_styled = df_tabel.style.set_properties(**{
        'background-color': '#E2E8F0',  # Putih untuk semua baris
        'color': '#1E293B',             # Warna teks gelap untuk kontras
        'border': '1px solid #E2E8F0',  # Border halus untuk setiap sel
        'border-radius': '5px',         # Sudut melengkung untuk estetika
        'padding': '8px'                # Padding agar teks tidak menempel ke border
    })

    tabel_event = st.dataframe(
        df_styled, 
        use_container_width = True, 
        hide_index = True, 
        height = 400,
        on_select = "rerun",           # Menginstruksikan streamlit untuk me-refresh saat diklik
        selection_mode = "single-row"  # Hanya boleh pilih 1 baris
    )

    # Untuk enangkap baris yang diklik
    selected_rows = tabel_event.selection.rows
    if len(selected_rows) > 0:
        # Jika ada yang diklik, ambil nama cabangnya
        selected_branch = df_tabel.iloc[selected_rows[0]]["Nama Cabang"]
        teks_judul = f"Cabang {selected_branch}"
        df_filtered = df[df['branch'] == selected_branch]
    else:
        # Jika tabel tidak diklik, tampilkan semua
        selected_branch = "Semua Cabang"
        teks_judul = "Semua Cabang"
        df_filtered = df.copy()

        # Logika untuk menangkap baris yang diklik
        selected_rows = tabel_event.selection.rows
        if len(selected_rows) > 0:
        # (Kodingan jika ada 1 cabang yang diklik)
            ...
        else:
        # Default
            selected_branch = "Semua Cabang"
            teks_judul = "Semua Cabang"
            df_filtered = df.copy() # <--- Menampilkan data seluruh cabang!

# =========================================================
# C. Line Chart 
with col_line: 
    # Judul otomatis berubah sesuai cabang yang diklik
    st.subheader(f"Tren KPI - {teks_judul}")

    # Multiselect untuk Metrik
    opsi_metrik = {'nps': "NPS", 'csi': "CSI", 'loyalty': "Loyalty", 'ces': "CES"}
    selected_metrics_line = st.multiselect(
        "Pilih Metrik KPI:", 
        options = list(opsi_metrik.keys()), 
        format_func = lambda x: opsi_metrik[x], 
        default = list(opsi_metrik.keys())
    )

    if len(selected_metrics_line) == 0:
        st.warning("⚠️ Pilih minimal satu metrik")
    else:
        # Menggunakan df_filtered agar mengikuti klik dari tabel
        df_trend = df_filtered.groupby('bulan')[selected_metrics_line].mean().reset_index()
        
        fig_line = px.line(
            df_trend, 
            x = 'bulan', 
            y = selected_metrics_line, 
            markers = True, 
            height = 350,
            labels = {"value": "Skor", 'variable': 'Metrik', 'bulan': ''}
        )
        
        fig_line.update_layout(
            margin = {"r": 0, "t": 20, "l": 0, "b": 0},
            legend = dict(orientation = "h", yanchor = "bottom", y = 1.02, xanchor = "right", x = 1),
            # --- PENYESUAIAN WARNA BARU ---
            paper_bgcolor = '#E2E8F0', # Menyamakan latar belakang luar grafik
            plot_bgcolor = '#E2E8F0',  # Menyamakan latar belakang dalam grafik
            font = dict(color = '#1E293B') # Memaksa semua teks di grafik berwarna gelap agar kontras
        )

        fig_line.update_xaxes(
            tickfont = dict(color = '#000000'),
            showgrid = True,
            gridwidth = 1,
            gridcolor = 'rgba(0, 0, 0, 0.15)'
        )

        fig_line.update_yaxes(
            tickfont = dict(color = '#000000'),
            showgrid = True,
            gridwidth = 1,
            gridcolor = 'rgba(0, 0, 0, 0.15)'
        )
        st.plotly_chart(fig_line, use_container_width = True)

# =========================================================
# D. Touchpoint Bar Chart
with col_bar:
    # Judul otomatis berubah sesuai cabang yang diklik
    st.subheader(f"Touchpoint - {teks_judul}")
    
    tp_cols = ['registration', 'doctor_consultation', 'nurse_service', 'pharmacy_service', 
               'laboratory', 'emergency_response', 'billing_process', 'facility_cleanliness', 
               'staff_friendliness', 'waiting_time']
    
    # Hitung rata-rata keseluruhan touchpoint (Gunakan df_filtered!)
    df_tp = df_filtered[tp_cols].mean().reset_index()
    df_tp.columns = ['Touchpoint', 'Rata_rata']
    df_tp['Touchpoint'] = df_tp['Touchpoint'].str.replace('_', ' ').str.title()
    
    # Urutkan dari terendah ke tertinggi agar grafik tersusun rapi
    df_tp = df_tp.sort_values('Rata_rata', ascending = True)

    fig_bar = px.bar(
        df_tp, 
        x = 'Rata_rata', 
        y = 'Touchpoint', 
        orientation = 'h', 
        text_auto = '.2f', 
        color = 'Rata_rata', 
        color_continuous_scale = 'Blues', 
        height = 450
    )
    
    fig_bar.update_layout(
        margin = {"r": 20, "t": 20, "l": 0, "b": 0}, 
        coloraxis_showscale = False, 
        yaxis_title = "",
        # --- PENYESUAIAN WARNA BARU (Hanya menimpa yang sudah ada) ---
        paper_bgcolor = '#E2E8F0',
        plot_bgcolor = '#E2E8F0',
        font = dict(color = '#1E293B') # Memaksa semua teks di grafik berwarna gelap agar terbaca
    )
    fig_bar.update_xaxes(tickfont = dict(color = '#000000'))
    fig_bar.update_yaxes(tickfont = dict(color = '#000000'))

    st.plotly_chart(fig_bar, use_container_width = True)

# =========================================================
# E. INSIGHT & REKOMENDASI 
st.markdown("---")
st.subheader("💡 Insight & Rekomendasi")

if 'improvement_feedback' in df.columns:
    # Preprocessing Data Feedback
    df_fb= df_filtered.dropna(subset=['improvement_feedback']).copy()
    df_fb['feedback_clean'] = df_fb['improvement_feedback'].astype(str).str.strip().str.lower()

    # Hapus NaN yang mungkin muncul setelah konversi
    df_fb = df_fb[df_fb['feedback_clean'] != 'nan']

    # Hitung persentase 
    total_fb = df_fb.shape[0]

    # Filter kategori 
    df_good = df_fb[df_fb['feedback_clean'] == 'service good']
    df_improve = df_fb[df_fb['feedback_clean'] != 'service good']
    
    jumlah_good = df_good.shape[0]
    jumlah_improve = df_improve.shape[0]

    # Persentase 
    persen_good = (jumlah_good / total_fb) * 100 if total_fb > 0 else 0
    persen_improve = (jumlah_improve / total_fb) * 100 if total_fb > 0 else 0    

    # Tampilkan Insight
    st.write(f"**Persentase feedback ({teks_judul}):**")
    col_fb1, col_fb2, col_fb3 = st.columns(3)
    
    with col_fb1:
        st.metric(label = "Total Keseluruhan Feedback", value = f"{total_fb} Data")
    with col_fb2:
        st.metric(label = "✅ Service Good", value = f"{persen_good:.1f} %", delta = f"{jumlah_good} data", delta_color = "normal")
    with col_fb3:
        # Delta inverse agar warnanya merah untuk area yang perlu perbaikan
        st.metric(label = "⚠️ Need Improve (Butuh Perbaikan)", value = f"{persen_improve:.1f} %", delta = f"- {jumlah_improve} data", delta_color = "normal")

    st.markdown("---")

    tab_rincian, tab_insight = st.tabs(["📋 Rincian Area Perbaikan", "🔍 Kesimpulan & Tindak Lanjut"])

    with tab_rincian:
        if jumlah_improve > 0:
            st.write(f"Persentase feedback (**{jumlah_improve}**):")

            # 1. Text Cleaning untuk data feedback
            # Diubah menjadi split(',') menyesuaikan format data aslinya
            teks_token = df_improve['feedback_clean'].str.replace('improve ', '', regex = False).str.split(',')
            
            # 2. Flatten list of lists (pisahkan list jadi individu)
            df_exploded = teks_token.explode().str.strip().str.title()
            
            # 3. Hitung frekuensi kata
            detil_improve = df_exploded.value_counts().reset_index()
            detil_improve.columns = ['Area Perbaikan', 'Jumlah Feedback']

            # 4. INI YANG KURANG: Hitung persentase sebelum masuk ke grafik
            detil_improve['Persentase'] = (detil_improve['Jumlah Feedback'] / jumlah_improve) * 100

            # Urutkan berdasarkan Persentase
            detil_improve = detil_improve.sort_values('Persentase', ascending = True).reset_index(drop = True)

            # Grafik Bar
            fig_improve = px.bar(
                detil_improve, 
                x = 'Persentase',    # Sesuaikan dengan nama kolom yang baru dibuat
                y = 'Area Perbaikan',
                orientation = 'h',
                text_auto = '.1f',
                color = 'Persentase',
                color_continuous_scale = 'Reds',
                height = 400
            )
            fig_improve.update_layout(
                margin = {"r": 30, "t": 20, "l": 0, "b": 0}, 
                coloraxis_showscale = False, 
                xaxis_title = "Persentase Keluhan (%)", 
                yaxis_title = "",
                # --- PENYESUAIAN WARNA BARU ---
                paper_bgcolor = '#E2E8F0',
                plot_bgcolor = '#E2E8F0',
                font = dict(color = '#1E293B'),

                # --- 💡 INI KUNCINYA AGAR TEXT AXIS TERBACA DI ATAS BIRU MUDA ---
                # Mengatur warna font untuk sumbu X (Angka)
                xaxis = dict(tickfont = dict(color = '#1E293B')),
                # Mengatur warna font untuk sumbu Y (Nama Area)
                yaxis = dict(tickfont = dict(color = '#1E293B'))
            )
            st.plotly_chart(fig_improve, use_container_width = True)
        else:
            st.success("🎉 Luar biasa! Tidak ada catatan keluhan yang masuk untuk cabang ini.")
    
    with tab_insight:
        st.info(f"""
        **Kesimpulan Evaluasi:**
        * Sebesar **{persen_good:.1f}%** pasien sudah merasa puas dengan standar pelayanan yang ada.
        * Namun, porsi **{persen_improve:.1f}%** *feedback* negatif tidak boleh diabaikan, terutama rincian masalah yang paling mendominasi di *tab* sebelah.
          """)
               
        st.success("""
        **Rekomendasi Tindak Lanjut:**
        1. **Fokus pada Prioritas:** Perbaiki segera masalah yang menduduki peringkat teratas pada grafik rincian keluhan, karena itu adalah akar masalah (bottleneck) utama.
        2. **Sidak dan Pelatihan:** Jika keluhan berkaitan dengan keramahan atau prosedur, lakukan penyegaran SOP staf di titik pelayanan (touchpoint) tersebut.
            """)