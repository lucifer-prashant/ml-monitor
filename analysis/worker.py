# analysis/worker.py (THE GUARANTEED VERSION)

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
REFERENCE_DATA_PATH = os.path.join(ROOT_DIR, 'reference_data.csv')
MODEL_PATH = os.path.join(ROOT_DIR, 'cancer_model_v1.0.joblib')
LIVE_DB_PATH = os.path.join(ROOT_DIR, 'live_data.db')
METRICS_DB_PATH = os.path.join(ROOT_DIR, 'metrics.db')
MODEL_VERSION = "cancer_model_v1.0"
ANALYSIS_INTERVAL_SECONDS = 15

try:
    model = joblib.load(MODEL_PATH)
    print("Model loaded successfully.")
except FileNotFoundError:
    print(f"Error: Model file not found at {MODEL_PATH}")
    exit()

def setup_metrics_db():
    conn = sqlite3.connect(METRICS_DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS model_performance (
            id INTEGER PRIMARY KEY AUTOINCREMENT, model_version TEXT NOT NULL, timestamp TIMESTAMP,
            accuracy REAL, precision REAL, recall REAL, f1_score REAL, data_drift_score REAL
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS feature_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT, model_version TEXT NOT NULL, timestamp TIMESTAMP,
            feature_name TEXT NOT NULL, drift_score REAL
        )
    ''')
    conn.commit()
    conn.close()
    print("Metrics database and all tables set up successfully.")

def find_metric_by_name(report_dict, name):
    for metric in report_dict.get('metrics', []):
        if metric.get('metric') == name:
            return metric.get('result')
    return None

def run_analysis():
    print(f"\n--- Running Analysis at {datetime.datetime.now()} ---")
    
    reference_df = pd.read_csv(REFERENCE_DATA_PATH)
    conn_live = sqlite3.connect(LIVE_DB_PATH)
    time_threshold = datetime.datetime.now() - datetime.timedelta(hours=1)
    query = f"SELECT feature_json, ground_truth FROM live_data WHERE ingested_at >= '{time_threshold}' AND model_version = '{MODEL_VERSION}'"
    live_data_rows = pd.read_sql(query, conn_live)
    conn_live.close()

    if len(live_data_rows) < 5:
        print(f"Not enough new data to run analysis (found {len(live_data_rows)} rows). Waiting for more.")
        return
    
    print(f"Found {len(live_data_rows)} new data points to analyze.")

    features_df = pd.DataFrame([json.loads(j) for j in live_data_rows['feature_json']])
    feature_columns = [col for col in reference_df.columns if col != 'target']
    
    current_features_only = features_df[feature_columns]

    report = Report(metrics=[
        ClassificationPreset(),
        DataDriftTable(), # Using a simple threshold is fine
    ])

    current_df_full = current_features_only.copy()
    current_df_full['target'] = live_data_rows['ground_truth'].values
    current_predictions = model.predict(current_features_only)
    current_df_full['prediction'] = current_predictions
    
    reference_df_copy = reference_df.copy()
    reference_df_copy['prediction'] = reference_df_copy['target']
    
    report.run(current_data=current_df_full, reference_data=reference_df_copy, column_mapping=ColumnMapping(target='target', prediction='prediction'))
    report_dict = report.as_dict()

    # --- SAVE RESULTS ---
    current_timestamp = datetime.datetime.now()
    conn_metrics = sqlite3.connect(METRICS_DB_PATH)
    c_metrics = conn_metrics.cursor()

    # --- THE FINAL, GUARANTEED PARSING LOGIC ---
    data_drift_score = 0
    feature_drift_count = 0
    
    drift_table_results = find_metric_by_name(report_dict, "DataDriftTable")

    if drift_table_results:
        # Instead of the overall flag, we will count drifted features ourselves
        number_of_drifted_columns = drift_table_results.get('number_of_drifted_columns', 0)
        data_drift_score = 1 if number_of_drifted_columns > 0 else 0
        print(f"Number of drifted columns: {number_of_drifted_columns}. Overall status: {'FAIL' if data_drift_score == 1 else 'SUCCESS'}")

        # The data is a dictionary where keys are feature names
        drift_details_dict = drift_table_results.get('drift_by_columns', {})
        for feature_name, details in drift_details_dict.items():
            # We don't care about the drift of target/prediction for the feature chart
            if feature_name in ['target', 'prediction']:
                continue
            
            drift_score = details.get('drift_score') # This is the p-value
            if drift_score is not None:
                c_metrics.execute("""
                    INSERT INTO feature_metrics (model_version, timestamp, feature_name, drift_score)
                    VALUES (?, ?, ?, ?)
                """, (MODEL_VERSION, current_timestamp, feature_name, drift_score))
                feature_drift_count += 1
        print(f"Saved drift details for {feature_drift_count} features.")
    else:
        print("Warning: DataDriftTable metric not found in report results.")

    # ... (rest of the classification code is the same)
    classification_results = find_metric_by_name(report_dict, "ClassificationQualityMetric")
    accuracy, precision, recall, f1 = 0.0, 0.0, 0.0, 0.0
    if classification_results:
        current_metrics = classification_results.get('current', {})
        accuracy = current_metrics.get('accuracy', 0.0)
        precision = current_metrics.get('precision', 0.0)
        recall = current_metrics.get('recall', 0.0)
        f1 = current_metrics.get('f1', 0.0)
    else:
        print("Warning: ClassificationQualityMetric not found in report results.")

    c_metrics.execute("""
        INSERT INTO model_performance (model_version, timestamp, accuracy, precision, recall, f1_score, data_drift_score)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (MODEL_VERSION, current_timestamp, accuracy, precision, recall, f1, data_drift_score))
    
    conn_metrics.commit()
    conn_metrics.close()
    print("--- Analysis Complete, metrics saved. ---")


if __name__ == "__main__":
    setup_metrics_db()
    while True:
        try:
            run_analysis()
        except Exception as e:
            print(f"An error occurred during analysis: {e}")
            traceback.print_exc()
        time.sleep(ANALYSIS_INTERVAL_SECONDS)