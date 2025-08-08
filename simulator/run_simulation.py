# simulator/run_simulation.py (Corrected with Grace Period)

import pandas as pd
import requests
import time
import random
import os
import argparse
import datetime

# --- Configuration ---  <- THIS WAS THE MISSING PART
API_URL = "http://127.0.0.1:8000/ingest"
SEND_INTERVAL_SECONDS = 2
# --- End of Configuration ---

def introduce_drift(data_row):
    drift_factor = 1.0 + (int(time.time() / 30) % 20) * 0.05
    data_row['mean radius'] *= (1 + drift_factor)
    data_row['mean smoothness'] += (drift_factor * 0.01)
    if 'mean texture' in data_row:
        noise = random.uniform(-5, 5)
        data_row['mean texture'] += noise
    return data_row


def run_simulation(model_version_id: str):
    """
    Runs the simulation for a specific model version ID.
    """
    reference_data_path = os.path.join('assets', model_version_id, 'reference_data.csv')

    try:
        df = pd.read_csv(reference_data_path)
        print(f"Reference data for '{model_version_id}' loaded successfully from '{reference_data_path}'.")
    except FileNotFoundError:
        print(f"Error: The reference data file for '{model_version_id}' was not found at '{reference_data_path}'.")
        exit()

    feature_columns = df.columns.drop('target', errors='ignore')
    target_column = 'target'
    
    # --- GRACE PERIOD SETUP ---
    start_time = datetime.datetime.now()
    grace_period_seconds = 60
    drift_engaged = False
    print(f"--- Starting Simulation for Model: {model_version_id} ---")
    print(f"--- Running in GRACE PERIOD for {grace_period_seconds} seconds (no drift) ---")
    print("Press CTRL+C to stop.")

    while True:
        try:
            # Check if grace period is over
            if not drift_engaged and (datetime.datetime.now() - start_time).seconds > grace_period_seconds:
                print("\n--- GRACE PERIOD OVER. DRIFT ENGINE ENGAGED. ---")
                drift_engaged = True

            random_row = df.sample(n=1)
            features = random_row[feature_columns].to_dict('records')[0]
            ground_truth = int(random_row[target_column].iloc[0]) if target_column in random_row.columns else 0

            # Only apply drift if engaged
            if drift_engaged:
                features = introduce_drift(features.copy())

            payload = {
                "model_version_id": model_version_id,
                "features": features, # Send original or drifted features
                "ground_truth": ground_truth
            }

            response = requests.post(API_URL, json=payload)
            response.raise_for_status()

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

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run a data simulation for a specific ML model.")
    parser.add_argument("model_version_id", type=str, help="The unique ID of the model to simulate data for (e.g., 'cancer_model_v1.0').")
    args = parser.parse_args()
    
    run_simulation(args.model_version_id)