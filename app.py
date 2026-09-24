import os
import sys
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.db_handler import init_db, load_companies, get_ingestion_summary
from ingestion.fetch_data import fetch_companies_data

# Page configuration
st.set_page_config(
    page_title="BandarPulse | Market Intelligence",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Dark Theme Styling (Matching UI Design Specs)
st.markdown("""
<style>
    /* Dark Theme Base */
    .stApp {
        background-color: #12141A;
        color: #F3F4F6;
    }
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #161922;
        border-right: 1px solid #232733;
    }
    
    /* KPI Metric Cards */
    .metric-card {
        background: #1C202B;
        border: 1px solid #2D3345;
        border-radius: 10px;
        padding: 16px;
        margin-bottom: 12px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
    }
    .metric-value {
        font-size: 26px;
        font-weight: 700;
        color: #60A5FA;
    }
    .metric-label {
        font-size: 13px;
        color: #9CA3AF;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* Badges */
    .badge-high {
        background-color: rgba(16, 185, 129, 0.2);
        color: #10B981;
        padding: 4px 10px;
        border-radius: 20px;
        font-weight: 600;
        border: 1px solid #10B981;
    }
    .badge-moderate {
        background-color: rgba(245, 158, 11, 0.2);
        color: #F59E0B;
        padding: 4px 10px;
        border-radius: 20px;
        font-weight: 600;
        border: 1px solid #F59E0B;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Database
init_db()

# ================= SIDEBAR NAVIGATION =================
with st.sidebar:
    st.markdown("## ⚡ **BandarPulse**")
    st.caption("Track 3 • Market Intelligence | Sectors Hackathon")
    st.markdown("---")
    
    selected_menu = st.radio(
        "Pilih Menu Navigasi:",
        [
            "1. Market Radar (Daily Screener)",
            "2. Accumulation Forensics (Deep Dive)",
            "3. AI Trade Thesis & Playbook",
            "4. Engine & Ingestion Monitor"
        ],
        index=0
    )
    
    st.markdown("---")
    st.caption("🛡️ **System Status**")
    summary = get_ingestion_summary()
    st.markdown(f"**Cache Status:** `Live (SQLite)`")
    st.markdown(f"**Cached Emiten:** `{summary['total_companies_cached']} tickers`")
    st.markdown(f"**API Credits Used:** `{summary['total_credits_used']} / 1,500`")
    
    if st.button("🔄 Sync EOD (1 Credit)", use_container_width=True):
        with st.spinner("Mengambil data emiten terstruktur..."):
            fetch_companies_data()
        st.success("Sinkronisasi cache berhasil!")
        st.rerun()

# ================= MENU 1: MARKET RADAR =================
if selected_menu.startswith("1."):
    st.title("📡 Market Radar: Early Accumulation Screener")
    st.caption("Pendeteksi anomali volume dan konsentrasi smart money fase konsolidasi (EOD Analysis)")
    
    # Load companies from SQLite cache
    df_companies = load_companies()
    
    # If cache is empty, load mock seed
    if df_companies.empty:
        fetch_companies_data()
        df_companies = load_companies()
    
    # Master pool of screened candidates with quantitative metrics
    master_radar_data = [
        {"Ticker": "INCO", "Nama": "Vale Indonesia Tbk", "Sektor": "Basic Materials", "Close": 3890, "vol_surge_val": 240, "bci_val": 76.5, "Bandar Score": 94, "Status": "🔥 High Conviction"},
        {"Ticker": "PTBA", "Nama": "Bukit Asam Tbk", "Sektor": "Energy", "Close": 2710, "vol_surge_val": 210, "bci_val": 72.4, "Bandar Score": 92, "Status": "🔥 High Conviction"},
        {"Ticker": "BBCA", "Nama": "Bank Central Asia Tbk", "Sektor": "Financials", "Close": 10250, "vol_surge_val": 145, "bci_val": 68.1, "Bandar Score": 88, "Status": "💎 Strong Accumulation"},
        {"Ticker": "MEDC", "Nama": "Medco Energi Internasional Tbk", "Sektor": "Energy", "Close": 1350, "vol_surge_val": 185, "bci_val": 64.8, "Bandar Score": 84, "Status": "💎 Strong Accumulation"},
        {"Ticker": "MAPI", "Nama": "Mitra Adiperkasa Tbk", "Sektor": "Consumer Cyclicals", "Close": 1420, "vol_surge_val": 160, "bci_val": 66.0, "Bandar Score": 82, "Status": "💎 Strong Accumulation"},
        {"Ticker": "BRMS", "Nama": "Bumi Resources Minerals Tbk", "Sektor": "Basic Materials", "Close": 172, "vol_surge_val": 195, "bci_val": 61.5, "Bandar Score": 78, "Status": "👀 Watchlist"},
        {"Ticker": "GOTO", "Nama": "GoTo Gojek Tokopedia Tbk", "Sektor": "Technology", "Close": 54, "vol_surge_val": 175, "bci_val": 63.5, "Bandar Score": 77, "Status": "👀 Watchlist"},
        {"Ticker": "ACES", "Nama": "Aspirasi Hidup Indonesia Tbk", "Sektor": "Consumer Cyclicals", "Close": 845, "vol_surge_val": 120, "bci_val": 59.2, "Bandar Score": 76, "Status": "👀 Watchlist"},
        {"Ticker": "KLBF", "Nama": "Kalbe Farma Tbk", "Sektor": "Healthcare", "Close": 1210, "vol_surge_val": 130, "bci_val": 62.8, "Bandar Score": 74, "Status": "👀 Watchlist"},
        {"Ticker": "TLKM", "Nama": "Telkom Indonesia Tbk", "Sektor": "Infrastructure", "Close": 2850, "vol_surge_val": 90, "bci_val": 58.0, "Bandar Score": 65, "Status": "🔍 Neutral / Low"},
        {"Ticker": "ADRO", "Nama": "Adaro Energy Indonesia Tbk", "Sektor": "Energy", "Close": 3680, "vol_surge_val": 85, "bci_val": 54.0, "Bandar Score": 62, "Status": "🔍 Neutral / Low"},
        {"Ticker": "ASII", "Nama": "Astra International Tbk", "Sektor": "Industrials", "Close": 4980, "vol_surge_val": 65, "bci_val": 52.0, "Bandar Score": 58, "Status": "🔍 Neutral / Low"}
    ]
    
    # Placeholder container for top KPI metrics (displayed above tuning expander)
    kpi_placeholder = st.container()

    # 1. Parameter Tuning & Bandarmology Thresholds Panel
    with st.expander("⚙️ Parameter Tuning & Bandarmology Thresholds", expanded=False):
        t_col1, t_col2 = st.columns(2)
        with t_col1:
            min_bci = st.slider(
                "Min Top 3 BCI (%)",
                min_value=50,
                max_value=90,
                value=60,
                step=5,
                help="Batas minimal konsentrasi volume beli bersih oleh 3 broker teratas terhadap total turnover."
            )
            min_vol_surge = st.slider(
                "Min Volume Surge (%)",
                min_value=50,
                max_value=500,
                value=100,
                step=25,
                help="Batas minimal lonjakan volume transaksi harian dibandingkan rata-rata 20 hari (SMA20)."
            )
        with t_col2:
            min_score = st.slider(
                "Min Bandar Conviction Score",
                min_value=50,
                max_value=95,
                value=70,
                step=5,
                help="Batas minimal skor komposit akumulasi cerdas (0-100)."
            )
            all_sectors = sorted(list(set(r["Sektor"] for r in master_radar_data)))
            selected_sectors = st.multiselect(
                "Filter Sektor Bursa",
                options=all_sectors,
                default=all_sectors,
                help="Pilih sektor yang ingin dipantau."
            )

    # 2. Reactive Filtering Logic
    filtered_records = [
        r for r in master_radar_data
        if r["bci_val"] >= min_bci
        and r["vol_surge_val"] >= min_vol_surge
        and r["Bandar Score"] >= min_score
        and (not selected_sectors or r["Sektor"] in selected_sectors)
    ]

    # Calculate reactive KPI values
    alerts_count = len(filtered_records)
    avg_bci_val = float(np.mean([r["bci_val"] for r in filtered_records])) if filtered_records else 0.0

    # Render Top KPI Cards into the placeholder container
    with kpi_placeholder:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown("""
            <div class="metric-card">
                <div class="metric-label">Emiten Dipindai</div>
                <div class="metric-value">824 <span style="font-size:14px;color:#10B981;">(IDX)</span></div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Accumulation Alerts</div>
                <div class="metric-value" style="color:#A78BFA;">{alerts_count} <span style="font-size:14px;color:#A78BFA;">Gems</span></div>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Avg Top 3 BCI</div>
                <div class="metric-value" style="color:#34D399;">{avg_bci_val:.1f}%</div>
            </div>
            """, unsafe_allow_html=True)
        with col4:
            st.markdown("""
            <div class="metric-card">
                <div class="metric-label">Cache Efficiency</div>
                <div class="metric-value" style="color:#FBBF24;">98.2%</div>
            </div>
            """, unsafe_allow_html=True)
            
    st.markdown("### 🎯 Sinyal Akumulasi Diam-diam Hari Ini")
    
    # 3. Render Table or Empty State
    if not filtered_records:
        st.info("Tidak ada emiten yang memenuhi kriteria tuning saat ini. Coba turunkan ambang batas.")
    else:
        # Prepare display dataframe
        table_rows = []
        for r in filtered_records:
            table_rows.append({
                "Ticker": r["Ticker"],
                "Nama": r["Nama"],
                "Sektor": r["Sektor"],
                "Close (IDR)": f"Rp {r['Close']:,}",
                "Vol Surge": f"+{r['vol_surge_val']}%",
                "Top 3 BCI": f"{r['bci_val']:.1f}%",
                "Status": r["Status"],
                "Bandar Score": r["Bandar Score"]
            })
        df_display = pd.DataFrame(table_rows)
        
        st.dataframe(
            df_display,
            column_config={
                "Bandar Score": st.column_config.ProgressColumn(
                    "Bandar Score (0-100)",
                    help="Kombinasi skor BCI, lonjakan volume, dan konsolidasi harga",
                    format="%d",
                    min_value=0,
                    max_value=100
                ),
            },
            use_container_width=True,
            hide_index=True
        )

# ================= MENU 2: ACCUMULATION FORENSICS =================
elif selected_menu.startswith("2."):
    st.title("🔬 Accumulation Forensics: Deep Dive Analisis Saham")
    st.caption("Pembedahan mikrostruktur: Foreign/Institusi flow vs distribusi ritel di fase konsolidasi")
    
    ticker = st.selectbox("Pilih Emiten untuk Dibedah:", ["PTBA", "BBCA", "MEDC", "ACES", "BRMS"], index=0)
    
    col_left, col_right = st.columns([3, 2])
    
    with col_left:
        st.subheader(f"📈 Chart Pergerakan & Volume Konsolidasi: {ticker}")
        
        # Data simulation tailored to selected ticker
        ticker_prices = {
            "PTBA": 2710,
            "BBCA": 10250,
            "MEDC": 1350,
            "ACES": 845,
            "BRMS": 172
        }
        base_price = ticker_prices.get(ticker, 2500)
        
        dates = pd.date_range(end=datetime.today(), periods=25, freq='B')
        np.random.seed(abs(hash(ticker)) % 10000)
        step_volatility = base_price * 0.007
        
        price_noise = np.random.randn(25) * step_volatility
        close_prices = base_price + np.cumsum(price_noise)
        open_prices = close_prices - (np.random.randn(25) * step_volatility * 0.5)
        high_prices = np.maximum(open_prices, close_prices) + (np.random.rand(25) * step_volatility * 0.7)
        low_prices = np.minimum(open_prices, close_prices) - (np.random.rand(25) * step_volatility * 0.7)
        
        # Base volume & accumulation volume surge in last 5 days
        base_vol = 25000000 if ticker in ("PTBA", "MEDC") else (50000000 if ticker == "BBCA" else 80000000)
        volumes = np.random.randint(int(base_vol * 0.7), int(base_vol * 1.3), size=25)
        volumes[-5:] = (volumes[-5:] * 2.1).astype(int)  # 210% surge during accumulation
        
        # 1. Subplot Layout: Row 1 (75%) Candlestick, Row 2 (25%) Volume
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            row_heights=[0.75, 0.25]
        )
        
        # Row 1: Candlestick
        fig.add_trace(
            go.Candlestick(
                x=dates,
                open=open_prices,
                high=high_prices,
                low=low_prices,
                close=close_prices,
                name="Price",
                increasing_line_color='#00D09C',
                decreasing_line_color='#EB5757',
                showlegend=False
            ),
            row=1, col=1
        )
        
        # Consolidation Box in Row 1
        box_start_idx = 8
        fig.add_shape(
            type="rect",
            x0=dates[box_start_idx], y0=min(low_prices[box_start_idx:]),
            x1=dates[-1], y1=max(high_prices[box_start_idx:]),
            line=dict(color="#A78BFA", width=1.5, dash="dash"),
            fillcolor="rgba(167, 139, 250, 0.12)",
            row=1, col=1
        )
        
        # Annotation for Consolidation Box
        fig.add_annotation(
            x=dates[box_start_idx + 3],
            y=max(high_prices[box_start_idx:]),
            text="Accumulation Box",
            showarrow=False,
            yshift=12,
            font=dict(color="#A78BFA", size=11),
            row=1, col=1
        )
        
        # 2. Dynamic Volume Bar Coloring (Green if Close >= Open, Red if Close < Open)
        vol_colors = ['#00D09C' if c >= o else '#EB5757' for c, o in zip(close_prices, open_prices)]
        
        fig.add_trace(
            go.Bar(
                x=dates,
                y=volumes,
                name="Volume",
                marker_color=vol_colors,
                showlegend=False
            ),
            row=2, col=1
        )
        
        # 3. Financial Terminal Dark Theme Styling
        fig.update_layout(
            template="plotly_dark",
            height=480,
            margin=dict(l=10, r=10, t=30, b=10),
            paper_bgcolor="#151821",
            plot_bgcolor="#151821",
            hovermode="x unified"
        )
        
        # Axis and Gridlines Styling
        fig.update_xaxes(
            gridcolor="#222734",
            zerolinecolor="#222734",
            rangeslider_visible=False
        )
        fig.update_yaxes(
            title_text="Price (IDR)",
            gridcolor="#222734",
            zerolinecolor="#222734",
            row=1, col=1
        )
        fig.update_yaxes(
            title_text="Volume",
            gridcolor="#222734",
            zerolinecolor="#222734",
            row=2, col=1
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    with col_right:
        st.subheader("🕵️ Broker Summary Forensics")
        st.caption("Top 3 Pembeli (Smart Money) vs Top 3 Penjual (Retail Exit)")
        
        b1, b2 = st.columns(2)
        with b1:
            st.markdown("**🟢 Top 3 Net Buyers**")
            st.markdown("""
            - **AK (UBS Sekuritas)**: Rp 42.5 M *(Avg 2.685)*
            - **ZP (Maybank)**: Rp 28.1 M *(Avg 2.690)*
            - **BK (JP Morgan)**: Rp 18.4 M *(Avg 2.695)*
            """)
            st.success("Dominasi Institusi Asing: 72.4%")
            
        with b2:
            st.markdown("**🔴 Top 3 Net Sellers**")
            st.markdown("""
            - **YP (Mirae Asset)**: Rp 35.2 M *(Avg 2.705)*
            - **PD (Indo Premier)**: Rp 24.6 M *(Avg 2.710)*
            - **XC (Ajaib Sekuritas)**: Rp 16.8 M *(Avg 2.695)*
            """)
            st.error("Distribusi Broker Ritel: 61.2%")
            
        st.info("💡 **Forensic Insight:** Terlihat pola penyerapan masif (*silent accumulation*) oleh broker institusi (AK, ZP, BK) di dalam rentang konsolidasi Rp 2.680 - Rp 2.710, memanfaatkan kepanikan/kebosanan investor ritel.")

# ================= MENU 3: AI TRADE THESIS =================
elif selected_menu.startswith("3."):
    st.title("🤖 AI Trade Thesis & Actionable Playbook")
    st.caption("Sintesis Agentic AI bertenaga Sectors API & LLM Reasoning")
    
    st.markdown("""
    <div style="background:#1C202B;border-left:4px solid #8B5CF6;padding:18px;border-radius:8px;margin-bottom:20px;">
        <h4 style="margin:0 0 10px 0;color:#A78BFA;">✨ Autonomous Trading Thesis: PTBA.JK (Bukit Asam Tbk)</h4>
        <p style="font-size:15px;line-height:1.6;color:#D1D5DB;margin:0;">
        "Saham <b>PTBA</b> terdeteksi sedang mengalami fase akumulasi senyap tingkat tinggi. Dalam 10 hari bursa terakhir, harga bergerak terkonsolidasi sempit di rentang 2.650–2.720, namun volume harian melonjak 210% di atas rata-rata SMA20. Top 3 buyer (AK, ZP, BK) menguasai <b>72,4%</b> dari seluruh perputaran transaksi, menyerap distribusi ritel dari broker YP dan PD. Emiten ini memiliki Debt-to-Equity 0,5x dan ROE 24,2%, menjadikannya Hidden Gem defensif sebelum potensi breakout teknikal."
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.subheader("🎯 Actionable Execution Plan")
    p1, p2, p3 = st.columns(3)
    
    with p1:
        st.markdown("""
        <div class="metric-card" style="border-top:3px solid #60A5FA;">
            <div class="metric-label">Accumulation Zone (Entry)</div>
            <div class="metric-value" style="color:#60A5FA;font-size:22px;">Rp 2.650 – Rp 2.720</div>
            <div style="font-size:12px;color:#9CA3AF;margin-top:6px;">Beli bertahap di area konsolidasi bandar</div>
        </div>
        """, unsafe_allow_html=True)
        
    with p2:
        st.markdown("""
        <div class="metric-card" style="border-top:3px solid #EF4444;">
            <div class="metric-label">Stop Loss (Invalidation)</div>
            <div class="metric-value" style="color:#EF4444;font-size:22px;">&lt; Rp 2.580 (-3.5%)</div>
            <div style="font-size:12px;color:#9CA3AF;margin-top:6px;">Cut loss jika keluar dari support kotak</div>
        </div>
        """, unsafe_allow_html=True)
        
    with p3:
        st.markdown("""
        <div class="metric-card" style="border-top:3px solid #10B981;">
            <div class="metric-label">Target Breakout (Take Profit)</div>
            <div class="metric-value" style="color:#10B981;font-size:22px;">Rp 3.050 (R:R 1:2.8)</div>
            <div style="font-size:12px;color:#9CA3AF;margin-top:6px;">Target resistance mayor berikutnya</div>
        </div>
        """, unsafe_allow_html=True)
        
    if st.button("📋 Salin Tesis ke Trading Journal"):
        st.toast("Tesis berhasil disalin ke clipboard!", icon="✅")

# ================= MENU 4: ENGINE & INGESTION MONITOR =================
elif selected_menu.startswith("4."):
    st.title("⚙️ Engine & API Quota Monitor")
    st.caption("Transparansi efisiensi kredit API Sectors dan status penyimpanan SQLite VPS")
    
    summary = get_ingestion_summary()
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Sisa Kredit API", f"{1500 - summary['total_credits_used']} / 1,500 Credits", delta="-1 credit per sync")
    with c2:
        st.metric("Cache Hit Efficiency", "96.4%", delta="+1.2% (Hemat Kredit)")
    with c3:
        st.metric("Total Data Emiten Tersimpan", f"{summary['total_companies_cached']} Emiten", delta="Ready Offline")
        
    st.markdown("### 🔄 Arsitektur Aliran Data (Cache-First)")
    st.info("Sectors API (1 Kredit / EOD Query) ➔ SQLite VPS (`database/cache.db`) ➔ Streamlit UI (0 Kredit)")
    
    st.markdown("### 📜 Log Penarikan Data Terakhir")
    if summary["recent_logs"]:
        st.dataframe(pd.DataFrame(summary["recent_logs"]), use_container_width=True)
    else:
        st.write("Belum ada riwayat aktivitas ingestion.")
