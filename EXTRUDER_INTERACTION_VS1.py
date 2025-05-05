import streamlit as st
import pandas as pd
from datetime import datetime

# Initialize session state
if 'history' not in st.session_state:
    st.session_state.history = []

# Navigation
page = st.sidebar.selectbox("Choose a page", ["Input Page", "History Page"])

if page == "Input Page":
    st.title("Extruder Settings Input")

    with st.form("input_form"):
        screw_speed = st.number_input("Screw Speed (rpm)", min_value=0.0, step=0.1)

        heating_zones = []
        for i in range(1, 11):
            val = st.number_input(f"Heating Zone {i} Temperature (°C)", min_value=0.0, step=0.1)
            heating_zones.append(val)

        die_temp = st.number_input("Die Temperature (°C)", min_value=0.0, step=0.1)

        comments = st.text_area("Operator Comments", height=200)

        submitted = st.form_submit_button("Submit")

    if submitted:
        entry = {
            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Screw Speed": screw_speed,
            **{f"Zone {i+1}": temp for i, temp in enumerate(heating_zones)},
            "Die Temp": die_temp,
            "Comments": comments
        }
        st.session_state.history.append(entry)
        st.success("Entry submitted successfully!")

elif page == "History Page":
    st.title("Input History")

    if st.session_state.history:
        df = pd.DataFrame(st.session_state.history)
        st.dataframe(df, use_container_width=True)

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download as CSV", csv, "input_history.csv", "text/csv")
    else:
        st.info("No input history available.")
