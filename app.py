import copy
import math
import streamlit as st
import folium
from streamlit_folium import st_folium

from solver import (
    Stop,
    DUMMY_COURIER_POSITION,
    DUMMY_PACKAGES,
    fetch_osrm_matrix,
    fetch_osrm_route_geometry,
    solve_tsp,
    estimate_savings,
    build_google_maps_url,
    VEHICLES,
    geocode_address,
)

st.set_page_config(
    page_title="KetKet Paket",
    page_icon="📦",
    layout="centered",
    initial_sidebar_state="collapsed",
)

CREAM   = "#F9F6F0"
BROWN   = "#3D2A1C"
TERRA   = "#E05A47"
NAVY    = "#1D3557"
LIGHT   = "#FFFFFF"
MUTED   = "#B5A99A"
CARD_BG = "#FFFFFF"
BORDER  = "#E8E0D6"

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=DM+Serif+Display&display=swap');

html, body, [class*="css"] {{
    font-family: 'Plus Jakarta Sans', sans-serif;
    background-color: #F8FAFC !important; 
    color: {BROWN};
}}

html, body {{
    overflow-y: auto !important;
    overflow-x: hidden !important;
    height: auto !important;
    margin: 0;
    padding: 0;
}}

.stApp {{
    background-color: #FFFFFF !important; 
    max-width: 480px;
    margin: 0 auto;
    overflow-y: auto !important;
    overflow-x: hidden !important;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    box-shadow: 0 0 30px rgba(0,0,0,0.05); 
}}

::-webkit-scrollbar {{
    width: 6px;
    height: 6px;
}}
::-webkit-scrollbar-track {{
    background: #F1F5F9;
}}
::-webkit-scrollbar-thumb {{
    background: {MUTED};
    border-radius: 3px;
}}
::-webkit-scrollbar-thumb:hover {{
    background: {BROWN};
}}

#MainMenu, footer, header {{ visibility: hidden; }}
.block-container {{ padding: 0 1rem 9rem 1rem !important; }}

.kk-header {{
    background: #FFFFFF !important;
    border-bottom: 1.5px solid {BORDER} !important;
    padding: 14px 20px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: space-between !important;
    margin: -1rem -1rem 1.2rem -1rem !important;
    border-radius: 0 !important;
}}

.kk-header-logo {{
    display: flex;
    align-items: center;
    gap: 12px;
}}
.logo-text {{
    display: flex;
    flex-direction: column;
    line-height: 1.05;
}}
.logo-title {{
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-weight: 800;
    font-size: 1.35rem;
    color: #3D2A1C;
    letter-spacing: -0.5px;
}}
.logo-subtitle {{
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-weight: 700;
    font-size: 1.25rem;
    color: #705342;
    letter-spacing: -0.5px;
    margin-top: -1px;
}}
.kk-header .profile-btn {{
    width: 32px;
    height: 32px;
    border-radius: 50%;
    border: 1.5px solid #3D2A1C;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #3D2A1C;
    font-size: 1.05rem;
    cursor: pointer;
    transition: background-color 0.2s, transform 0.2s;
}}
.kk-header .profile-btn:hover {{
    background-color: rgba(61, 42, 28, 0.08);
    transform: scale(1.05);
}}
.kk-header .profile-btn:active {{
    transform: scale(0.95);
}}

.kk-section-label {{
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: {MUTED};
    margin: 1rem 0 0.5rem 0;
}}

.kk-queue-header {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 1.2rem;
    padding: 0 4px;
}}
.kk-queue-title {{
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-weight: 800;
    font-size: 1.45rem;
    color: {BROWN};
    letter-spacing: -0.3px;
}}
.kk-sort-icon {{
    display: flex;
    align-items: center;
    cursor: pointer;
}}

.timeline-col {{
    display: flex;
    flex-direction: column;
    align-items: center;
    position: relative;
    height: 100%;
    min-height: 80px;
}}
.timeline-col::after {{
    content: '';
    position: absolute;
    top: 36px;
    bottom: -15px;
    width: 0;
    border-left: 2px dashed #E2E8F0;
    z-index: 1;
}}
.timeline-col.last::after {{
    display: none;
}}
.timeline-badge {{
    position: relative;
    z-index: 2;
    width: 36px;
    height: 36px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 0.95rem;
    color: #FFFFFF;
}}
.timeline-badge.green {{
    background-color: #0F8A5F;
}}
.timeline-badge.brown {{
    background-color: #705342;
}}
.timeline-text {{
    display: flex;
    flex-direction: column;
    padding-top: 6px;
    padding-bottom: 12px;
}}
.timeline-title {{
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-weight: 700;
    font-size: 0.98rem;
    color: #3D2A1C;
    line-height: 1.25;
}}
.timeline-subtitle {{
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-weight: 400;
    font-size: 0.82rem;
    color: #64748B;
    line-height: 1.45;
    margin-top: 4px;
}}

div.timeline-del-container button {{
    background: transparent !important;
    border: none !important;
    color: #EF4444 !important;
    font-size: 1.25rem !important;
    padding: 0 !important;
    margin-top: 6px !important;
    box-shadow: none !important;
    cursor: pointer;
}}

