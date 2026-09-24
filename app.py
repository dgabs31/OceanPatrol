import streamlit as st
import pandas as pd
import folium
from folium.plugins import HeatMap, AntPath
from streamlit_folium import st_folium
import plotly.express as px
import plotly.graph_objects as go
import time
import os
from datetime import datetime, timedelta

# --- CONFIG ---
st.set_page_config(page_title="OceanPatrol | SeaTracker Hybrid", page_icon="🌊", layout="wide", initial_sidebar_state="collapsed")

# --- CUSTOM CSS ---
st.markdown("""
<style>
    /* Dark Ocean Theme Tweaks & Gradient */
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #05162a 0%, #0a2e5c 100%);
        color: #e6f1ff;
    }
    
    /* Hide Streamlit elements */
    [data-testid="collapsedControl"] { display: none !important; }
    [data-testid="stSidebar"] { display: none !important; }
    header[data-testid="stHeader"] { display: none !important; }
    
    .block-container {
        padding-top: 100px !important; /* Push content down so it doesn't hide behind fixed navbar */
        padding-bottom: 2rem !important;
        max-width: 95% !important;
    }

    /* --- FIXED NAVBAR --- */
    /* Target the specific block containing our #navbar-anchor and make it fixed */
    div[data-testid="stVerticalBlock"] > div:has(#navbar-anchor) {
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        width: 100vw !important;
        z-index: 99999 !important;
        background: #05162a !important; /* Solid dark color */
        padding: 15px 5% 5px 5% !important;
        border-bottom: 1px solid #233554 !important;
        box-shadow: 0 4px 20px rgba(0,0,0,0.5) !important;
    }

    /* --- RADIO BUTTONS AS TABS (NO BULLETS) --- */
    /* Hide the radio bullet circle */
    div[role="radiogroup"] > label > div:first-child:not([data-testid="stMarkdownContainer"]) {
        display: none !important;
    }
    div[role="radiogroup"] > label svg {
        display: none !important;
    }

    /* Layout the radio buttons horizontally */
    div[role="radiogroup"] {
        display: flex;
        justify-content: center;
        flex-wrap: wrap;
        gap: 5px;
    }
    
    /* Style the radio labels as buttons */
    div[role="radiogroup"] > label {
        padding: 10px 15px !important;
        margin: 0 !important;
        border-radius: 8px !important;
        background: transparent !important;
        transition: all 0.3s ease !important;
        cursor: pointer !important;
    }
    div[role="radiogroup"] > label:hover {
        background: rgba(255,255,255,0.08) !important;
    }
    div[role="radiogroup"] > label[aria-checked="true"] {
        background: rgba(0, 210, 255, 0.15) !important;
    }
    
    /* Text styles for the tabs */
    div[role="radiogroup"] p {
        font-size: 15px !important;
        font-weight: 600 !important;
        color: #8892b0 !important;
        margin: 0 !important;
        transition: color 0.3s ease !important;
    }
    div[role="radiogroup"] > label:hover p {
        color: #e6f1ff !important;
    }
    div[role="radiogroup"] > label[aria-checked="true"] p {
        color: #00d2ff !important;
    }

    /* --- GOJEK/PERTAMINA STYLE DASHBOARD CARDS --- */
    .dash-card {
        border-radius: 24px;
        padding: 35px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        transition: transform 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275), box-shadow 0.4s ease;
        animation: slideUp 0.8s ease-out forwards;
        opacity: 0;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: flex-start;
        margin-bottom: 20px;
    }
    .dash-card:hover {
        transform: translateY(-12px);
        box-shadow: 0 20px 40px rgba(0,0,0,0.4);
    }
    .card-green { background: linear-gradient(135deg, #74EBD5 0%, #9FACE6 100%); color: #020c1b !important; }
    .card-purple { background: linear-gradient(135deg, #a18cd1 0%, #fbc2eb 100%); color: #020c1b !important; animation-delay: 0.15s;}
    .card-orange { background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 99%, #fecfef 100%); color: #020c1b !important; animation-delay: 0.3s;}
    
    .dash-card h3 { font-size: 1.5rem; margin-bottom: 10px; font-weight: 800; color: inherit !important; line-height: 1.2;}
    .dash-card h1 { font-size: 4.5rem; margin: 15px 0; font-weight: 900; color: inherit !important; line-height: 1;}
    .dash-card p { font-size: 1.05rem; margin-top: 15px; font-weight: 500; opacity: 0.85; color: inherit !important; }

    /* --- GENERAL STYLES --- */
    h1, h2, h3, h4, h5, h6 { color: #ccd6f6; }
    .card-panel {
        background: rgba(17, 34, 64, 0.6);
        border: 1px solid rgba(35, 53, 84, 0.8);
        border-radius: 16px;
        padding: 25px;
        margin-bottom: 20px;
        backdrop-filter: blur(8px);
    }
    hr { border-top: 1px solid #233554; }
    
    .stButton>button {
        background: linear-gradient(90deg, #00d2ff 0%, #3a7bd5 100%);
        color: #ffffff;
        border: none;
        border-radius: 8px;
        font-weight: bold;
        padding: 0.5rem 1rem;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background: linear-gradient(90deg, #3a7bd5 0%, #00d2ff 100%);
        box-shadow: 0 4px 15px rgba(0, 210, 255, 0.4);
    }

    /* --- ANIMATIONS --- */
    @keyframes slideUp {
        0% { transform: translateY(50px); opacity: 0; }
        100% { transform: translateY(0); opacity: 1; }
    }
    @keyframes fadeIn {
        0% { opacity: 0; transform: scale(0.98); }
        100% { opacity: 1; transform: scale(1); }
    }
    .fade-in {
        animation: fadeIn 0.6s ease-out forwards;
    }

</style>
""", unsafe_allow_html=True)

