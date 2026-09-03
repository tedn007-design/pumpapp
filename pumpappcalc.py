import streamlit as st
import math

# Page Configuration
st.set_page_config(
    page_title="Open-Pit Dewatering Sizer",
    page_icon="⛏️",
    layout="wide"
)

st.title("⛏️ Open-Pit Sump Dewatering & Pump Sizer")
st.markdown("A practical sizing tool built for non-specialists to quickly calculate head, check pipe velocity, and validate selected pumps.")

# --- SIDEBAR: INPUTS ---
st.sidebar.header("1. Site & Fluid Inputs")
flow_target = st.sidebar.number_input("Target Inflow / Pumping Rate (L/s)", value=30.0, step=5.0, format="%.1f")
fluid_type = st.sidebar.selectbox("Water Condition", ["Clean / Rainwater", "Light Mud / Silty", "Heavy Slurry / Gritty"])

st.sidebar.header("2. Geometry & Pipe Layout")
sump_rl = st.sidebar.number_input("Sump Floor Level (RL in meters)", value=100.0, step=1.0)
discharge_rl = st.sidebar.number_input("Surface Discharge Point Level (RL in meters)", value=220.0, step=1.0)
pipe_length = st.sidebar.number_input("Total Pipe Length (m)", value=450.0, step=10.0)
pipe_dia = st.sidebar.selectbox("HDPE Pipe Diameter (mm)", [100, 150, 200, 250, 300], index=1)

# --- CALCULATIONS ---
static_head = discharge_rl - sump_rl

viscosity_multiplier = {
    "Clean / Rainwater": 1.0, 
    "Light Mud / Silty": 1.15, 
    "Heavy Slurry / Gritty": 1.35
}[fluid_type]

friction_loss = (pipe_length / 100.0) * (flow_target / pipe_dia) * 2.2 * viscosity_multiplier
tdh = static_head + friction_loss
estimated_power_kw = (flow_target * tdh * 9.81) / (1000 * 0.65)

# --- MAIN PANEL: RESULTS ---
st.subheader("📊 System & Head Results")
col1, col2, col3 = st.columns(3)
col1.metric("Required Flow", f"{flow_target:.1f} L/s")
col2.metric("Total Dynamic Head (TDH)", f"{tdh:.1f} m")
col3.metric("Est. Shaft Power", f"{estimated_power_kw:.1f} kW")

st.divider()

# --- PUMP LINK & SPEC VALIDATOR ---
st.subheader("🔗 External Pump Link & Spec Validator")
st.markdown("Found a pump online? Paste its link and its rated maximum specs below to see if it can handle your pit's requirements.")

with st.form(key="pump_validator_form"):
    col_link, col_name = st.columns([2, 1])
    with col_link:
        pump_url = st.text_input("Pump Product URL", placeholder="https://www.supplier-catalog.com/pump-model-x")
    with col_name:
        pump_model_name = st.text_input("Pump Model Name / Brand", placeholder="e.g., Toyo DP-30")
        
    st.markdown("##### Enter the Pump's Rated Specifications (from its data sheet):")
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        rated_max_flow = st.number_input("Rated Max Flow (L/s)", value=35.0, step=5.0)
    with col_p2:
        rated_max_head = st.number_input("Rated Max Head (m)", value=140.0, step=5.0)
        
    submit_validation = st.form_submit_button("🔍 Validate Pump Suitability")

if submit_validation:
    st.markdown("---")
    st.markdown(f"### Evaluation for: **{pump_model_name if pump_model_name else 'Selected Pump'}**")
    if pump_url:
        st.markdown(f"🔗 **Source Link:** [View Pump Listing]({pump_url})")
        
    flow_ok = rated_max_flow >= flow_target
    head_ok = rated_max_head >= tdh
    
    col_v1, col_v2 = st.columns(2)
    with col_v1:
        if flow_ok:
            st.success(f"✅ **Flow Check Passed:** Rated flow ({rated_max_flow} L/s) meets or exceeds target ({flow_target} L/s).")
        else:
            st.error(f"❌ **Flow Check Failed:** Rated flow ({rated_max_flow} L/s) is too low for your target ({flow_target} L/s).")
            
    with col_v2:
        if head_ok:
            st.success(f"✅ **Head Check Passed:** Rated head ({rated_max_head} m) can handle the required TDH ({tdh:.1f} m).")
        else:
            st.error(f"❌ **Head Check Failed:** Rated head ({rated_max_head} m) cannot overcome your total head ({tdh:.1f} m).")
            
    if flow_ok and head_ok:
        st.success("🎉 **Verdict:** This pump model appears **SUITABLE** for your system curve based on its maximum rating boundaries!")
    else:
        st.warning("⚠️ **Verdict:** This pump is **UNSUITABLE** or runs too close to its limit. Look for a larger model or implement a multi-stage configuration.")

st.divider()

# --- ELECTRICAL & PIPELINE HEALTH CHECKS ---
st.subheader("⚡ Electrical & Pipeline Health Checks")
col_gen, col_vel = st.columns(2)

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
