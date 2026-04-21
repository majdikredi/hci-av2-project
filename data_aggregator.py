import pandas as pd
from pathlib import Path
import json

def aggregate_scenario_data():
    # dataset path and where to save data
    dataset_dir = Path("/home/majdikredi/argoverse_data/sensor")
    output_file = Path("/home/majdikredi/hci_project/scenarios_metadata.json")
    
    print("Looking for scenarios in the dataset...")
    
    # Look for all the annotations-files
    feather_files = list(dataset_dir.rglob("annotations.feather"))
    total_files = len(feather_files)
    
    if total_files == 0:
        print("could not find any files. Check the path!")
        return

    print(f"found {total_files} scenarios. starting to extract data...")
    
    all_scenarios = []
    
    # loop thru each file
    for index, file_path in enumerate(feather_files, 1):
        log_id = file_path.parent.name
        
        try:
            # read file and drop doubles to get unique objects
            df = pd.read_feather(file_path)
            unique_objects = df.drop_duplicates(subset=['track_uuid'])
            
            # Count classes and convert to dictionary
            # we convert numpy int64 to normal int so Json can read it
            category_counts = {k: int(v) for k, v in unique_objects['category'].value_counts().items()}
            
            # create nice data object for this scenario
            scenario_data = {
                "id": log_id,
                "objects": category_counts
            }
            
            all_scenarios.append(scenario_data)
            
            # print little update in terminal to see its working
            if index % 20 == 0 or index == total_files:
                print(f"Processed {index}/{total_files} scenarios...")
                
        except Exception as e:
            print(f"couldnt read logg {log_id}. error: {e}")

    # 3. save all to a JSON-file
    print(f"\nSaving this data to {output_file}...")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_scenarios, f, indent=4)
        
    print("success! Database is finished and ready to use.")

if __name__ == "__main__":
    aggregate_scenario_data()