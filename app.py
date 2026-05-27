"""
app.py — KetKet Paket Frontend
Mobile-friendly Streamlit app for courier route optimization.
Run with: streamlit run app.py
"""

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
    solve_tsp,
    estimate_savings,
    build_google_maps_url,
)

# ---------------------------------------------------------------------------
# Page config — MUST be first Streamlit call
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="KetKet Paket",
    page_icon="📦",
    layout="centered",
    initial_sidebar_state="collapsed",
)


# ---------------------------------------------------------------------------
# Theme & Global CSS
# ---------------------------------------------------------------------------

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
/* ── Google Fonts ── */
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=DM+Serif+Display&display=swap');

/* ── Global reset ── */
html, body, [class*="css"] {{
    font-family: 'Plus Jakarta Sans', sans-serif;
    background-color: {CREAM} !important;
    color: {BROWN};
}}

.stApp {{
    background-color: {CREAM} !important;
    max-width: 480px;
    margin: 0 auto;
}}

/* ── Hide default streamlit chrome ── */
#MainMenu, footer, header {{ visibility: hidden; }}
.block-container {{ padding: 0 1rem 6rem 1rem !important; }}

/* ── App header bar ── */
.kk-header {{
    background: {BROWN};
    color: {CREAM};
    padding: 14px 20px;
    display: flex;
    align-items: center;
    gap: 10px;
    border-radius: 0 0 16px 16px;
    margin: -1rem -1rem 1.2rem -1rem;
    font-weight: 700;
    font-size: 1.15rem;
    letter-spacing: -0.3px;
}}
.kk-header .icon {{ font-size: 1.4rem; }}
.kk-header .profile {{
    margin-left: auto;
    width: 34px; height: 34px;
    border-radius: 50%;
    background: {TERRA};
    display: flex; align-items: center; justify-content: center;
    font-size: 0.9rem;
}}

/* ── Section label ── */
.kk-section-label {{
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: {MUTED};
    margin: 1rem 0 0.5rem 0;
}}

/* ── Queue count ── */
.kk-queue-header {{
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    margin-bottom: 0.6rem;
}}
.kk-queue-title {{
    font-family: 'DM Serif Display', serif;
    font-size: 1.35rem;
    color: {BROWN};
}}
.kk-sort-btn {{
    font-size: 0.72rem;
    font-weight: 700;
    color: {TERRA};
    letter-spacing: 0.8px;
    text-transform: uppercase;
    cursor: pointer;
}}

/* ── Package card ── */
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
    transition: box-shadow .2s;
}}
.kk-pkg-card:hover {{ box-shadow: 0 4px 16px rgba(61,42,28,0.12); }}
.kk-pkg-icon {{
    width: 38px; height: 38px;
    border-radius: 10px;
    background: {CREAM};
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

/* ── Primary button ── */
.kk-btn-primary {{
    background: {TERRA};
    color: white;
    border: none;
    border-radius: 14px;
    padding: 16px;
    font-size: 0.95rem;
    font-weight: 700;
    width: 100%;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    letter-spacing: 0.2px;
    box-shadow: 0 4px 14px rgba(224,90,71,0.35);
    transition: transform .15s, box-shadow .15s;
}}
.kk-btn-primary:active {{ transform: scale(0.98); }}

/* ── Nav card (Peta Rute) ── */
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
    font-family: 'DM Serif Display', serif;
    font-size: 1.15rem;
    color: {BROWN};
    line-height: 1.3;
}}
.kk-nav-dist {{
    background: {CREAM};
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
    background: {CREAM};
    border-radius: 10px;
    margin: 10px 0;
    font-size: 0.82rem;
    color: {BROWN};
}}

/* ── Summary stats card ── */
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
    font-family: 'DM Serif Display', serif;
    font-size: 1.6rem;
    color: {BROWN};
    line-height: 1.1;
}}
.kk-stat-icon {{
    width: 42px; height: 42px;
    border-radius: 12px;
    background: {CREAM};
    display: flex; align-items: center; justify-content: center;
    font-size: 1.1rem;
}}

