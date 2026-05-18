import pandas as pd
from pathlib import Path
import json
import os


def generate_visualization_data(dataset_import):
    # dataset_dir = Path("/home/majdikredi/argoverse_data/sensor")
    # dataset_dir = Path("C:/Users/amosb/Documents/civdata/t8/HCI/sensor")

    # Create a subfolder where all JSON files for plotting will be stored
    # output_dir = Path("/home/majdikredi/hci_project/plot_data")
    dataset_dir = Path(dataset_import)

    # output_dir = Path("C:/Users/amosb/Documents/civdata/t8/HCI/project/hci-av2-project/plot_data")
    output_dir = Path(__file__).parent / "plot_data"
    output_dir.mkdir(parents=True, exist_ok=True)

    feather_files = list(dataset_dir.rglob("annotations.feather"))
    print(f"Found {len(feather_files)} scenarios. Starting to extract coordinates...")

    for index, file_path in enumerate(feather_files, 1):
        log_id = file_path.parent.name

        try:
            df = pd.read_feather(file_path)

            plot_data = df[["category", "tx_m", "ty_m", "timestamp_ns"]].copy()

            plot_data.columns = ["category", "x", "y", "timestamp_ns"]

            # Save to JSON
            output_file = output_dir / f"{log_id}.json"
            plot_data.to_json(output_file, orient="records", indent=4)

            if index % 20 == 0:
                print(f"Have saved coordinates for {index} scenarios...")

        except Exception as e:
            print(f"couldnt process log {log_id}: {e}")


if __name__ == "__main__":
    generate_visualization_data()
