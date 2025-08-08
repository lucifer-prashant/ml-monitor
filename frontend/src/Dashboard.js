// frontend/src/Dashboard.js
import "./App.css"
import PerformanceChart from "./PerformanceChart.js"
import FeatureDriftChart from "./FeatureDriftChart.js"
import { useParams } from "react-router-dom" // NEW: Import useParams

function Dashboard() {
	// NEW: Get the modelVersion from the URL
	const { modelVersion } = useParams()

	return (
		<div className="App">
			<header className="App-header">
				<h1>ML-Monitor Dashboard</h1>
				{/* NEW: Display the dynamic model version */}
				<h2>Tracking: {modelVersion}</h2>
			</header>
			<main>
				{/* NEW: Pass the dynamic model version to the charts */}
				<PerformanceChart modelVersion={modelVersion} />
				<FeatureDriftChart modelVersion={modelVersion} />
			</main>
		</div>
	)
}

export default Dashboard
