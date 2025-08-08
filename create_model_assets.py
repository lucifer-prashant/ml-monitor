# create_model_assets.py

import pandas as pd
from sklearn.datasets import load_breast_cancer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
import joblib

print("--- Starting Model and Data Creation ---")

# 1. Load the dataset from scikit-learn
# as_frame=True loads the data into a clean pandas DataFrame.
cancer_dataset = load_breast_cancer(as_frame=True)
df = cancer_dataset.frame

# The 'target' column is our label (0 for malignant, 1 for benign).
# All other columns are our features.
X = df.drop('target', axis=1)
y = df['target']

print("Dataset loaded successfully.")

# For our project, we will use the ENTIRE dataset as our "reference" dataset.
# This is the "golden copy" that we will compare all future live data against.
reference_df = df
reference_df.to_csv('reference_data.csv', index=False)
print("Saved reference data to 'reference_data.csv'.")


# 2. Train a simple model
# We'll train a new model just for saving.
model = LogisticRegression(solver='liblinear', max_iter=200)
model.fit(X, y)

print("Model trained successfully.")


# 3. Save the trained model to a file
# We use joblib because it's efficient for scikit-learn objects.
model_filename = 'cancer_model_v1.0.joblib'
joblib.dump(model, model_filename)

print(f"Model saved to '{model_filename}'.")
print("--- Script Finished ---")