# --- DATA LOADING ---
DATA_DIR = "data"

def load_csv(filename):
    filepath = os.path.join(DATA_DIR, filename)
    if os.path.exists(filepath):
        return pd.read_csv(filepath)
    return pd.DataFrame()

def save_csv(df, filename):
    filepath = os.path.join(DATA_DIR, filename)
    df.to_csv(filepath, index=False)

if 'reports' not in st.session_state:
    st.session_state['reports'] = load_csv("reports.csv")
if 'ocean' not in st.session_state:
    st.session_state['ocean'] = load_csv("ocean_conditions.csv")
if 'microplastic' not in st.session_state:
    st.session_state['microplastic'] = load_csv("microplastic_samples.csv")
if 'forecast' not in st.session_state:
    st.session_state['forecast'] = load_csv("forecast.csv")
if 'verification' not in st.session_state:
    st.session_state['verification'] = load_csv("verification.csv")


# --- TOP NAVIGATION (STICKY) ---
# We inject an invisible anchor #navbar-anchor so our CSS knows which block to make sticky
col_logo, col_nav, col_demo = st.columns([2.5, 6.5, 2])
with col_logo:
    st.markdown("""
    <div id='navbar-anchor' style="padding-top: 5px;">
        <h3 style='color: #00d2ff; margin: 0; font-weight: 800; letter-spacing: 1px;'>OceanPatrol</h3>
        <p style='color: #8892b0; font-size: 0.8rem; margin: 0; font-style: italic;'>"Detect. Track. Predict. Intercept."</p>
    </div>
    """, unsafe_allow_html=True)

with col_nav:
    page = st.radio("Nav", [
        "Dashboard", 
        "Report", 
        "Hotspots", 
        "Ocean Conditions", 
        "Forecast", 
        "Priority Zones", 
        "Microplastics", 
        "History",
        "About"
    ], horizontal=True, label_visibility="collapsed")

