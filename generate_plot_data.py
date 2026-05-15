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

            # Find the very first frame in the scenario
            first_timestamp = df["timestamp_ns"].min()
            frame_df = df[df["timestamp_ns"] == first_timestamp]

            # Only extract the columns we need
            # tx_m = X-coordinate, ty_m = Y-coordinate
            plot_data = frame_df[["category", "tx_m", "ty_m", "timestamp_ns"]].copy()

            # Rename the columns to make them clearer
            plot_data.columns = ["category", "x", "y", "timestamp_ns"]

            # Convert to a list of dictionaries and save
            output_file = output_dir / f"{log_id}.json"
            plot_data.to_json(output_file, orient="records", indent=4)

            if index % 20 == 0:
                print(f"Saved coordinates for {index} scenarios...")

        except Exception as e:
            print(f"Could not process log {log_id}: {e}")

    print(f"Done! All coordinate files are now located in {output_dir}")


if __name__ == "__main__":
    generate_visualization_data()
