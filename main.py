import folium
from streamlit_folium import st_folium
from math import radians, cos, sin, asin, sqrt
from datetime import datetime, timedelta
import streamlit as st
import numpy as np
import pandas as pd
import requests
import matplotlib.pyplot as plt
import base64
import os
import PyCO2SYS as pyco2

# ---- Haversine Function for Distance Calculation ----
def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great-circle distance between two points
    on the Earth using the Haversine formula.
    """
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371  # Radius of Earth in kilometers
    return c * r

# ---- BACKGROUND IMAGE FUNCTION ----
def set_background(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as image_file:
            encoded = base64.b64encode(image_file.read()).decode()
        page_bg_img = f"""
        <style>
        .stApp {{
            background-image: url("data:image/png;base64,{encoded}");
            background-size: cover;
            background-attachment: fixed;
        }}
        </style>
        """
        st.markdown(page_bg_img, unsafe_allow_html=True)
    else:
        st.warning("Background image not found. Proceeding without it.")

# ---- SETUP PAGE ----
st.set_page_config(page_title="Coastal & Ocean Engineering Toolkit", layout="wide")

# ---- Set Background ----
set_background("assets/coastal_bg.jpg")

# ---- TITLE ----
st.markdown("""
    <h1 style='text-align: center; color: black; font-weight: bold;'>🌊 Coastal & Ocean Engineering Toolkit</h1>
    <p style='text-align: center; color: black;'>Analyze tides, sediment transport, and shoreline change.</p>
""", unsafe_allow_html=True)

# ---- SIDEBAR ----
module = st.sidebar.radio("Choose Module", ["Tidal Analysis", "Sediment Transport", "Shoreline Change Prediction"])

# ---- 1. Tidal Analysis ----
stations = pd.DataFrame({
    "station_id": ["500-041", "500-065", "500-067", "500-081", "500-083",
                   "500-084", "500-085", "500-086", "500-087", "500-088"],
    "name": ["Mumbai", "Mormugao", "Karwar", "Cochin", "Chennai",
             "Visakhapatnam", "Paradeep", "Haldia", "Garden Reach", "Port Blair"],
    "lat": [18.95, 15.42, 14.8, 9.97, 13.1, 17.68, 20.32, 22.03, 22.54, 11.67],
    "lon": [72.82, 73.8, 74.13, 76.27, 80.29, 83.27, 86.61, 88.06, 88.31, 92.75]
})
if module == "Tidal Analysis":
    st.subheader("🌙 Tidal Analysis (Click on Map to Select Location)")

    m = folium.Map(location=[20.5, 80], zoom_start=5)
    for _, row in stations.iterrows():
        folium.Marker([row["lat"], row["lon"]], tooltip=row["name"]).add_to(m)

    map_data = st_folium(m, height=500, width=800)

    if map_data and map_data.get("last_clicked"):
        lat_clicked = map_data["last_clicked"]["lat"]
        lon_clicked = map_data["last_clicked"]["lng"]

        stations["distance_km"] = stations.apply(
            lambda row: haversine(lon_clicked, lat_clicked, row["lon"], row["lat"]), axis=1
        )
        nearest = stations.loc[stations["distance_km"].idxmin()]

        st.success(f"Nearest Station: {nearest['name']} ({nearest['station_id']})")

        # ---- Replace this block with real data fetching logic ----
        st.markdown("### Tidal Data (Mocked Example Plot)")
        dates = pd.date_range(datetime.now() - timedelta(days=3), periods=72, freq='H')
        heights = np.sin(np.linspace(0, 12 * np.pi, 72)) + 2

        fig, ax = plt.subplots()
        ax.plot(dates, heights, label='Tide Height', color='navy')
        ax.set_title(f"Tide Predictions - {nearest['name']}")
        ax.set_xlabel("Time")
        ax.set_ylabel("Tide Height (m)")
        ax.grid(True)
        ax.legend()
        st.pyplot(fig)

        st.metric("Estimated Tidal Range", f"{heights.max() - heights.min():.2f} m")

# ---- 2. Sediment Transport ----
elif module == "Sediment Transport":
    st.subheader("🏖️ Sediment Transport Calculator")

    u = st.number_input("Flow velocity (m/s)", value=1.0)
    d50 = st.number_input("Median grain size D50 (mm)", value=0.2)

    if st.button("Calculate Bedload Transport"):
        try:
            rho = 1025
            g = 9.81
            d50_m = d50 / 1000
            tau = rho * g * d50_m * u
            qs = 8 * ((tau - 0.047 * rho * g * d50_m)**1.5)
            st.metric("Sediment Transport Rate", f"{qs:.4f} m³/s/m")
        except Exception as e:
            st.error(f"Error in sediment transport calculation: {e}")

# ---- 3. Shoreline Change Prediction ----
elif module == "Shoreline Change Prediction":
    st.subheader("📉 Shoreline Change Prediction")

    ta = st.number_input("Total Alkalinity (µmol/kg)", value=2300)
    dic = st.number_input("Dissolved Inorganic Carbon (µmol/kg)", value=2000)
    temp = st.number_input("Temperature (°C)", value=20.0)
    sal = st.number_input("Salinity", value=35.0)

    if st.button("Run CO2SYS"):
        try:
            result = pyco2.sys(
                par1=dic, par2=ta, par1_type=2, par2_type=1,
                salinity=sal, temperature=temp, pressure=0,
                opt_pH_scale=1, opt_k_carbonic=10
            )
            omega_arag = result["saturation_aragonite"]
            st.metric("Ωₐ (Aragonite Saturation State)", f"{omega_arag:.2f}")
        except Exception as e:
            st.error(f"Error running PyCO2SYS: {e}")

    st.subheader("Shoreline Erosion Projection")
    year = st.slider("Years to Project", 1, 100, 10)
    erosion_rate = st.number_input("Erosion Rate (m/year)", value=0.5)

    future_change = erosion_rate * year
    st.metric("Projected Shoreline Retreat", f"{future_change:.2f} meters")
