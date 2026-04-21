from pathlib import Path
import io

import pandas as pd
import plotly.express as px
import streamlit as st


tab1, tab2 = st.tabs(["Filter", "2D Map",])




def load_data(folder_path="plot_data"):
    folder = Path(folder_path)
    all_dfs = []

    for i, file in enumerate(folder.glob("*.json")):
        df = pd.read_json(file)
        df["scenario"] = file.stem
        df["scenario_id"] = i
        all_dfs.append(df)

    if not all_dfs:
        return pd.DataFrame()

    return pd.concat(all_dfs, ignore_index=True)


def button_export(df_to_export):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_to_export.to_excel(writer, index=False, sheet_name="Data")

    excel_data = output.getvalue()

    st.download_button(
        label="Ladda ned som Excel",
        data=excel_data,
        file_name="filtered_argoverse.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


def stream_lit():
    
    
    

    with tab1:
        st.set_page_config(page_title="Scenario analysis", layout="wide")
        st.title("Scenario filtering")
        st.header("The filtering")
        
        big_df = load_data()

        if big_df.empty:
            st.warning("Inga JSON-filer hittades i mappen 'plot_data'.")
            return

        if "category" not in big_df.columns:
            st.error("Kolumnen 'category' saknas i datan.")
            return

        categories = sorted(big_df["category"].dropna().unique())

        # Räkna antal objekt per scenario och kategori
        count_df = (
            big_df.groupby(["scenario", "category"])
            .size()
            .reset_index(name="count")
        )

        with st.sidebar:
            st.header("Sök scenarion")
            selected_categories = st.multiselect("Välj kategorier", categories)

        slider_values = {}

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

        # Starta med alla scenarion
        matching_scenarios = set(big_df["scenario"].unique())

        # Filtrera scenarion som matchar EXAKT antal för varje vald kategori
        for cat, desired_count in slider_values.items():
            matching_for_cat = set(
                count_df[
                    (count_df["category"] == cat) &
                    (count_df["count"] == desired_count)
                ]["scenario"].unique()
            )

            # Om desired_count = 0 måste vi även ta med scenarion där kategorin inte finns alls
            if desired_count == 0:
                scenarios_with_cat = set(
                    count_df[count_df["category"] == cat]["scenario"].unique()
                )
                all_scenarios = set(big_df["scenario"].unique())
                scenarios_without_cat = all_scenarios - scenarios_with_cat
                matching_for_cat = matching_for_cat | scenarios_without_cat

            matching_scenarios = matching_scenarios & matching_for_cat

        filtered_df = big_df[big_df["scenario"].isin(matching_scenarios)]

        st.subheader("Matchande scenarion")
        st.write("Antal scenarion:", filtered_df["scenario"].nunique())

        if filtered_df.empty:
            st.info("Inga scenarion matchade filtreringen.")
            return

        # Visa summering per scenario och kategori
        filtered_count_df = (
            filtered_df.groupby(["scenario_id", "category"])
            .size()
            .reset_index(name="count")
        )

        st.subheader("Summering")
        st.dataframe(filtered_count_df)

        st.subheader("Alla objekt i matchande scenarion")
        st.dataframe(filtered_df)

        button_export(filtered_df)

        fig = px.bar(
            filtered_count_df,
            x="scenario_id",
            y="count",
            color="category",
            title="Objekt per kategori i matchande scenarion"
        )

        st.plotly_chart(fig, use_container_width=True)
        
        
      
    with tab2:
        
        
        
        number = st.number_input(
        "Insert a number",step = 1, value=None, placeholder="Type a scenario"
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
        title="X-Y by Category"
        
        )
        fig1.add_scatter(
        x=[0], y=[0],
        mode="markers",
        marker=dict(size=12, color="red"),
        name="Car position"
        )
        fig.update_layout(
        template="plotly_dark",
        plot_bgcolor="rgba(0,0,0,1)",
        paper_bgcolor="rgba(0,0,0,1)",
        font=dict(color="black")
        
)       
        fig1.update_xaxes(
        showgrid=True,
        gridcolor="rgba(255,255,255,0.1)"
        )

        fig1.update_yaxes(
        showgrid=True,
        gridcolor="rgba(255,255,255,0.1)"
)
        fig1.update_yaxes(scaleanchor="x", scaleratio=1)
        
        st.plotly_chart(fig1, use_container_width=True)
    
    
    

if __name__ == "__main__":
    stream_lit()