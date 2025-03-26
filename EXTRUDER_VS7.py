import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta
import time

st.set_page_config(page_title="Extruder Dashboard", layout="wide")

# Sidebar Navigation
page = st.sidebar.radio("Navigation", ["Extruder Diagram", "Temperature Chart", "Process Control QC Band", "Live SPC Monitoring"])

# Default temperature profile for 10 zones (Celsius)
default_temps = [180, 190, 200, 210, 220, 230, 230, 220, 210, 200]

data_file = "extruder_data.csv"
live_data_file = "live_spc_data.csv"

# Initialize input storage
zone_temps = []

if page == "Extruder Diagram":
    st.title("Extruder System Overview")

    # Input boxes directly below extruder zones
    st.subheader("Extruder Diagram with Zone Inputs")
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.set_xlim(0, 15)
    ax.set_ylim(0, 4)
    ax.axis('off')

    # Barrel
    ax.add_patch(plt.Rectangle((2, 1.5), 10, 1, linewidth=2, edgecolor='black', facecolor='lightgrey'))

    # Screw inside barrel
    for i in range(40):
        x = 2 + i * 0.25
        y = 2
        ax.add_patch(plt.Circle((x, y), 0.08, color='black'))

    # Hopper
    ax.add_patch(plt.Polygon([[1.5, 3], [2.5, 3], [2.2, 2.5], [1.8, 2.5]], closed=True, facecolor='blue', edgecolor='black'))
    ax.text(1.6, 3.1, "Hopper", fontsize=9)

    # Heating Zones
    for i in range(10):
        ax.add_patch(plt.Rectangle((2 + i, 1.3), 1, 1.4, linewidth=1, edgecolor='red', facecolor='none', linestyle='--'))
        ax.text(2.5 + i, 2.9, f"Z{i+1}", fontsize=8, ha='center')

    # Motor and Gearbox
    ax.add_patch(plt.Rectangle((0.5, 1.7), 1, 0.6, linewidth=2, edgecolor='black', facecolor='gray'))
    ax.text(0.55, 2.4, "Motor", fontsize=9)
    ax.add_patch(plt.Rectangle((1.5, 1.7), 0.5, 0.6, linewidth=2, edgecolor='black', facecolor='darkgray'))
    ax.text(1.55, 2.4, "Gearbox", fontsize=9)

    # Die
    ax.add_patch(plt.Rectangle((12.2, 1.7), 1, 0.6, linewidth=2, edgecolor='black', facecolor='orange'))
    ax.text(12.3, 2.4, "Die", fontsize=9)

    # Output product
    ax.add_patch(plt.Rectangle((13.3, 1.9), 1.5, 0.2, linewidth=1, edgecolor='black', facecolor='green'))
    ax.text(13.4, 2.2, "Extrudate", fontsize=9)

    st.pyplot(fig)

    # Input directly below diagram, aligned with zones
    st.subheader("Enter Temperatures for Each Zone")
    cols = st.columns(10)
    for i, col in enumerate(cols):
        temp = col.number_input(f"Z{i+1}", min_value=0, max_value=400, value=default_temps[i], step=1, key=f"zone_{i+1}")
        zone_temps.append(temp)

    screw_speed = st.number_input("Screw Speed (RPM)", min_value=0, max_value=500, value=50, step=1, key="screw_speed")
    st.metric("Screw Speed", f"{screw_speed} RPM")

    # Save button
    if st.button("Save Data"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        row = [timestamp] + zone_temps + [screw_speed]
        columns = ["Timestamp"] + [f"Zone_{i+1}" for i in range(10)] + ["Screw_Speed"]

        if not os.path.exists(data_file):
            df = pd.DataFrame([row], columns=columns)
        else:
            df = pd.read_csv(data_file)
            new_row = pd.DataFrame([row], columns=columns)
            df = pd.concat([df, new_row], ignore_index=True)

        df.to_csv(data_file, index=False)
        st.success("Data saved successfully!")

elif page == "Temperature Chart":
    st.title("Temperature Profile Across Zones")
    st.subheader("Visual Representation of Barrel Heating Zones")

    # Recreate temperatures from session state
    for i in range(10):
        zone_temps.append(st.session_state.get(f"zone_{i+1}", default_temps[i]))

    df = pd.DataFrame({"Zone": list(range(1, 11)), "Temperature (°C)": zone_temps})
    df = df.set_index("Zone")
    st.bar_chart(df)

    # Show screw speed if exists
    screw_speed = st.session_state.get("screw_speed", 50)
    st.write(f"**Screw Speed:** {screw_speed} RPM")

    # If data file exists, show QC band
    if os.path.exists(data_file):
        st.subheader("Quality Control Operating Band")
        historical_df = pd.read_csv(data_file)
        st.line_chart(historical_df[[f"Zone_{i+1}" for i in range(10)]])

elif page == "Process Control QC Band":
    st.title("Process Control Quality Bands")
    st.subheader("Simulated Zone Readings Over Time")

    # Simulate 60 minutes of data, once per minute
    timestamps = [datetime.now() - timedelta(minutes=i) for i in range(59, -1, -1)]
    data = {
        "Timestamp": timestamps
    }
    for i in range(10):
        base = default_temps[i]
        data[f"Zone_{i+1}"] = base + np.random.normal(0, 2, 60)
    data["Screw_Speed"] = 50 + np.random.normal(0, 2, 60)

    df_sim = pd.DataFrame(data)
    df_sim.set_index("Timestamp", inplace=True)

    st.line_chart(df_sim[[f"Zone_{i+1}" for i in range(10)]])
    st.line_chart(df_sim[["Screw_Speed"]])

elif page == "Live SPC Monitoring":
    st.title("Live SPC Monitoring: Heating Zones & Screw Speed")

    # Load or initialize data
    if os.path.exists(live_data_file):
        df_live = pd.read_csv(live_data_file, parse_dates=["Timestamp"])
    else:
        df_live = pd.DataFrame(columns=["Timestamp"] + [f"Zone_{i+1}" for i in range(10)] + ["Screw_Speed"])

    # Generate new data every 15 seconds and append to CSV
    current_time = datetime.now()
    if len(df_live) == 0 or (current_time - df_live.iloc[-1]["Timestamp"]).total_seconds() >= 15:
        new_row = {
            "Timestamp": current_time,
            **{f"Zone_{i+1}": default_temps[i] + np.random.normal(0, 2) for i in range(10)},
            "Screw_Speed": 50 + np.random.normal(0, 1)
        }
        df_live = pd.concat([df_live, pd.DataFrame([new_row])], ignore_index=True).tail(100)
        df_live.to_csv(live_data_file, index=False)

    df_live["Timestamp"] = pd.to_datetime(df_live["Timestamp"])
    df_live.set_index("Timestamp", inplace=True)

    # Show SPC charts
    for i in range(10):
        zone = f"Zone_{i+1}"
        mean = df_live[zone].mean()
        std = df_live[zone].std()
        ucl = mean + 3 * std
        lcl = mean - 3 * std

        st.subheader(f"{zone} SPC Chart")
        fig, ax = plt.subplots()
        ax.plot(df_live.index, df_live[zone], label='Value')
        ax.axhline(mean, color='green', linestyle='--', label='Mean')
        ax.axhline(ucl, color='red', linestyle='--', label='UCL')
        ax.axhline(lcl, color='red', linestyle='--', label='LCL')
        ax.set_ylabel('Temperature (°C)')
        ax.set_xlabel('Time')
        ax.legend()
        st.pyplot(fig)

    # Screw Speed SPC Chart
    mean_ss = df_live["Screw_Speed"].mean()
    std_ss = df_live["Screw_Speed"].std()
    ucl_ss = mean_ss + 3 * std_ss
    lcl_ss = mean_ss - 3 * std_ss

    st.subheader("Screw Speed SPC Chart")
    fig, ax = plt.subplots()
    ax.plot(df_live.index, df_live["Screw_Speed"], label='Screw Speed', color='purple')
    ax.axhline(mean_ss, color='green', linestyle='--', label='Mean')
    ax.axhline(ucl_ss, color='red', linestyle='--', label='UCL')
    ax.axhline(lcl_ss, color='red', linestyle='--', label='LCL')
    ax.set_ylabel('RPM')
    ax.set_xlabel('Time')
    ax.legend()
    st.pyplot(fig)

    st.toast("Updated with new data if 15 seconds have passed.", icon="🔄")
    st.experimental_rerun()
