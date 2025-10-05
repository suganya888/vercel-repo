from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import json
import numpy as np
from pathlib import Path

app = FastAPI()

# Enable CORS for POST requests from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST"],
    allow_headers=["*"],
)

# Load telemetry bundle from file in the same project directory
telemetry_file = Path("q-vercel-latency.json")
with open(telemetry_file) as f:
    telemetry_data = json.load(f)

# Preprocess telemetry by region
regions_data = {}
for record in telemetry_data:
    region = record["region"]
    regions_data.setdefault(region, {"latency_ms": [], "uptime_pct": []})
    regions_data[region]["latency_ms"].append(record["latency_ms"])
    regions_data[region]["uptime_pct"].append(record["uptime_pct"])

# Change route to /latency
@app.post("/latency")
async def latency_metrics(payload: dict):
    requested_regions = payload.get("regions", [])
    threshold_ms = payload.get("threshold_ms", 180)

    response = {}
    for region in requested_regions:
        if region in regions_data:
            latencies = np.array(regions_data[region]["latency_ms"])
            uptimes = np.array(regions_data[region]["uptime_pct"])

            avg_latency = np.mean(latencies)
            p95_latency = np.percentile(latencies, 95)
            avg_uptime = np.mean(uptimes)
            breaches = int(np.sum(latencies > threshold_ms))

            response[region] = {
                "avg_latency": float(avg_latency),
                "p95_latency": float(p95_latency),
                "avg_uptime": float(avg_uptime),
                "breaches": breaches,
            }

    return JSONResponse(content=response)
