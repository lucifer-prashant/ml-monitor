// frontend/src/App.js
import "./App.css"
import PerformanceChart from "./PerformanceChart.js" // <-- Import
import FeatureDriftChart from "./FeatureDriftChart.js"

function App() {
	const modelVersion = "cancer_model_v1.0" // Hard-coded for now

	return (
		<div className="App">
			<header className="App-header">
				<h1>ML-Monitor Dashboard</h1>
				<h2>Tracking: {modelVersion}</h2>
			</header>
			<main>
				<PerformanceChart modelVersion={modelVersion} /> {/* <-- Use it here */}
				<FeatureDriftChart modelVersion={modelVersion} />
			</main>
		</div>
	)
}

export default App
