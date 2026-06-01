from pathlib import Path
import io
import os
import json
import pandas as pd
import plotly.express as px
import streamlit as st
import tkinter as tk
from tkinter import filedialog
import atexit
import shutil
import sys

# Import your custom functions
from data_aggregator import aggregate_scenario_data
from generate_plot_data import generate_visualization_data

# --- SETUP ---
st.set_page_config(page_title="ArgoFilter", layout="wide")
st.title("Frame Analysis Dashboard")
st.markdown(
    "Search all scenarios globally, then deep-dive into specific traffic situations."
)

# Define paths - these will be in the same directory as this script
SCRIPT_DIR = Path(__file__).parent
METADATA_FILE = SCRIPT_DIR / "scenarios_metadata.json"
PLOT_DATA_DIR = SCRIPT_DIR / "plot_data"


def cleanup_metadata():
    """Remove metadata file and plot data directory when the app closes"""
    try:
        if METADATA_FILE.exists():
            METADATA_FILE.unlink()
            print(f"Removed {METADATA_FILE}")

        if PLOT_DATA_DIR.exists():
            shutil.rmtree(PLOT_DATA_DIR)
            print(f"Removed {PLOT_DATA_DIR}")
    except Exception as e:
        print(f"Error during cleanup: {e}")


# Register cleanup function - this will run when the Python process exits
atexit.register(cleanup_metadata)

# Initialize session state
if "paths" not in st.session_state:
    st.session_state.paths = []
if "processing" not in st.session_state:
    st.session_state.processing = False


