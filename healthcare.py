import sqlite3
import pandas as pd 
import plotly.express as px
import numpy as np
import streamlit as st

# =========================================================
# 1. KONFIGURASI HALAMAN & CSS 
# =========================================================
# 👉 Parameter 'initial_sidebar_state="expanded"' membuat sidebar selalu terbuka
st.set_page_config(page_title="Always Healthy Hospital", layout="wide", initial_sidebar_state="expanded")

st.markdown(
    """
    <style>
    .stApp { background-color: #F8FAFC; }
    h1, h2, h3, h4 { color: #0F4C75; }
    [data-testid="stMetric"] { background-color: #FFFFFF !important; padding: 15px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05); }
    [data-testid="stPlotlyChart"] { background-color: #E2E8F0 !important; padding: 12px; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03); overflow: hidden !important; }
    
    /* Sidebar Global Styling */
    [data-testid="stSidebar"] { background-color: #0F4C75 !important; }
    [data-testid="stSidebar"] * { color: white !important; }
    
    /* Memaksa teks di dalam Dropdown (Selectbox) menjadi Hitam */
    [data-testid="stSidebar"] div[data-baseweb="select"] * { 
        color: #000000 !important; 
    }
    
    /* Memaksa teks di dalam kotak Input (termasuk kalender) menjadi Hitam */
    [data-testid="stSidebar"] div[data-baseweb="input"] *, 
    [data-testid="stSidebar"] input { 
        color: #000000 !important; 
    }
    
    /* Menghilangkan tombol panah (<<) agar sidebar terkunci permanen */
    [data-testid="stSidebarCollapseButton"] { 
        display: none !important; 
    }
    </style>
    """,
    unsafe_allow_html = True
)

# =========================================================
# 2. PREPROCESSING DATASET
# =========================================================
@st.cache_data
def load_data():
    file_path = "health care dataset.csv"
    df = pd.read_csv(file_path, sep=None, engine='python')

    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    if 'datetime' in df.columns:
        df['datetime'] = df['datetime'].astype(str).str.replace('.', ':', regex=False)
        df['date_dt'] = pd.to_datetime(df['datetime'], dayfirst=True, errors='coerce')
        df['tanggal'] = df['date_dt'].dt.date
        df['bulan'] = df['date_dt'].dt.to_period('M').astype(str)
       
    if 'branch' in df.columns:
        df['branch'] = df['branch'].str.replace('Always Healthy Hospital ', '', case=False, regex=False)
        df['branch'] = df['branch'].str.strip().str.title()
    if 'gender' in df.columns:
        df['gender'] = df['gender'].str.strip().str.title()
        
    kpi_cols = ['nps', 'csi', 'loyalty', 'ces']
    for col in kpi_cols:
        df[col] = pd.to_numeric(df[col], errors = 'coerce') 

    return df  

df = load_data()

# =========================================================
# 3. SIDEBAR (MASTER FILTER & MENU NAVIGASI)
# =========================================================
st.sidebar.markdown("<h2 style='color:#FFFFFF;'>Menu</h2>", unsafe_allow_html=True)
st.sidebar.write("---")

# 1. Menu Navigasi (Pengganti Tab)
menu = st.sidebar.radio("Pilih Halaman:", ["Executive Summary", "Detail Analisis"])

st.sidebar.write("---")

# 2. Filter Rentang Waktu (Sidebar)
daftar_periode = ["Semua Periode", "3 Bulan Terakhir", "5 Bulan Terakhir", "10 Bulan Terakhir", "Custom"]
pilihan_periode = st.sidebar.selectbox("Pilih Rentang Waktu:", daftar_periode)

# Menyiapkan variabel tanggal maksimum (terbaru) dan minimum (terlama) dari dataset
max_date = df['tanggal'].max()
min_date = df['tanggal'].min()

# Logika memunculkan input kalender JIKA user memilih "Custom"
if pilihan_periode == "Custom":
    rentang_custom = st.sidebar.date_input(
        "Pilih Rentang Tanggal:",
        value=(min_date, max_date), # Default otomatis terpilih dari awal sampai akhir
        min_value=min_date,         # Batas paling lama yang bisa diklik
        max_value=max_date          # Batas paling baru yang bisa diklik
    )

# Filter Cabang (khusus page 2)
if menu == "Detail Analisis":
    st.sidebar.write("---")
    daftar_cabang = ["Semua Cabang"] + sorted(df['branch'].dropna().unique().tolist())
    pilihan_cabang = st.sidebar.selectbox("Pilih Cabang:", daftar_cabang)

st.sidebar.write("---")
st.sidebar.caption("Always Healthy Hospital Dashboard © 2026")

