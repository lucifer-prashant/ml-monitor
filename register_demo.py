# register_demo.py
import sqlite3, datetime, os
model_name = "cancer_model"
model_version = "v1.0"
model_version_id = f"{model_name}_{model_version}"
conn = sqlite3.connect('model_registry.db')
c = conn.cursor()
# Create table if it doesn't exist (for the first run)
c.execute('''
    CREATE TABLE IF NOT EXISTS model_registry (
        id INTEGER PRIMARY KEY AUTOINCREMENT, model_name TEXT, model_version TEXT, 
        model_version_id TEXT UNIQUE, registered_at TIMESTAMP, description TEXT)''')
c.execute("INSERT OR IGNORE INTO model_registry (model_name, model_version, model_version_id, registered_at, description) VALUES (?, ?, ?, ?, ?)",
          (model_name, model_version, model_version_id, datetime.datetime.now(), "Default Scikit-learn Breast Cancer Model"))
conn.commit()
conn.close()
print("Demo model registered.")