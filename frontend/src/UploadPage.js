// frontend/src/UploadPage.js
import React, { useState } from "react"
import axios from "axios"
import { useNavigate } from "react-router-dom"
import "./UploadPage.css" // We'll create this CSS file

function UploadPage() {
	const [modelName, setModelName] = useState("")
	const [modelVersion, setModelVersion] = useState("")
	const [modelFile, setModelFile] = useState(null)
	const [dataFile, setDataFile] = useState(null)
	const [error, setError] = useState("")
	const [isUploading, setIsUploading] = useState(false)
	const navigate = useNavigate()

	const handleSubmit = async (e) => {
		e.preventDefault()
		if (!modelName || !modelVersion || !modelFile || !dataFile) {
			setError("All fields and files are required.")
			return
		}
		setIsUploading(true)
		setError("")

		const formData = new FormData()
		formData.append("model_name", modelName)
		formData.append("model_version", modelVersion)
		formData.append("model_file", modelFile)
		formData.append("data_file", dataFile)

		try {
			const response = await axios.post("/upload_and_register", formData, {
				headers: {
					"Content-Type": "multipart/form-data",
				},
			})
			// On success, redirect to the new model's dashboard
			const { model_version_id } = response.data
			navigate(`/dashboard/${model_version_id}`)
		} catch (err) {
			setError(err.response?.data?.error || "An error occurred during upload.")
			setIsUploading(false)
		}
	}

	return (
		<div className="upload-container">
			<div className="upload-box">
				<h1>Upload Your Model</h1>
				<form onSubmit={handleSubmit}>
					<div className="form-group">
						<label>Model Name</label>
						<input
							type="text"
							placeholder="e.g., Loan Risk Predictor"
							value={modelName}
							onChange={(e) => setModelName(e.target.value)}
						/>
					</div>
					<div className="form-group">
						<label>Model Version</label>
						<input
							type="text"
							placeholder="e.g., v1.0"
							value={modelVersion}
							onChange={(e) => setModelVersion(e.target.value)}
						/>
					</div>
					<div className="form-group">
						<label>Model File (.joblib)</label>
						<input
							type="file"
							accept=".joblib"
							onChange={(e) => setModelFile(e.target.files[0])}
						/>
					</div>
					<div className="form-group">
						<label>Reference Data (.csv)</label>
						<input
							type="file"
							accept=".csv"
							onChange={(e) => setDataFile(e.target.files[0])}
						/>
					</div>
					{error && <p className="error-message">{error}</p>}
					<button
						type="submit"
						className="upload-button"
						disabled={isUploading}>
						{isUploading ? "Uploading..." : "Upload and Monitor"}
					</button>
				</form>
			</div>
		</div>
	)
}

export default UploadPage