# =========================================================
# 4. FILTERING DATA GLOBAL & VARIABEL UMUM
# =========================================================
# Secara default, batas akhirnya adalah tanggal terbaru di data
end_date = max_date 

if pilihan_periode == "Semua Periode":
    start_date = min_date
    teks_waktu = "Semua Periode"
    
elif pilihan_periode == "3 Bulan Terakhir":
    # Menghitung mundur 3 bulan dari tanggal terbaru
    start_date = (pd.to_datetime(max_date) - pd.DateOffset(months=3)).date()
    teks_waktu = "3 Bulan Terakhir"
    
elif pilihan_periode == "5 Bulan Terakhir":
    # Menghitung mundur 5 bulan dari tanggal terbaru
    start_date = (pd.to_datetime(max_date) - pd.DateOffset(months=5)).date()
    teks_waktu = "5 Bulan Terakhir"
    
elif pilihan_periode == "10 Bulan Terakhir":
    # Menghitung mundur 10 bulan dari tanggal terbaru
    start_date = (pd.to_datetime(max_date) - pd.DateOffset(months=10)).date()
    teks_waktu = "10 Bulan Terakhir"
    
elif pilihan_periode == "Custom":
    # Jika user memilih Custom, kalender akan mengembalikan Tuple.
    # Kita perlu mengecek apakah user sudah selesai mengeklik 2 tanggal (start dan end)
    if len(rentang_custom) == 2:
        start_date, end_date = rentang_custom
        teks_waktu = f"{start_date.strftime('%d %b %Y')} s.d. {end_date.strftime('%d %b %Y')}"
    else:
        # Jika user baru mengeklik 1 tanggal (belum klik tanggal akhirnya), 
        # amankan agar kode tidak error dengan menyamakan start dan end.
        start_date = rentang_custom[0]
        end_date = rentang_custom[0]
        teks_waktu = f"{start_date.strftime('%d %b %Y')}"

# Eksekusi Filter Data berdasarkan rentang start_date sampai end_date
df_filtered = df[(df['tanggal'] >= start_date) & (df['tanggal'] <= end_date)].copy()

