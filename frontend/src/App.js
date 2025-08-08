// frontend/src/App.js
import { BrowserRouter, Routes, Route } from "react-router-dom"
import LandingPage from "./LandingPage"
import UploadPage from "./UploadPage"
import Dashboard from "./Dashboard"

function App() {
	return (
		<BrowserRouter>
			<Routes>
				<Route path="/" element={<LandingPage />} />
				<Route path="/upload" element={<UploadPage />} />
				{/* The route for the dashboard is now dynamic */}
				<Route path="/dashboard/:modelVersion" element={<Dashboard />} />
			</Routes>
		</BrowserRouter>
	)
}

export default App
