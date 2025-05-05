import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

# --- Google Sheets Setup ---
def get_gsheet_connection():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_info(st.secrets["gsheets"], scopes=scope)
    client = gspread.authorize(creds)
    sheet = client.open("ExtruderLog").sheet1
    ensure_headers_exist(sheet)
    return sheet

def ensure_headers_exist(sheet):
    expected_headers = (
        ["Timestamp", "Screw Speed"] +
        [f"Zone {i+1}" for i in range(10)] +
        ["Die Temp", "Comments"]
    )
    current = sheet.row_values(1)
    if current != expected_headers:
        sheet.delete_rows(1)
        sheet.insert_row(expected_headers, index=1)

def save_to_gsheet(entry):
    sheet = get_gsheet_connection()
    sheet.append_row(list(entry.values()))

def load_history_from_gsheet():
    sheet = get_gsheet_connection()
    records = sheet.get_all_records()
    return pd.DataFrame(records)

def get_last_entry(df):
    if not df.empty:
        return df.iloc[-1].to_dict()
    else:
        return {
            "Timestamp": "",
            "Screw Speed": 0.0,
            **{f"Zone {i+1}": 0.0 for i in range(10)},
            "Die Temp": 0.0,
            "Comments": ""
        }

# --- Streamlit UI ---
st.set_page_config(page_title="Extruder Logbook", layout="wide")
page = st.sidebar.selectbox("Choose a page", ["Input Page", "History Page"])

if page == "Input Page":
    st.title("Extruder Settings Input")

    df_history = load_history_from_gsheet()
    last_entry = get_last_entry(df_history)

    with st.form("input_form"):
        screw_speed = st.number_input("Screw Speed (rpm)", value=float(last_entry.get("Screw Speed", 0.0)), step=0.1)

        heating_zones = []
        for i in range(10):
            val = st.number_input(
                f"Heating Zone {i+1} Temperature (°C)",
                value=float(last_entry.get(f"Zone {i+1}", 0.0)),
                step=0.1
            )
            heating_zones.append(val)

        die_temp = st.number_input("Die Temperature (°C)", value=float(last_entry.get("Die Temp", 0.0)), step=0.1)
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
        save_to_gsheet(entry)
        st.success("Entry submitted and saved to Google Sheets!")

elif page == "History Page":
    st.title("Input History")
    df_history = load_history_from_gsheet()

    if not df_history.empty:
        st.dataframe(df_history, use_container_width=True)
        csv = df_history.to_csv(index=False).encode("utf-8")
        st.download_button("Download as CSV", csv, "input_history.csv", "text/csv")
    else:
        st.info("No history found.")