tp_cols = ['registration', 'doctor_consultation', 'nurse_service', 'pharmacy_service', 'laboratory', 'emergency_response', 'billing_process', 'facility_cleanliness', 'staff_friendliness', 'waiting_time']
# =========================================================
# 5. HALAMAN 1: EXECUTIVE SUMMARY
# =========================================================
if menu == "Executive Summary":
    st.markdown("<h1 style='color: #0F4C75;'>Always Healthy Hospital</h1>", unsafe_allow_html = True)
    st.markdown(f"<h3 style='color: #0F4C75;'>Executive Summary - {teks_waktu}</h3>", unsafe_allow_html = True)

    # ---------------------------------------------------------
    # KALKULASI NPS BERDASARKAN RUMUS STANDAR (-100 s.d 100)
    # ---------------------------------------------------------
    total_nps_aktual = len(df_filtered['nps'].dropna())
    if total_nps_aktual > 0:
        promoter_aktual = len(df_filtered[df_filtered['nps'] >= 9])
        detractor_aktual = len(df_filtered[df_filtered['nps'] <= 6])
        current_nps = ((promoter_aktual - detractor_aktual) / total_nps_aktual) * 100
    else:
        current_nps = 0

    # Menentukan Kategori Interpretasi Kinerja NPS
    if current_nps < 0:
        nps_kategori = "Buruk"
        nps_warna = "inverse"  # Teks akan menjadi Merah
    elif current_nps <= 50:
        nps_kategori = "Cukup Baik"
        nps_warna = "off"      # Teks akan menjadi Abu-abu
    else:
        nps_kategori = "Sangat Baik"
        nps_warna = "normal"   # Teks akan menjadi Hijau
    
    # ---------------------------------------------------------
    # KALKULASI METRIK LAINNYA (Tetap menggunakan rata-rata)
    # ---------------------------------------------------------
    current_csi = df_filtered['csi'].mean()
    current_loyalty = df_filtered['loyalty'].mean()
    current_ces = df_filtered['ces'].mean()

    bench_csi = df['csi'].mean()
    bench_loyalty = df['loyalty'].mean()
    bench_ces = df['ces'].mean()

    # ---------------------------------------------------------
    # TAMPILAN KARTU METRIK
    # ---------------------------------------------------------
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric(
    label="NPS (Net Promoter Score)", 
    value=f"{current_nps:.2f}%", 
    delta=f"Kinerja: {nps_kategori}", 
    delta_color=nps_warna 
    )
    kpi2.metric("CSI (Customer Satisfaction)", f"{current_csi:.2f}", f"{current_csi - bench_csi:.2f} vs. Baseline")
    kpi3.metric("Customer Loyalty", f"{current_loyalty:.2f}", f"{current_loyalty - bench_loyalty:.2f} vs. Baseline")
    kpi4.metric("Customer Effort Score", f"{current_ces:.2f}", f"{current_ces - bench_ces:.2f} vs. Baseline", delta_color="inverse")
    st.write("---")

    # FEEDBACK ANALYSIS
    jumlah_good, jumlah_improve, persen_good, persen_improve, total_fb = 0, 0, 0, 0, 0

    if 'improvement_feedback' in df.columns:
        df_fb= df_filtered.dropna(subset=['improvement_feedback']).copy()
        df_fb['feedback_clean'] = df_fb['improvement_feedback'].astype(str).str.strip().str.lower()
        df_fb = df_fb[df_fb['feedback_clean'] != 'nan']

        total_fb = df_fb.shape[0]
        if total_fb > 0:
            df_good = df_fb[df_fb['feedback_clean'] == 'service good']
            df_improve = df_fb[df_fb['feedback_clean'] != 'service good']
            jumlah_good = df_good.shape[0]
            jumlah_improve = df_improve.shape[0]

    # HTML Super Card
    total_pasien = len(df_filtered)
    jumlah_laki = len(df_filtered[df_filtered['gender'] == 'Male'])
    jumlah_perempuan = len(df_filtered[df_filtered['gender'] == 'Female'])
            
    str_total = f"{total_pasien:,.0f}".replace(",", ".")
    str_laki = f"{jumlah_laki:,.0f}".replace(",", ".")
    str_perempuan = f"{jumlah_perempuan:,.0f}".replace(",", ".")

    html_card = (
        f"<div style='background-color: #F8FAFC; padding: 20px; border-radius: 12px; border: 1px solid #E2E8F0; display: flex; align-items: center; justify-content: space-between; gap: 15px; margin-bottom: 15px; flex-wrap: wrap;'>"
        f"  <div style='flex: 1; min-width: 150px;'>"
        f"      <p style='margin: 0px; font-size: 14px; color: #475569; font-weight: 600;'>👥 Total Pasien ({teks_waktu})</p>"
        f"      <h2 style='margin: 5px 0px 0px 0px; color: #0F172A; font-size: 28px;'>{str_total} <span style='font-size: 13px; font-weight: normal; color: #64748B;'>Pasien</span></h2>"
        f"  </div>"
        f"  <div style='display: flex; gap: 10px; flex: 1.2; min-width: 200px;'>"
        f"      <div style='flex: 1; background-color: #EFF6FF; padding: 10px; border-radius: 8px; border: 1px solid #BFDBFE;'>"
        f"          <p style='margin: 0px; font-size: 12px; color: #1E3A8A; font-weight: bold;'>👨 Laki-laki</p>"
        f"          <h4 style='margin: 3px 0px 0px 0px; color: #2563EB; font-size: 17px;'>{str_laki} <span style='font-size: 12px; font-weight: normal;'>orang</span></h4>"
        f"      </div>"
        f"      <div style='flex: 1; background-color: #FDF2F8; padding: 10px; border-radius: 8px; border: 1px solid #FBCFE8;'>"
        f"          <p style='margin: 0px; font-size: 12px; color: #831843; font-weight: bold;'>👩 Perempuan</p>"
        f"          <h4 style='margin: 3px 0px 0px 0px; color: #DB2777; font-size: 17px;'>{str_perempuan} <span style='font-size: 12px; font-weight: normal;'>orang</span></h4>"
        f"      </div>"
        f"  </div>"
        f"</div>"
    )
    st.markdown(html_card, unsafe_allow_html=True)
    
    col_left, col_right = st.columns(2)
    
    # AREA KIRI
    with col_left:
        # TREN KPI (LINE CHART)
        metrik_asli = ['csi', 'loyalty', 'ces']
        df_trend = df_filtered.groupby('bulan')[metrik_asli].mean().reset_index()
        df_trend = df_trend.rename(columns={'csi': 'CSI', 'loyalty': 'Loyalty', 'ces': 'CES'})
        metrik_tampil = ['CSI', 'Loyalty', 'CES']

        fig_line = px.line(df_trend, x='bulan', y=metrik_tampil, markers=True, height=350, labels={"value": "Skor", 'variable': '', 'bulan': ''})
        fig_line.update_layout(
            title=dict(text="<b>Tren KPI</b>", font=dict(size=18, color='#1E293B'), x=0.02, y=0.98),
            margin={"r": 20, "t": 60, "l": 0, "b": 70}, 
            legend=dict(orientation="h", yanchor="top", y=1.15, xanchor="right", x=1, title_text=""),
            paper_bgcolor='#E2E8F0', plot_bgcolor='#E2E8F0'
        )
        st.plotly_chart(fig_line, use_container_width=True, config={'displayModeBar': False})

        # DOUGHNUT CHART
        if total_fb > 0:
            df_donut = pd.DataFrame({'Kategori': ['Service Good', 'Need Improve'], 'Jumlah': [jumlah_good, jumlah_improve]})
            fig_donut = px.pie(df_donut, values='Jumlah', names='Kategori', hole=0.6, color='Kategori', color_discrete_map={'Service Good': '#0E3B6E', 'Need Improve': '#94A3B8'})
            fig_donut.update_traces(textposition='outside', texttemplate='<b>%{label}</b><br>%{percent}', textfont_size=13, rotation=90, hovertemplate="<b>%{label}</b><br>Jumlah: %{value} Pasien<br>Proporsi: %{percent}<extra></extra>")
            fig_donut.update_layout(title=dict(text="<b>Persentase Feedback</b>", font=dict(size=16, color='#1E293B'), x=0.02, y=0.95), margin={"r": 80, "t": 60, "l": 80, "b": 80}, showlegend=False, paper_bgcolor='#E2E8F0', plot_bgcolor='#E2E8F0', height=360)
            st.plotly_chart(fig_donut, use_container_width=True, config={'displayModeBar': False})
        else:
            st.info("Tidak ada data feedback di periode ini.")

    # AREA KANAN
    with col_right:
        # TOUCHPOINT ANALYSIS (BAR CHART)
        df_tp = df_filtered[tp_cols].mean().reset_index()
        df_tp.columns = ['Touchpoint', 'Rata_rata']
        df_tp['Touchpoint'] = df_tp['Touchpoint'].str.replace('_', ' ').str.title()
        df_tp = df_tp.sort_values('Rata_rata', ascending=True)

        fig_bar = px.bar(df_tp, x='Rata_rata', y='Touchpoint', orientation='h', text_auto='.2f', color='Rata_rata', color_continuous_scale='Blues', height=350)
        fig_bar.update_traces(textfont_size=13, textposition="inside")
        fig_bar.update_layout(title=dict(text="<b>Touchpoint</b>", font=dict(size=18, color='#1E293B'), x=0.02, y=0.98), margin={"r": 20, "t": 60, "l": 0, "b": 70}, coloraxis_showscale=False, yaxis_title="", xaxis_title="Rataan Skor Touchpoint", paper_bgcolor='#E2E8F0', plot_bgcolor='#E2E8F0')
        st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})

        # BAR CHART AREA PERBAIKAN
        if jumlah_improve > 0:
            teks_token = df_improve['feedback_clean'].str.replace('improve ', '', regex=False).str.split(',')
            df_exploded = teks_token.explode().str.strip().str.title()
            detil_improve = df_exploded.value_counts().reset_index()
            detil_improve.columns = ['Area Perbaikan', 'Jumlah Feedback']
            detil_improve['Persentase'] = (detil_improve['Jumlah Feedback'] / jumlah_improve) * 100
            detil_improve = detil_improve.sort_values('Persentase', ascending=True).reset_index(drop=True)

            fig_improve = px.bar(detil_improve, x='Persentase', y='Area Perbaikan', orientation='h', text_auto='.1f', color='Persentase', color_continuous_scale='Reds', height=360)
            fig_improve.update_traces(textangle=0)
            fig_improve.update_layout(title=dict(text="<b>Distribusi Area Perbaikan Utama</b>", font=dict(size=18, color='#1E293B'), x=0.02, y=0.98), margin={"r": 30, "t": 60, "l": 0, "b": 70}, coloraxis_showscale=False, xaxis_title="Persentase Keluhan (%)", yaxis_title="", paper_bgcolor='#E2E8F0', plot_bgcolor='#E2E8F0')
            st.plotly_chart(fig_improve, use_container_width=True, config={'displayModeBar': False})

