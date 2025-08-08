// frontend/src/LandingPage.js
import React from "react"
import { Link } from "react-router-dom"
import "./LandingPage.css" // We'll create this CSS file next

function LandingPage() {
	return (
		<div className="landing-container">
			<div className="landing-box">
				<h1>Welcome to ML-Monitor</h1>
				<p>Choose how you'd like to start:</p>
				<div className="button-container">
					<Link to="/dashboard/cancer_model_v1.0" className="landing-button">
						See the Live Demo
					</Link>
					<Link to="/upload" className="landing-button primary">
						Upload Your Own Model
					</Link>
				</div>
			</div>
		</div>
	)
}

export default LandingPage
