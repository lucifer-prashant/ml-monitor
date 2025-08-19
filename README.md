# ML-Monitor

A comprehensive machine learning model monitoring system that provides real-time performance tracking, data drift detection, and multi-model support. Built with FastAPI, React, and Evidently AI.

## 🚀 Features

- **Multi-Model Support**: Monitor multiple ML models simultaneously
- **Real-time Performance Tracking**: Track accuracy, precision, recall, and F1-score over time
- **Data Drift Detection**: Automatically detect when your model's input data distribution changes
- **Interactive Dashboard**: Beautiful, real-time charts powered by ECharts
- **Model Registry**: Upload and manage your models with version control
- **Live Demo**: Includes a pre-configured cancer prediction model for immediate testing
- **Data Simulation**: Built-in simulator to generate realistic drift scenarios

## 📋 Prerequisites

- Python 3.8+
- Node.js 16+
- npm or yarn

## 🛠️ Installation

### 1. Clone the Repository
```bash
git clone https://github.com/lucifer-prashant/ml-monitor
cd ml-monitor
```

### 2. Backend Setup
```bash
# Install Python dependencies
pip install fastapi uvicorn pandas sqlite3 evidently joblib scikit-learn

# Start the backend server
cd backend
python main.py
# Or using uvicorn directly:
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Frontend Setup
```bash
# Install Node.js dependencies
cd frontend
npm install

# Start the development server
npm start
```

### 4. Analysis Worker Setup
```bash
# Start the analysis worker (in a separate terminal)
cd analysis
python worker.py
```

The application will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## 🎯 Quick Start

### Option 1: Try the Live Demo
1. Navigate to http://localhost:3000
2. Click "See the Live Demo" to view the pre-configured cancer model
3. Start the data simulator to see real-time monitoring:
   ```bash
   cd simulator
   python run_simulation.py cancer_model_v1.0
   ```

### Option 2: Upload Your Own Model
1. Navigate to http://localhost:3000
2. Click "Upload Your Own Model"
3. Fill in the form:
   - **Model Name**: A descriptive name (e.g., "Loan Risk Predictor")
   - **Model Version**: Version identifier (e.g., "v1.0")
   - **Model File**: Your trained model saved as `.joblib` format
   - **Reference Data**: CSV file with your training/reference data

## 📊 Model Requirements

### Model File Format
- Must be a scikit-learn compatible model
- Saved using `joblib.dump(model, 'model.joblib')`
- Should have a `.predict()` method

### Reference Data Format
- CSV file with features and target column
- Target column must be named 'target'
- Features should match what your model expects
- Example structure:
```csv
feature_1,feature_2,feature_3,target
1.2,3.4,5.6,0
2.1,4.3,6.5,1
...
```

## 🔄 Data Simulation

The system includes a sophisticated data simulator that:
- Sends data points every 2 seconds
- Includes a 60-second grace period with clean data
- Gradually introduces realistic drift patterns
- Simulates real-world model degradation scenarios

```bash
# Run simulation for your model
python simulator/run_simulation.py your_model_name_v1.0
```

## 📈 Monitoring Features

### Performance Metrics
- **Accuracy**: Overall model accuracy over time
- **Precision**: Positive prediction accuracy
- **Recall**: True positive detection rate
- **F1-Score**: Harmonic mean of precision and recall

### Drift Detection
- **Data Drift Score**: Binary indicator of distribution changes
- **Feature-Level Drift**: Individual feature drift scores
- **Top 5 Drifted Features**: Most significantly changed features
- **Statistical Tests**: Uses Evidently AI's robust drift detection

## 🏗️ Architecture

```
ml-monitor/
├── backend/           # FastAPI backend server
│   └── main.py       # API endpoints and database setup
├── frontend/         # React frontend application
│   ├── src/
│   │   ├── App.js           # Main app component
│   │   ├── Dashboard.js     # Monitoring dashboard
│   │   ├── PerformanceChart.js
│   │   ├── FeatureDriftChart.js
│   │   ├── LandingPage.js
│   │   └── UploadPage.js
│   └── package.json
├── analysis/         # Background analysis worker
│   └── worker.py     # Evidently AI analysis engine
├── simulator/        # Data simulation tools
│   └── run_simulation.py
└── assets/          # Model and data storage
    └── [model_id]/
        ├── model.joblib
        └── reference_data.csv
```

## 🗄️ Database Schema

The system uses SQLite databases for simplicity:

### Model Registry (`model_registry.db`)
- Stores registered model metadata
- Tracks model versions and descriptions

### Live Data (`live_data.db`)
- Stores incoming prediction requests
- Links data to specific model versions

### Metrics (`metrics.db`)
- Performance metrics over time
- Feature-level drift scores
- Analysis timestamps

## 🔧 Configuration

### Analysis Frequency
Modify `ANALYSIS_INTERVAL_SECONDS` in `analysis/worker.py` to change how often analysis runs (default: 15 seconds).

### Simulation Speed
Adjust `SEND_INTERVAL_SECONDS` in `simulator/run_simulation.py` to control data ingestion rate (default: 2 seconds).

### Grace Period
Change `grace_period_seconds` in the simulator to adjust the clean data period before drift begins (default: 60 seconds).

## 🚨 Troubleshooting

### Common Issues

1. **"No data available for this model yet"**
   - Ensure the data simulator is running
   - Wait for the analysis worker to process data (runs every 15 seconds)

2. **Backend connection errors**
   - Verify the FastAPI server is running on port 8000
   - Check that all dependencies are installed

3. **Model upload fails**
   - Ensure model is saved in `.joblib` format
   - Verify CSV has a 'target' column
   - Check that model name/version combination is unique

4. **Charts not updating**
   - Confirm the analysis worker is running
   - Check browser console for API errors
   - Verify data is being ingested successfully



---

**Happy Monitoring!** 📊✨
