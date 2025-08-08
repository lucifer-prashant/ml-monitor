# backend/main.py

import os
import pandas as pd
import sqlite3
import datetime
import json
import shutil
from fastapi import FastAPI, UploadFile, File, Form
from pydantic import BaseModel

# --- Define Absolute Paths for Databases and ASSETS ---
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)

METRICS_DB_PATH = os.path.join(ROOT_DIR, 'metrics.db')
REGISTRY_DB_PATH = os.path.join(ROOT_DIR, 'model_registry.db')
LIVE_DATA_DB_PATH = os.path.join(ROOT_DIR, 'live_data.db')
ASSETS_DIR = os.path.join(ROOT_DIR, 'assets')
# --- End of Path Definitions ---


# --- API Setup ---
app = FastAPI(title="ML-Monitor Backend")


# --- Database Setup on Startup ---
@app.on_event("startup")
def startup_event():
    # This function is now just for creating tables if they don't exist.
    
    # Setup model registry database
    conn_registry = sqlite3.connect(REGISTRY_DB_PATH)
    c_registry = conn_registry.cursor()
    c_registry.execute('''
        CREATE TABLE IF NOT EXISTS model_registry (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model_name TEXT NOT NULL,
            model_version TEXT NOT NULL,
            model_version_id TEXT UNIQUE NOT NULL,
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
            model_version_id TEXT NOT NULL,
            feature_json TEXT NOT NULL,
            ground_truth INTEGER,
            ingested_at TIMESTAMP
        )
    ''')
    conn_live.commit()
    conn_live.close()

    # Ensure the base assets directory exists
    os.makedirs(ASSETS_DIR, exist_ok=True)


# --- API Models (Data Shapes) ---
class ModelInfo(BaseModel):
    model_name: str
    model_version: str
    description: str | None = None

class IngestionData(BaseModel):
    model_version_id: str
    features: dict
    ground_truth: int


# --- API Endpoints ---
@app.get("/")
def read_root():
    return {"message": "Welcome to the ML-Monitor API. Go to /docs to see available endpoints."}

@app.post("/upload_and_register")
def upload_and_register(
    model_name: str = Form(...),
    model_version: str = Form(...),
    description: str = Form(None),
    model_file: UploadFile = File(...),
    data_file: UploadFile = File(...)
):
    model_version_id = f"{model_name.replace(' ', '_').lower()}_{model_version}"
    model_asset_path = os.path.join(ASSETS_DIR, model_version_id)
    os.makedirs(model_asset_path, exist_ok=True)

    model_path = os.path.join(model_asset_path, 'model.joblib')
    data_path = os.path.join(model_asset_path, 'reference_data.csv')

    try:
        with open(model_path, "wb") as buffer:
            shutil.copyfileobj(model_file.file, buffer)
        with open(data_path, "wb") as buffer:
            shutil.copyfileobj(data_file.file, buffer)
    finally:
        model_file.file.close()
        data_file.file.close()
    
    conn = sqlite3.connect(REGISTRY_DB_PATH)
    c = conn.cursor()
    try:
        c.execute(
            "INSERT INTO model_registry (model_name, model_version, model_version_id, registered_at, description) VALUES (?, ?, ?, ?, ?)",
            (model_name, model_version, model_version_id, datetime.datetime.now(), description)
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return {"error": f"Model version ID '{model_version_id}' already exists. Please choose a different name or version."}, 400
    conn.close()

    return {"message": "Model registered successfully.", "model_version_id": model_version_id}


@app.post("/ingest")
def ingest_data(data: IngestionData):
    conn = sqlite3.connect(LIVE_DATA_DB_PATH)
    c = conn.cursor()
    feature_string = json.dumps(data.features)
    c.execute("INSERT INTO live_data (model_version_id, feature_json, ground_truth, ingested_at) VALUES (?, ?, ?, ?)",
              (data.model_version_id, feature_string, data.ground_truth, datetime.datetime.now()))
    conn.commit()
    conn.close()
    return {"message": "Data ingested successfully."}

@app.get("/api/metrics/{model_version_id}")
def get_metrics(model_version_id: str):
    conn = sqlite3.connect(METRICS_DB_PATH)
    query = f"""
        SELECT timestamp, accuracy, precision, recall, f1_score, data_drift_score 
        FROM model_performance 
        WHERE model_version_id = '{model_version_id}'
        ORDER BY timestamp ASC
    """
    try:
        df = pd.read_sql(query, conn)
    except Exception:
        # If table doesn't exist or there's an error, return empty
        return []
    conn.close()
    return df.to_dict('records')

@app.get("/api/feature_drift/{model_version_id}")
def get_feature_drift(model_version_id: str):
    conn = sqlite3.connect(METRICS_DB_PATH)
    
    # --- THIS IS THE FIX ---
    # The query now correctly uses "model_version_id" to match the database schema.
    latest_timestamp_query = f"SELECT MAX(timestamp) FROM feature_metrics WHERE model_version_id = '{model_version_id}'"
    
    try:
        latest_timestamp = pd.read_sql(latest_timestamp_query, conn).iloc[0, 0]
    except Exception:
        latest_timestamp = None

    if pd.isna(latest_timestamp):
        conn.close()
        return []

    query = f"""
        SELECT feature_name, drift_score
        FROM feature_metrics
        WHERE model_version_id = '{model_version_id}' AND timestamp = '{latest_timestamp}'
        ORDER BY drift_score ASC
    """
    
    df = pd.read_sql(query, conn)
    conn.close()
    
    return df.to_dict('records')