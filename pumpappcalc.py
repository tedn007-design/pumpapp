import streamlit as st
import math
import pandas as pd

# Page Configuration
st.set_page_config(
    page_title="Open-Pit Dewatering Sizer",
    page_icon="⛏️",
    layout="wide"
)

# --- CLASS DEFINITION: ADVANCED PERFORMANCE RANGE DATABASE ---
class MinePumpDatabase:
    def __init__(self):
        # Initializing manufacturer datasets with real-world optimal operating boundaries
        self.pumps_db = [
            {
                "Manufacturer": "Weir Minerals (Warman)",
                "Model": "Warman DWU",
                "Min_Flow_m3h": 400, "Max_Flow_m3h": 1200,
                "Min_Head_m": 40, "Max_Head_m": 130,
                "Water_Type": "Slurry / Dirty",
                "Max_Solids_mm": 40.0,
                "Drive_Type": "Electric / Diesel",
                "Best_For": "Abrasive pit floor cleanup and dirty sump management"
            },
            {
                "Manufacturer": "Weir Minerals (Multiflo)",
                "Model": "Multiflo RF Series",
                "Min_Flow_m3h": 600, "Max_Flow_m3h": 2200,
                "Min_Head_m": 60, "Max_Head_m": 220,
                "Water_Type": "Dirty / Runoff",
                "Max_Solids_mm": 60.0,
                "Drive_Type": "Diesel",
                "Best_For": "High-volume open-cut flood/storm emergency dewatering"
            },
            {
                "Manufacturer": "Xylem (Godwin)",
                "Model": "Godwin Dri-Prime CD200M",
                "Min_Flow_m3h": 150, "Max_Flow_m3h": 520,
                "Min_Head_m": 15, "Max_Head_m": 50,
                "Water_Type": "Dirty / Runoff",
                "Max_Solids_mm": 75.0,
                "Drive_Type": "Diesel",
                "Best_For": "Snore conditions, fast automatic priming, and high solids transfer"
            },
            {
                "Manufacturer": "KSB Australia",
                "Model": "UPA 200 Borehole",
                "Min_Flow_m3h": 200, "Max_Flow_m3h": 1000,
                "Min_Head_m": 100, "Max_Head_m": 420,
                "Water_Type": "Clear / Saline",
                "Max_Solids_mm": 2.0,
                "Drive_Type": "Electric",
                "Best_For": "Deep pit wall depressurisation and groundwater lowering"
            },
            {
                "Manufacturer": "KSB Australia",
                "Model": "Multitec Horizontal",
                "Min_Flow_m3h": 300, "Max_Flow_m3h": 1500,
                "Min_Head_m": 250, "Max_Head_m": 1000,
                "Water_Type": "Clear / Low-Solids",
                "Max_Solids_mm": 5.0,
                "Drive_Type": "Electric / Diesel",
                "Best_For": "Ultra high-pressure multi-stage staging lines out of ultra-deep mines"
            },
            {
                "Manufacturer": "Sykes Group",
                "Model": "Sykes XH200-636",
                "Min_Flow_m3h": 250, "Max_Flow_m3h": 828,
                "Min_Head_m": 70, "Max_Head_m": 208,
                "Water_Type": "Dirty / Runoff",
                "Max_Solids_mm": 31.0,
                "Drive_Type": "Diesel",
                "Best_For": "High-head pit bottom extraction with variable solids handling"
            },
            {
                "Manufacturer": "Pioneer Pump",
                "Model": "PP Series High-Head",
                "Min_Flow_m3h": 400, "Max_Flow_m3h": 1800,
                "Min_Head_m": 60, "Max_Head_m": 210,
                "Water_Type": "Dirty / Runoff",
                "Max_Solids_mm": 76.0,
                "Drive_Type": "Diesel / Electric",
                "Best_For": "High-volume staging with high solids handling profiles"
            }
        ]
        self.df = pd.DataFrame(self.pumps_db)

    def get_recommendation(self, head_required_m, flow_required_m3h, water_profile):
        is_slurry_requested = water_profile.lower() == "slurry"
        
        matches = self.df[
            (head_required_m >= self.df["Min_Head_m"]) & (head_required_m <= self.df["Max_Head_m"]) &
            (flow_required_m3h >= self.df["Min_Flow_m3h"]) & (flow_required_m3h <= self.df["Max_Flow_m3h"])
        ]
        
        if is_slurry_requested:
            matches = matches[matches["Water_Type"].str.contains("Slurry|Dirty", case=False)]
        
        if matches.empty:
            return None
            
        return matches.sort_values(by=["Max_Head_m"], ascending=True)

# --- INIT DATABASE ---
pump_selector = MinePumpDatabase()

st.title("⛏️ Open-Pit Sump Dewatering & Pump Sizer")
st.markdown("A practical sizing tool built for non-specialists to automatically calculate geometric lengths, map performance ranges, and select matching industry pumps.")

# --- SIDEBAR: INPUTS ---
st.sidebar.header("1. Site & Fluid Inputs")
flow_target = st.sidebar.number_input("Target Pumping Rate (L/s)", value=30.0, step=5.0, format="%.1f")
fluid_type = st.sidebar.selectbox("Water Condition", ["Clean / Rainwater", "Light Mud / Silty", "Heavy Slurry / Gritty"])

st.sidebar.header("2. Geometry & Pit Layout")
sump_rl = st.sidebar.number_input("Sump Floor Level (RL in meters)", value=100.0, step=1.0)
discharge_rl = st.sidebar.number_input("Surface Discharge Point Level (RL in meters)", value=220.0, step=1.0)

# AUTOMATED PIPE LENGTH LOGIC BASED ON HEIGHT DIFFERENCE
static_head = discharge_rl - sump_rl