# =========================================================
# 6. HALAMAN 2: DETAIL ANALISIS
# =========================================================
elif menu == "Detail Analisis":
    st.markdown("<h1 style='color: #0F4C75;'>Always Healthy Hospital</h1>", unsafe_allow_html = True)
    st.markdown(f"<h3 style='color: #0F4C75;'>Detail Analisis - {teks_waktu}</h3>", unsafe_allow_html = True)

    # MEMBUAT DUA TAB DI HALAMAN 2
    tab_Kinerja, tab_Pasien = st.tabs(["Kinerja Cabang", "Pasien"])
    
    # ---------------------------------------------------------
    # TAB 1: KINERJA CABANG & KUADRAN IPA
    # ---------------------------------------------------------
    with tab_Kinerja:
        st.markdown("<h4 style='color: #0F4C75; margin-top: 0px;'>Kinerja Cabang & Kuadran Prioritas</h4>", unsafe_allow_html=True)
        
        col_c_left, col_c_right = st.columns([1.1, 1])
        
        # AREA KIRI (Grafik Peringkat NPS)
        with col_c_left: 
            df_rank = df_filtered.groupby('branch')['nps'].mean().reset_index()
            df_rank = df_rank.rename(columns={'nps': 'Rataan NPS'})
            # Diurutkan ascending agar nilai terendah di bawah dan tertinggi di atas grafik batang
            df_rank = df_rank.sort_values('Rataan NPS', ascending=True).reset_index(drop=True) 

            fig_rank = px.bar(
                df_rank, x='Rataan NPS', y='branch', orientation='h', text_auto='.2f',
                color='Rataan NPS', color_continuous_scale='Blues' 
            )
            fig_rank.update_layout(
                title=dict(text="<b>Peringkat Cabang (Berdasarkan NPS)</b>", font=dict(size=16, color='#1E293B')),
                margin={"r": 20, "t": 50, "l": 0, "b": 20}, xaxis_title="", yaxis_title="",
                coloraxis_showscale=False, paper_bgcolor='#E2E8F0', plot_bgcolor='#E2E8F0', height=500
            )
            fig_rank.update_traces(textposition='inside', textfont_size=13)

            # Fitur klik (on_select) diaktifkan
            event_chart = st.plotly_chart(
                fig_rank, use_container_width=True, config={'displayModeBar': False},
                on_select="rerun", selection_mode="points"     
            )
        
        # AREA KANAN (Scatter Plot Kuadran IPA - Responsif terhadap Klik Bar Chart)
        with col_c_right: 
            # 1. Menangkap Filter Cabang dari Klik Grafik
            if len(event_chart.selection.points) > 0:
                selected_branch_kuadran = event_chart.selection.points[0]["y"]
                df_kuadran = df_filtered[df_filtered['branch'] == selected_branch_kuadran]
                judul_kuadran = f"<b>Matriks Kepuasan - Cabang {selected_branch_kuadran}</b>"
            else:
                df_kuadran = df_filtered.copy()
                judul_kuadran = "<b>Matriks Kepuasan - Seluruh Cabang</b>"

            # 2. Kalkulasi Data Kuadran Berdasarkan Data yang Tersaring
            mean_scores, correlations = [], []
            for tp in tp_cols:
                mean_scores.append(df_kuadran[tp].mean())
                valid_data = df_kuadran[[tp, 'csi']].dropna()
                corr = valid_data[tp].corr(valid_data['csi']) if len(valid_data) > 1 else 0
                correlations.append(corr)
            
            tp_label = [tp.replace('_', ' ').title() for tp in tp_cols]
            df_driver = pd.DataFrame({'Aspek Layanan': tp_label, 'Performa': mean_scores, 'Kepentingan': correlations}).dropna()
            
            # 3. Menggambar Matriks
            if not df_driver.empty:
                avg_x = df_driver['Performa'].mean()
                avg_y = df_driver['Kepentingan'].mean()

                jarak_x = max(abs(df_driver['Performa'].max() - avg_x), abs(df_driver['Performa'].min() - avg_x))
                jarak_y = max(abs(df_driver['Kepentingan'].max() - avg_y), abs(df_driver['Kepentingan'].min() - avg_y))
                
                pad_x, pad_y = jarak_x * 0.15, jarak_y * 0.15
                batas_x = [avg_x - jarak_x - pad_x, avg_x + jarak_x + pad_x]
                batas_y = [avg_y - jarak_y - pad_y, avg_y + jarak_y + pad_y]

                fig_quad = px.scatter(df_driver, x='Performa', y='Kepentingan', text='Aspek Layanan', height=500)
                fig_quad.update_traces(marker=dict(size=14, color='#0E3B6E', line=dict(width=1.5, color='white')), textposition='top center', textfont=dict(size=11.5, color='#1E293B'), hovertemplate="<b>%{text}</b><br>Skor: %{x:.2f}<br>Korelasi: %{y:.2f}<extra></extra>")
                fig_quad.add_hline(y=avg_y, line_dash="dash", line_color="#94A3B8")
                fig_quad.add_vline(x=avg_x, line_dash="dash", line_color="#94A3B8")
                
                pos_x_kiri, pos_x_kanan = avg_x - (jarak_x / 2), avg_x + (jarak_x / 2)
                pos_y_atas, pos_y_bawah = avg_y + (jarak_y / 2), avg_y - (jarak_y / 2)

                fig_quad.update_layout(
                    title=dict(text=judul_kuadran, font=dict(size=18, color='#1E293B')),
                    margin={"r": 30, "t": 85, "l": 20, "b": 50}, paper_bgcolor='#E2E8F0', plot_bgcolor='#E2E8F0',
                    xaxis=dict(title="Performa Aktual", range=batas_x, showgrid=True),
                    yaxis=dict(title="Tingkat Kepentingan", range=batas_y, showgrid=True),
                    annotations=[
                        dict(text="<b>PRIORITAS UTAMA</b>", x=pos_x_kiri, y=pos_y_atas, xref="x", yref="y", showarrow=False, font=dict(size=14, color="#1C2CB9"), opacity=0.3),
                        dict(text="<b>PERTAHANKAN KINERJA</b>", x=pos_x_kanan, y=pos_y_atas, xref="x", yref="y", showarrow=False, font=dict(size=14, color="#15803D"), opacity=0.3),
                        dict(text="<b>PRIORITAS RENDAH</b>", x=pos_x_kiri, y=pos_y_bawah, xref="x", yref="y", showarrow=False, font=dict(size=14, color="#64748B"), opacity=0.3),
                        dict(text="<b>ALOKASI BERLEBIH</b>", x=pos_x_kanan, y=pos_y_bawah, xref="x", yref="y", showarrow=False, font=dict(size=14, color="#D90606"), opacity=0.3)
                    ]
                )
                st.plotly_chart(fig_quad, use_container_width=True, config={'displayModeBar': False})
            else:
                st.info("Data tidak cukup untuk membentuk Kuadran Analisis di pilihan cabang/periode ini.")
        # =========================================================
        # SECTION: INSIGHT & RECOMMENDATION (Otomatis menyesuaikan data)
        # =========================================================

        st.markdown("<h4 style='color: #0F4C75;'>💡 Ringkasan Eksekutif & Saran Strategis</h4>", unsafe_allow_html=True)
        
        # Ekstrak data terendah untuk prioritas perbaikan
        lowest_aspects = df_driver.sort_values(by='Performa').head(2)
        
        # Ekstrak cabang terbaik (NPS tertinggi, indeks terakhir karena data di-sort ascending) dan terburuk (NPS terendah, indeks ke-0)
        worst_branch = df_rank.iloc[0] if not df_rank.empty else None
        best_branch = df_rank.iloc[-1] if not df_rank.empty else None

        col_ins1, col_ins2 = st.columns(2)

        with col_ins1:
            st.markdown("##### 🩺 Area Prioritas Peningkatan Pelayanan")
            if len(lowest_aspects) >= 2:
                aspek1 = lowest_aspects.iloc[0]['Aspek Layanan']
                skor1 = lowest_aspects.iloc[0]['Performa']
                kor1 = lowest_aspects.iloc[0]['Kepentingan']
                
                aspek2 = lowest_aspects.iloc[1]['Aspek Layanan']
                skor2 = lowest_aspects.iloc[1]['Performa']

                st.info(
                    f"**1. Perbaikan Target Utama:** Berdasarkan matriks pelayanan, layanan **{aspek1}** mencatat "
                    f"rata-rata kepuasan terendah saat ini ({skor1:.2f}/10). Mengingat area ini memiliki pengaruh nyata "
                    f"terhadap penilaian pasien (Korelasi: {kor1:.2f}), manajemen disarankan untuk memprioritaskan peninjauan ulang alur kerja di titik ini."
                )
                st.info(
                    f"**2. Antisipasi Layanan Sekunder:** Prioritas peningkatan mutu berikutnya berada pada layanan **{aspek2}** "
                    f"(Skor: {skor2:.2f}/10). Evaluasi standar dan prosedur operasional klinis di area ini sangat dianjurkan untuk menjaga tingkat kenyamanan pasien."
                )

        with col_ins2:
            st.markdown("##### 🏆 Komparasi Kinerja Antar Cabang")
            if worst_branch is not None and best_branch is not None:
                st.success(
                    f"**Pencapaian Mutu Terbaik:** Cabang **{best_branch['branch']}** memimpin performa dengan tingkat kepuasan tertinggi "
                    f"(Rataan NPS: **{best_branch['Rataan NPS']:.2f}**). Pola komunikasi klinis dan manajemen pelayanan di cabang ini sangat layak "
                    f"dijadikan Standar Acuan (*Role Model*) bagi rumah sakit cabang lainnya."
                )
                st.error(
                    f"**Area Perlu Intervensi:** Cabang **{worst_branch['branch']}** saat ini berada di posisi terbawah "
                    f"(Rataan NPS: **{worst_branch['Rataan NPS']:.2f}**). Tim Manajemen Mutu disarankan menjadwalkan audit layanan guna memetakan "
                    f"akar kendala yang dialami oleh pasien di lokasi tersebut."
                )
        

    # ---------------------------------------------------------
    # TAB 2: PASIEN (Profil, Umur, Kedatangan & Feedback Gender)
    # ---------------------------------------------------------
    with tab_Pasien:
        st.markdown("<h4 style='color: #0F4C75; margin-top: 0px;'>Profil Demografi & Tren Kunjungan</h4>", unsafe_allow_html=True)
        
        # 1. KARTU TOTAL PASIEN
        total_pasien_t2 = len(df_filtered)
        jumlah_laki_t2 = len(df_filtered[df_filtered['gender'] == 'Male'])
        jumlah_perempuan_t2 = len(df_filtered[df_filtered['gender'] == 'Female'])
                
        str_total_t2 = f"{total_pasien_t2:,.0f}".replace(",", ".")
        str_laki_t2 = f"{jumlah_laki_t2:,.0f}".replace(",", ".")
        str_perempuan_t2 = f"{jumlah_perempuan_t2:,.0f}".replace(",", ".")

        html_card_t2 = (
            f"<div style='background-color: #F8FAFC; padding: 20px; border-radius: 12px; border: 1px solid #E2E8F0; display: flex; align-items: center; justify-content: space-between; gap: 15px; margin-bottom: 15px; flex-wrap: wrap;'>"
            f"  <div style='flex: 1; min-width: 150px;'>"
            f"      <p style='margin: 0px; font-size: 14px; color: #475569; font-weight: 600;'>👥 Total Pasien ({teks_waktu})</p>"
            f"      <h2 style='margin: 5px 0px 0px 0px; color: #0F172A; font-size: 28px;'>{str_total_t2} <span style='font-size: 13px; font-weight: normal; color: #64748B;'>Pasien</span></h2>"
            f"  </div>"
            f"  <div style='display: flex; gap: 10px; flex: 1.2; min-width: 200px;'>"
            f"      <div style='flex: 1; background-color: #EFF6FF; padding: 10px; border-radius: 8px; border: 1px solid #BFDBFE;'>"
            f"          <p style='margin: 0px; font-size: 12px; color: #1E3A8A; font-weight: bold;'>👨 Laki-laki</p>"
            f"          <h4 style='margin: 3px 0px 0px 0px; color: #2563EB; font-size: 17px;'>{str_laki_t2} <span style='font-size: 12px; font-weight: normal;'>orang</span></h4>"
            f"      </div>"
            f"      <div style='flex: 1; background-color: #FDF2F8; padding: 10px; border-radius: 8px; border: 1px solid #FBCFE8;'>"
            f"          <p style='margin: 0px; font-size: 12px; color: #831843; font-weight: bold;'>👩 Perempuan</p>"
            f"          <h4 style='margin: 3px 0px 0px 0px; color: #DB2777; font-size: 17px;'>{str_perempuan_t2} <span style='font-size: 12px; font-weight: normal;'>orang</span></h4>"
            f"      </div>"
            f"  </div>"
            f"</div>"
        )
        st.markdown(html_card_t2, unsafe_allow_html=True)

        col_p_left, col_p_right = st.columns(2)
        
        # 2. AREA KIRI (Distribusi Umur)
        with col_p_left:
            kolom_umur = 'age' if 'age' in df_filtered.columns else 'umur' if 'umur' in df_filtered.columns else None
            
            if kolom_umur:
                # 1. Mendefinisikan batas rentang umur dan labelnya
                # Ubah angka ini jika kamu punya standar rentang yang berbeda
                batas_umur = [0, 18, 26, 36, 46, 56, 100]
                label_umur = ['<18', '18-25', '26-35', '36-45', '46-55', '>55']
                
                # 2. Mengelompokkan umur ke dalam kategori
                df_age = df_filtered.copy()
                df_age['Kelompok Umur'] = pd.cut(df_age[kolom_umur], bins=batas_umur, labels=label_umur, right=False)
                
                # 3. Menghitung jumlah pasien per kelompok umur
                df_age_group = df_age.groupby('Kelompok Umur').size().reset_index(name='Jumlah Pasien')
                
                # 4. Bar Chart
                fig_age = px.bar(
                    df_age_group, x='Kelompok Umur', y='Jumlah Pasien', 
                    text_auto=True, color_discrete_sequence=['#0F4C75'], height=350
                )
                fig_age.update_traces(textposition='outside')
                fig_age.update_layout(
                    title=dict(text="<b>Distribusi Rentang Umur</b>", font=dict(size=18, color='#1E293B'), x=0.02, y=0.98),
                    margin={"r": 20, "t": 60, "l": 20, "b": 50}, 
                    yaxis_title="Jumlah Pasien", xaxis_title="Rentang Umur (Tahun)",
                    paper_bgcolor='#E2E8F0', plot_bgcolor='#E2E8F0'
                )
                st.plotly_chart(fig_age, use_container_width=True, config={'displayModeBar': False})
            else:
                st.info("Data kolom umur pasien tidak ditemukan di dataset ini.")

        # 3. AREA KANAN (Tren Kunjungan)
        with col_p_right:
            if pilihan_periode == "Semua Periode":
                df_visit = df_filtered.groupby('bulan').size().reset_index(name='Jumlah Kunjungan')
                x_axis_col = 'bulan'
                judul_visit = "<b>Tren Kedatangan Pasien Bulanan</b>"
            else:
                df_visit = df_filtered.groupby('tanggal').size().reset_index(name='Jumlah Kunjungan')
                x_axis_col = 'tanggal'
                judul_visit = f"<b>Kedatangan Pasien Harian ({pilihan_periode})</b>"

            if not df_visit.empty:
                fig_visit = px.line(
                    df_visit, x=x_axis_col, y='Jumlah Kunjungan', markers=True, height=350,
                    labels={'Jumlah Kunjungan': 'Jumlah Pasien', x_axis_col: ''}
                )
                fig_visit.update_traces(line_color='#2563EB', fill='tozeroy', fillcolor='rgba(37, 99, 235, 0.1)')
                fig_visit.update_layout(
                    title=dict(text=judul_visit, font=dict(size=18, color='#1E293B'), x=0.02, y=0.98),
                    margin={"r": 20, "t": 60, "l": 20, "b": 50}, 
                    yaxis_title="Jumlah Kunjungan", xaxis_title="",
                    paper_bgcolor='#E2E8F0', plot_bgcolor='#E2E8F0'
                )
                st.plotly_chart(fig_visit, use_container_width=True, config={'displayModeBar': False})
            else:
                st.info("Data tanggal/kedatangan tidak ditemukan.")

        # =========================================================
        # 4. AREA BAWAH (Proporsi Area Perbaikan Berdasarkan Gender)
        # =========================================================
                
        if 'improvement_feedback' in df_filtered.columns and 'gender' in df_filtered.columns:
            # Menyaring dan membersihkan data feedback
            df_gen_fb = df_filtered.dropna(subset=['improvement_feedback', 'gender']).copy()
            df_gen_fb['feedback_clean'] = df_gen_fb['improvement_feedback'].astype(str).str.strip().str.lower()
            df_gen_fb = df_gen_fb[(df_gen_fb['feedback_clean'] != 'nan') & (df_gen_fb['feedback_clean'] != 'service good')]

            if not df_gen_fb.empty:
                # Memecah keluhan ganda (explode) agar dihitung satu-satu
                df_gen_fb['feedback_clean'] = df_gen_fb['feedback_clean'].str.replace('improve ', '', regex=False).str.split(',')
                df_exploded_gen = df_gen_fb.explode('feedback_clean')
                df_exploded_gen['feedback_clean'] = df_exploded_gen['feedback_clean'].str.strip().str.title()

                # Menghitung agregasi per gender
                df_gen_agg = df_exploded_gen.groupby(['feedback_clean', 'gender']).size().reset_index(name='Jumlah')

                # Menggambar Grouped Bar Chart
                fig_gen_fb = px.bar(
                    df_gen_agg,
                    y='feedback_clean',
                    x='Jumlah',
                    color='gender',
                    orientation='h',
                    barmode='group', # Grouped agar bar Laki-laki dan Perempuan bersebelahan
                    color_discrete_map={'Male': '#2563EB', 'Female': '#DB2777'}, # Sinkron dengan warna di atas
                    height=550
                )
                
                fig_gen_fb.update_layout(
                    title=dict(text="<b>Proporsi Feedback Berdasarkan Gender</b>", font=dict(size=18, color='#1E293B'), x=0.02, y=0.98),
                    margin={"r": 20, "t": 60, "l": 0, "b": 90},
                    yaxis_title="",
                    xaxis_title="Jumlah Keluhan Pasien",
                    legend_title="Gender",
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    paper_bgcolor='#E2E8F0', plot_bgcolor='#E2E8F0'
                )
                # Mengurutkan area dari yang paling banyak dikeluhkan
                fig_gen_fb.update_yaxes(categoryorder='total ascending', tickfont=dict(color='#1E293B'))
                
                st.plotly_chart(fig_gen_fb, use_container_width=True, config={'displayModeBar': False})
            else:
                st.info("Tidak ada data keluhan yang memerlukan perbaikan pada filter ini.")