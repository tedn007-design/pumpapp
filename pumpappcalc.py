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
        
        # Range-based matching window conditions
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

# Avoid calculation errors if user types an inverse geometry profile
if static_head <= 0:
    st.sidebar.error("Discharge RL must be higher than Sump RL.")
    static_head = 1.0

# Pit pipes travel up a ramp (1 in 10 mining grade = 10% slope angle). 
# Distance traveled up ramp = vertical height * 10
base_ramp_length = static_head * 10.0

st.sidebar.markdown(f"**Calculated Minimum Ramp Pipe Length:** `{base_ramp_length:.0f} m` *(based on 1:10 haul road gradient)*")
pipe_slack_m = st.sidebar.number_input("Additional Pipe Slack / Surface Run (m)", value=50.0, step=10.0)

# Unified length used for downstream equations
pipe_length = base_ramp_length + pipe_slack_m

pipe_dia = st.sidebar.selectbox("HDPE Pipe Diameter (mm)", [100, 150, 200, 250, 300], index=1)

# --- HYDRAULIC CALCULATIONS ---
viscosity_multiplier = {
    "Clean / Rainwater": 1.0, 
    "Light Mud / Silty": 1.15, 
    "Heavy Slurry / Gritty": 1.35
}[fluid_type]

# Unit conversion for matching the algorithm dataset bounds (L/s to m3/h)
flow_m3h = flow_target * 3.6

friction_loss = (pipe_length / 100.0) * (flow_target / pipe_dia) * 2.2 * viscosity_multiplier
tdh = static_head + friction_loss
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
col1, col2, col3, col4 = st.columns(4)
col1.metric("Required Flow Window", f"{flow_target:.1f} L/s", delta=f"{flow_m3h:.0f} m³/h equivalent")
col2.metric("Total Dynamic Head (TDH)", f"{tdh:.1f} m", delta=f"Incl. {friction_loss:.1f}m friction")
col3.metric("Auto Pipe Length", f"{pipe_length:.0f} m", delta=f"Vertical Lift: {static_head:.0f}m")
col4.metric("Est. Shaft Power", f"{estimated_power_kw:.1f} kW")

st.divider()

# --- AUTOMATED RANGE-BASED MATCH RECOMMENDATIONS ---
st.subheader("🏆 Performance Window Range Match Matrix")
st.markdown("The algorithm screens manufacturer operating windows to find pumps where your system requirements drop directly into the **Optimal Performance Range**:")

db_fluid_profile = "Clear" if "Clean" in fluid_type else ("Slurry" if "Heavy" in fluid_type else "Dirty")

recommendations = pump_selector.get_recommendation(
    head_required_m=tdh,
    flow_required_m3h=flow_m3h,
    water_profile=db_fluid_profile
)

if recommendations is None or recommendations.empty:
    st.error("❌ **No Single Pump Matches This Operating Window Range:** Your current combination of flow and head requirements sits outside standard performance curves. Adjust your sliders (e.g., increase pipe diameter to lower friction head, or select a lower flow target) or plan a multi-pump mid-pit staging setup.")
else:
    st.success(f"✅ Found **{len(recommendations)} standard industry assets** where your target requirements sit within optimal operational parameters:")
    
    for idx, row in recommendations.iterrows():
        with st.expander(f"👉 **{row['Manufacturer']} - {row['Model']}** (Ideal Range Fit)"):
            c_card1, c_card2 = st.columns(2)
            with c_card1:
                st.markdown(f"**Operational Role:** {row['Best_For']}")
                st.markdown(f"**Fluid Capability Classification:** Characterized for `{row['Water_Type']}` profiles.")
                st.markdown(f"**Max Permissible Solid Diameter:** Passing up to **{row['Max_Solids_mm']} mm** fragments.")
            with c_card2:
                st.markdown(f"📊 **Engineered Operational Window Range:**")
                st.markdown(f"*   **Optimal Head Range:** `{row['Min_Head_m']} m` up to `{row['Max_Head_m']} m`")
                st.markdown(f"*   **Optimal Flow Range:** `{row['Min_Flow_m3h']} m³/h` up to `{row['Max_Flow_m3h']} m³/h`")
                st.caption(f"🔧 **Drive Layout:** {row['Drive_Type']}")

st.divider()

# --- ELECTRICAL & PIPELINE HEALTH CHECKS ---
st.subheader("⚡ Electrical & Pipeline Health Checks")
col_gen, col_vel, col_press = st.columns(3)

with col_gen:
    st.markdown("#### Diesel Generator Sizing")
    motor_efficiency = 0.85
    generator_power_kva = (estimated_power_kw / motor_efficiency) * 1.25 / 0.8 
    st.metric("Minimum Recommended Genset", f"{generator_power_kva:.0f} kVA")
