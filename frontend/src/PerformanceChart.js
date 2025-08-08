// frontend/src/PerformanceChart.js

import React, { useState, useEffect } from "react"
import ReactECharts from "echarts-for-react"
import axios from "axios"

const PerformanceChart = ({ modelVersion }) => {
	// 'chartOptions' will hold the configuration for our chart.
	// We start with an empty object.
	const [chartOptions, setChartOptions] = useState({})
	const [error, setError] = useState("")

	// 'useEffect' is a React hook that runs code after the component renders.
	// It's perfect for making API calls.
	useEffect(() => {
		const fetchData = async () => {
			try {
				// Use axios to make a GET request to our backend API endpoint.
				// NOTE: We use a proxy to avoid CORS issues (see next step).
				const response = await axios.get(`/api/metrics/${modelVersion}`)
				const data = response.data

				if (data.length === 0) {
					setError("No data available for this model yet.")
					return
				}

				// The data from the API is an array of objects. We need to transform it
				// into separate arrays for our chart's axes and series.
				const timestamps = data.map((d) =>
					new Date(d.timestamp).toLocaleTimeString()
				)
				const accuracies = data.map((d) => d.accuracy)
				const driftScores = data.map((d) => d.data_drift_score)

				// This is the configuration object that ECharts uses to draw the chart.
				const options = {
					tooltip: { trigger: "axis" },
					legend: {
						data: ["Accuracy", "Data Drift Score"],
						textStyle: { color: "#FFF" },
					},
					xAxis: {
						type: "category",
						data: timestamps,
						axisLine: { lineStyle: { color: "#FFF" } },
					},
					yAxis: [
						{
							type: "value",
							name: "Accuracy",
							min: 0,
							max: 1,
							axisLabel: { formatter: "{value}" },
							axisLine: { lineStyle: { color: "#FFF" } },
						},
						{
							type: "value",
							name: "Drift Score",
							min: 0,
							max: 1,
							axisLabel: { formatter: "{value}" },
							axisLine: { lineStyle: { color: "#FFF" } },
						},
					],
					series: [
						{
							name: "Accuracy",
							type: "line",
							yAxisIndex: 0, // Use the first y-axis
							data: accuracies,
							smooth: true,
							color: "#61dafb",
						},
						{
							name: "Data Drift Score",
							type: "line",
							yAxisIndex: 1, // Use the second y-axis
							data: driftScores,
							smooth: true,
							color: "#ff4d4d",
						},
					],
				}

				setChartOptions(options)
				setError("")
			} catch (err) {
				console.error("Error fetching metrics:", err)
				setError("Failed to fetch metrics. Is the backend server running?")
			}
		}

		fetchData() // Fetch data immediately on component load.

		// Set up an interval to fetch data every 15 seconds.
		const interval = setInterval(fetchData, 15000)

		// This is a cleanup function. It runs when the component is unmounted
		// to prevent memory leaks by clearing the interval.
		return () => clearInterval(interval)
	}, [modelVersion]) // The effect depends on modelVersion. It will re-run if it changes.

	if (error) {
		return <div style={{ color: "red" }}>{error}</div>
	}

	return (
		<ReactECharts
			option={chartOptions}
			style={{ height: "500px", width: "100%" }}
		/>
	)
}

export default PerformanceChart
