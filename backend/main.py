# backend/main.py (Final, Robust Version)

import os
import pandas as pd
import sqlite3
import datetime
import json
from fastapi import FastAPI
from pydantic import BaseModel

# --- Define Absolute Paths for Databases ---
# This makes the script's location irrelevant.
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)

METRICS_DB_PATH = os.path.join(ROOT_DIR, 'metrics.db')
REGISTRY_DB_PATH = os.path.join(ROOT_DIR, 'model_registry.db')
LIVE_DATA_DB_PATH = os.path.join(ROOT_DIR, 'live_data.db')
# --- End of Path Definitions ---


# --- API Setup ---
app = FastAPI(title="ML-Monitor Backend")


# --- Database Setup on Startup ---
@app.on_event("startup")
def startup_event():
    # This function is now just for creating tables if they don't exist.
    # The analysis worker is responsible for creating metrics.db
    
    # Setup model registry database
    conn_registry = sqlite3.connect(REGISTRY_DB_PATH)
    c_registry = conn_registry.cursor()
    c_registry.execute('''
        CREATE TABLE IF NOT EXISTS model_registry (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model_name TEXT NOT NULL,
            model_version TEXT NOT NULL,
            registered_at TIMESTAMP,
            description TEXT
        )
    ''')
    conn_registry.commit()
    conn_registry.close()
    
    # Setup live data ingestion database
    conn_live = sqlite3.connect(LIVE_DATA_DB_PATH)
    c_live = conn_live.cursor()
    c_live.execute('''
        CREATE TABLE IF NOT EXISTS live_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model_version TEXT NOT NULL,
            feature_json TEXT NOT NULL,
            ground_truth INTEGER,
            ingested_at TIMESTAMP
        )
    ''')
    conn_live.commit()
    conn_live.close()


# --- API Models (Data Shapes) ---
class ModelInfo(BaseModel):
    model_name: str
    model_version: str
    description: str | None = None

class IngestionData(BaseModel):
    model_version: str
    features: dict
    ground_truth: int


# --- API Endpoints ---
@app.get("/")
def read_root():
    return {"message": "Welcome to the ML-Monitor API. Go to /docs to see available endpoints."}

@app.post("/register_model")
def register_model(model: ModelInfo):
    conn = sqlite3.connect(REGISTRY_DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO model_registry (model_name, model_version, registered_at, description) VALUES (?, ?, ?, ?)",
              (model.model_name, model.model_version, datetime.datetime.now(), model.description))
    conn.commit()
    conn.close()
    return {"message": f"Model '{model.model_name} v{model.model_version}' registered successfully."}

@app.post("/ingest")
def ingest_data(data: IngestionData):
    conn = sqlite3.connect(LIVE_DATA_DB_PATH)
    c = conn.cursor()
    feature_string = json.dumps(data.features)
    c.execute("INSERT INTO live_data (model_version, feature_json, ground_truth, ingested_at) VALUES (?, ?, ?, ?)",
              (data.model_version, feature_string, data.ground_truth, datetime.datetime.now()))
    conn.commit()
    conn.close()
    return {"message": "Data ingested successfully."}

@app.get("/api/metrics/{model_version}")
def get_metrics(model_version: str):
    conn = sqlite3.connect(METRICS_DB_PATH)
    query = f"""
        SELECT timestamp, accuracy, precision, recall, f1_score, data_drift_score 
        FROM model_performance 
        WHERE model_version = '{model_version}' 
        ORDER BY timestamp ASC
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df.to_dict('records')

@app.get("/api/feature_drift/{model_version}")
def get_feature_drift(model_version: str):
    conn = sqlite3.connect(METRICS_DB_PATH)
    
    # Query to get the most recent timestamp from the feature_metrics table
    latest_timestamp_query = f"SELECT MAX(timestamp) FROM feature_metrics WHERE model_version = '{model_version}'"
    
    try:
        latest_timestamp = pd.read_sql(latest_timestamp_query, conn).iloc[0, 0]
    except Exception:
        # This handles the case where the table is empty or doesn't exist yet
        latest_timestamp = None

    if pd.isna(latest_timestamp):
        return []

    # Now, get all feature drift records that match that latest timestamp
    query = f"""
        SELECT feature_name, drift_score
        FROM feature_metrics
        WHERE model_version = '{model_version}' AND timestamp = '{latest_timestamp}'
        ORDER BY drift_score ASC
    """
    
    df = pd.read_sql(query, conn)
    conn.close()
    
    return df.to_dict('records')