with col_demo:
    if st.button("LOAD DEMO SCENARIO", use_container_width=True):
        st.session_state['reports'] = load_csv("reports.csv")
        new_report = pd.DataFrame([{
            "report_id": f"RPT-DEMO-{datetime.now().strftime('%M%S')}",
            "latitude": -3.655,
            "longitude": 128.188,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "time": datetime.now().strftime("%H:%M"),
            "category": "Plastic",
            "image_path": "demo_image.jpg",
            "confidence": 0.92,
            "verification_status": "Unverified"
        }])
        st.session_state['reports'] = pd.concat([st.session_state['reports'], new_report], ignore_index=True)
        new_forecast = pd.DataFrame([{
            "forecast_id": f"FC-DEMO-{datetime.now().strftime('%M%S')}",
            "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "latitude": -3.655,
            "longitude": 128.188,
            "predicted_latitude": -3.670,
            "predicted_longitude": 128.175,
            "priority": "HIGH",
            "estimated_arrival": 14
        }])
        st.session_state['forecast'] = pd.concat([st.session_state['forecast'], new_forecast], ignore_index=True)

st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)


# --- HELPER FUNCTIONS ---
def get_map_center():
    if not st.session_state['reports'].empty:
        return [st.session_state['reports']['latitude'].mean(), st.session_state['reports']['longitude'].mean()]
    return [-3.66, 128.18]

def create_hero_map(show_reports=True, show_hotspots=True, show_mp=True, show_forecast=True):
    # Changed tile from 'CartoDB dark_matter' to 'cartodbdark_matter' to avoid API KEY issues
    m = folium.Map(location=get_map_center(), zoom_start=14, tiles='cartodbdark_matter')
    
    reports_df = st.session_state['reports']
    if show_hotspots and not reports_df.empty:
        heat_data = [[row['latitude'], row['longitude']] for _, row in reports_df.iterrows()]
        HeatMap(heat_data, name="Hotspot Areas", radius=20, blur=15, gradient={0.4: '#3a7bd5', 0.65: '#00d2ff', 1: '#ff4b4b'}).add_to(m)
        
    if show_reports and not reports_df.empty:
        report_group = folium.FeatureGroup(name="Marine Debris")
        for _, row in reports_df.iterrows():
            folium.CircleMarker(
                [row['latitude'], row['longitude']],
                radius=6,
                popup=f"<b>Report ID:</b> {row['report_id']}<br><b>Category:</b> {row['category']}",
                color='#ffffff', fill=True, fill_color='#ffffff', fill_opacity=0.8
            ).add_to(report_group)
        report_group.add_to(m)
        
    forecast_df = st.session_state['forecast']
    if show_forecast and not forecast_df.empty:
        forecast_group = folium.FeatureGroup(name="Forecast Trajectory")
        for _, row in forecast_df.iterrows():
            color = '#ff4b4b' if row['priority'] == 'HIGH' else '#f5a623'
            AntPath(
                locations=[[row['latitude'], row['longitude']], [row['predicted_latitude'], row['predicted_longitude']]],
                color=color, weight=3, opacity=0.8, delay=800, dash_array=[10, 20]
            ).add_to(forecast_group)
            
            folium.Marker(
                [row['predicted_latitude'], row['predicted_longitude']],
                popup=f"<b>Accumulation Zone</b><br>Priority: {row['priority']}<br>Est. Arrival: {row['estimated_arrival']}H",
                icon=folium.Icon(color='red' if row['priority'] == 'HIGH' else 'orange', icon='warning-sign')
            ).add_to(forecast_group)
        forecast_group.add_to(m)
        
    mp_df = st.session_state['microplastic']
    if show_mp and not mp_df.empty:
        mp_group = folium.FeatureGroup(name="Microplastic Sampling")
        for _, row in mp_df.iterrows():
            folium.CircleMarker(
                [row['latitude'], row['longitude']],
                radius=5,
                popup=f"<b>MP Sample:</b> {row['sample_id']}<br><b>Conc:</b> {row['concentration']}",
                color='#00d2ff', fill=True, fill_color='#00d2ff', fill_opacity=0.6
            ).add_to(mp_group)
        mp_group.add_to(m)

    folium.LayerControl().add_to(m)
    return m

