from pathlib import Path
import io
import os
import platform
import subprocess
import pandas as pd
import plotly.express as px
import streamlit as st
import tkinter as tk
from tkinter import filedialog

st.title("Scenario Analysis Dashboard")
st.markdown(
    "Import folders, filter traffic scenarios, and visualize results."
)


path_list = []


#For tabs 
tab1, tab2, tab3 = st.tabs(["Filter","Plot", "2D Map"])


def load_data(folder_path="plot_data"):
    folder = Path(folder_path)
    all_dfs = [] # list for all data. each json-list = one data frame. 
    #Reading all the json-files into datastruct. 
    for i, file in enumerate(folder.glob("*.json")): #picks everything matching with json-format. 
        df = pd.read_json(file) #Reads into df, each json file. 
        df["scenario"] = file.stem #add extra column for scenario name
        df["scenario_id"] = i #Adding id. 
        all_dfs.append(df) 

    if not all_dfs: 
        return pd.DataFrame()

    return pd.concat(all_dfs, ignore_index=True) #Merge into one big table. 


def button_export(df_to_export):
    output = io.BytesIO() #creates buffer file. 
    with pd.ExcelWriter(output, engine="openpyxl") as writer: #write excel data into output
        df_to_export.to_excel(writer, index=False, sheet_name="Data")

    excel_data = output.getvalue()

    st.download_button( #Button for downloading. 
        label="Download Data",
        data=excel_data,
        file_name="filtered_argoverse.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )



def stream_lit():
    
    st.set_page_config(page_title="ArgoFilter", layout="wide") 
   #Filter tab
    with tab1:
        import_button()
        
        big_df = load_data() #Loading in the file. 

        if big_df.empty: 
            st.warning("No json-files inside the folder...")
            return

        if "category" not in big_df.columns:
            st.error("category missing")
            return

        #Sorting the data for categories, A-->Z. Removing (if NaN). 
        categories = sorted(big_df["category"].dropna().unique())

        
        # counting number of objects in scenarios and categories. 
        #Sorting the numbers of scenarios with numver of objects for each scenario.
        count_df = (
            big_df.groupby(["scenario", "category"])
            .size()
            .reset_index(name="count")
        )

        #creating a sidebar with multiselection for each category
        with st.sidebar:
            st.header("Find scenario")
            
            selected_categories = st.multiselect("Select Categories", categories)
            

        slider_values = {}

        
        #creating sliders for each category. Get the slider value
        
        with st.sidebar:
            for cat in selected_categories:
                max_count = int(count_df[count_df["category"] == cat]["count"].max())
                slider_values[cat] = st.slider(
                    f"Antal {cat}",
                    min_value=0,
                    max_value=max_count,
                    value=0,
                    key=f"slider_{cat}"
                )

        # Starting all scenarios. 
        matching_scenarios = set(big_df["scenario"].unique()) # Gets all unique scenario names. No duplicates. Set converts into pythonlist

        # Filtrera scenarion som matchar EXAKT antal för varje vald kategori
        for cat, desired_count in slider_values.items(): #Looks trough the slider values and match with the count of each category. 
            matching_for_cat = set(
                count_df[
                    (count_df["category"] == cat) &
                    (count_df["count"] == desired_count)
                ]["scenario"].unique()
            )

            # Only used when the 0 - category is used. 
            if desired_count == 0: 
                scenarios_with_cat = set(
                    count_df[count_df["category"] == cat]["scenario"].unique() #finds all scenarios where the category exists at least once. 
                )
                all_scenarios = set(big_df["scenario"].unique()) #create set of all scenarios in the whole dataset. 
                scenarios_without_cat = all_scenarios - scenarios_with_cat # Take all secenarios, remove the ones that contains this category.
                matching_for_cat = matching_for_cat | scenarios_without_cat #Adds the scenarios with no such category to the already matching scenario. 

            matching_scenarios = matching_scenarios & matching_for_cat #Keeps only scenarios that were already valid, and match current category condition

        filtered_df = big_df[big_df["scenario"].isin(matching_scenarios)]

        st.subheader("Matching scenarios")
        st.write("Number of scenarios:", filtered_df["scenario"].nunique())

        if filtered_df.empty:
            st.info("No matching scenarios.")
            return

        
        
        # Visa summering per scenario och kategori
        filtered_count_df = (
            filtered_df.groupby(["scenario_id", "category"])
            .size()
            .reset_index(name="count")
        )

        col1, col2 = st.columns([1, 1], gap=None)
        
        with col1: 
            st.subheader("Overview")
            st.dataframe(filtered_count_df,
                        width = "content")
        button_export(filtered_df)
        with col2:
            st.subheader("All objects in matching scenarios")
            st.dataframe(filtered_df, width = "content")
            
    #Plot tab         
    with tab2: 
        fig = px.bar(
            filtered_count_df,
            x="scenario_id",
            y="count",
            color="category",
            title="Object for each category in matching scenario"
            
        )

        st.plotly_chart(fig, use_container_width=True)
    
    
    with tab3:
        
        number = st.number_input(
        "Insert a number",step = 1, value=0, placeholder="Type a scenario"
        )
        st.write("The current number is ", number)
        
        st.header("2D map")
        import plotly.express as py
        df = filtered_df[filtered_df['scenario_id'] == number]
        fig1 = px.scatter(
        df,
        x="x",
        y="y",
        color="category",   # optional
        title="Object X-Y coordinates by Category surrounding the car"
        
        )
        fig1.add_scatter(
        x=[0], y=[0],
        mode="text",
        text=["🚗"] ,
        textfont=dict(size=20),
        name="Car position"
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
            borderwidth=1
        )
        )
        
 
        fig1.update_xaxes(
        showgrid=True,
        gridcolor="rgba(255,255,255,0.1)",
        zeroline=False,
        showline=False
        )

        fig1.update_yaxes(
        showgrid=True,
        gridcolor="rgba(255,255,255,0.1)",
        zeroline=False,
        showline=False
        )

     
        fig1.update_yaxes(scaleanchor="x", scaleratio=1)
        
        st.plotly_chart(
        fig1,
        use_container_width=True,
        config={
            "scrollZoom": True,
            "displaylogo": False
    }
)   
        

""" Implement logic for preprossing the data"""


#def prep_data():#
    #Logic for loading the data and creating the json objects. 
    #Use the preproccesing functions already implemented. 
    
    
    #The path for each file that the user wants to open are found in list path_list. 
    # for paths in pathlist:
        #bla bla bla
     
     
     
     
     
def import_button(): 

    clicked = st.button("Import Folder", type="primary")

    if "paths" not in st.session_state:
        st.session_state["paths"] = []

    if clicked:
        selected_path = importer()
        if selected_path and selected_path not in st.session_state["paths"]:
            st.session_state["paths"].append(selected_path)
        if st.session_state["paths"] not in path_list:
            path_list.append(path_list.append(selected_path))
            
    
    for i, p in enumerate(st.session_state["paths"]):
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.write(p)
        with col2:
            if st.button("Remove", key=f"remove_{i}"):
                del st.session_state["paths"][i]
                st.rerun()
        
    
    

#For opening file-system using tkinter. One file at a time. 
    
def importer():
    root = tk.Tk()
    root.withdraw()
    path = filedialog.askdirectory(initialdir=".", title = "Select Folder" )
    root.destroy()
    return path







if __name__ == "__main__":
    stream_lit()
    print(path_list)
    
