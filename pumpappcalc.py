import streamlit as st
import math
import pandas as pd

# Page Configuration
st.set_page_config(
    page_title="Open-Pit Dewatering Sizer",
    page_icon="⛏️",
    layout="wide"
)

# --- CLASS DEFINITION: INTEGRATED MANUFACTURER DATABASE ---
class MinePumpDatabase:
    def __init__(self):
        self.pumps_db = [
            {
                "Manufacturer": "Weir Minerals (Warman)",
                "Model": "Warman DWU",
                "Max_Flow_m3h": 1200,
                "Max_Head_m": 130,
                "Water_Type": "Slurry / Dirty",
                "Max_Solids_mm": 40.0,
                "Drive_Type": "Electric / Diesel",
                "Best_For": "Abrasive pit floor cleanup and dirty sump management"
            },
            {
                "Manufacturer": "Weir Minerals (Multiflo)",
                "Model": "Multiflo RF Series",
                "Max_Flow_m3h": 2200,
                "Max_Head_m": 220,
                "Water_Type": "Dirty / Runoff",
                "Max_Solids_mm": 60.0,
                "Drive_Type": "Diesel",
                "Best_For": "High-volume open-cut flood/storm emergency dewatering"
            },
            {
                "Manufacturer": "Xylem (Godwin)",
                "Model": "Godwin Dri-Prime CD200M",
                "Max_Flow_m3h": 520,
                "Max_Head_m": 50,
                "Water_Type": "Dirty / Runoff",
                "Max_Solids_mm": 75.0,
                "Drive_Type": "Diesel",
                "Best_For": "Snore conditions, fast automatic priming, and high solids transfer"
            },
            {
                "Manufacturer": "KSB Australia",
                "Model": "UPA 200 Borehole",
                "Max_Flow_m3h": 1000,
                "Max_Head_m": 420,
                "Water_Type": "Clear / Saline",
                "Max_Solids_mm": 2.0,
                "Drive_Type": "Electric",
                "Best_For": "Deep pit wall depressurisation and groundwater lowering"
            },
            {
                "Manufacturer": "KSB Australia",
                "Model": "Multitec Horizontal",
                "Max_Flow_m3h": 1500,
                "Max_Head_m": 1000,
                "Water_Type": "Clear / Low-Solids",
                "Max_Solids_mm": 5.0,
                "Drive_Type": "Electric / Diesel",
                "Best_For": "Ultra high-pressure multi-stage staging lines out of ultra-deep mines"
            },
            {
                "Manufacturer": "Sykes Group",
                "Model": "Sykes XH200-636",
                "Max_Flow_m3h": 828,
                "Max_Head_m": 208,
                "Water_Type": "Dirty / Runoff",
                "Max_Solids_mm": 31.0,
                "Drive_Type": "Diesel",
                "Best_For": "High-head pit bottom extraction with variable solids handling"
            },
            {
                "Manufacturer": "Pioneer Pump",
                "Model": "PP Series High-Head",
                "Max_Flow_m3h": 1800,
                "Max_Head_m": 210,
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
            
        return matches.sort_values(by=["Max_Head_m", "Max_Flow_m3h"], ascending=True)

# --- INIT DATABASE ---
pump_selector = MinePumpDatabase()

st.title("⛏️ Open-Pit Sump Dewatering & Pump Sizer")
st.markdown("A practical sizing tool built for non-specialists to quickly calculate head, check pipe velocity, and auto-recommend matching industry pumps.")

# --- SIDEBAR: INPUTS ---
st.sidebar.header("1. Site & Fluid Inputs")
flow_target = st.sidebar.number_input("Target Inflow / Pumping Rate (L/s)", value=30.0, step=5.0, format="%.1f")
fluid_type = st.sidebar.selectbox("Water Condition", ["Clean / Rainwater", "Light Mud / Silty", "Heavy Slurry / Gritty"])

st.sidebar.header("2. Geometry & Pipe Layout")
sump_rl = st.sidebar.number_input("Sump Floor Level (RL in meters)", value=100.0, step=1.0)
discharge_rl = st.sidebar.number_input("Surface Discharge Point Level (RL in meters)", value=220.0, step=1.0)
pipe_length = st.sidebar.number_input("Total Pipe Length (m)", value=450.0, step=10.0)
pipe_dia = st.sidebar.selectbox("HDPE Pipe Diameter (mm)", [100, 150, 200, 250, 300], index=1)

# --- HYDRAULIC CALCULATIONS ---
static_head = discharge_rl - sump_rl

viscosity_multiplier = {
    "Clean / Rainwater": 1.0, 
    "Light Mud / Silty": 1.15, 
    "Heavy Slurry / Gritty": 1.35
}[fluid_type]

# Unit conversion for matching the algorithm dataset (L/s to m3/h)
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
col1, col2, col3 = st.columns(3)
col1.metric("Required Flow", f"{flow_target:.1f} L/s", delta=f"{flow_m3h:.0f} m³/h equivalent")
col2.metric("Total Dynamic Head (TDH)", f"{tdh:.1f} m")
col3.metric("Est. Shaft Power", f"{estimated_power_kw:.1f} kW")

st.divider()

# --- AUTOMATED DATABASE MATCHING RECOMMENDATIONS ---
st.subheader("🏆 Automated Fleet & Manufacturer Match Matrix")
st.markdown("The system has cross-referenced your system curve against heavy industrial mining assets from **Weir Minerals, Xylem, KSB, and Sykes**:")

# Map interface select box text cleanly into database profile triggers
db_fluid_profile = "Clear" if "Clean" in fluid_type else ("Slurry" if "Heavy" in fluid_type else "Dirty")

recommendations = pump_selector.get_recommendation(
    head_required_m=tdh,
    flow_required_m3h=flow_m3h,
    water_profile=db_fluid_profile
)

if recommendations is not pd.DataFrame or recommendations.empty:
    st.error("❌ **No Single Pump Matches These Parameters Natively:** Your current lift or volume demands exceed single-stage boundaries. Consider a multi-pump series (staging layout), expanding your pipe diameter to drop friction head, or lower your target flow rate input.")
else:
    st.success(f"✅ Found **{len(recommendations)} viable industry assets** matching or exceeding your system requirements:")
    
    # Render out custom layout cards for matching pumps
    for idx, row in recommendations.iterrows():
        with st.expander(f"👉 **{row['Manufacturer']} - {row['Model']}** (Viable Setup Option)"):
            c_card1, c_card2 = st.columns([2, 1])
            with c_card1:
                st.markdown(f"**Operational Role:** {row['Best_For']}")
                st.markdown(f"**Fluid Capability Classification:** Rated for `{row['Water_Type']}` conditions.")
                st.markdown(f"**Max Permissible Solid Diameter:** Passing up to **{row['Max_Solids_mm']} mm** fragments clean.")
            with c_card2:
                st.metric("Max Rated Head", f"{row['Max_Head_m']} m")
                st.metric("Max Rated Flow", f"{row['Max_Flow_m3h']} m³/h")
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
    st.caption("💡 *Includes safety buffer for motor startup surge loads.*")

with col_vel:
    st.markdown("#### Pipeline Velocity Check")
    pipe_radius_m = (pipe_dia / 1000.0) / 2.0
    cross_section_area = math.pi * (pipe_radius_m ** 2)
    velocity_mps = (flow_target / 1000.0) / cross_section_area
    st.metric("Calculated Flow Velocity", f"{velocity_mps:.2f} m/s")
    if velocity_mps < 1.0:
        st.warning("⚠️ **Too Low (< 1.0 m/s):** Solids may settle out.")
    elif velocity_mps > 3.5:
        st.error("⚠️ **Too High (> 3.5 m/s):** High risk of erosion.")
    else:
        st.success("✅ **Optimal Velocity:** Ideal range (1.0 - 3.5 m/s).")

with col_press:
    st.markdown("#### Pipe Pressure Advisor")
    if pn_status == "Success":
        st.metric("Minimum Pipe Rating", recommended_pn, delta=f"{tdh_bar:.1f} bar req.")
        st.success("✅ Safe using standard poly lines.")
    elif pn_status == "Warning":
        st.metric("Minimum Pipe Rating", recommended_pn, delta=f"{tdh_bar:.1f} bar req.", delta_color="inverse")
        st.warning("⚠️ Heavy wall HDPE required.")
    else:
        st.metric("Pressure Error", recommended_pn, delta=f"{tdh_bar:.1f} bar!", delta_color="inverse")
        st.error("🚨 OVERPRESSURE: Needs multi-stage setup!")
