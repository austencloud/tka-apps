import os
import json

def add_layer_attributes(folder_path: str) -> None:
    # Iterate through all files and subdirectories in the given folder
    for root, dirs, files in os.walk(folder_path):
        for filename in files:
            # Check if the file is a JSON file
            if filename.endswith(".json"):
                # Get the full path of the JSON file
                json_file_path = os.path.join(root, filename)

                # Load the JSON data from the file
                with open(json_file_path, 'r') as json_file:
                    data = json.load(json_file)
                    print(f"Successfully loaded JSON data from {json_file_path}")

                # Iterate through all top-level keys in the JSON data
                for key in data:
                    # Check if the value of the key is a list of lists
                    if isinstance(data[key], list) and all(isinstance(sublist, list) for sublist in data[key]):
                        # Iterate through each sub-array in the JSON data
                        for sub_array in data[key]:
                            for entry in sub_array:
                                # Check if entry is a motion object
                                if all(key in entry for key in ["color", "motion_type", "rotation_direction", "arrow_location"]):
                                    # Add 'start_layer' and 'end_layer' attributes with value 1
                                    entry['start_layer'] = 1
                                    entry['end_layer'] = 1
                                    print("Successfully added layer attributes to motion object")

                # Write the modified data back to the file
                with open(json_file_path, 'w') as json_file:
                    json.dump(data, json_file, indent=4)
                    print(f"Successfully added layer attributes to {json_file_path}")

# Example usage
folder_path = 'resources/json/'  # Replace with the actual path to your folder
add_layer_attributes(folder_path)
