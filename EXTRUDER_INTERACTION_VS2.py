import streamlit as st
import pandas as pd
from datetime import datetime

# Initialize history
if 'history' not in st.session_state:
    st.session_state.history = []

# Get last entry for pre-filling
def get_last_entry():
    if st.session_state.history:
        return st.session_state.history[-1]
    else:
        return {
            "Screw Speed": 0.0,
            **{f"Zone {i+1}": 0.0 for i in range(10)},
            "Die Temp": 0.0,
            "Comments": ""
        }

# Navigation
page = st.sidebar.selectbox("Choose a page", ["Input Page", "History Page"])

if page == "Input Page":
    st.title("Extruder Settings Input")
    last_entry = get_last_entry()

    with st.form("input_form"):
        screw_speed = st.number_input("Screw Speed (rpm)", value=last_entry["Screw Speed"], step=0.1)

        heating_zones = []
        for i in range(10):
            val = st.number_input(
                f"Heating Zone {i+1} Temperature (°C)",
                value=last_entry[f"Zone {i+1}"],
                step=0.1
            )
            heating_zones.append(val)

        die_temp = st.number_input("Die Temperature (°C)", value=last_entry["Die Temp"], step=0.1)

        comments = st.text_area("Operator Comments", value="", height=200)

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
