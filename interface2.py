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
tab1, tab2, tab3, tab4 = st.tabs(["Filter", "Plot", "2D Map", "Frame-shifter"])


def load_data(folder_path="plot_data"):
    folder = Path(folder_path)
    all_dfs = []  # list for all data. each json-list = one data frame.
    # Reading all the json-files into datastruct.
    for i, file in enumerate(
        folder.glob("*.json")
    ):  # picks everything matching with json-format.
        df = pd.read_json(file)  # Reads into df, each json file.
        df["frame"] = file.stem  # add extra column for frame name
        df["frame_id"] = i  # Adding id.
        all_dfs.append(df)

    if not all_dfs:
        return pd.DataFrame()

    return pd.concat(all_dfs, ignore_index=True)  # Merge into one big table.


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
        import_button()

        big_df = load_data()  # Loading in the file.

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
        count_df = (
            big_df.groupby(["frame", "category"]).size().reset_index(name="count")
        )

        # creating a sidebar with multiselection for each category
        with st.sidebar:
            st.header("Find frame")
            selected_categories = st.multiselect(
                "Select Categories", categories
            )  # Returns a list of the selected categories in the drop-down slider.

        slider_values = {}  # Dict for all the vales from the sliders.

        # creating sliders for each category. Get the slider value

        with st.sidebar:
            for (
                cat
            ) in (
                selected_categories
            ):  # for each category, in the list of selected categories.
                max_count = int(
                    count_df[count_df["category"] == cat]["count"].max()
                )  # Find the ocurrences in each category
                # create sliders for eeach category. The max_count is the maximum count of occurences for each category.
                slider_values[cat] = st.slider(
                    f"Antal {cat}",
                    min_value=0,
                    max_value=max_count,
                    value=0,
                    key=f"slider_{cat}",
                )

        # Starting all frames.
        matching_frames = set(
            big_df["frame"].unique()
        )  # Gets all unique frame names. No duplicates. Set converts into python set for unique values.

        # Filtrera framen som matchar EXAKT antal för varje vald kategori
        for (
            cat,
            desired_count,
        ) in (
            slider_values.items()
        ):  # Looks trough the slider values (dict) and match with the count of each category.
            # hitta alla frames där
            matching_for_cat = set(
                count_df[
                    (count_df["category"] == cat) & (count_df["count"] == desired_count)
                ]["frame"].unique()
            )  # Using intersection to match with slider values and its categories.

            # Only used when the 0 - category is used.
            if desired_count == 0:
                frames_with_cat = set(
                    count_df[count_df["category"] == cat]["frame"].unique()
                )  # finds all frames where the category exists at least once.
                all_frames = set(
                    big_df["frame"].unique()
                )  # create set of all frames in the whole dataset.
                # Finding frames without that categories.
                frames_without_cat = (
                    all_frames - frames_with_cat
                )  # Take all secenarios, remove the ones that contains this category.
                matching_for_cat = (
                    matching_for_cat | frames_without_cat
                )  # Adds the frames with no such category to the already matching frame.

            matching_frames = (
                matching_frames & matching_for_cat
            )  # Keeps only frames that were already valid, and match current category condition

        # The filtered frame containing  all the matching frames with the "selection through sliders"
        filtered_df = big_df[big_df["frame"].isin(matching_frames)]

        st.subheader("Matching frames")
        st.write("Number of frames:", filtered_df["frame"].nunique())
        st.write(
            "Frames that match filter criteria:",
            layout.get_frame_ranges(filtered_df["frame_id"].unique()),
        )

        if filtered_df.empty:
            st.info("No matching frames.")
            return

        # Visa summering per frame och kategori
        filtered_count_df = (
            filtered_df.groupby(["frame_id", "category"])
            .size()
            .reset_index(name="count")
        )

        col1, col2 = st.columns([1, 1], gap=None)

        with col1:
            st.subheader("Overview")
            st.dataframe(filtered_count_df, width="content")
        button_export(filtered_df)
        with col2:
            st.subheader("All objects in matching frames")
            st.dataframe(filtered_df, width="content")

    # Plot tab
    with tab2:
        fig = px.bar(
            filtered_count_df,
            x="frame_id",
            y="count",
            color="category",
            title="Object for each category in matching frame",
        )

        st.plotly_chart(fig, width="stretch")

    with tab3:
        frame_num = st.selectbox(
            label="Select a frame", options=filtered_df["frame_id"].unique()
        )

        st.write("The current frame is ", frame_num)

        st.header("2D map")
        import plotly.express as py

        df = filtered_df[filtered_df["frame_id"] == frame_num]
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
        play_frame_button(filtered_df)


