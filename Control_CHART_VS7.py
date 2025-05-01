import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from io import StringIO

st.set_page_config(page_title="ActVal Processor & Control Chart", layout="wide")
st.title("📊 ActVal Cleaner & Control Chart Analyzer")

# Upload raw CSV file
uploaded_file = st.sidebar.file_uploader("Upload raw ActVal.csv", type=["csv"])

if uploaded_file:
    try:
        # Load the file (comma-separated)
        df = pd.read_csv(uploaded_file, encoding='ascii', sep=',', on_bad_lines='skip')
        st.success("✅ Successfully loaded CSV using comma separator")

        # Check and convert 'Date' column
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            df = df[~df['Date'].isna()]  # Remove rows with invalid dates
            df.set_index('Date', inplace=True)
        else:
            st.error("❌ 'Date' column not found. Cannot continue.")
            st.stop()

        # Replace negative values in numeric columns with 0
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            df[col] = df[col].apply(lambda x: 0 if pd.notnull(x) and x < 0 else x)

        # Fill missing values
        for col in df.columns:
            if pd.api.types.is_numeric_dtype(df[col]):
                df[col].fillna(0, inplace=True)
            else:
                df[col].fillna('', inplace=True)

        # Ensure throughput column exists
        throughput_col = 'Dosing station 1: Total throughput'
        if throughput_col in df.columns:
            df[throughput_col] = pd.to_numeric(df[throughput_col], errors='coerce').fillna(0)
            df['Cumulative Throughput'] = df[throughput_col].cumsum()
            st.success("✅ Cumulative Throughput column added")
        else:
            st.warning(f"Column '{throughput_col}' not found. Skipping cumulative throughput.")

        # Download cleaned CSV
        cleaned_csv = df.reset_index().to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Cleaned CSV",
            data=cleaned_csv,
            file_name="ActVal_cleaned.csv",
            mime="text/csv"
        )

        # --- CONTROL CHART SECTION ---
        st.header("📈 Generate Control Charts")

        # Parameter groups
        main_parameters = {
            'Screw Speed': 'Extruder 1: Screw rotation speed',
            'Torque': 'Extruder 1: Screw torque',
            'Pressure': 'Extruder 1: Melt pressure 1',
            'Throughput': 'Dosing station 1: Total throughput'
        }

        heating_zone_cols = [col for col in df.columns if 'Extruder 1: temperature zone' in col]
        heating_zones = {
            f'Heating Zone {col.split("zone")[-1].strip()}': col for col in heating_zone_cols
        }

        all_parameters = {**main_parameters, **heating_zones}

        # Sidebar controls
        param_display = st.sidebar.selectbox("Choose Parameter for Control Chart", list(all_parameters.keys()))
        param_column = all_parameters[param_display]

        # Time range slider
        start_time, end_time = st.sidebar.slider(
            "Select Time Range",
            min_value=df.index.min().to_pydatetime(),
            max_value=df.index.max().to_pydatetime(),
            value=(df.index.min().to_pydatetime(), df.index.max().to_pydatetime()),
            format="YYYY-MM-DD HH:mm"
        )

        # Filter data
        df_filtered = df.loc[pd.Timestamp(start_time):pd.Timestamp(end_time)]
        data = df_filtered[[param_column]].dropna()
        series = data[param_column]

        # Compute control chart statistics
        mean = series.mean()
        std = series.std()
        ucl = mean + 3 * std
        lcl = mean - 3 * std
        if lcl < 0:
            lcl = max(0, series[series > 0].min() if series[series > 0].size > 0 else 0)

        points_above_ucl = (series > ucl).sum()
        points_below_lcl = (series < lcl).sum()
        total_points = len(series)
        pct_out = (points_above_ucl + points_below_lcl) / total_points * 100 if total_points else 0

        # --- Custom Label Annotation ---
        st.sidebar.markdown("### 🏷️ Add Custom Event Label to Chart")
        label_date = st.sidebar.date_input("Select Date for Label", value=start_time.date())
        label_clock = st.sidebar.time_input("Select Time for Label", value=start_time.time())
        label_text = st.sidebar.text_input("Enter Label Text", value="Custom Event")
        label_time = pd.to_datetime(f"{label_date} {label_clock}")

        # Plot the control chart
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(series.index, series, label=param_display, alpha=0.5)
        ax.axhline(mean, color='black', linestyle='-', label=f'Mean = {mean:.2f}')
        ax.axhline(ucl, color='red', linestyle='--', label=f'UCL = {ucl:.2f}')
        ax.axhline(lcl, color='red', linestyle='--', label=f'LCL = {lcl:.2f}')
        ax.plot(series[series > ucl].index, series[series > ucl], 'ro', label='Above UCL')
        ax.plot(series[series < lcl].index, series[series < lcl], 'go', label='Below LCL')
        ax.set_title(f'Control Chart for {param_display}')
        ax.set_xlabel('Time')
        ax.set_ylabel(param_display)
        ax.legend(loc='best')

        # Add label if valid
        if label_text.strip() != "":
            if label_time in series.index:
                label_value = series.loc[label_time]
                ax.annotate(
                    label_text,
                    xy=(label_time, label_value),
                    xytext=(label_time, label_value + 0.05 * (ucl - lcl)),
                    arrowprops=dict(facecolor='blue', shrink=0.05, width=1, headwidth=6),
                    fontsize=9,
                    color='blue',
                    rotation=30,
                    ha='left'
                )
            else:
                st.sidebar.warning("⚠️ Selected time not in visible data range.")

        # Format datetime axis
        locator = mdates.AutoDateLocator()
        formatter = mdates.ConciseDateFormatter(locator)
        ax.xaxis.set_major_locator(locator)
        ax.xaxis.set_major_formatter(formatter)
        fig.autofmt_xdate()

        st.pyplot(fig)

        # Display stats
        st.subheader("📊 Control Chart Statistics")
        stats_df = pd.DataFrame({
            'Statistic': ['Mean', 'Std Dev', 'UCL', 'LCL', 'Points Above UCL',
                          'Points Below LCL', 'Total Points', 'Out of Control %'],
            'Value': [f"{mean:.2f}", f"{std:.2f}", f"{ucl:.2f}", f"{lcl:.2f}",
                      points_above_ucl, points_below_lcl, total_points, f"{pct_out:.2f}%"]
        })

        st.table(stats_df)

        # Download stats
        stats_csv = stats_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Statistics CSV",
            data=stats_csv,
            file_name=f"{param_display.replace(' ', '_')}_stats.csv",
            mime='text/csv'
        )

    except Exception as e:
        st.error(f"❌ Error processing file: {e}")

else:
    st.info("📤 Upload a raw ActVal CSV file (comma-separated) to begin.")
