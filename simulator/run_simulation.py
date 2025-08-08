# simulator/run_simulation.py (with Drift Engine)

import pandas as pd
import requests
import time
import random

# --- Configuration ---
API_URL = "http://127.0.0.1:8000/ingest"
MODEL_VERSION = "cancer_model_v1.0"
REFERENCE_DATA_PATH = 'reference_data.csv'
SEND_INTERVAL_SECONDS = 2

# --- NEW: The Drift Engine Function ---
# def introduce_drift(data_row):
#     """
#     Artificially introduces drift by modifying a feature.
#     Let's make 'mean radius' slowly increase over time.
#     """
#     # This drift factor will increase by 0.1 every 30 seconds.
#     # It creates a slow, noticeable change.
#     drift_factor = 1.0 + (int(time.time() / 30) % 10) * 0.1
    
#     # Increase the 'mean radius' by the drift factor.
#     data_row['mean radius'] *= drift_factor
    
#     # To make it more interesting, let's also add some random noise to another feature.
#     if 'mean texture' in data_row:
#         noise = random.uniform(-2, 2)
#         data_row['mean texture'] += noise

#     return data_row
# In simulator/run_simulation.py

# --- NEW: The AGGRESSIVE Drift Engine Function ---
# def introduce_drift(data_row):
#     """
#     Artificially introduces EXTREME drift to guarantee detection.
#     """
#     # This drift factor will now increase by a much larger amount, more quickly.
#     # It will go from 1.0 to 3.0 over the course of about 2 minutes.
#     drift_factor = 1.0 + (int(time.time() / 15) % 20) * 0.1
    
#     # Dramatically increase the 'mean radius'.
#     data_row['mean radius'] *= (drift_factor * 1.5) # Multiply by an even bigger factor
    
#     # Also, let's make another feature drift hard.
#     # We will shift the 'mean smoothness' value significantly.
#     data_row['mean smoothness'] += 0.1 # This is a huge shift for this feature
    
#     # And add more noise to texture
#     if 'mean texture' in data_row:
#         noise = random.uniform(-10, 10) # Much larger noise range
#         data_row['mean texture'] += noise

#     return data_row
# In simulator/run_simulation.py

# --- NEW: The BALANCED Drift Engine ---
def introduce_drift(data_row):
    """
    Introduces significant but statistically sound drift.
    """
    # We'll use a smoother, less extreme drift factor that still has a strong effect.
    # It will go from 1.0 to 2.0 over about 5 minutes.
    drift_factor = 1.0 + (int(time.time() / 30) % 20) * 0.05
    
    # Increase 'mean radius'. The change is significant but not astronomical.
    data_row['mean radius'] *= (1 + drift_factor)
    
    # Also, let's moderately shift 'mean smoothness'.
    data_row['mean smoothness'] += (drift_factor * 0.01)

    # Add some noise to 'mean texture' but keep it within a reasonable range.
    if 'mean texture' in data_row:
        noise = random.uniform(-5, 5) # A more controlled noise range
        data_row['mean texture'] += noise

    return data_row
# --- Load the Reference Data ---
try:
    df = pd.read_csv(REFERENCE_DATA_PATH)
    print("Reference data loaded successfully.")
except FileNotFoundError:
    print(f"Error: The file '{REFERENCE_DATA_PATH}' was not found.")
    exit()

feature_columns = df.columns.drop('target')
target_column = 'target'

print(f"--- Starting Simulation for Model Version: {MODEL_VERSION} ---")
print("--- DRIFT ENGINE ENGAGED ---")
print(f"Sending a new data point every {SEND_INTERVAL_SECONDS} seconds.")
print("Press CTRL+C to stop.")

# --- The Main Simulation Loop ---
while True:
    try:
        random_row = df.sample(n=1)
        features = random_row[feature_columns].to_dict('records')[0]
        ground_truth = int(random_row[target_column].iloc[0])
        
        # --- APPLY THE DRIFT! ---
        drifted_features = introduce_drift(features)
        
        payload = {
            "model_version": MODEL_VERSION,
            "features": drifted_features, # Send the drifted features
            "ground_truth": ground_truth
        }
        
        response = requests.post(API_URL, json=payload)
        response.raise_for_status()
        
        # We won't print every point to keep the console clean.
        # print(f"Sent data point. Ground Truth: {ground_truth}.")

        time.sleep(SEND_INTERVAL_SECONDS)

    except requests.exceptions.RequestException as e:
        print(f"Error sending data: Could not connect to the API at {API_URL}.")
        time.sleep(5)
    except KeyboardInterrupt:
        print("\nSimulation stopped by user.")
        break
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        break