/* ── Celebration header ── */
.kk-celebration {{
    text-align: center;
    padding: 28px 16px 20px;
}}
.kk-celeb-icon {{
    font-size: 3.5rem;
    background: {CREAM};
    border-radius: 24px;
    width: 88px; height: 88px;
    display: flex; align-items: center; justify-content: center;
    margin: 0 auto 16px;
}}
.kk-celeb-title {{
    font-family: 'DM Serif Display', serif;
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

/* ── Tab styling override ── */
.stTabs [data-baseweb="tab-list"] {{
    background: {CARD_BG};
    border-radius: 14px;
    padding: 4px;
    gap: 2px;
    border: 1.5px solid {BORDER};
    margin-bottom: 1rem;
    position: fixed;
    bottom: 12px;
    left: 50%;
    transform: translateX(-50%);
    width: calc(min(480px, 100vw) - 2rem);
    z-index: 999;
    box-shadow: 0 4px 20px rgba(61,42,28,0.14);
}}
.stTabs [data-baseweb="tab"] {{
    border-radius: 10px !important;
    font-size: 0.72rem;
    font-weight: 600;
    color: {MUTED} !important;
    padding: 8px 6px !important;
    flex: 1;
    gap: 4px;
}}
.stTabs [aria-selected="true"] {{
    background: {BROWN} !important;
    color: {CREAM} !important;
}}
.stTabs [data-baseweb="tab-panel"] {{ padding-top: 0.2rem; }}

/* ── Input field ── */
.stTextInput > div > div > input {{
    border-radius: 12px !important;
    border: 1.5px solid {BORDER} !important;
    background: {CARD_BG} !important;
    color: {BROWN} !important;
    font-size: 0.9rem !important;
    padding: 12px 16px !important;
}}
.stTextInput > div > div > input:focus {{
    border-color: {TERRA} !important;
    box-shadow: 0 0 0 3px rgba(224,90,71,0.15) !important;
}}

/* ── Selectbox ── */
.stSelectbox > div > div {{
    border-radius: 12px !important;
    border: 1.5px solid {BORDER} !important;
    background: {CARD_BG} !important;
    font-size: 0.88rem !important;
}}

/* ── Spinner ── */
.stSpinner > div {{ color: {TERRA} !important; }}

/* ── Alerts ── */
.stSuccess {{ border-radius: 12px; }}
.stWarning {{ border-radius: 12px; }}
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Session-state initialisation
# ---------------------------------------------------------------------------

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
    if "optimized" not in st.session_state:
        st.session_state.optimized = False
    if "nav_index" not in st.session_state:
        st.session_state.nav_index = 1   # 0 = depot; 1 = first delivery
    if "active_tab" not in st.session_state:
        st.session_state.active_tab = 0


init_state()


# ---------------------------------------------------------------------------
# Helper: pending packages (not yet delivered)
# ---------------------------------------------------------------------------

def pending_packages() -> list:
    return [p for p in st.session_state.packages if p.stop_id not in st.session_state.done_ids]


def all_stops_for_solver() -> list:
    return [st.session_state.courier] + pending_packages()


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

st.markdown(f"""
<div class="kk-header">
    <span class="icon">📦</span>
    <span>KetKet Paket</span>
    <div class="profile">👤</div>
</div>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------

tab_daftar, tab_peta, tab_ringkasan = st.tabs(
    ["📋  Daftar Paket", "🗺️  Peta Rute", "📊  Ringkasan"]
)


# ===========================================================================
# TAB 1 — Daftar Paket
# ===========================================================================

with tab_daftar:

    # ── Add new address ──────────────────────────────────────────────────
    st.markdown('<div class="kk-section-label">Tambah Alamat Baru</div>', unsafe_allow_html=True)

    col_inp, col_btn = st.columns([5, 1])
    with col_inp:
        new_addr = st.text_input(
            label="",
            placeholder="Masukkan alamat pengiriman...",
            label_visibility="collapsed",
            key="new_address_input",
        )
    with col_btn:
        st.markdown("<br>", unsafe_allow_html=True)
        add_clicked = st.button("➕", use_container_width=True, help="Tambah alamat")

    if add_clicked and new_addr.strip():
        # Simple geocoding placeholder — center of Surabaya with small random offset
        import random
        new_stop = Stop(
            name=new_addr.strip()[:25],
            address=new_addr.strip(),
            lat=-7.2575 + random.uniform(-0.03, 0.03),
            lng=112.7488 + random.uniform(-0.03, 0.03),
            recipient="Penerima Baru",
            stop_id=f"PKG_{len(st.session_state.packages)+1:03d}",
        )
        st.session_state.packages.append(new_stop)
        st.session_state.optimized = False
        st.session_state.route_result = None
        label = new_addr.strip()[:30]
        st.success(f"✅ Alamat '{label}' berhasil ditambahkan!")
        st.rerun()

    # ── Queue list ───────────────────────────────────────────────────────
    pkgs = pending_packages()
    total_all = len(st.session_state.packages)
    done_count = len(st.session_state.done_ids)

    st.markdown(f"""
    <div class="kk-queue-header">
        <div class="kk-queue-title">Daftar Antrean ({len(pkgs)})</div>
        <div class="kk-sort-btn">Urutkan</div>
    </div>
    """, unsafe_allow_html=True)

    if not pkgs:
        st.markdown("""
        <div style="text-align:center;padding:40px 0;color:#B5A99A;">
            <div style="font-size:2.5rem;margin-bottom:10px;">🎉</div>
            <div style="font-weight:700;font-size:1rem;">Semua paket sudah diantar!</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Determine display order (optimised if available)
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

        for idx, pkg in enumerate(ordered):
            order_num = idx + 1
            col_card, col_del = st.columns([11, 1])
            with col_card:
                badge_class = "kk-order-badge"
                st.markdown(f"""
                <div class="kk-pkg-card">
                    <div class="{badge_class}">{order_num}</div>
                    <div class="kk-pkg-icon">📍</div>
                    <div>
                        <div class="kk-pkg-name">{pkg.name}</div>
                        <div class="kk-pkg-addr">{pkg.address}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            with col_del:
                st.markdown("<br><br>", unsafe_allow_html=True)
                if st.button("🗑️", key=f"del_{pkg.stop_id}", help=f"Hapus {pkg.name}"):
                    st.session_state.packages = [
                        p for p in st.session_state.packages if p.stop_id != pkg.stop_id
                    ]
                    st.session_state.optimized = False
                    st.session_state.route_result = None
                    st.rerun()

    # ── Completed packages (collapsible) ────────────────────────────────
    if done_count > 0:
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

    # ── Optimise button ──────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("✨  Optimalkan Rute", type="primary", use_container_width=True, key="btn_optimise"):
        if len(pkgs) == 0:
            st.warning("Tidak ada paket dalam antrian!")
        else:
            stops = all_stops_for_solver()
            with st.spinner("Menghitung rute optimal…"):
                dist_mat, dur_mat = fetch_osrm_matrix(stops)
                result = solve_tsp(stops, dist_mat, depot_index=0)

            st.session_state.dist_matrix = dist_mat
            st.session_state.dur_matrix = dur_mat
            st.session_state.route_result = result
            st.session_state.optimized = True
            st.session_state.nav_index = 1
            st.success(f"🎯 Rute optimal ditemukan! {len(pkgs)} titik diurutkan.")
            st.rerun()


# ===========================================================================
# TAB 2 — Peta Rute
# ===========================================================================

with tab_peta:

    if not st.session_state.optimized or not st.session_state.route_result:
        st.markdown("""
        <div style="text-align:center;padding:60px 0 40px;color:#B5A99A;">
            <div style="font-size:3rem;margin-bottom:12px;">🗺️</div>
            <div style="font-weight:700;font-size:1.05rem;color:#3D2A1C;">Rute belum dioptimalkan</div>
            <div style="font-size:0.85rem;margin-top:6px;">Pergi ke tab Daftar Paket dan<br>tekan "Optimalkan Rute" terlebih dahulu.</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        result = st.session_state.route_result
        route_stops = result["route_stops"]  # [courier, pkg1, pkg2, ...]
        dur_mat = st.session_state.dur_matrix
        dist_mat = st.session_state.dist_matrix

        # Determine current navigation target
        # route_stops[0] = courier, route_stops[1..] = packages
        # nav_index counts through 1..n
        nav_idx = st.session_state.nav_index
        delivery_stops = [s for s in route_stops if s.stop_id != st.session_state.courier.stop_id]

        if nav_idx > len(delivery_stops):
            nav_idx = len(delivery_stops)

        # ── Folium Map ───────────────────────────────────────────────────
        # Centre map between courier and next dest
        courier = st.session_state.courier
        centre_lat = courier.lat
        centre_lng = courier.lng

        m = folium.Map(
            location=[centre_lat, centre_lng],
            zoom_start=13,
            tiles="CartoDB Positron",
        )

        # Courier marker (red)
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
                    🚴
                </div>""",
                icon_size=(32, 32),
                icon_anchor=(16, 16),
            ),
        ).add_to(m)

        # Package markers (white pins with order number)
        all_route = [courier] + delivery_stops
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

        # Route polyline (Navy dashed style via ant-path-like coords)
        route_coords = [[s.lat, s.lng] for s in all_route]
        folium.PolyLine(
            locations=route_coords,
            color=NAVY,
            weight=3.5,
            opacity=0.75,
            dash_array="8 5",
            tooltip="Jalur TSP Optimal",
        ).add_to(m)

        st_folium(m, height=280, use_container_width=True, returned_objects=[])

        # ── Navigation card ──────────────────────────────────────────────
        if nav_idx <= len(delivery_stops):
            target = delivery_stops[nav_idx - 1]

            # Distance/time from previous stop
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

            gmaps_url = build_google_maps_url(target)

            col_info, col_dist = st.columns([3, 1])
            with col_info:
                st.markdown(f"""
                <div class="kk-nav-card">
                    <div class="kk-nav-dest-label">Tujuan Berikutnya</div>
                    <div class="kk-nav-dest-name">{target.name} – {target.address}</div>
                </div>
                """, unsafe_allow_html=True)
            with col_dist:
                st.markdown(f"""
                <div style="height:100%;display:flex;align-items:center;padding-top:4px;">
                    <div class="kk-nav-dist">
                        {seg_dist_km}<br><span style="font-size:0.65rem;font-weight:600;">km</span><br>
                        <span style="font-size:0.7rem;font-weight:600;color:{MUTED};">{seg_dur_min} Menit</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown(f"""
            <div class="kk-recipient-row">
                👤 &nbsp;<strong>Penerima</strong>&nbsp;&nbsp;{target.recipient or '—'}
            </div>
            """, unsafe_allow_html=True)

            # Navigation + Done buttons
            col_nav, col_done = st.columns([5, 1])
            with col_nav:
                st.link_button(
                    "🧭  Mulai Navigasi",
                    url=gmaps_url,
                    use_container_width=True,
                )
            with col_done:
                if st.button("✅", key="btn_done_nav", help="Tandai Selesai Antar"):
                    st.session_state.done_ids.add(target.stop_id)
                    st.session_state.nav_index += 1

                    # Re-optimise remaining route
                    remaining = pending_packages()
                    if remaining:
                        stops = all_stops_for_solver()
                        with st.spinner("Memperbarui rute…"):
                            dist_mat_new, dur_mat_new = fetch_osrm_matrix(stops)
                            result_new = solve_tsp(stops, dist_mat_new, depot_index=0)
                        st.session_state.dist_matrix = dist_mat_new
                        st.session_state.dur_matrix = dur_mat_new
                        st.session_state.route_result = result_new
                    else:
                        st.session_state.route_result = None
                        st.session_state.optimized = False

                    st.rerun()

            # Route progress strip
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown('<div class="kk-section-label">Urutan Rute</div>', unsafe_allow_html=True)
            for i, stop in enumerate(delivery_stops):
                order = i + 1
                is_done = stop.stop_id in st.session_state.done_ids
                is_next = (order == nav_idx)
                icon = "✅" if is_done else ("🔵" if is_next else "⚪")
                style = f"color:{MUTED};text-decoration:line-through;" if is_done else (
                    f"color:{NAVY};font-weight:700;" if is_next else f"color:{BROWN};"
                )
                st.markdown(f"""
                <div style="display:flex;align-items:center;gap:10px;padding:6px 0;
                     border-bottom:1px solid {BORDER};">
                    <span style="font-size:0.75rem;">{icon}</span>
                    <span style="font-size:0.82rem;{style}">{order}. {stop.name}</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="text-align:center;padding:30px 0;color:#4CAF50;">
                <div style="font-size:2.5rem;">🎉</div>
                <div style="font-weight:700;margin-top:8px;">Semua paket diantar!</div>
            </div>
            """, unsafe_allow_html=True)


# ===========================================================================
# TAB 3 — Ringkasan
# ===========================================================================

with tab_ringkasan:

    done_count = len(st.session_state.done_ids)
    total_count = len(st.session_state.packages)
    all_done = done_count == total_count and total_count > 0

    if all_done:
        # Celebration screen
        st.markdown(f"""
        <div class="kk-celebration">
            <div class="kk-celeb-icon">🎉</div>
            <div class="kk-celeb-title">Antaran Selesai!</div>
            <div class="kk-celeb-sub">
                Kerja bagus, Kurir KetKet! Semua paket hari ini telah terkirim dengan aman.
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="padding:20px 0 8px;text-align:center;">
            <div style="font-family:'DM Serif Display',serif;font-size:1.4rem;color:{BROWN};">
                Progres Hari Ini
            </div>
            <div style="font-size:0.82rem;color:{MUTED};margin-top:4px;">
                {done_count} dari {total_count} paket diantar
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Progress bar
        pct = done_count / total_count if total_count else 0
        st.progress(pct)

    # ── Stats ────────────────────────────────────────────────────────────
    if st.session_state.optimized and st.session_state.dist_matrix:
        all_s = all_stops_for_solver()
        result = st.session_state.route_result

        # Only compute savings if we have a result
        if result:
            ri = result["route_indices"]
            savings = estimate_savings(all_s, ri, st.session_state.dist_matrix)
        else:
            savings = {"distance_saved_km": 0, "fuel_saved_rp": 0, "time_saved_min": 0}

        total_dist_km = round(result["total_distance"] / 1000, 1) if result else 0
        dur_mat = st.session_state.dur_matrix

        # Total duration from matrix if available
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

        stats = [
            ("JARAK DIHEMAT",   f"{savings['distance_saved_km']} KM",   "📈"),
            ("BENSIN DIHEMAT",  fmt_rp(savings['fuel_saved_rp']),         "⛽"),
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
        <div style="text-align:center;padding:40px 0;color:{MUTED};">
            <div style="font-size:2.5rem;margin-bottom:10px;">📊</div>
            <div style="font-weight:700;color:{BROWN};">Belum ada data</div>
            <div style="font-size:0.82rem;margin-top:6px;">
                Optimalkan rute terlebih dahulu untuk melihat ringkasan penghematan.
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Route summary table ───────────────────────────────────────────────
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

    # ── Reset button ─────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔄  Mulai Antaran Baru", use_container_width=True, type="primary", key="btn_reset"):
        for key in ["packages", "courier", "done_ids", "route_result",
                    "dist_matrix", "dur_matrix", "optimized", "nav_index"]:
            if key in st.session_state:
                del st.session_state[key]
        init_state()
        st.rerun()