.kk-pkg-card {{
    background: {CARD_BG};
    border: 1.5px solid {BORDER};
    border-radius: 14px;
    padding: 13px 16px;
    margin-bottom: 10px;
    display: flex;
    align-items: flex-start;
    gap: 12px;
    box-shadow: 0 1px 4px rgba(61,42,28,0.06);
}}
.kk-pkg-icon {{
    width: 38px; height: 38px;
    border-radius: 10px;
    background: #F1F5F9;
    border: 1.5px solid {BORDER};
    display: flex; align-items: center; justify-content: center;
    font-size: 1rem;
    flex-shrink: 0;
    margin-top: 2px;
}}
.kk-pkg-done .kk-pkg-icon {{ background: #e8f5e9; border-color: #a5d6a7; }}
.kk-pkg-name {{
    font-weight: 700;
    font-size: 0.92rem;
    color: {BROWN};
    line-height: 1.3;
}}
.kk-pkg-addr {{
    font-size: 0.78rem;
    color: {MUTED};
    margin-top: 2px;
    line-height: 1.4;
}}
.kk-order-badge {{
    background: {TERRA};
    color: white;
    border-radius: 50%;
    width: 22px; height: 22px;
    font-size: 0.7rem;
    font-weight: 800;
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0;
    margin-top: 2px;
}}
.kk-order-badge.depot {{ background: {BROWN}; }}

[data-testid="stButton"]:has(button[kind="primary"]) {{
    position: fixed !important;
    bottom: 4.2rem !important;
    left: 50% !important;
    transform: translateX(-50%) !important;
    width: calc(100% - 2rem) !important;
    max-width: 448px !important;
    z-index: 998 !important;
    box-sizing: border-box !important;
    background: linear-gradient(to top, #FFFFFF 85%, transparent) !important;
    padding: 10px 0 4px 0 !important;
}}
[data-testid="stButton"]:has(button[kind="primary"]) button {{
    background-color: #705342 !important;
    color: #FFFFFF !important;
    border-radius: 12px !important;
    padding: 15px 20px !important;
    font-weight: 700 !important;
    font-size: 1.05rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
    width: 100% !important;
    border: none !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    gap: 8px !important;
    box-shadow: 0 4px 14px rgba(112, 83, 66, 0.25) !important;
    transition: transform .15s, background-color 0.2s !important;
}}
[data-testid="stButton"]:has(button[kind="primary"]) button:hover {{
    background-color: #5D4037 !important;
}}
[data-testid="stButton"]:has(button[kind="primary"]) button:active {{
    transform: scale(0.98) !important;
}}

div.btn-reset-container button {{
    background-color: #705342 !important;
    color: #FFFFFF !important;
    border-radius: 12px !important;
    padding: 13px 20px !important;
    font-weight: 700 !important;
    font-size: 1rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
    width: 100% !important;
    border: none !important;
    box-shadow: 0 3px 10px rgba(112, 83, 66, 0.2) !important;
    transition: transform .15s, background-color 0.2s !important;
}}
div.btn-reset-container button:hover {{
    background-color: #5D4037 !important;
}}

.kk-nav-card {{
    background: {CARD_BG};
    border: 1.5px solid {BORDER};
    border-radius: 16px;
    padding: 16px;
    margin-bottom: 12px;
    box-shadow: 0 1px 4px rgba(61,42,28,0.06);
}}
.kk-nav-dest-label {{
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 1.5px;
    color: {TERRA};
    text-transform: uppercase;
    margin-bottom: 4px;
}}
.kk-nav-dest-name {{
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-weight: 700;
    font-size: 1.15rem;
    color: {BROWN};
    line-height: 1.3;
}}
.kk-nav-dist {{
    background: #F1F5F9;
    border-radius: 10px;
    padding: 8px 12px;
    text-align: center;
    font-weight: 800;
    font-size: 0.9rem;
    color: {BROWN};
    line-height: 1.3;
    min-width: 58px;
}}
.kk-recipient-row {{
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 10px 12px;
    background: #F1F5F9;
    border-radius: 10px;
    margin: 10px 0;
    font-size: 0.82rem;
    color: {BROWN};
}}

.kk-stat-card {{
    background: {CARD_BG};
    border: 1.5px solid {BORDER};
    border-radius: 14px;
    padding: 16px 18px;
    margin-bottom: 10px;
    display: flex;
    align-items: center;
    justify-content: space-between;
}}
.kk-stat-label {{
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: {MUTED};
    margin-bottom: 4px;
}}
.kk-stat-value {{
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-weight: 800;
    font-size: 1.5rem;
    color: {BROWN};
    line-height: 1.1;
}}
.kk-stat-icon {{
    width: 42px; height: 42px;
    border-radius: 12px;
    background: #F1F5F9;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.1rem;
}}

.kk-celebration {{
    text-align: center;
    padding: 28px 16px 20px;
}}
.kk-celeb-icon {{
    font-size: 3.5rem;
    background: #F1F5F9;
    border-radius: 24px;
    width: 88px; height: 88px;
    display: flex; align-items: center; justify-content: center;
    margin: 0 auto 16px;
}}
.kk-celeb-title {{
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-weight: 800;
    font-size: 1.7rem;
    color: {BROWN};
    margin-bottom: 8px;
}}
.kk-celeb-sub {{
    font-size: 0.85rem;
    color: {MUTED};
    line-height: 1.5;
    max-width: 280px;
    margin: 0 auto;
}}

.stTabs [data-baseweb="tab-list"] {{
    background: #FFFFFF !important;
    border-radius: 16px 16px 0 0 !important;
    padding: 8px 16px !important;
    gap: 8px !important;
    border-top: 1.5px solid #E2E8F0 !important;
    border-left: none !important;
    border-right: none !important;
    border-bottom: none !important;
    position: fixed !important;
    bottom: 0 !important;
    left: 50% !important;
    transform: translateX(-50%) !important;
    width: 100% !important;
    max-width: 480px !important;
    z-index: 999 !important;
    box-shadow: 0 -4px 16px rgba(0,0,0,0.04) !important;
    box-sizing: border-box !important;
}}
.stTabs [data-baseweb="tab"] {{
    border-radius: 12px !important;
    font-size: 0.72rem !important;
    font-weight: 700 !important;
    color: #64748B !important;
    padding: 10px 8px !important;
    flex: 1 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    gap: 6px !important;
    background: transparent !important;
    border: none !important;
    transition: all 0.2s ease !important;
    min-width: 0 !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
}}
.stTabs [aria-selected="true"] {{
    background: #705342 !important;
    color: #FFFFFF !important;
}}
.stTabs [data-baseweb="tab-panel"] {{ padding-top: 0.2rem; }}
.stTabs [data-baseweb="tab-border"] {{
    display: none !important;
}}
.stTabs [data-baseweb="tab-highlight-container"] {{
    display: none !important;
}}

.stTextInput input {{
    border-radius: 12px !important;
    border: 1.5px solid #E2E8F0 !important;
    background: #FFFFFF !important;
    color: {BROWN} !important;
    font-size: 0.95rem !important;
    padding: 10px 14px !important;
    height: 44px !important;
}}

.stTextInput input::placeholder {{
    color: #64748B !important;
    -webkit-text-fill-color: #64748B !important;
    opacity: 1 !important;
}}
.stTextInput input::-webkit-input-placeholder {{
    color: #64748B !important;
    -webkit-text-fill-color: #64748B !important;
    opacity: 1 !important;
}}
.stTextInput input::-moz-placeholder {{
    color: #64748B !important;
    opacity: 1 !important;
}}
.stTextInput input:-ms-input-placeholder {{
    color: #64748B !important;
    opacity: 1 !important;
}}
.stTextInput input:focus {{
    border-color: #705342 !important;
    box-shadow: 0 0 0 3px rgba(112, 83, 66, 0.15) !important;
}}

[data-testid="stColumn"]:has([class*="st-key-btn-add-pkg"]),
[data-testid="stColumn"]:has([class*="st-key-btn_add_pkg"]),
[data-testid="stColumn"]:has(.st-key-btn-add-pkg),
[data-testid="stColumn"]:has(.st-key-btn_add_pkg) {{
    display: flex !important;
    align-items: flex-start !important;
}}
[data-testid="stColumn"]:has([class*="st-key-btn-add-pkg"]) [data-testid="stButton"],
[data-testid="stColumn"]:has([class*="st-key-btn_add_pkg"]) [data-testid="stButton"],
[data-testid="stColumn"]:has(.st-key-btn-add-pkg) [data-testid="stButton"],
[data-testid="stColumn"]:has(.st-key-btn_add_pkg) [data-testid="stButton"] {{
    width: 100% !important;
}}
[class*="st-key-btn-add-pkg"] button,
[class*="st-key-btn_add_pkg"] button,
.st-key-btn-add-pkg button,
.st-key-btn_add_pkg button {{
    height: 104px !important;
    font-size: 1.8rem !important;
    font-weight: 700 !important;
    background-color: #705342 !important;
    color: #FFFFFF !important;
    border-radius: 8px !important;
    border: none !important;
    width: 100% !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    box-shadow: 0 4px 10px rgba(112, 83, 66, 0.2) !important;
    transition: transform 0.15s, background-color 0.2s !important;
}}
[class*="st-key-btn-add-pkg"] button:hover,
[class*="st-key-btn_add_pkg"] button:hover,
.st-key-btn-add-pkg button:hover,
.st-key-btn_add_pkg button:hover {{
    background-color: #5D4037 !important;
}}
[class*="st-key-btn-add-pkg"] button:active,
[class*="st-key-btn_add_pkg"] button:active,
.st-key-btn-add-pkg button:active,
.st-key-btn_add_pkg button:active {{
    transform: scale(0.96) !important;
}}

[data-testid="stColumn"]:has([class*="st-key-del-"]),
[data-testid="stColumn"]:has([class*="st-key-del_"]) {{
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}}
[class*="st-key-del-"] button,
[class*="st-key-del_"] button {{
    background: transparent !important;
    border: none !important;
    color: #EF4444 !important;
    font-size: 1.25rem !important;
    padding: 0 !important;
    margin-top: 0px !important;
    line-height: 1 !important;
    box-shadow: none !important;
    cursor: pointer !important;
}}

.stSelectbox > div > div {{
    border-radius: 12px !important;
    border: 1.5px solid #E2E8F0 !important;
    background: #FFFFFF !important;
    font-size: 0.88rem !important;
}}

[data-testid="stExpander"] {{
    background-color: #FFFFFF !important;
    border: 1.5px solid {BORDER} !important;
    border-radius: 12px !important;
    margin-top: 10px !important;
    margin-bottom: 10px !important;
    box-shadow: 0 1px 4px rgba(61,42,28,0.06) !important;
}}
[data-testid="stExpander"] summary {{
    color: #3D2A1C !important;
    font-weight: 700 !important;
    font-size: 0.9rem !important;
}}
[data-testid="stExpander"] summary p {{
    color: #3D2A1C !important;
    font-weight: 700 !important;
    font-size: 0.9rem !important;
}}
[data-testid="stExpander"] summary svg {{
    fill: #3D2A1C !important;
}}

.kk-vehicle-row {{
    display: flex;
    gap: 8px;
    margin: 0.6rem 0 1rem 0;
    overflow-x: auto;
    padding-bottom: 4px;
    -webkit-overflow-scrolling: touch;
    scrollbar-width: none;
}}
.kk-vehicle-row::-webkit-scrollbar {{ display: none; }}
.kk-vehicle-pill {{
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 8px 14px;
    border-radius: 50px;
    border: 1.5px solid #E2E8F0;
    background: #F8FAFC;
    font-size: 0.82rem;
    font-weight: 600;
    color: #64748B;
    white-space: nowrap;
    cursor: pointer;
    flex-shrink: 0;
    transition: all 0.18s ease;
}}
.kk-vehicle-pill.active {{
    background: #705342;
    border-color: #705342;
    color: #FFFFFF;
    box-shadow: 0 3px 10px rgba(112, 83, 66, 0.25);
}}
.kk-vehicle-pill .pill-icon {{
    font-size: 1.05rem;
    line-height: 1;
}}
.kk-vehicle-label {{
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 1.2px;
    text-transform: uppercase;
    color: {MUTED};
    margin-bottom: 4px;
}}

[data-testid="stButton"] button[kind="secondary"] {{
    border-radius: 50px !important;
    border: 1.5px solid #E2E8F0 !important;
    background: #F8FAFC !important;
    color: #3D2A1C !important;
    font-size: 0.78rem !important;
    font-weight: 700 !important;
    padding: 7px 6px !important;
    transition: all 0.18s ease !important;
    box-shadow: none !important;
}}
[data-testid="stButton"] button[kind="secondary"]:hover {{
    border-color: #705342 !important;
    background: #FAF4EE !important;
    color: #705342 !important;
}}
[data-testid="stButton"] button[kind="secondary"]:disabled,
[data-testid="stButton"] button[kind="secondary"][disabled] {{
    background: #705342 !important;
    border-color: #705342 !important;
    color: #FFFFFF !important;
    opacity: 1 !important;
    box-shadow: 0 3px 10px rgba(112, 83, 66, 0.28) !important;
    cursor: default !important;
}}

.stSpinner > div {{ color: #705342 !important; }}

.stSuccess {{ border-radius: 12px; }}
.stWarning {{ border-radius: 12px; }}

div.btn-selesai-container button {{
    background-color: #FFFFFF !important;
    color: #1D3557 !important;
    border: 2px solid #E8E0D6 !important;
    border-radius: 14px !important;
    padding: 14px 20px !important;
    font-weight: 700 !important;
    font-size: 0.92rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
    width: 100% !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    gap: 8px !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06) !important;
    transition: background-color 0.2s, border-color 0.2s !important;
}}
div.btn-selesai-container button:hover {{
    background-color: #F0FFF4 !important;
    border-color: #4CAF50 !important;
    color: #2E7D32 !important;
}}

@media (max-width: 400px) {{
    .kk-header {{
        padding: 10px 14px !important;
    }}
    .kk-queue-title {{
        font-size: 1.25rem;
    }}
    .kk-nav-card {{
        padding: 12px;
    }}
    .kk-nav-dest-name {{
        font-size: 1rem;
    }}
    .kk-nav-dist {{
        font-size: 0.8rem;
        padding: 6px 8px;
    }}
}}
</style>
""", unsafe_allow_html=True)

def init_state():
    if "packages" not in st.session_state:
        st.session_state.packages = copy.deepcopy(DUMMY_PACKAGES)
    if "courier" not in st.session_state:
        st.session_state.courier = copy.deepcopy(DUMMY_COURIER_POSITION)
    if "done_ids" not in st.session_state:
        st.session_state.done_ids = set()
    if "route_result" not in st.session_state:
        st.session_state.route_result = None
    if "dist_matrix" not in st.session_state:
        st.session_state.dist_matrix = None
    if "dur_matrix" not in st.session_state:
        st.session_state.dur_matrix = None
    if "route_geometry" not in st.session_state:
        st.session_state.route_geometry = None
    if "optimized" not in st.session_state:
        st.session_state.optimized = False
    if "nav_index" not in st.session_state:
        st.session_state.nav_index = 1   
    if "active_tab" not in st.session_state:
        st.session_state.active_tab = 0
    if "selected_vehicle" not in st.session_state:
        st.session_state.selected_vehicle = "motorcycle"

init_state()

def pending_packages() -> list:
    return [p for p in st.session_state.packages if p.stop_id not in st.session_state.done_ids]


def all_stops_for_solver() -> list:
    return [st.session_state.courier] + pending_packages()

import base64

def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except Exception:
        return ""

logo_base64 = get_base64_image("assets/logo.webp")
package_base64 = get_base64_image("assets/package.webp")
map_base64 = get_base64_image("assets/peta.webp")
data_base64 = get_base64_image("assets/data.webp")

st.markdown(f"""
<div class="kk-header">
<div class="kk-header-logo">
<img src="data:image/webp;base64,{logo_base64}" alt="Logo" style="height:50px;">
</div>
<div class="profile-btn">
<svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
<circle cx="12" cy="8" r="4" stroke="#3D2A1C" stroke-width="2"/>
<path d="M5 20C5 16.6863 8.13401 14 12 14C15.866 14 19 16.6863 19 20" stroke="#3D2A1C" stroke-width="2" stroke-linecap="round"/>
</svg>
</div>
</div>
""", unsafe_allow_html=True)

tab_daftar, tab_peta, tab_ringkasan = st.tabs(
    ["📋  Daftar Paket", "🗺️  Peta Rute", "📊  Ringkasan"]
)

with tab_daftar:
    st.markdown('<div class="kk-section-label">Tambah Alamat Baru</div>', unsafe_allow_html=True)

    col_inp, col_btn = st.columns([4, 1])
    with col_inp:
        new_recipient = st.text_input(
            label="",
            placeholder="Nama Penerima",
            label_visibility="collapsed",
            key="new_recipient_input",
        )
        new_addr = st.text_input(
            label="",
            placeholder="Alamat Lengkap",
            label_visibility="collapsed",
            key="new_address_input",
        )
    with col_btn:
        add_clicked = st.button("+", key="btn_add_pkg", use_container_width=True)

    if add_clicked and new_addr.strip():
        recipient_val = new_recipient.strip() if new_recipient.strip() else "Penerima Baru"
        with st.spinner("📍 Mencari koordinat alamat…"):
            coords = geocode_address(new_addr.strip())
        if coords:
            pkg_lat, pkg_lng = coords
            st.success(f"✅ Alamat '{new_addr.strip()[:30]}' berhasil ditambahkan!")
        else:
            pkg_lat = st.session_state.courier.lat
            pkg_lng = st.session_state.courier.lng
            st.warning(
                "⚠️ Alamat tidak ditemukan. Titik sementara diset ke lokasi gudang — "
                "harap edit atau gunakan alamat yang lebih lengkap (tambahkan nama kota)."
            )
        new_stop = Stop(
            name=recipient_val[:25],
            address=new_addr.strip(),
            lat=pkg_lat,
            lng=pkg_lng,
            recipient=recipient_val,
            stop_id=f"PKG_{len(st.session_state.packages)+1:03d}",
        )
        st.session_state.packages.append(new_stop)
        st.session_state.optimized = False
        st.session_state.route_result = None
        st.success(f"✅ Alamat '{new_addr.strip()[:30]}' berhasil ditambahkan!")
        st.rerun()

    st.markdown('<div class="kk-vehicle-label">Kendaraan</div>', unsafe_allow_html=True)
    vehicle_options = list(VEHICLES.keys())
    vcols = st.columns(len(vehicle_options))
    for i, vk in enumerate(vehicle_options):
        vcfg = VEHICLES[vk]
        is_active = (vk == st.session_state.selected_vehicle)
        label = f"{vcfg['icon']} {vcfg['name']}" if not is_active else f"{vcfg['icon']} {vcfg['name']}"
        with vcols[i]:
            if st.button(
                label,
                key=f"veh_btn_{vk}",
                use_container_width=True,
                disabled=is_active,
                type="secondary",
            ):
                st.session_state.selected_vehicle = vk
                st.session_state.optimized = False
                st.session_state.route_result = None
                st.rerun()

    pkgs = pending_packages()
    total_all = len(pkgs) + 1 if pkgs else 0
    done_count = len(st.session_state.done_ids)

    st.markdown(f"""
    <div class="kk-queue-header">
        <div class="kk-queue-title">Daftar Antrean ({total_all} Paket)</div>
        <div class="kk-sort-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M3 6H21M6 12H18M10 18H14" stroke="#705342" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if not pkgs:
        st.markdown(f"""
        <div style="text-align:center;padding:40px 0;">
            <img src="data:image/webp;base64,{package_base64}" alt="Package" style="width:80px;margin-bottom:16px;">
            <div style="font-weight:700;font-size:1.1rem;color:#64748B;">Belum ada paket dalam antrean</div>
            <div style="font-size:0.85rem;color:#94A3B8;margin-top:6px;">Tambah alamat baru di atas untuk memulai.</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        if st.session_state.optimized and st.session_state.route_result:
            ordered = [
                s for s in st.session_state.route_result["route_stops"]
                if s.stop_id != st.session_state.courier.stop_id
            ]
            # Add any pkgs not in route (edge case)
            in_route_ids = {s.stop_id for s in ordered}
            ordered += [p for p in pkgs if p.stop_id not in in_route_ids]
        else:
            ordered = pkgs

        st.markdown('<div class="timeline-container">', unsafe_allow_html=True)
        
        is_depot_last = (len(ordered) == 0)
        col_badge, col_text, col_del = st.columns([1.5, 8.5, 1])
        with col_badge:
            last_class = " last" if is_depot_last else ""
            st.markdown(f"""
            <div class="timeline-col{last_class}">
                <div class="timeline-badge green">A</div>
            </div>
            """, unsafe_allow_html=True)
        with col_text:
            st.markdown(f"""
            <div class="timeline-text">
                <div class="timeline-title">{st.session_state.courier.name}</div>
                <div class="timeline-subtitle">{st.session_state.courier.address}</div>
            </div>
            """, unsafe_allow_html=True)
        with col_del:
            st.write("")

        for idx, pkg in enumerate(ordered):
            is_last = (idx == len(ordered) - 1)
            col_badge, col_text, col_del = st.columns([1.5, 8.5, 1])
            with col_badge:
                last_class = " last" if is_last else ""
                st.markdown(f"""
                <div class="timeline-col{last_class}">
                    <div class="timeline-badge brown">{idx + 1}</div>
                </div>
                """, unsafe_allow_html=True)
            with col_text:
                st.markdown(f"""
                <div class="timeline-text">
                    <div class="timeline-title">{pkg.recipient or pkg.name}</div>
                    <div class="timeline-subtitle">{pkg.address}</div>
                </div>
                """, unsafe_allow_html=True)
            with col_del:
                if st.button("❌", key=f"del_{pkg.stop_id}", help=f"Hapus {pkg.recipient or pkg.name}"):
                    st.session_state.packages = [
                        p for p in st.session_state.packages if p.stop_id != pkg.stop_id
                    ]
                    st.session_state.optimized = False
                    st.session_state.route_result = None
                    st.rerun()
                
        st.markdown('</div>', unsafe_allow_html=True)

with tab_peta:

    if not st.session_state.optimized or not st.session_state.route_result:
        st.markdown(f"""
        <div style="text-align:center;padding:60px 0 40px;">
            <img src="data:image/webp;base64,{map_base64}" alt="Map" style="width:80px;margin-bottom:16px;">
            <div style="font-weight:700;font-size:1.15rem;color:#3D2A1C;">Rute belum dioptimalkan</div>
            <div style="font-size:0.85rem;color:#94A3B8;margin-top:6px;">Pergi ke tab Daftar Paket dan<br>tekan "Optimalkan Rute" terlebih dahulu.</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        result = st.session_state.route_result
        route_stops = result["route_stops"]  
        dur_mat = st.session_state.dur_matrix
        dist_mat = st.session_state.dist_matrix

        nav_idx = st.session_state.nav_index
        delivery_stops = [s for s in route_stops if s.stop_id != st.session_state.courier.stop_id]

        if nav_idx > len(delivery_stops):
            nav_idx = len(delivery_stops)

        courier = st.session_state.courier

        if nav_idx <= len(delivery_stops):
            target_now = delivery_stops[nav_idx - 1]
            centre_lat = (courier.lat + target_now.lat) / 2
            centre_lng = (courier.lng + target_now.lng) / 2
        else:
            centre_lat = courier.lat
            centre_lng = courier.lng

        m = folium.Map(
            location=[centre_lat, centre_lng],
            zoom_start=13,
            tiles="CartoDB Positron",
        )

        vehicle_cfg = VEHICLES.get(st.session_state.selected_vehicle, VEHICLES["motorcycle"])
        vehicle_icon = vehicle_cfg["icon"]

        folium.Marker(
            location=[courier.lat, courier.lng],
            popup="Posisi Kurir",
            tooltip="📍 Posisi Kurir",
            icon=folium.DivIcon(
                html=f"""
                <div style="background:{TERRA};color:white;border-radius:50%;
                     width:32px;height:32px;display:flex;align-items:center;
                     justify-content:center;font-size:14px;font-weight:700;
                     box-shadow:0 2px 8px rgba(0,0,0,0.3);border:2px solid white;">
                    {vehicle_icon}
                </div>""",
                icon_size=(32, 32),
                icon_anchor=(16, 16),
            ),
        ).add_to(m)

        for i, stop in enumerate(delivery_stops):
            order = i + 1
            is_next = (order == nav_idx)
            is_done = stop.stop_id in st.session_state.done_ids

            if is_done:
                bg = "#4CAF50"; txt = "✓"; border = "2px solid #2E7D32"
            elif is_next:
                bg = NAVY; txt = str(order); border = f"3px solid {TERRA}"
            else:
                bg = LIGHT; txt = str(order); border = "2px solid #ccc"

            color = "white" if (is_done or is_next) else BROWN
            folium.Marker(
                location=[stop.lat, stop.lng],
                popup=f"{stop.name}<br>{stop.address}<br>{stop.recipient}",
                tooltip=f"📦 {order}. {stop.name}",
                icon=folium.DivIcon(
                    html=f"""
                    <div style="background:{bg};color:{color};border-radius:50%;
                         width:28px;height:28px;display:flex;align-items:center;
                         justify-content:center;font-size:11px;font-weight:800;
                         box-shadow:0 2px 6px rgba(0,0,0,0.25);border:{border};">
                        {txt}
                    </div>""",
                    icon_size=(28, 28),
                    icon_anchor=(14, 14),
                ),
            ).add_to(m)

        road_geom = st.session_state.get("route_geometry")
        if road_geom and len(road_geom) > 1:
            # Draw full road geometry fetched from OSRM /route/v1
            folium.PolyLine(
                locations=road_geom,
                color=NAVY,
                weight=4,
                opacity=0.80,
                tooltip="Jalur TSP Optimal",
            ).add_to(m)
        else:
            all_route = [courier] + delivery_stops
            route_coords = [[s.lat, s.lng] for s in all_route]
            folium.PolyLine(
                locations=route_coords,
                color=NAVY,
                weight=3.5,
                opacity=0.75,
                dash_array="8 5",
                tooltip="Jalur TSP Optimal",
            ).add_to(m)

        st_folium(m, height=260, use_container_width=True, returned_objects=[])

        if nav_idx <= len(delivery_stops):
            target = delivery_stops[nav_idx - 1]

            # Compute distance/time for current segment
            all_stops_list = all_stops_for_solver()
            stops_map = {s.stop_id: i for i, s in enumerate(all_stops_list)}
            prev_idx = 0 if nav_idx == 1 else stops_map.get(delivery_stops[nav_idx - 2].stop_id, 0)
            curr_idx = stops_map.get(target.stop_id, 1)

            if dist_mat and len(dist_mat) > max(prev_idx, curr_idx):
                seg_dist_km = round(dist_mat[prev_idx][curr_idx] / 1000, 1)
                seg_dur_min = max(1, dur_mat[prev_idx][curr_idx] // 60)
            else:
                seg_dist_km = "—"
                seg_dur_min = "—"

            gmaps_url = build_google_maps_url(target, travelmode=vehicle_cfg["gmaps_mode"])

            card_html = (
                f'<div style="background:#FFFFFF;border:1.5px solid #E8E0D6;border-radius:16px;padding:16px;margin:12px 0 10px 0;box-shadow:0 1px 6px rgba(61,42,28,0.07);">'
                f'<div style="font-size:0.62rem;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;color:#B5A99A;margin-bottom:4px;">PENGANTARAN SEKARANG</div>'
                f'<div style="font-family:Plus Jakarta Sans,sans-serif;font-weight:800;font-size:1.45rem;color:#3D2A1C;line-height:1.2;margin-bottom:2px;">{target.recipient or target.name}</div>'
                f'<div style="font-size:0.82rem;color:#64748B;margin-bottom:12px;">{target.address}</div>'
                f'<div style="display:flex;align-items:center;background:#F8FAFC;border:1.5px solid #E8E0D6;border-radius:12px;padding:10px 0;">'
                f'<div style="flex:1;text-align:center;border-right:1.5px solid #E8E0D6;">'
                f'<div style="font-size:0.58rem;font-weight:700;letter-spacing:1.2px;text-transform:uppercase;color:#B5A99A;margin-bottom:4px;">JARAK</div>'
                f'<div style="font-size:0.98rem;font-weight:800;color:#3D2A1C;">&#128739; {seg_dist_km} KM</div>'
                f'</div>'
                f'<div style="flex:1;text-align:center;">'
                f'<div style="font-size:0.58rem;font-weight:700;letter-spacing:1.2px;text-transform:uppercase;color:#B5A99A;margin-bottom:4px;">ESTIMASI</div>'
                f'<div style="font-size:0.98rem;font-weight:800;color:#3D2A1C;">&#128336; {seg_dur_min} MNT</div>'
                f'</div>'
                f'</div>'
                f'</div>'
            )
            st.markdown(card_html, unsafe_allow_html=True)

            nav_btn_html = (
                f'<a href="{gmaps_url}" target="_blank" style="'
                'display:block;background:#705342;color:#FFFFFF;text-align:center;'
                'padding:15px 20px;border-radius:14px;'
                'font-family:Plus Jakarta Sans,sans-serif;font-weight:800;font-size:0.98rem;'
                'letter-spacing:1px;text-transform:uppercase;text-decoration:none;'
                'margin-bottom:10px;box-shadow:0 4px 14px rgba(112,83,66,0.28);">'
                '&#128506;&nbsp; MULAI NAVIGASI</a>'
            )
            st.markdown(nav_btn_html, unsafe_allow_html=True)

            done_col, _ = st.columns([1, 0.001])
            with done_col:
                st.markdown("<div class='btn-selesai-container'>", unsafe_allow_html=True)
                if st.button("✅  SELESAI ANTAR / TERKIRIM", key="btn_done_nav",
                             use_container_width=True, type="secondary"):
                    st.session_state.done_ids.add(target.stop_id)
                    st.session_state.nav_index += 1

                    remaining = pending_packages()
                    if remaining:
                        stops = all_stops_for_solver()
                        with st.spinner("Memperbarui rute…"):
                            dist_mat_new, dur_mat_new = fetch_osrm_matrix(stops, vehicle=st.session_state.selected_vehicle)
                            result_new = solve_tsp(stops, dist_mat_new, depot_index=0)
                            road_geom_new = fetch_osrm_route_geometry(result_new["route_stops"])
                        st.session_state.dist_matrix = dist_mat_new
                        st.session_state.dur_matrix = dur_mat_new
                        st.session_state.route_result = result_new
                        st.session_state.route_geometry = road_geom_new
                    else:
                        st.session_state.route_result = None
                        st.session_state.route_geometry = None
                        st.session_state.optimized = False

                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

            if nav_idx < len(delivery_stops):
                next_stop = delivery_stops[nav_idx] 
                next_html = (
                    '<div style="margin-top:14px;">'
                    '<div style="font-size:0.62rem;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;color:#B5A99A;margin-bottom:6px;">PENGANTARAN BERIKUTNYA</div>'
                    f'<div style="background:#F8FAFC;border:1.5px solid #E8E0D6;border-radius:12px;padding:12px 14px;">'
                    f'<div style="font-weight:700;font-size:0.92rem;color:#3D2A1C;">{next_stop.recipient or next_stop.name}</div>'
                    f'<div style="font-size:0.78rem;color:#64748B;margin-top:2px;">{next_stop.address}</div>'
                    '</div>'
                    '</div>'
                )
                st.markdown(next_html, unsafe_allow_html=True)

        else:
            st.markdown("""
            <div style="text-align:center;padding:30px 0;color:#4CAF50;">
                <div style="font-size:2.5rem;">🎉</div>
                <div style="font-weight:700;margin-top:8px;">Semua paket diantar!</div>
            </div>
            """, unsafe_allow_html=True)

        done_count = len(st.session_state.done_ids)
        if done_count > 0:
            st.markdown("<br>", unsafe_allow_html=True)
            with st.expander(f"✅ Sudah Diantar ({done_count})", expanded=False):
                for pkg in st.session_state.packages:
                    if pkg.stop_id in st.session_state.done_ids:
                        st.markdown(f"""
                        <div class="kk-pkg-card kk-pkg-done" style="opacity:0.65;">
                            <div class="kk-pkg-icon" style="background:#e8f5e9;border-color:#a5d6a7;">✅</div>
                            <div>
                                <div class="kk-pkg-name" style="text-decoration:line-through;">{pkg.name}</div>
                                <div class="kk-pkg-addr">{pkg.address}</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

with tab_ringkasan:

    done_count = len(st.session_state.done_ids)
    total_count = len(st.session_state.packages)
    all_done = done_count == total_count and total_count > 0
    vehicle_cfg = VEHICLES.get(st.session_state.selected_vehicle, VEHICLES["motorcycle"])

    if all_done:
        st.markdown(f"""
        <div class="kk-celebration">
            <div class="kk-celeb-icon">🎉</div>
            <div class="kk-celeb-title">Antaran Selesai!</div>
            <div class="kk-celeb-sub">
                Kerja bagus, Kurir KetKet! Semua paket hari ini telah terkirim menggunakan <strong>{vehicle_cfg['icon']} {vehicle_cfg['name']}</strong> dengan aman.
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="padding:20px 0 8px;text-align:center;">
            <div style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:800;font-size:1.4rem;color:{BROWN};">
                Progres Hari Ini
            </div>
            <div style="font-size:0.82rem;color:{MUTED};margin-top:4px;">
                {done_count} dari {total_count} paket diantar &nbsp;|&nbsp; {vehicle_cfg['icon']} {vehicle_cfg['name']}
            </div>
        </div>
        """, unsafe_allow_html=True)

        pct = done_count / total_count if total_count else 0
        st.progress(pct)

    if st.session_state.optimized and st.session_state.dist_matrix:
        all_s = all_stops_for_solver()
        result = st.session_state.route_result

        if result:
            ri = result["route_indices"]
            savings = estimate_savings(all_s, ri, st.session_state.dist_matrix, vehicle=st.session_state.selected_vehicle)
        else:
            savings = {"distance_saved_km": 0, "fuel_saved_rp": 0, "time_saved_min": 0}

        total_dist_km = round(result["total_distance"] / 1000, 1) if result else 0
        dur_mat = st.session_state.dur_matrix

        if dur_mat and result:
            ri = result["route_indices"]
            total_min = sum(
                dur_mat[ri[i]][ri[i + 1]] // 60
                for i in range(len(ri) - 1)
                if ri[i] < len(dur_mat) and ri[i + 1] < len(dur_mat[ri[i]])
            )
        else:
            total_min = 0

        def fmt_rp(n):
            return f"Rp {n:,.0f}".replace(",", ".")

        fuel_saved_str = fmt_rp(savings['fuel_saved_rp'])
        if vehicle_cfg['fuel_consumption_km_l'] == 0:
            fuel_saved_str = "Rp 0 (Bebas Emisi! 🌿)"

        stats = [
            ("JARAK DIHEMAT",   f"{savings['distance_saved_km']} KM",   "📈"),
            ("BENSIN DIHEMAT",  fuel_saved_str,                        "⛽"),
            ("WAKTU EFISIEN",   f"{savings['time_saved_min']} Menit Lebih Cepat", "⏱️"),
            ("TOTAL JARAK",     f"{total_dist_km} KM",                   "🛣️"),
            ("ESTIMASI WAKTU",  f"~{total_min} Menit",                   "🕐"),
        ]

        for label, value, icon in stats:
            st.markdown(f"""
            <div class="kk-stat-card">
                <div>
                    <div class="kk-stat-label">{label}</div>
                    <div class="kk-stat-value">{value}</div>
                </div>
                <div class="kk-stat-icon">{icon}</div>
            </div>
            """, unsafe_allow_html=True)

    else:
        st.markdown(f"""
        <div style="text-align:center;padding:40px 0;">
            <img src="data:image/webp;base64,{data_base64}" alt="Data" style="width:80px;margin-bottom:16px;">
            <div style="font-weight:700;color:{BROWN};font-size:1.1rem;">Belum ada data</div>
            <div style="font-size:0.85rem;color:#94A3B8;margin-top:6px;">
                Optimalkan rute terlebih dahulu untuk melihat ringkasan penghematan.
            </div>
        </div>
        """, unsafe_allow_html=True)

    if st.session_state.optimized and st.session_state.route_result:
        result = st.session_state.route_result
        delivery_stops = [
            s for s in result["route_stops"]
            if s.stop_id != st.session_state.courier.stop_id
        ]
        if delivery_stops:
            st.markdown(f'<div class="kk-section-label" style="margin-top:1rem;">Detail Urutan Rute</div>', unsafe_allow_html=True)
            for i, stop in enumerate(delivery_stops):
                is_done = stop.stop_id in st.session_state.done_ids
                icon = "✅" if is_done else f"{i+1}"
                style = f"opacity:0.5;text-decoration:line-through;" if is_done else ""
                st.markdown(f"""
                <div class="kk-pkg-card" style="{style}">
                    <div class="kk-order-badge">{icon}</div>
                    <div class="kk-pkg-icon">📍</div>
                    <div>
                        <div class="kk-pkg-name">{stop.name}</div>
                        <div class="kk-pkg-addr">{stop.address}</div>
                        <div class="kk-pkg-addr" style="margin-top:3px;">👤 {stop.recipient or '—'}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<div class='btn-reset-container'>", unsafe_allow_html=True)
    if st.button("🔄  Mulai Antaran Baru", use_container_width=True, type="secondary", key="btn_reset"):
        for key in ["packages", "courier", "done_ids", "route_result",
                    "dist_matrix", "dur_matrix", "optimized", "nav_index"]:
            if key in st.session_state:
                del st.session_state[key]
        init_state()
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div class='btn-optimize-container'>", unsafe_allow_html=True)
_pkgs = pending_packages()
if st.button("⚡  OPTIMALKAN RUTE", type="primary", use_container_width=True, key="btn_optimise"):
    if len(_pkgs) == 0:
        st.warning("Tidak ada paket dalam antrian!")
    else:
        stops = all_stops_for_solver()
        with st.spinner("Menghitung rute optimal…"):
            dist_mat, dur_mat = fetch_osrm_matrix(stops, vehicle=st.session_state.selected_vehicle)
            result = solve_tsp(stops, dist_mat, depot_index=0)
            ordered_stops = result["route_stops"]
            road_geom = fetch_osrm_route_geometry(ordered_stops)
        st.session_state.dist_matrix = dist_mat
        st.session_state.dur_matrix = dur_mat
        st.session_state.route_result = result
        st.session_state.route_geometry = road_geom
        st.session_state.optimized = True
        st.session_state.nav_index = 1
        st.success(f"🎯 Rute optimal ditemukan! {len(_pkgs)} titik diurutkan.")
        st.rerun()
st.markdown("</div>", unsafe_allow_html=True)