# This function simply plots each dataframe when called.
def play_2D_map(df, placeholder):

    fig2 = px.scatter(
        df,
        x="x",
        y="y",
        color="category",
        title="Object X-Y coordinates by Category surrounding the car",
    )
    fig2.add_scatter(
        x=[0],
        y=[0],
        mode="text",
        text=["🚗"],
        textfont=dict(size=20),
        name="Car position",
    )
    fig2.update_xaxes(
        showgrid=True, gridcolor="rgba(255,255,255,0.1)", zeroline=False, showline=False
    )

    fig2.update_yaxes(
        showgrid=True, gridcolor="rgba(255,255,255,0.1)", zeroline=False, showline=False
    )

    fig2.update_yaxes(scaleanchor="x", scaleratio=1)

    placeholder.plotly_chart(fig2, use_container_width=True)

    # This button uses the already filtered frames play frame by frame in streamlit.


def play_frame_button(filtered_df):

    st.header("Interactive 2D map")

    play_back = filtered_df  # The filtered dataframes.
    play_back["time_index"] = 0
    placeholder = st.empty()  # Reserved empty place.

    col1, col2, col3 = st.columns(3)  # columns for each button.
    with col1:
        play = st.button("Play frame")
    with col2:
        backward = st.button("Previous Frame")
    with col3:
        forward = st.button("Next frame")

    if (
        "play_state" not in st.session_state
    ):  # Initiating empty streamlit "dict" for storing data. Each time a user interacts with streamlit, it updates so variables are not stored.
        st.session_state.play_state = 0

    timestamps = sorted(
        play_back["timestamp_ns"].unique()
    )  # list of all frames sorted according to time.
    frame_lenght = len(play_back["timestamp_ns"].unique())  # Same but with lenght
    text_placeholder = st.empty()
    if play:  # if play button is pressed..
        st.write()
        for i, timestamp_ns in enumerate(
            sorted(play_back["timestamp_ns"].unique())
        ):  # Loop over the timestamps in sorted order.
            df = play_back[play_back["timestamp_ns"] == timestamp_ns]  # Save the frame.
            text_placeholder.write(
                f"Timestamp: {timestamp_ns}"
            )  # add txt to placeholder
            play_2D_map(df, placeholder)  # Run function to plot map frame by frame
            time.sleep(
                0.5
            )  # small delay in loop. Could make this into a button if we want to controll.

    if forward and st.session_state.play_state < frame_lenght - 1:
        st.session_state.play_state += 1
        current_ts = timestamps[st.session_state.play_state]
        df = play_back[play_back["timestamp_ns"] == current_ts]
        text_placeholder.write(f"Timestamp: {current_ts}")
        play_2D_map(df, placeholder)

    if backward and st.session_state.play_state > 0:
        st.session_state.play_state -= 1
        current_ts = timestamps[st.session_state.play_state]
        df = play_back[play_back["timestamp_ns"] == current_ts]
        text_placeholder.write(f"Timestamp: {current_ts}")
        play_2D_map(df, placeholder)


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


if __name__ == "__main__":
    stream_lit()
    print(path_list)