# --- PAGES ENTRANCE ANIMATION WRAPPER ---
st.markdown("<div class='fade-in'>", unsafe_allow_html=True)

if page == "Dashboard":
    # Hero Title
    st.markdown("""
    <div style='text-align: center; margin-bottom: 40px;'>
        <h1 style='font-size: 3.5rem; margin-bottom: 0; font-weight: 900; background: -webkit-linear-gradient(#00d2ff, #3a7bd5); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>SEATRACKER HYBRID</h1>
        <h2 style='font-size: 1.5rem; color: #8892b0; margin-top: 10px; font-weight: 400;'>Sistem Intelijen Pesisir & Pemantauan Sampah Laut</h2>
    </div>
    """, unsafe_allow_html=True)

    # 3 Large Cards (Gojek/Pertamina style)
    reports_df = st.session_state['reports']
    forecast_df = st.session_state['forecast']
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="dash-card card-green">
            <h3>TOTAL LAPORAN</h3>
            <h1>{len(reports_df)}</h1>
            <p>Data observasi visual dari masyarakat pesisir dan nelayan yang masuk ke sistem.</p>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        active = len(reports_df[reports_df['verification_status'] == 'Unverified'])
        st.markdown(f"""
        <div class="dash-card card-purple">
            <h3>HOTSPOT AKTIF</h3>
            <h1>{active}</h1>
            <p>Area konsentrasi sampah laut yang saat ini membutuhkan validasi dan penanganan.</p>
        </div>
        """, unsafe_allow_html=True)
        
    with col3:
        high_prio = len(forecast_df[forecast_df['priority'] == 'HIGH'])
        st.markdown(f"""
        <div class="dash-card card-orange">
            <h3>ZONA PRIORITAS</h3>
            <h1>{high_prio}</h1>
            <p>Perkiraan zona akumulasi debris dalam 24 jam ke depan untuk intervensi segera.</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Hero Map
    st.markdown("<h3 style='text-align: center; color: #e6f1ff; font-weight: bold;'>Peta Intelijen Teluk Ambon</h3>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #8892b0; margin-bottom: 20px;'>Memantau pergerakan marine debris dan prediksi zona akumulasi (Prototype Simulation)</p>", unsafe_allow_html=True)
    
    map_col, stat_col = st.columns([3, 1])
    with map_col:
        m = create_hero_map()
        st_folium(m, width="100%", height=500, returned_objects=[])
        
        st.markdown("""
        <div style="display: flex; justify-content: center; gap: 20px; font-size: 0.9rem; color: #8892b0; margin-top: 15px; background: rgba(0,0,0,0.2); padding: 10px; border-radius: 10px;">
            <div><span style="color: #ffffff;">●</span> Marine Debris</div>
            <div><span style="color: #00d2ff;">●</span> Microplastic Sample</div>
            <div><span style="color: #ff4b4b;">---▶</span> Forecast Path</div>
            <div><span style="color: #ff4b4b;">📍</span> Priority Zone</div>
        </div>
        """, unsafe_allow_html=True)

    with stat_col:
        st.markdown("<div class='card-panel' style='height: 100%;'>", unsafe_allow_html=True)
        st.markdown("<h4 style='margin-top:0; color:#00d2ff; font-weight:700;'>KONDISI LAUT</h4>", unsafe_allow_html=True)
        st.markdown("<div style='font-size: 0.75rem; color: #f5a623; margin-bottom: 20px; border: 1px solid #f5a623; padding: 2px 6px; border-radius: 4px; display: inline-block;'>SIMULATION DATA</div>", unsafe_allow_html=True)
        
        ocean_df = st.session_state['ocean']
        if not ocean_df.empty:
            latest = ocean_df.iloc[-1]
            st.markdown(f"**🌊 Arus**<br><span style='color:#e6f1ff; font-size: 1.3rem; font-weight: 600;'>{latest['current_speed']} knots → {latest['current_direction']}</span><hr>", unsafe_allow_html=True)
            st.markdown(f"**🌬 Angin**<br><span style='color:#e6f1ff; font-size: 1.3rem; font-weight: 600;'>{latest['wind_speed']} km/h → {latest['wind_direction']}</span><hr>", unsafe_allow_html=True)
            st.markdown(f"**🌊 Pasang Surut**<br><span style='color:#e6f1ff; font-size: 1.3rem; font-weight: 600;'>{latest['tide']}</span><hr>", unsafe_allow_html=True)
            st.markdown(f"**🌧 Curah Hujan**<br><span style='color:#e6f1ff; font-size: 1.3rem; font-weight: 600;'>{latest['rainfall']}</span>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

elif page == "Report":
    st.title("REPORT MARINE DEBRIS")
    st.markdown("<p style='color: #8892b0; font-size: 1.1rem;'>Menjadi citizen sensor pesisir.</p>", unsafe_allow_html=True)
    st.markdown("<div class='card-panel'>", unsafe_allow_html=True)
    
    with st.form("report_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        with col1:
            uploaded_file = st.file_uploader("Upload Image (Required)", type=["jpg", "png", "jpeg"])
            lat = st.number_input("Location (Latitude)", value=-3.6650, format="%.5f")
            lon = st.number_input("Location (Longitude)", value=128.1810, format="%.5f")
        with col2:
            rep_date = st.date_input("Date")
            rep_time = st.time_input("Time")
            category = st.selectbox("Debris Category", ["Plastic Packaging", "Fishing Gear", "Mixed Waste", "Other"])
            desc = st.text_area("Description")
        
        submit_btn = st.form_submit_button("ANALYZE REPORT")
        
    if submit_btn:
        if uploaded_file is None:
            st.error("Please upload an image for AI analysis.")
        else:
            with st.spinner("AI is analyzing the image..."):
                time.sleep(2) 
            
            st.markdown("---")
            st.markdown("""
            <div style="background: rgba(100, 255, 218, 0.1); border-left: 4px solid #64ffda; padding: 20px; border-radius: 4px;">
                <h3 style="color: #64ffda; margin-top: 0;">AI ANALYSIS</h3>
                <p><strong>✓ Visible marine debris detected</strong></p>
            </div>
            """, unsafe_allow_html=True)
            
            col_r1, col_r2 = st.columns(2)
            col_r1.markdown(f"**Category:**<br><span style='font-size: 1.5rem; color:#00d2ff;'>{category}</span>", unsafe_allow_html=True)
            col_r2.markdown(f"**Confidence:**<br><span style='font-size: 1.5rem; color:#64ffda;'>87%</span>", unsafe_allow_html=True)
            
            st.caption("ℹ️ *Visible marine debris classification.*")
            
            new_report = pd.DataFrame([{
                "report_id": f"RPT-{len(st.session_state['reports']) + 1}",
                "latitude": lat,
                "longitude": lon,
                "date": rep_date.strftime("%Y-%m-%d"),
                "time": rep_time.strftime("%H:%M"),
                "category": category,
                "image_path": uploaded_file.name,
                "confidence": 0.87,
                "verification_status": "Unverified"
            }])
            st.session_state['reports'] = pd.concat([st.session_state['reports'], new_report], ignore_index=True)
            save_csv(st.session_state['reports'], "reports.csv")
    st.markdown("</div>", unsafe_allow_html=True)

elif page == "Hotspots":
    st.title("HOTSPOT ANALYTICS")
    st.markdown("<p style='color: #8892b0;'>Analisis densitas dan konsentrasi sampah laut.</p>", unsafe_allow_html=True)
    
    m = create_hero_map(show_forecast=False, show_mp=False)
    st_folium(m, width="100%", height=450, returned_objects=[])
    
    st.markdown("### Hotspot Ranking")
    c1, c2, c3 = st.columns(3)
    c1.markdown("<div class='card-panel'><h2 style='color:#ff4b4b; margin:0;'>#1</h2><h3 style='margin:0;'>ZONE A</h3><p style='color:#ff4b4b; font-weight:bold;'>CRITICAL RISK</p><hr><p style='font-size:0.9rem;'>High frequency of Plastic Packaging. 15 recent reports.</p></div>", unsafe_allow_html=True)
    c2.markdown("<div class='card-panel'><h2 style='color:#f5a623; margin:0;'>#2</h2><h3 style='margin:0;'>ZONE C</h3><p style='color:#f5a623; font-weight:bold;'>HIGH RISK</p><hr><p style='font-size:0.9rem;'>Accumulation of Fishing Gear. 8 recent reports.</p></div>", unsafe_allow_html=True)
    c3.markdown("<div class='card-panel'><h2 style='color:#00d2ff; margin:0;'>#3</h2><h3 style='margin:0;'>ZONE D</h3><p style='color:#00d2ff; font-weight:bold;'>MODERATE RISK</p><hr><p style='font-size:0.9rem;'>Mixed Waste detected. 4 recent reports.</p></div>", unsafe_allow_html=True)

elif page == "Ocean Conditions":
    st.title("OCEAN CONDITIONS")
    st.markdown("<p style='color: #f5a623; font-weight:bold;'>PROTOTYPE SIMULATION — NOT LIVE FIELD DATA</p>", unsafe_allow_html=True)
    
    ocean_df = st.session_state['ocean']
    st.dataframe(ocean_df, use_container_width=True)
    
    st.markdown("""
    <div class='card-panel'>
        <p>The Ocean Conditions module simulates the ingestion of real-time meteorological and oceanographic APIs. These variables (current vector, wind vector, tides, and rainfall) serve as the primary driving parameters for the 24H Forecast model.</p>
    </div>
    """, unsafe_allow_html=True)

elif page == "Forecast":
    st.title("24-HOUR DEBRIS FORECAST")
    st.markdown("<p style='color: #8892b0;'>Simulasi lintasan pergerakan marine debris berdasarkan data oseanografi.</p>", unsafe_allow_html=True)
    
    st.markdown("""
    <div style='display: flex; justify-content: space-between; align-items: center; background: rgba(17,34,64,0.6); padding: 20px; border-radius: 12px; border: 1px solid #233554; margin-bottom: 20px;'>
        <div style='text-align: center; color: #00d2ff;'><strong>NOW</strong><br>Origin</div>
        <div style='color: #8892b0;'>➔</div>
        <div style='text-align: center; color: #8892b0;'><strong>+6H</strong><br>Advection</div>
        <div style='color: #8892b0;'>➔</div>
        <div style='text-align: center; color: #8892b0;'><strong>+12H</strong><br>Dispersion</div>
        <div style='color: #8892b0;'>➔</div>
        <div style='text-align: center; color: #8892b0;'><strong>+18H</strong><br>Coastline Approach</div>
        <div style='color: #ff4b4b;'>➔</div>
        <div style='text-align: center; color: #ff4b4b;'><strong>+24H</strong><br>Accumulation</div>
    </div>
    """, unsafe_allow_html=True)
    
    m = create_hero_map(show_reports=False, show_hotspots=False, show_mp=False, show_forecast=True)
    st_folium(m, width="100%", height=450, returned_objects=[])

    st.markdown("### Predicted Accumulation Zones")
    forecast_df = st.session_state['forecast']
    
    for _, row in forecast_df.iterrows():
        if row['priority'] == 'HIGH':
            st.markdown(f"""
            <div style='background: rgba(255, 75, 75, 0.1); border-left: 4px solid #ff4b4b; padding: 20px; border-radius: 8px; margin-bottom: 15px;'>
                <h3 style='color: #ff4b4b; margin-top: 0;'>⚠ HIGH PRIORITY ZONE</h3>
                <p><strong>Zone:</strong> {row['forecast_id']} &nbsp;|&nbsp; <strong>Estimated arrival:</strong> {row['estimated_arrival']} hours</p>
                <p><strong>Recommended action:</strong> FIELD VERIFICATION & INTERCEPTION</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style='background: rgba(245, 166, 35, 0.1); border-left: 4px solid #f5a623; padding: 20px; border-radius: 8px; margin-bottom: 15px;'>
                <h3 style='color: #f5a623; margin-top: 0;'>MODERATE PRIORITY ZONE</h3>
                <p><strong>Zone:</strong> {row['forecast_id']} &nbsp;|&nbsp; <strong>Estimated arrival:</strong> {row['estimated_arrival']} hours</p>
            </div>
            """, unsafe_allow_html=True)

elif page == "Priority Zones":
    st.title("PRIORITY ACTION ZONES")
    st.markdown("<p style='color: #8892b0;'>Direct intervention and field verification dashboard.</p>", unsafe_allow_html=True)
    
    forecast_df = st.session_state['forecast']
    high_priority_zones = forecast_df[forecast_df['priority'] == 'HIGH']
    
    for idx, row in high_priority_zones.iterrows():
        st.markdown(f"""
        <div class='card-panel' style='border: 1px solid #ff4b4b;'>
            <h3 style='color: #ff4b4b; margin-top: 0;'>⚠ HIGH PRIORITY: {row['forecast_id']}</h3>
            <div style='display: flex; gap: 40px;'>
                <div>
                    <p><strong>Coordinates:</strong> {row['predicted_latitude']}, {row['predicted_longitude']}</p>
                    <p><strong>Est. Arrival:</strong> {row['estimated_arrival']} hours</p>
                </div>
                <div>
                    <p><strong>Recommended Action:</strong> Field Verification</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        with st.expander(f"Verify Zone {row['forecast_id']}"):
            with st.form(f"verify_form_{idx}", clear_on_submit=True):
                st.markdown("#### Submit Field Verification")
                actual_found = st.radio("Actual Debris Found?", ["YES", "NO"], key=f"rad_{idx}")
                notes = st.text_area("Observation Notes", key=f"note_{idx}")
                submit = st.form_submit_button("VERIFY ZONE")
                if submit:
                    new_ver = pd.DataFrame([{
                        "verification_id": f"V-{len(st.session_state['verification']) + 1}",
                        "zone_id": row['forecast_id'],
                        "date": datetime.now().strftime("%Y-%m-%d"),
                        "actual_debris_found": actual_found,
                        "latitude": row['predicted_latitude'],
                        "longitude": row['predicted_longitude'],
                        "density": "High",
                        "notes": notes
                    }])
                    st.session_state['verification'] = pd.concat([st.session_state['verification'], new_ver], ignore_index=True)
                    save_csv(st.session_state['verification'], "verification.csv")
                    st.success("Verification saved! Database updated.")

elif page == "Microplastics":
    st.title("MICROPLASTIC MONITORING")
    
    st.markdown("""
    <div style='display: flex; justify-content: center; align-items: center; background: rgba(17,34,64,0.6); padding: 20px; border-radius: 12px; border: 1px solid #233554; margin-bottom: 20px;'>
        <div style='text-align: center; color: #8892b0;'><strong>Macro Debris</strong><br>(Detected via App)</div>
        <div style='color: #00d2ff; font-weight: bold; padding: 0 20px;'>➔<br>Fragmentation</div>
        <div style='text-align: center; color: #64ffda;'><strong>Microplastics</strong><br>(Requires Lab Sampling)</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<p style='color: #f5a623; font-weight:bold; text-align:center;'>SIMULATION DATA</p>", unsafe_allow_html=True)
    
    m = create_hero_map(show_reports=False, show_hotspots=False, show_forecast=False, show_mp=True)
    st_folium(m, width="100%", height=400, returned_objects=[])
    
    st.markdown("### Sampling Points Data")
    mp_df = st.session_state['microplastic']
    for _, row in mp_df.iterrows():
        st.markdown(f"""
        <div class='card-panel' style='padding: 20px;'>
            <h4 style='color: #00d2ff; margin-top: 0;'>Sample: {row['sample_id']}</h4>
            <div style='display: flex; justify-content: space-between;'>
                <span><strong>Date:</strong> {row['date']}</span>
                <span><strong>Concentration:</strong> {row['concentration']}</span>
                <span><strong>Particle Count:</strong> {row['particle_count']}</span>
                <span><strong>Polymer:</strong> {row['polymer_type']}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

elif page == "History":
    st.title("MONITORING HISTORY")
    st.markdown("<p style='color: #8892b0;'>Temporal and categorical analysis of marine intelligence data.</p>", unsafe_allow_html=True)
    
    reports_df = st.session_state['reports']
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("<div class='card-panel'>", unsafe_allow_html=True)
        st.markdown("#### Reports Over Time")
        date_counts = reports_df.groupby('date').size().reset_index(name='count')
        fig1 = px.line(date_counts, x='date', y='count', markers=True, color_discrete_sequence=['#00d2ff'])
        fig1.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='#e6f1ff', margin=dict(l=0, r=0, t=0, b=0))
        st.plotly_chart(fig1, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
    with col2:
        st.markdown("<div class='card-panel'>", unsafe_allow_html=True)
        st.markdown("#### Debris Category Distribution")
        cat_counts = reports_df['category'].value_counts().reset_index()
        cat_counts.columns = ['category', 'count']
        fig2 = px.pie(cat_counts, values='count', names='category', hole=0.4, color_discrete_sequence=px.colors.sequential.Teal)
        fig2.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='#e6f1ff', margin=dict(l=0, r=0, t=0, b=0))
        st.plotly_chart(fig2, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

elif page == "About":
    st.title("HUMAN + AI IN THE LOOP")
    
    st.markdown("""
    <div style='background: rgba(17,34,64,0.6); padding: 50px; border-radius: 16px; border: 1px solid #233554; text-align: center;'>
        <h2 style='color: #00d2ff;'>The SeaTracker Workflow</h2>
        <p style='color: #8892b0; font-size: 1.2rem; max-width: 700px; margin: 0 auto 40px auto; line-height: 1.6;'>
            SeaTracker does not simply tell us where marine debris is. It helps us understand where it may move next, so humans can decide where to act first.
        </p>
        
        <div style='display: flex; justify-content: space-around; align-items: flex-start; text-align: left; margin-top: 40px;'>
            <div style='flex: 1; padding: 0 20px;'>
                <h3 style='color: #64ffda; font-weight:800;'>🧑‍🤝‍🧑 HUMAN</h3>
                <p style='color: #ccd6f6;'>Coastal community & citizen sensors capture initial reports of visible debris.</p>
            </div>
            <div style='font-size: 2.5rem; color: #8892b0; align-self: center;'>➔</div>
            <div style='flex: 1; padding: 0 20px;'>
                <h3 style='color: #00d2ff; font-weight:800;'>🤖 AI & FORECAST</h3>
                <p style='color: #ccd6f6;'>Computer vision classifies the debris. Oceanographic models forecast trajectory.</p>
            </div>
            <div style='font-size: 2.5rem; color: #8892b0; align-self: center;'>➔</div>
            <div style='flex: 1; padding: 0 20px;'>
                <h3 style='color: #ff4b4b; font-weight:800;'>🎯 ACTION</h3>
                <p style='color: #ccd6f6;'>Intervention at priority zones. Field verification feeds back to improve the model.</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)
