# ARGOFILTER  - Interactive Scenario Retrieval

## Contributors: Amos Lund, Majdi Kredi, Rowan De Block

## Course: Advanced Human-Computer Interaction, VT26, DT507A

## Örebro University

## Description

Argofilter is an interactive scenario retrieval interface for the autonomous driving dataset Argoverse 2.
The interface lets the user load a sensor dataset from the file-browser, filter amongst different scenarios and study each scenario on the depth by providing a global search, overview, static 2d map, and native playback. The user can also download filtered dataset and export it as an Excel document.

## Functions

- Data_aggregator.py - Used for creating metadata.  
- Generate_plot_data.py - Used for retrieving specific scenarios.
- interface.py - The interface that runs through streamlit.

## Get Started

### Requirements

- Python 3.10 or later version
- pip
- Streamlit
- Pandas
- Plotly
- openpyxl
- tkinter (usually provided with python)
- Projectfiles:
  - `interface.py`
  - `data_aggregator.py`
  - `generate_plot_data.py`
  - `config.toml.txt`

The program expects the users to have access to a folder with ArgoVerse 2 sensor-data.

[To download Argoverse 2 sensor data, follow the provided link](https://www.argoverse.org/av2.html#sensor-link)

### Installation

Install required packages:

Windows:

```bash
py -m pip install streamlit pandas plotly openpyxl
```

macOS/Linux:

``` bash
python3 -m pip install streamlit pandas plotly openpyxl 
```

tkinter for Linux users:

```bash
sudo apt install python3-tk 
```

### Running the interface

```bash
streamlit run interface.py
```

## Project Folder

```text
argofilter/
├──  .streamlit/
    └── config.toml
├── __pycache__/
├── deprecated interfaces
├── plot_data/ (after import in streamlit)
    ├── 00a6ffc1-6ce9-3bc3-a060-6006e9893a1a
    ├── ...
    └── 11420316-aec9-3ad9-8b4a-d618bcd180e9
├── data_aggregator.py
├── generate_plot_data.py
├── interface.py
├── README
└── scenarios_metadata.json
```

The `plot_data/`folder and `scenarios_metadata.json` files are generated after importing Argoverse 2 sensor folder in the Streamlit interface and will be deleted when the program is closed or if the delete button is used.