if static_head <= 0:
    st.sidebar.error("Discharge RL must be higher than Sump RL.")
    static_head = 1.0

# 1 in 10 mining grade haul road gradient geometry calculation
base_ramp_length = static_head * 10.0

st.sidebar.markdown(f"**Calculated Minimum Ramp Pipe Length:** `{base_ramp_length:.0f} m` *(based on 1:10 haul road gradient)*")
pipe_slack_m = st.sidebar.number_input("Additional Pipe Slack / Surface Run (m)", value=50.0, step=10.0)

# Unified layout length used across all hydraulic math equations
pipe_length = base_ramp_length + pipe_slack_m

pipe_dia = st.sidebar.selectbox("HDPE Pipe Diameter (mm)", [100, 150, 200, 250, 300], index=1)

# --- REAL-WORLD WEIGHT CALCULATIONS (PE100 PN16 / SDR11 Specs) ---
# Approximate weight per meter metrics for standard mining poly sizes (kg/m)
weight_lookup_kg_m = {100: 3.2, 150: 7.1, 200: 12.3, 250: 19.1, 300: 27.5}
unit_weight = weight_lookup_kg_m.get(pipe_dia, 7.1)
total_pipeline_weight_kg = pipe_length * unit_weight
total_pipeline_weight_tonnes = total_pipeline_weight_kg / 1000.0

# --- STAGING & ENVELOPE REDIRECT LOGIC ---
# Standard high-head dewatering single-stage limit boundary rule (m)
SINGLE_STAGE_MAX_HEAD = 130.0
is_multistage_required = static_head > SINGLE_STAGE_MAX_HEAD

if is_multistage_required:
    active_calc_head = SINGLE_STAGE_MAX_HEAD
    recommended_booster_rl = sump_rl + SINGLE_STAGE_MAX_HEAD
else:
    active_calc_head = static_head

# --- HYDRAULIC CALCULATIONS ---
viscosity_multiplier = {
    "Clean / Rainwater": 1.0, 
    "Light Mud / Silty": 1.15, 
    "Heavy Slurry / Gritty": 1.35
}[fluid_type]

flow_m3h = flow_target * 3.6

# Friction loss is bounded strictly to the active extraction lift stage
friction_loss = (pipe_length / 100.0) * (flow_target / pipe_dia) * 2.2 * viscosity_multiplier
tdh = active_calc_head + friction_loss
estimated_power_kw = (flow_target * tdh * 9.81) / (1000 * 0.65)

# --- PIPE PRESSURE RATING ADVISOR CALCULATIONS ---
tdh_bar = tdh / 10.197

if tdh_bar <= 6.0:
    recommended_pn = "PN6 (SDR 26)"
    pn_status = "Success"
elif tdh_bar <= 10.0:
    recommended_pn = "PN10 (SDR 17)"
    pn_status = "Success"
elif tdh_bar <= 16.0:
    recommended_pn = "PN16 (SDR 11)"
    pn_status = "Success"
elif tdh_bar <= 20.0:
    recommended_pn = "PN20 (SDR 9)"
    pn_status = "Warning"
else:
    recommended_pn = "EXCEEDS STANDARD HDPE"
    pn_status = "Critical"

# --- MAIN PANEL: RESULTS ---
st.subheader("📊 System & Head Results")

# Render alert message box layout if multi-stage staging limits are breached
if is_multistage_required:
    st.warning(f"🚨 **Multi-Stage Staging System Advised:** Total vertical lift ({static_head:.0f}m) exceeds efficient single-stage mining boundaries ({SINGLE_STAGE_MAX_HEAD:.0f}m). **Downstream calculations have been auto-bounded to a Single Stage execution.** You must install a mid-pit booster staging station at or below **RL {recommended_booster_rl:.0f}m**.")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Required Flow Window", f"{flow_target:.1f} L/s", delta=f"{flow_m3h:.0f} m³/h equivalent")
col2.metric("Total Dynamic Head (TDH)", f"{tdh:.1f} m", delta=f"Single Stage Target Lift: {active_calc_head:.0f}m")
col3.metric("Auto Pipe Length", f"{pipe_length:.0f} m", delta=f"Total Total Lift: {static_head:.0f}m")
col4.metric("Est. Shaft Power", f"{estimated_power_kw:.1f} kW")

st.divider()

# --- AUTOMATED RANGE-BASED MATCH RECOMMENDATIONS ---
st.subheader("🏆 Performance Window Range Match Matrix")
st.markdown("The algorithm screens manufacturer operating windows to find single-stage pumps matching your calculated target boundaries:")

db_fluid_profile = "Clear" if "Clean" in fluid_type else ("Slurry" if "Heavy" in fluid_type else "Dirty")

recommendations = pump_selector.get_recommendation(
    head_required_m=tdh,
    flow_required_m3h=flow_m3h,
    water_profile=db_fluid_profile
)

if recommendations is None or recommendations.empty:
    st.error("❌ **No Single Pump Matches This Operating Window Range:** Your current combination of flow and head requirements sits outside standard performance curves. Adjust your sliders (e.g., increase pipe diameter to lower friction head, or select a lower flow target) or plan an aggressive multi-pump mid-pit staging setup.")
else:
    st.success(f"✅ Found **{len(recommendations)} standard industry assets** compatible with your single-stage design curve specs:")
    
    for idx, row in recommendations.iterrows():
        with st.expander(f"👉 **{row['Manufacturer']} - {row['Model']}** (Ideal Range Fit)"):
            c_card1, c_card2 = st.columns(2)
            with c_card1:
                st.markdown(f"**Operational Role:** {row['Best_For']}")
