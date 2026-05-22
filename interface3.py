from pathlib import Path
import io
import os
import platform
import subprocess
import generate_plot_data as gn_data
import pandas as pd
import plotly.express as px
import streamlit as st
import tkinter as tk
from tkinter import filedialog
import time
import layout_func as layout

st.set_page_config(page_title="ArgoFilter", layout="wide")
st.title("frame Analysis Dashboard")
st.markdown("Import folders, filter traffic frames, and visualize results.")


path_list = []  # List for holding all the different paths.


# For tabs
tab1, tab2, tab3, tab4 = st.tabs(["Filter", "Plot", "2D Map", "Native Playback"])


def load_scenario_data():
    if "selected_scenario_path" not in st.session_state or not st.session_state["selected_scenario_path"]:
        return pd.DataFrame()  # Return empty DataFrame if no scenario is selected

    scenario_path = st.session_state["selected_scenario_path"]
    try:
        df = pd.read_json(scenario_path)
        #df["scenario"] = os.path.basename(scenario_path)  # Add scenario name column
        return df
    except Exception as e:
        st.error(f"Error loading scenario: {e}")
        return pd.DataFrame()  # Return empty DataFrame on error
    
    
def button_export(df_to_export):
    output = io.BytesIO()  # creates buffer file.
    with pd.ExcelWriter(
        output, engine="openpyxl"
    ) as writer:  # write excel data into output
        df_to_export.to_excel(writer, index=False, sheet_name="Data")

    excel_data = output.getvalue()

    st.download_button(  # Button for downloading.
        label="Download Data",
        data=excel_data,
        file_name="filtered_argoverse.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


def stream_lit():

    # Filter tab
    with tab1:
        import_button() #Importing folder 
        select_scenario_button() #Importing scenarios from the folder. Once converted into json
        big_df = load_scenario_data()  # Loading in the file.

        if big_df.empty:
            st.warning(
                "No json-files inside the folder..."
            )  # Writes a warning in streamlit
            return
        if "category" not in big_df.columns:
            st.error("category missing")
            return

        # Sorting the data for categories, A-->Z. Removing (if NaN).
        categories = sorted(big_df["category"].dropna().unique())
        # counting number of objects in frames and categories.
        # Sorting the numbers of frames with numver of objects for each frame and creating a new data-frame.
        count_df = (big_df.groupby(["timestamp_ns", "category"]).size().reset_index(name="count"))
        
        
        f_table = count_df.pivot_table(
                index="timestamp_ns",
                columns="category",
                values="count",
                fill_value=0,
                aggfunc="sum"
                )
        # creating a sidebar with multiselection for each category
        with st.sidebar:
            st.header("Find frame")
            selected_categories = st.multiselect(
                "Select Categories", categories
            )  # Returns a list of the selected categories in the drop-down slider.


        

        slider_values = {}
        current_table = f_table.copy()#Copy of the table to apply filters on. 

        with st.sidebar:
            
            for category in selected_categories: 
                available_counts = sorted(current_table[category].unique())

                if len(available_counts) == 0:
                    st.warning(f"No available counts for {category}")
                    continue

                elif len(available_counts) == 1:
                    selected_count = available_counts[0]
                    st.write(f"{category}: {selected_count}")

                else:
                    selected_count = st.select_slider(
                        f"Select number of {category} in frame",
                        options=available_counts)

                slider_values[category] = selected_count

                current_table = current_table[current_table[category] == selected_count]
        
        filtered_df = pd.DataFrame(columns = ["timestamp_ns","category","count"]) #Empty dataframe for filtered data. 
        
        matching_timestamps = current_table.index

        filtered_df = count_df[count_df["timestamp_ns"].isin(matching_timestamps)]

        plot_df = big_df[big_df["timestamp_ns"].isin(matching_timestamps)]
        plot_count_df = (plot_df.groupby(["timestamp_ns", "category"]).size().reset_index(name="count"))
        
        col1, col2 = st.columns([1, 1], gap=None)

    with col1:
        st.write("Number of frames matching the filter: ", len(filtered_df["timestamp_ns"].unique()))
        st.subheader("Overview")
        st.dataframe(filtered_df, width="content")
        button_export(filtered_df)
    with col2:
        st.subheader("All objects in matching frames")
        st.dataframe(plot_df, width="content") 

    
        
        
       # Plot tab
    with tab2:
        fig = px.bar(
            plot_count_df,
            x="timestamp_ns",
            y="count",
            color="category",
            title="Object for each category in matching frame",
        )

        st.plotly_chart(fig, use_container_width=True,config = {"scrollZoom": True, "displaylogo": False})
    
    
    with tab3:
        frame_num = st.selectbox(
            label="Select a frame", options=plot_df["timestamp_ns"].unique()
        )

        st.write("The current frame is ", frame_num)
        st.header("2D map")
      
      
        df = plot_df[plot_df["timestamp_ns"] == frame_num]
        fig1 = px.scatter(
            df,
            x="x",
            y="y",
            color="category",  # optional
            title="Object X-Y coordinates by Category surrounding the car",
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
            legend=dict(
                x=0.02,
                y=0.98,
                font=dict(size=14, color="white"),
                bgcolor="rgba(30,30,30,0.9)",
                bordercolor="white",
                borderwidth=1,
            ),
        )

        fig1.update_xaxes(
            showgrid=True,
            gridcolor="rgba(255,255,255,0.1)",
            zeroline=False,
            showline=False,
        )

        fig1.update_yaxes(
            showgrid=True,
            gridcolor="rgba(255,255,255,0.1)",
            zeroline=False,
            showline=False,
        )

        fig1.update_yaxes(scaleanchor="x", scaleratio=1)

        st.plotly_chart(
            fig1,
            use_container_width=True,
            config={"scrollZoom": True, "displaylogo": False},
        )

    with tab4:
        play_frame_button(big_df) 


def play_2D_map_animated(df):
    view_range = 70 

    # 1. THE MAGIC: "animation_frame" tells Plotly to build a video automatically
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
    
    # 2. Add concentric radar rings
    for radius in [20, 40, 60]:
        fig2.add_shape(
            type="circle",
            xref="x", yref="y",
            x0=-radius, y0=-radius, x1=radius, y1=radius,
            line=dict(color="rgba(255, 255, 255, 0.15)", width=1, dash="dash"),
        )
    
    fig2.update_traces(marker=dict(size=12, opacity=0.8, line=dict(width=1, color='DarkSlateGrey')))

    # 3. Add ego vehicle as an annotation (so it stays in every single frame of the animation)
    fig2.update_layout(
        annotations=[
            dict(
                x=0, y=0, xref="x", yref="y",
                text="🚗", showarrow=False, font=dict(size=24)
            )
        ],
        plot_bgcolor="rgba(20,20,20,1)",
        paper_bgcolor="rgba(20,20,20,1)",
        font=dict(color="white"),
        showlegend=True,
        legend=dict(
            x=1.02, y=1,
            font=dict(size=12, color="white"),
            bgcolor="rgba(30,30,30,0.5)",
            bordercolor="rgba(255,255,255,0.2)",
            borderwidth=1
        )
    )

    # 4. CRITICAL: Speed up the native Plotly player to "Super Fast" (50ms per frame)
    if fig2.layout.updatemenus:
        fig2.layout.updatemenus[0].buttons[0].args[1]["frame"]["duration"] = 50
        fig2.layout.updatemenus[0].buttons[0].args[1]["transition"]["duration"] = 0 # Disables "morphing" between dots

    fig2.update_xaxes(showgrid=True, gridcolor="rgba(255,255,255,0.05)", zeroline=True, zerolinecolor="rgba(255,255,255,0.3)", showline=False)
    fig2.update_yaxes(showgrid=True, gridcolor="rgba(255,255,255,0.05)", zeroline=True, zerolinecolor="rgba(255,255,255,0.3)", showline=False, scaleanchor="x", scaleratio=1)

    st.plotly_chart(fig2, use_container_width=True)

    
def play_frame_button(filtered_df):
    st.header("Interactive 2D Map (Native Playback)")

 

    # Filter out the scenario and SORT by timestamp so the video plays in order
    scenario_df = filtered_df.copy()  # Make a copy to avoid modifying the original DataFrame
    scenario_df = scenario_df.sort_values("timestamp_ns")

    if scenario_df.empty:
        st.warning("No frames found for this scenario.")
        return

    # Pass the ENTIRE scenario dataframe to the plotter at once
    play_2D_map_animated(scenario_df)




def select_scenario_button():
    clicked = st.button("Selected Scenario from plot_data",type="primary")
    
    if "selected_scenario_path" not in st.session_state:
        st.session_state["selected_scenario_path"] = []
        
    if clicked: 
        st.session_state["selected_scenario_path"] = import_scenario_path()  # Using the same importer function to select a scenario folder.
        st.write("Selected scenario path:", st.session_state["selected_scenario_path"])
    







def import_button():

    clicked = st.button("Import Folder", type="primary")  # Uses st button  for clicked.

    if "paths" not in st.session_state:  # Checking if there is a path avalible in state
        st.session_state["paths"] = []  # Initiates an empty slot.

    if clicked:  # Clicked is abool. Returns true if clicked.

        selected_path = (
            importer()
        )  # Calling in the tkinter functions to find native path.
        gn_data.generate_visualization_data(
            selected_path
        )  # Using Majdi's function to read from a folder. Imported fron workspace folder.
        if selected_path and selected_path not in st.session_state["paths"]:
            st.session_state["paths"].append(
                selected_path
            )  # Checking if the path is in session_state["path"] and appends if not.
        if st.session_state["paths"] not in path_list:  # Adding to path_list.
            path_list.append(path_list.append(selected_path))

    for i, p in enumerate(
        st.session_state["paths"]
    ):  # This is for creating buttons on the fly as the size of frames may increase with multiple folders selected.
        col1, col2 = st.columns(
            [1, 1]
        )  # Left position for the pathname and right for remove-button.

        with col1:
            st.write(p)
        with col2:
            if st.button("Remove", key=f"remove_{i}"):
                del st.session_state["paths"][
                    i
                ]  # Removing the path when pressed removed.
                st.rerun()  # Updating streamlit.


# For opening file-system using tkinter. One file at a time.


def importer():
    root = tk.Tk()
    root.withdraw()  # Hides annoying tkinter window.
    root.attributes("-topmost", True)
    path = filedialog.askdirectory(
        initialdir=".", title="Select Folder"
    )  # Getting the local path for a folder.
    root.destroy()
    return path  # Returns the path as a string.



def import_scenario_path():
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    path = filedialog.askopenfilename(
        initialdir=".", title="Select Scenario JSON", filetypes=[("JSON files", "*.json")])
    root.destroy()
    return path

if __name__ == "__main__":
    stream_lit()
