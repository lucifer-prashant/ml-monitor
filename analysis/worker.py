# analysis/worker.py (Updated for Multi-Model)

import os
import pandas as pd
import sqlite3
import json
import time
import datetime
import joblib
import traceback

from evidently.report import Report
from evidently.metric_preset import ClassificationPreset
from evidently.pipeline.column_mapping import ColumnMapping
from evidently.metrics import DataDriftTable

# --- Configuration ---
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
LIVE_DB_PATH = os.path.join(ROOT_DIR, 'live_data.db')
METRICS_DB_PATH = os.path.join(ROOT_DIR, 'metrics.db')
REGISTRY_DB_PATH = os.path.join(ROOT_DIR, 'model_registry.db') # NEW
ASSETS_DIR = os.path.join(ROOT_DIR, 'assets') # NEW
ANALYSIS_INTERVAL_SECONDS = 15

def setup_metrics_db():
    conn = sqlite3.connect(METRICS_DB_PATH)
    c = conn.cursor()
    # Updated schema to use model_version_id
    c.execute('''
        CREATE TABLE IF NOT EXISTS model_performance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model_version_id TEXT NOT NULL,
            timestamp TIMESTAMP,
            accuracy REAL, precision REAL, recall REAL, f1_score REAL,
            data_drift_score REAL
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS feature_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model_version_id TEXT NOT NULL,
            timestamp TIMESTAMP,
            feature_name TEXT NOT NULL,
            drift_score REAL
        )
    ''')
    conn.commit()
    conn.close()
    print("Metrics database and tables are up to date.")

def find_metric_by_name(report_dict, name):
    for metric in report_dict.get('metrics', []):
        if metric.get('metric') == name:
            return metric.get('result')
    return None

def run_analysis_for_model(model_version_id: str):
    """
    Performs data drift and performance analysis for a single model version.
    """
    print(f"\n--- Analyzing Model: {model_version_id} ---")

    # --- 1. Load Assets for this specific model ---
    model_asset_path = os.path.join(ASSETS_DIR, model_version_id)
    reference_data_path = os.path.join(model_asset_path, 'reference_data.csv')
    model_path = os.path.join(model_asset_path, 'model.joblib')

    try:
        reference_df = pd.read_csv(reference_data_path)
        model = joblib.load(model_path)
    except FileNotFoundError as e:
        print(f"Could not find assets for {model_version_id}. Skipping. Error: {e}")
        return

    # --- 2. Load Live Data for this model from the last hour ---
    conn_live = sqlite3.connect(LIVE_DB_PATH)
    time_threshold = datetime.datetime.now() - datetime.timedelta(hours=1)
    query = f"SELECT feature_json, ground_truth FROM live_data WHERE ingested_at >= ? AND model_version_id = ?"
    live_data_rows = pd.read_sql(query, conn_live, params=(time_threshold, model_version_id))
    conn_live.close()

    if len(live_data_rows) < 5:
        print(f"Not enough new data to analyze (found {len(live_data_rows)} rows).")
        return

    print(f"Found {len(live_data_rows)} new data points to analyze.")

    # --- 3. Prepare DataFrames for Evidently ---
    features_df = pd.DataFrame([json.loads(j) for j in live_data_rows['feature_json']])
    feature_columns = [col for col in reference_df.columns if col != 'target']
    
    current_features_only = features_df[feature_columns]

    current_df_full = current_features_only.copy()
    current_df_full['target'] = live_data_rows['ground_truth'].values
    current_predictions = model.predict(current_features_only)
    current_df_full['prediction'] = current_predictions
    
    reference_df_copy = reference_df.copy()
    # To run ClassificationPreset, the reference data also needs a 'prediction' column
    # We can use the true labels as "perfect" predictions for the reference set.
    reference_df_copy['prediction'] = reference_df_copy['target']
    
    # --- 4. Run Evidently Report ---
    report = Report(metrics=[
        ClassificationPreset(),
        DataDriftTable(),
    ])
    report.run(
        current_data=current_df_full, 
        reference_data=reference_df_copy, 
        column_mapping=ColumnMapping(target='target', prediction='prediction')
    )
    report_dict = report.as_dict()

    # --- 5. Parse and Save Results ---
    current_timestamp = datetime.datetime.now()
    conn_metrics = sqlite3.connect(METRICS_DB_PATH)
    c_metrics = conn_metrics.cursor()

    # Data Drift
    data_drift_score = 0
    drift_table_results = find_metric_by_name(report_dict, "DataDriftTable")
    if drift_table_results:
        number_of_drifted_columns = drift_table_results.get('number_of_drifted_columns', 0)
        data_drift_score = 1 if number_of_drifted_columns > 0 else 0
        
        drift_details_dict = drift_table_results.get('drift_by_columns', {})
        for feature_name, details in drift_details_dict.items():
            if feature_name in ['target', 'prediction']:
                continue
            drift_score = details.get('drift_score')
            if drift_score is not None:
                c_metrics.execute("""
                    INSERT INTO feature_metrics (model_version_id, timestamp, feature_name, drift_score)
                    VALUES (?, ?, ?, ?)
                """, (model_version_id, current_timestamp, feature_name, drift_score))
    
    # Classification Metrics
    classification_results = find_metric_by_name(report_dict, "ClassificationQualityMetric")
    accuracy, precision, recall, f1 = 0.0, 0.0, 0.0, 0.0
    if classification_results:
        current_metrics = classification_results.get('current', {})
        accuracy = current_metrics.get('accuracy', 0.0)
        precision = current_metrics.get('precision', 0.0)
        recall = current_metrics.get('recall', 0.0)
        f1 = current_metrics.get('f1', 0.0)

    # Save overall performance
    c_metrics.execute("""
        INSERT INTO model_performance (model_version_id, timestamp, accuracy, precision, recall, f1_score, data_drift_score)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (model_version_id, current_timestamp, accuracy, precision, recall, f1, data_drift_score))
    
    conn_metrics.commit()
    conn_metrics.close()
    print(f"--- Analysis for {model_version_id} complete. Metrics saved. ---")

if __name__ == "__main__":
    setup_metrics_db()
    while True:
        try:
            # --- The Main Loop ---
            # 1. Get all registered models
            conn_registry = sqlite3.connect(REGISTRY_DB_PATH)
            models_to_analyze = pd.read_sql("SELECT model_version_id FROM model_registry", conn_registry)
            conn_registry.close()

            print(f"\nFound {len(models_to_analyze)} models to analyze: {models_to_analyze['model_version_id'].tolist()}")

            # 2. Analyze each one
            for model_id in models_to_analyze['model_version_id']:
                run_analysis_for_model(model_id)
            
        except Exception as e:
            print(f"An error occurred in the main worker loop: {e}")
            traceback.print_exc()
            
        print(f"\n--- Worker sleeping for {ANALYSIS_INTERVAL_SECONDS} seconds ---")
        time.sleep(ANALYSIS_INTERVAL_SECONDS)