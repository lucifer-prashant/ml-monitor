// frontend/src/FeatureDriftChart.js

import React, { useState, useEffect } from "react"
import ReactECharts from "echarts-for-react"
import axios from "axios"

const FeatureDriftChart = ({ modelVersion }) => {
	const [chartOptions, setChartOptions] = useState({})
	const [error, setError] = useState("")

	useEffect(() => {
		const fetchData = async () => {
			try {
				const response = await axios.get(`/api/feature_drift/${modelVersion}`)
				let data = response.data

				if (!data || data.length === 0) {
					setError("No feature drift data available.")
					return
				}

				// We only want to show the top 5 most drifted features.
				// The API already sorts them for us (lowest p-value first), so we just take the first 5.
				const top5Drifted = data.slice(0, 5)

				// For the bar chart, we need to reverse the order so the most drifted
				// feature (lowest score) appears at the top of the chart.
				top5Drifted.reverse()

				const featureNames = top5Drifted.map((d) => d.feature_name)
				const driftScores = top5Drifted.map((d) => d.drift_score)

				const options = {
					title: {
						text: "Top 5 Most Drifted Features",
						textStyle: { color: "#FFF" },
					},
					tooltip: {
						trigger: "axis",
						axisPointer: { type: "shadow" },
						formatter: "Feature: {b}<br/>Drift Score (p-value): {c}",
					},
					grid: { left: "3%", right: "4%", bottom: "3%", containLabel: true },
					xAxis: {
						type: "value",
						boundaryGap: [0, 0.01],
						axisLine: { lineStyle: { color: "#FFF" } },
					},
					yAxis: {
						type: "category",
						data: featureNames,
						axisLine: { lineStyle: { color: "#FFF" } },
					},
					series: [
						{
							name: "Drift Score",
							type: "bar",
							data: driftScores,
							itemStyle: {
								color: "#ff4d4d", // Use the same red color for drift
							},
						},
					],
				}

				setChartOptions(options)
				setError("")
			} catch (err) {
				console.error("Error fetching feature drift:", err)
				setError("Failed to fetch feature drift data.")
			}
		}

		fetchData()
		const interval = setInterval(fetchData, 15000) // Refresh every 15 seconds
		return () => clearInterval(interval)
	}, [modelVersion])

	if (error) {
		return <div style={{ color: "red" }}>{error}</div>
	}

	return (
		<ReactECharts
			option={chartOptions}
			style={{ height: "400px", width: "100%", marginTop: "40px" }}
		/>
	)
}

export default FeatureDriftChart
