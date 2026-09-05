import streamlit as st
import math
import pandas as pd

# Page Configuration
st.set_page_config(
    page_title="Open-Pit Dewatering Sizer",
    page_icon="⛏️",
    layout="wide"
)

# --- CLASS DEFINITION: PUMP RANGE DATABASE ---
class MinePumpDatabase:
    def __init__(self):
        # Initializing manufacturer datasets with standard operating ranges
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
            (self.df["Max_Head_m"] >= head_required_m) & 
            (self.df["Max_Flow_m3h"] >= flow_required_m3h)
        ]
        
        if is_slurry_requested:
            matches = matches[matches["Water_Type"].str.contains("Slurry|Dirty", case=False)]
        
        if matches.empty:
            return None
            
        return matches.sort_values(by=["Max_Head_m"], ascending=True)

# --- INIT DATABASE ---
pump_selector = MinePumpDatabase()

st.title("Open-Pit Sump Dewatering & Pump Sizer")
st.markdown("A practical layout estimator built to quickly calculate pipeline length, estimate pipe pressure, and find matching catalog pumps.")

# --- SIDEBAR: INPUTS ---
st.sidebar.header("1. Water & Flow Settings")
flow_target = st.sidebar.number_input("Target Pumping Speed (Litres per second)", value=30.0, step=5.0, format="%.1f")
fluid_type = st.sidebar.selectbox("Water Condition", ["Clean / Rainwater", "Light Mud / Silty", "Heavy Slurry / Gritty"])

st.sidebar.header("2. Pit Elevations & Layout")
sump_rl = st.sidebar.number_input("Sump Floor Level (RL in meters)", value=100.0, step=1.0)
discharge_rl = st.sidebar.number_input("Surface Discharge Point (RL in meters)", value=220.0, step=1.0)

# AUTOMATED PIPE LENGTH LOGIC BASED ON HEIGHT DIFFERENCE
static_head = discharge_rl - sump_rl

if static_head <= 0:
    st.sidebar.error("The surface discharge level must be higher than the sump level.")
    static_head = 1.0

# 1:10 standard ramp gradient calculation
base_ramp_length = static_head * 10.0
st.sidebar.markdown(f"**Estimated Pit Ramp Distance:** `{base_ramp_length:.0f} m` *(assumes standard 1:10 haul road ramp)*")
pipe_slack_m = st.sidebar.number_input("Extra Pipe for Flat Ground / Bends (m)", value=50.0, step=10.0)

# Unified layout length used across all hydraulic math equations
pipe_length = base_ramp_length + pipe_slack_m
pipe_dia = st.sidebar.selectbox("Poly (HDPE) Pipe Diameter (mm)", [100, 150, 200, 250, 300], index=1)

# --- STAGING LOGIC ---
SINGLE_STAGE_MAX_HEAD = 130.0
is_multistage_required = static_head > SINGLE_STAGE_MAX_HEAD

if is_multistage_required:
    active_calc_head = SINGLE_STAGE_MAX_HEAD
    recommended_booster_rl = sump_rl + SINGLE_STAGE_MAX_HEAD
else:
    active_calc_head = static_head

# --- CALCULATIONS ---
viscosity_multiplier = {
    "Clean / Rainwater": 1.0, 
    "Light Mud / Silty": 1.15, 
    "Heavy Slurry / Gritty": 1.35
}[fluid_type]

flow_m3h = flow_target * 3.6
friction_loss = (pipe_length / 100.0) * (flow_target / pipe_dia) * 2.2 * viscosity_multiplier
tdh = active_calc_head + friction_loss
estimated_power_kw = (flow_target * tdh * 9.81) / (1000 * 0.65)

# --- PIPE PRESSURE ADVISOR CALCULATIONS ---
tdh_bar = tdh / 10.197

if tdh_bar <= 6.0:
    recommended_pn = "PN6"
    sdr_val = 26.0
    pn_status = "Success"
elif tdh_bar <= 10.0:
    recommended_pn = "PN10"
    sdr_val = 17.0
    pn_status = "Success"
elif tdh_bar <= 16.0:
    recommended_pn = "PN16"
    sdr_val = 11.0
    pn_status = "Success"
elif tdh_bar <= 20.0:
    recommended_pn = "PN20"
    sdr_val = 9.0
    pn_status = "Warning"
else:
    recommended_pn = "EXCEEDS STANDARD LIMITS"
    sdr_val = 7.4
    pn_status = "Critical"

# --- PIPE WEIGHT CALCULATIONS ---
calculated_wall_thickness = pipe_dia / sdr_val
calculated_internal_dia = pipe_dia - (2.0 * calculated_wall_thickness)
cross_section_poly_area_m2 = (math.pi / 4.0) * (((pipe_dia / 1000.0)**2) - ((calculated_internal_dia / 1000.0)**2))
unit_weight_kg_m = cross_section_poly_area_m2 * 955.0
total_pipeline_weight_kg = pipe_length * unit_weight_kg_m
total_pipeline_weight_tonnes = total_pipeline_weight_kg / 1000.0

# --- MAIN PANEL: RESULTS ---
st.subheader("System Results Summary")

if is_multistage_required:
    st.error(f"Setup Warning: The vertical lift ({static_head:.0f}m) is too high for a standard single pump setup ({SINGLE_STAGE_MAX_HEAD:.0f}m limit). The calculations below have been limited to a Single Stage layout. You will need to add a second booster pump station around RL {recommended_booster_rl:.0f}m.")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Pumping Speed", f"{flow_target:.1f} L/s", delta=f"{flow_m3h:.0f} m³/h equivalent")
col2.metric("Total Pumping Head", f"{tdh:.1f} m", delta=f"Includes {friction_loss:.1f}m pipe friction")
col3.metric("Total Pipe Needed", f"{pipe_length:.0f} m", delta=f"Vertical Lift: {static_head:.0f}m")
col4.metric("Estimated Motor Power", f"{estimated_power_kw:.1f} kW")

st.divider()

# --- RECONCILED PUMP SELECTIONS ---
st.subheader("Recommended Supplier Pump Models")
st.markdown("These industrial pumps from major brands can handle your setup requirements comfortably within their normal operating windows:")

db_fluid_profile = "Clear" if "Clean" in fluid_type else ("Slurry" if "Heavy" in fluid_type else "Dirty")

recommendations = pump_selector.get_recommendation(
    head_required_m=tdh,
    flow_required_m3h=flow_m3h,
    water_profile=db_fluid_profile
)

if recommendations is None or recommendations.empty:
    st.error("No Single Pump Matches: Your setup demands sit outside normal equipment ranges. Try choosing a larger pipe diameter to reduce friction pressure, or lower your target pumping speed.")
else:
    st.success(f"Found {len(recommendations)} standard industry models capable of running this line setup:")
    
    for idx, row in recommendations.iterrows():
        with st.expander(f"{row['Manufacturer']} — {row['Model']}"):
            c_card1, c_card2 = st.columns(2)
            with c_card1:
                st.markdown(f"**What it's used for:** {row['Best_For']}")
                st.markdown(f"**Water capability:** Safe for `{row['Water_Type']}` conditions.")
                st.markdown(f"**Maximum solid size:** Can pass dirt/debris up to **{row['Max_Solids_mm']} mm**.")
            with c_card2:
                st.markdown(f"**Pump Capabilities:**")
                st.markdown(f"*   **Safe Head Range:** `{row['Min_Head_m']} m` to `{row['Max_Head_m']} m`")
                st.markdown(f"*   **Safe Flow Range:** `{row['Min_Flow_m3h']} m³/h` to `{row['Max_Flow_m3h']} m³/h`")