# --- DATA LOADING FUNCTIONS ---
@st.cache_data
def load_metadata():
    """Load metadata from scenarios_metadata.json"""
    if not METADATA_FILE.exists():
        return pd.DataFrame()

    with open(METADATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    rows = []
    for item in data:
        row = {"id": item["id"]}
        row.update(item["objects"])
        rows.append(row)

    df = pd.DataFrame(rows).fillna(0)
    return df


@st.cache_data
def load_scenario_data(scenario_path):
    if not scenario_path or not os.path.exists(scenario_path):
        return pd.DataFrame()
    try:
        df = pd.read_json(scenario_path)
        return df
    except Exception as e:
        st.error(f"Error loading scenario: {e}")
        return pd.DataFrame()


def button_export(df_to_export):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_to_export.to_excel(writer, index=False, sheet_name="Data")
    excel_data = output.getvalue()
    st.download_button(
        label="Download Data",
        data=excel_data,
        file_name="filtered_scenario.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


# --- PLOTTING FUNCTIONS ---
def play_2D_map_animated(df):
    view_range = 70

    # MINIMAL FIX: Add a dummy row for each category at the first timestamp (invisible)
    all_categories = df["category"].unique()
    first_timestamp = df["timestamp_ns"].min()

    dummy_rows = []
    for cat in all_categories:
        if cat not in df[df["timestamp_ns"] == first_timestamp]["category"].values:
            dummy_rows.append(
                {
                    "timestamp_ns": first_timestamp,
                    "category": cat,
                    "x": 999,  # Way outside view range
                    "y": 999,
                    # Add any other required columns with placeholder values
                }
            )

    if dummy_rows:
        dummy_df = pd.DataFrame(dummy_rows)
        # Add any missing columns that your df has
        for col in df.columns:
            if col not in dummy_df.columns:
                dummy_df[col] = 0
        df = pd.concat([df, dummy_df], ignore_index=True)

    fig2 = px.scatter(
        df,
        x="x",
        y="y",
        color="category",
        animation_frame="timestamp_ns",
        range_x=[-view_range, view_range],
        range_y=[-view_range, view_range],
        title="Object X-Y coordinates by Category surrounding the car",
    )

    # Rest of your existing code unchanged...
    for radius in [20, 40, 60]:
        fig2.add_shape(
            type="circle",
            xref="x",
            yref="y",
            x0=-radius,
            y0=-radius,
            x1=radius,
            y1=radius,
            line=dict(color="rgba(255, 255, 255, 0.15)", width=1, dash="dash"),
        )
    fig2.update_traces(
        marker=dict(size=12, opacity=0.8, line=dict(width=1, color="DarkSlateGrey"))
    )
    fig2.update_layout(
        height=800,
        annotations=[
            dict(
                x=0,
                y=0,
                xref="x",
                yref="y",
                text="🚘",
                showarrow=False,
                font=dict(size=24),
            )
        ],
        template="plotly_dark",
        plot_bgcolor="rgba(20,20,20,1)",
        paper_bgcolor="rgba(20,20,20,1)",
        font=dict(color="white"),
        showlegend=True,
        legend=dict(
            x=1.02,
            y=1,
            font=dict(size=12, color="white"),
            bgcolor="rgba(30,30,30,0.5)",
            bordercolor="rgba(255,255,255,0.2)",
            borderwidth=1,
        ),
    )
    if fig2.layout.updatemenus:
        fig2.layout.updatemenus[0].buttons[0].args[1]["frame"]["duration"] = 50
        fig2.layout.updatemenus[0].buttons[0].args[1]["transition"]["duration"] = 0
    fig2.update_xaxes(
        showgrid=True,
        gridcolor="rgba(255,255,255,0.05)",
        zeroline=True,
        zerolinecolor="rgba(255,255,255,0.3)",
        showline=False,
    )
    fig2.update_yaxes(
        showgrid=True,
        gridcolor="rgba(255,255,255,0.05)",
        zeroline=True,
        zerolinecolor="rgba(255,255,255,0.3)",
        showline=False,
        scaleanchor="x",
        scaleratio=1,
    )
    st.plotly_chart(fig2, width="stretch")


def importer():
    """Open folder selection dialog"""
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    path = filedialog.askdirectory(
        initialdir=".", title="Select ArgoVerse Sensor Folder"
    )
    root.destroy()
    return path


def import_button():
    """Handle folder import and run both aggregation functions"""

    col1, col2 = st.columns([1, 1])
    with col1:
        clicked = st.button(
            "📁 Import ArgoVerse Folder", type="primary", use_container_width=True
        )
    with col2:
        if st.button("🗑️ Clear All Data", use_container_width=True):
            try:
                if METADATA_FILE.exists():
                    METADATA_FILE.unlink()
                if PLOT_DATA_DIR.exists():
                    shutil.rmtree(PLOT_DATA_DIR)
                st.session_state.paths = []
                st.cache_data.clear()
                st.success("✅ All data cleared!")
                st.rerun()
            except Exception as e:
                st.error(f"Error clearing data: {e}")

    if "paths" not in st.session_state:
        st.session_state["paths"] = []

    if clicked and not st.session_state.processing:
        selected_path = importer()
        if selected_path:
            st.session_state.processing = True

            try:
                with st.spinner("Processing scenarios... This may take a few minutes."):
                    # Run both aggregation functions
                    progress_bar = st.progress(0)

                    st.write("📊 Generating metadata...")
                    aggregate_scenario_data(selected_path)
                    progress_bar.progress(50)

                    st.write("🎨 Generating visualization data...")
                    generate_visualization_data(selected_path)
                    progress_bar.progress(100)

                    # Add to session state if not already there
                    if selected_path not in st.session_state["paths"]:
                        st.session_state["paths"].append(selected_path)

                    # Clear the cache to force reload of metadata
                    st.cache_data.clear()

                    st.success(
                        f"✅ Successfully imported and processed: {selected_path}"
                    )
                    st.balloons()
                    st.rerun()

            except Exception as e:
                st.error(f"❌ Error processing folder: {e}")
                st.session_state.processing = False
        else:
            st.info("No folder selected.")
            st.session_state.processing = False

    # Display imported paths
    if st.session_state.paths:
        st.markdown("### 📂 Previously Imported Folders")
        for i, p in enumerate(st.session_state.paths):
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.write(f"📁 {p}")
            with col2:
                if st.button("Re-import", key=f"reimport_{i}"):
                    try:
                        with st.spinner(f"Re-processing {p}..."):
                            aggregate_scenario_data(p)
                            generate_visualization_data(p)
                            st.cache_data.clear()
                            st.success("Re-import successful!")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
            with col3:
                if st.button("Remove", key=f"remove_{i}"):
                    st.session_state.paths.pop(i)
                    st.rerun()


# --- MAIN APP ---
def stream_lit():
    # Sidebar with status and cleanup options
    with st.sidebar:
        st.markdown("### 📊 Data Status")

        # Show status of metadata file
        if METADATA_FILE.exists():
            file_size = METADATA_FILE.stat().st_size / 1024  # KB
            st.success(f"✅ Metadata: {file_size:.1f} KB")
        else:
            st.warning("❌ No metadata file")

        if PLOT_DATA_DIR.exists():
            num_files = len(list(PLOT_DATA_DIR.glob("*.json")))
            st.success(f"✅ Plot data: {num_files} scenarios")
        else:
            st.warning("❌ No plot data")

    tab1, tab2, tab3, tab4 = st.tabs(
        ["Global Search", "Category Overview", "Static 2D Map", "Native Playback"]
    )

    # TAB 1: GLOBAL SEARCH (METADATA)
    with tab1:
        import_button()
        st.header("Global Scenario Search")

        # Add a manual refresh button
        col1, col2 = st.columns([4, 1])
        with col1:
            st.subheader("Search Scenarios")
        with col2:
            if st.button("🔄 Refresh", use_container_width=True):
                st.cache_data.clear()
                st.rerun()

        meta_df = load_metadata()

        if meta_df.empty:
            st.warning(
                "⚠️ No data found. Please import an ArgoVerse sensor folder using the button above."
            )
            st.info(
                "📖 **How to use:**\n"
                "1. Click 'Import ArgoVerse Folder'\n"
                "2. Select a folder containing ArgoVerse sensor data\n"
                "3. Wait for processing (may take a few minutes)\n"
                "4. Browse and filter scenarios"
            )
        else:
            st.sidebar.header("Global Filter")
            all_categories = sorted([col for col in meta_df.columns if col != "id"])
            selected_categories = st.sidebar.multiselect(
                "Filter by Categories", all_categories
            )

            filtered_meta_df = meta_df.copy()
            with st.sidebar:
                for cat in selected_categories:
                    max_val = int(meta_df[cat].max())
                    min_val = st.slider(
                        f"Minimum {cat}", min_value=0, max_value=max_val, value=0
                    )
                    filtered_meta_df = filtered_meta_df[
                        filtered_meta_df[cat] >= min_val
                    ]

            st.subheader(f"🎯 Found {len(filtered_meta_df)} matching scenarios")
            st.dataframe(filtered_meta_df, use_container_width=True)

            if not filtered_meta_df.empty:
                st.markdown("---")
                st.subheader("🔍 Deep Dive Analysis")
                selected_id = st.selectbox(
                    "Select a Scenario ID to analyze:", filtered_meta_df["id"].tolist()
                )

                if st.button("Load Scenario for Playback", type="primary"):
                    heavy_json_path = PLOT_DATA_DIR / f"{selected_id}.json"
                    if heavy_json_path.exists():
                        st.session_state["selected_scenario_path"] = str(
                            heavy_json_path
                        )
                        st.success(
                            f"✅ Scenario {selected_id} loaded! Check the other tabs."
                        )
                    else:
                        st.error(
                            f"❌ Could not find {heavy_json_path}. Make sure the data was generated properly."
                        )

    # Check if a scenario is loaded for tabs 2, 3, and 4
    scenario_path = st.session_state.get("selected_scenario_path", None)
    scenario_df = load_scenario_data(scenario_path)

    # TAB 2: OVERVIEW
    with tab2:
        if scenario_df.empty:
            st.info("ℹ️ Please load a scenario in the 'Global Search' tab first.")
        else:
            plot_count_df = (
                scenario_df.groupby(["timestamp_ns", "category"])
                .size()
                .reset_index(name="count")
            )
            fig = px.bar(
                plot_count_df,
                x="timestamp_ns",
                y="count",
                color="category",
                title="Objects over time in this scenario",
            )
            st.plotly_chart(
                fig,
                use_container_width=True,
                config={"scrollZoom": True, "displaylogo": False},
            )
            button_export(scenario_df)

    # TAB 3: STATIC MAP
    with tab3:
        if scenario_df.empty:
            st.info("ℹ️ Please load a scenario in the 'Global Search' tab first.")
        else:
            frame_num = st.selectbox(
                "Select a specific timestamp (frame)",
                options=sorted(scenario_df["timestamp_ns"].unique()),
            )
            df_frame = scenario_df[scenario_df["timestamp_ns"] == frame_num]
            fig1 = px.scatter(
                df_frame,
                x="x",
                y="y",
                color="category",
                title="Static 2D Map for selected frame",
            )
            fig1.add_scatter(
                x=[0],
                y=[0],
                mode="text",
                text=["🚗"],
                textfont=dict(size=20),
                name="Car position",
            )
            fig1.update_layout(
                template="plotly_dark",
                plot_bgcolor="rgba(20,20,20,1)",
                paper_bgcolor="rgba(20,20,20,1)",
                font=dict(color="white"),
            )
            fig1.update_yaxes(scaleanchor="x", scaleratio=1)
            st.plotly_chart(fig1, use_container_width=True)

    # TAB 4: NATIVE PLAYBACK
    with tab4:
        if scenario_df.empty:
            st.info("ℹ️ Please load a scenario in the 'Global Search' tab first.")
        else:
            st.header("Interactive 2D Map (Native Playback)")
            play_2D_map_animated(scenario_df.sort_values("timestamp_ns"))


if __name__ == "__main__":
    stream_lit()
