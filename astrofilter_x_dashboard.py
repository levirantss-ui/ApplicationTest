"""
ASTROFILTER-X - ISRU Output Dashboard
Built for the NASA Space Apps Challenge.

Converts two salvaged raw materials (parachute fabric and radioisotope
heater units) into fabricated HEPA air-filtration cartridges, and
estimates the resulting astronaut clean-air supply.

Run locally with:
    pip install streamlit
    streamlit run astrofilter_x_dashboard.py

Keep the accompanying .streamlit/config.toml in the same folder as this
file - it sets the dark mission-console color theme for native widgets
(sliders, progress bars).
"""

import streamlit as st

# ----------------------------------------------------------------------
# PAGE CONFIG (must be the first Streamlit command)
# ----------------------------------------------------------------------
st.set_page_config(
    page_title="ASTROFILTER-X: ISRU Output Dashboard",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----------------------------------------------------------------------
# PRODUCTION RULES - edit these to re-tune the simulation
# ----------------------------------------------------------------------
FABRIC_PER_CARTRIDGE = 10    # kg of parachute fabric per cartridge
RHU_PER_CARTRIDGE = 2        # RHU units per cartridge
AIR_DAYS_PER_CARTRIDGE = 5   # days of clean air per cartridge
MISSION_TARGET_DAYS = 30     # example life-support threshold for the log readout

WEIGHT_MAX = 500
RHU_MAX = 100

# ----------------------------------------------------------------------
# MISSION CONSOLE THEME - fonts, colors and layout for the custom HTML
# blocks below. Native widget colors (slider, progress fill) come from
# the accompanying .streamlit/config.toml instead of CSS overrides,
# since that is the mechanism Streamlit itself provides for theming them.
# ----------------------------------------------------------------------
CONSOLE_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap');

:root {
    --bg: #0A0D12;
    --surface: #121820;
    --surface-raised: #1A2129;
    --line: #29323C;
    --text: #DCE6E0;
    --text-dim: #7E8C97;
    --nominal: #39D97A;
    --caution: #F5A623;
    --critical: #FF5C4D;
}

html, body, [class*="css"] { font-family: 'Space Grotesk', sans-serif; }
.stApp { background: var(--bg); color: var(--text); }
footer { visibility: hidden; }

section[data-testid="stSidebar"] {
    background: var(--surface);
    border-right: 1px solid var(--line);
}

.status-strip {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.4rem 0.1rem 0.7rem 0.1rem;
    border-bottom: 1px solid var(--line);
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.78rem;
    color: var(--text-dim);
    letter-spacing: 0.03em;
}
.status-dot {
    display: inline-block;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    margin-right: 0.5rem;
}

.wordmark {
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 700;
    font-size: 2.2rem;
    color: var(--text);
    margin: 0.9rem 0 0.3rem 0;
    letter-spacing: -0.01em;
}
.wordmark-sub {
    font-size: 1.25rem;
    font-weight: 400;
    color: var(--text-dim);
}
.tagline {
    color: var(--text-dim);
    font-size: 0.95rem;
    max-width: 60ch;
    margin-bottom: 1.8rem;
    line-height: 1.5;
}

.readout {
    background: var(--surface);
    border: 1px solid var(--line);
    border-top: 3px solid var(--line);
    border-radius: 6px;
    padding: 1.1rem 1.3rem;
}
.readout .label {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 0.78rem;
    color: var(--text-dim);
    margin-bottom: 0.4rem;
}
.readout .value {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 2.6rem;
    font-weight: 600;
    color: var(--text);
    line-height: 1;
}
.readout .unit {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1rem;
    color: var(--text-dim);
    margin-left: 0.5rem;
}

.section-label {
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 600;
    font-size: 0.95rem;
    color: var(--text);
    border-bottom: 1px solid var(--line);
    padding-bottom: 0.4rem;
    margin: 2rem 0 1rem 0;
}

.gauge-head {
    display: flex;
    justify-content: space-between;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.82rem;
    color: var(--text-dim);
    margin-bottom: 0.3rem;
}
.gauge-head b { color: var(--text); font-weight: 500; }

div[data-testid="stProgress"] > div > div {
    background-color: var(--surface-raised);
}

.log-panel {
    background: var(--surface);
    border-left: 3px solid var(--line);
    border-radius: 0 6px 6px 0;
    padding: 1rem 1.2rem;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.85rem;
    line-height: 1.8;
}
.log-nominal  { color: var(--nominal); }
.log-caution  { color: var(--caution); }
.log-critical { color: var(--critical); }
</style>
"""
st.markdown(CONSOLE_CSS, unsafe_allow_html=True)

# ----------------------------------------------------------------------
# SIDEBAR - control panel (the two required inputs live here)
# ----------------------------------------------------------------------
with st.sidebar:
    st.markdown("**Control Panel**")
    st.caption("Set the quantities recovered from the descent site.")
    st.write("")

    parachute_weight = st.slider(
        "Salvaged Parachute Weight (kg)",
        min_value=0,
        max_value=WEIGHT_MAX,
        value=200,
        step=1,
        format="%d kg",
    )

    rhu_units = st.slider(
        "Collected RHU Units",
        min_value=0,
        max_value=RHU_MAX,
        value=30,
        step=1,
    )

    st.write("")
    st.markdown("---")
    st.caption(f"Recipe: {FABRIC_PER_CARTRIDGE} kg fabric + {RHU_PER_CARTRIDGE} RHU \u2192 1 HEPA cartridge")
    st.caption(f"Each cartridge sustains {AIR_DAYS_PER_CARTRIDGE} days of clean air.")

# ----------------------------------------------------------------------
# CALCULATIONS
# ----------------------------------------------------------------------
cartridges_from_fabric = parachute_weight // FABRIC_PER_CARTRIDGE
cartridges_from_rhu = rhu_units // RHU_PER_CARTRIDGE
hepa_cartridges = int(min(cartridges_from_fabric, cartridges_from_rhu))
clean_air_days = hepa_cartridges * AIR_DAYS_PER_CARTRIDGE

max_cartridges = min(WEIGHT_MAX // FABRIC_PER_CARTRIDGE, RHU_MAX // RHU_PER_CARTRIDGE)
max_air_days = max_cartridges * AIR_DAYS_PER_CARTRIDGE

fabric_used = hepa_cartridges * FABRIC_PER_CARTRIDGE
rhu_used = hepa_cartridges * RHU_PER_CARTRIDGE
fabric_leftover = parachute_weight - fabric_used
rhu_leftover = rhu_units - rhu_used

fabric_utilization = (fabric_used / parachute_weight) if parachute_weight > 0 else 0.0
rhu_utilization = (rhu_used / rhu_units) if rhu_units > 0 else 0.0

if hepa_cartridges == 0:
    status_level = "critical"
elif cartridges_from_fabric == cartridges_from_rhu and fabric_leftover == 0 and rhu_leftover == 0:
    status_level = "nominal"
else:
    status_level = "caution"

STATUS_COPY = {
    "critical": ("OFFLINE", "var(--critical)"),
    "caution": ("SUBOPTIMAL", "var(--caution)"),
    "nominal": ("NOMINAL", "var(--nominal)"),
}
status_label, status_color = STATUS_COPY[status_level]

# ----------------------------------------------------------------------
# STATUS STRIP
# ----------------------------------------------------------------------
st.markdown(
    f"""
    <div class="status-strip">
        <span>FABRICATION UNIT ISRU-7</span>
        <span><span class="status-dot" style="background:{status_color};"></span>{status_label}</span>
    </div>
    """,
    unsafe_allow_html=True,
)

# ----------------------------------------------------------------------
# TITLE (exact dashboard title, split by weight/size - not by color -
# into the system name and its descriptor)
# ----------------------------------------------------------------------
st.markdown(
    """
    <h1 class="wordmark">ASTROFILTER-X<span class="wordmark-sub">: ISRU Output Dashboard</span></h1>
    <p class="tagline">
        Converts salvaged parachute fabric and radioisotope heater units
        into HEPA filtration cartridges for astronaut life support.
    </p>
    """,
    unsafe_allow_html=True,
)

# ----------------------------------------------------------------------
# HERO READOUTS - the two required outputs
# ----------------------------------------------------------------------
col1, col2 = st.columns(2)
with col1:
    st.markdown(
        f"""
        <div class="readout" style="border-top-color:{status_color};">
            <div class="label">HEPA Cartridges Produced</div>
            <div class="value">{hepa_cartridges}<span class="unit">/ {max_cartridges}</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with col2:
    st.markdown(
        f"""
        <div class="readout" style="border-top-color:{status_color};">
            <div class="label">Days of Clean Air</div>
            <div class="value">{clean_air_days}<span class="unit">days</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ----------------------------------------------------------------------
# FABRICATION GAUGES - the required progress bars
# ----------------------------------------------------------------------
st.markdown('<h3 class="section-label">Fabrication Gauges</h3>', unsafe_allow_html=True)


def gauge(label: str, value_text: str, ratio: float) -> None:
    st.markdown(
        f'<div class="gauge-head"><span>{label}</span><b>{value_text}</b></div>',
        unsafe_allow_html=True,
    )
    st.progress(min(max(ratio, 0.0), 1.0))


gauge(
    "Cartridge output",
    f"{hepa_cartridges} / {max_cartridges}",
    hepa_cartridges / max_cartridges if max_cartridges else 0.0,
)
gauge(
    "Air supply",
    f"{clean_air_days} / {max_air_days} days",
    clean_air_days / max_air_days if max_air_days else 0.0,
)
gauge("Fabric utilization", f"{fabric_used} / {parachute_weight} kg", fabric_utilization)
gauge("RHU utilization", f"{rhu_used} / {rhu_units} units", rhu_utilization)

# ----------------------------------------------------------------------
# MISSION LOG - bonus: bottleneck + life-support status commentary.
# Safe to delete this whole section if you only want the four gauges.
# ----------------------------------------------------------------------
st.markdown('<h3 class="section-label">Mission Log</h3>', unsafe_allow_html=True)

log_lines = []

if status_level == "critical":
    log_lines.append(("critical", "Insufficient material - 0 cartridges fabricated. Increase salvage inputs."))
elif cartridges_from_rhu > cartridges_from_fabric:
    log_lines.append(("caution", f"Bottleneck: parachute fabric. {rhu_leftover} RHU unit(s) unused."))
elif cartridges_from_fabric > cartridges_from_rhu:
    log_lines.append(("caution", f"Bottleneck: RHU units. {fabric_leftover} kg of fabric unused."))
elif fabric_leftover > 0 or rhu_leftover > 0:
    log_lines.append((
        "caution",
        f"Partial batch remainder - {fabric_leftover} kg fabric and {rhu_leftover} "
        f"RHU unit(s) short of the next cartridge.",
    ))
else:
    log_lines.append(("nominal", "All salvaged material fully utilized."))

if clean_air_days >= MISSION_TARGET_DAYS:
    log_lines.append((
        "nominal",
        f"Life support: {clean_air_days} days meets the {MISSION_TARGET_DAYS}-day mission threshold.",
    ))
else:
    log_lines.append((
        "caution",
        f"Life support: {clean_air_days} days is below the {MISSION_TARGET_DAYS}-day mission threshold.",
    ))

log_html = "".join(f'<div class="log-{level}">&gt; {message}</div>' for level, message in log_lines)
st.markdown(f'<div class="log-panel">{log_html}</div>', unsafe_allow_html=True)
