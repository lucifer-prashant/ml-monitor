# simulator/run_simulation.py (Updated for Multi-Model)

import pandas as pd
import requests
import time
import random
import os       # NEW
import argparse # NEW

# --- Configuration ---
API_URL = "http://127.0.0.1:8000/ingest"
SEND_INTERVAL_SECONDS = 2

# The drift engine function remains the same for now
def introduce_drift(data_row):
    drift_factor = 1.0 + (int(time.time() / 30) % 20) * 0.05
    data_row['mean radius'] *= (1 + drift_factor)
    data_row['mean smoothness'] += (drift_factor * 0.01)
    if 'mean texture' in data_row:
        noise = random.uniform(-5, 5)
        data_row['mean texture'] += noise
    return data_row

# --- NEW: Main function to handle dynamic model loading ---
def run_simulation(model_version_id: str):
    """
    Runs the simulation for a specific model version ID.
    """
    # Dynamically construct the path to the reference data
    reference_data_path = os.path.join('assets', model_version_id, 'reference_data.csv')

    try:
        df = pd.read_csv(reference_data_path)
        print(f"Reference data for '{model_version_id}' loaded successfully from '{reference_data_path}'.")
    except FileNotFoundError:
        print(f"Error: The reference data file for '{model_version_id}' was not found at '{reference_data_path}'.")
        print("Please ensure you have uploaded this model via the UI or registered it correctly.")
        exit()

    feature_columns = df.columns.drop('target', errors='ignore')
    target_column = 'target'

    print(f"--- Starting Simulation for Model: {model_version_id} ---")
    print("--- DRIFT ENGINE ENGAGED ---")
    print(f"Sending a new data point every {SEND_INTERVAL_SECONDS} seconds.")
    print("Press CTRL+C to stop.")

    while True:
        try:
            random_row = df.sample(n=1)
            features = random_row[feature_columns].to_dict('records')[0]
            ground_truth = 0 # Default value
            if target_column in random_row.columns:
                ground_truth = int(random_row[target_column].iloc[0])

            drifted_features = introduce_drift(features.copy())

            # The payload now uses the dynamic model_version_id
            payload = {
                "model_version_id": model_version_id,
                "features": drifted_features,
                "ground_truth": ground_truth
            }

            response = requests.post(API_URL, json=payload)
            response.raise_for_status()

            # Optional: uncomment to see data points being sent
            # print(".", end="", flush=True)

            time.sleep(SEND_INTERVAL_SECONDS)

        except requests.exceptions.RequestException:
            print(f"\nError: Could not connect to the API at {API_URL}. Retrying...")
            time.sleep(5)
        except KeyboardInterrupt:
            print("\nSimulation stopped by user.")
            break
        except Exception as e:
            print(f"\nAn unexpected error occurred: {e}")
            break

# --- NEW: Script entry point with argument parsing ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run a data simulation for a specific ML model.")
    parser.add_argument("model_version_id", type=str, help="The unique ID of the model to simulate data for (e.g., 'cancer_model_v1.0').")
    args = parser.parse_args()
    
    run_simulation(args.model_version_id)