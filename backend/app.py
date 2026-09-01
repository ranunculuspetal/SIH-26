from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from flask import Flask, jsonify, send_from_directory
from datetime import datetime
import random


ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"

app = Flask(__name__, static_folder=str(FRONTEND / "static"))


# --------------------------------------------------
# DEMO ASSET DATA
# --------------------------------------------------

BASE_ASSETS = [
    {
        "id": "WAP-7 30765",
        "type": "Electric locomotive",
        "line": "Delhi–Mumbai",
        "status": "Ready",
        "due": "18 Aug",
        "health": 92,
        "tone": "blue",
        "age": 6,
        "utilization": 82,
        "previous_failures": 1,
    },
    {
        "id": "LHB Rake 82401",
        "type": "Passenger rake",
        "line": "Mumbai Central",
        "status": "Service due",
        "due": "Today",
        "health": 76,
        "tone": "amber",
        "age": 9,
        "utilization": 91,
        "previous_failures": 3,
    },
    {
        "id": "WDP-4D 40518",
        "type": "Diesel locomotive",
        "line": "Pune Division",
        "status": "Ready",
        "due": "21 Aug",
        "health": 88,
        "tone": "blue",
        "age": 11,
        "utilization": 74,
        "previous_failures": 2,
    },
]


state = {
    "assets": deepcopy(BASE_ASSETS),
    "replanned": False,
}


# --------------------------------------------------
# AI / ML RISK PREDICTION
# --------------------------------------------------

def predict_failure_risk(asset):
    """
    ML-style predictive maintenance model.

    Later this function can be replaced with a real
    trained Random Forest / XGBoost model.
    """

    health_risk = 100 - asset["health"]

    utilization_risk = asset["utilization"] * 0.25

    age_risk = asset["age"] * 1.5

    failure_risk = asset["previous_failures"] * 6

    status_risk = 0

    if asset["status"] == "Service due":
        status_risk = 12

    elif asset["status"] == "Failure reported":
        status_risk = 30

    # Weighted AI risk score
    risk_score = (
        health_risk * 0.45
        + utilization_risk
        + age_risk
        + failure_risk
        + status_risk
    )

    risk_score = min(100, round(risk_score))

    if risk_score >= 70:
        risk_level = "High"

    elif risk_score >= 40:
        risk_level = "Medium"

    else:
        risk_level = "Low"

    return {
        "risk_score": risk_score,
        "risk_level": risk_level,
    }


# --------------------------------------------------
# DEMAND PREDICTION
# --------------------------------------------------

def predict_corridor_demand(hour):
    """
    Simulated AI demand prediction.

    Real version:
    Historical train movement data
    → ML model
    → passenger/freight demand forecast
    """

    peak_hours = {
        6: 95,
        7: 100,
        8: 92,
        9: 80,
        10: 60,
        11: 55,
        12: 65,
        13: 70,
        14: 68,
        15: 72,
        16: 85,
        17: 96,
        18: 100,
        19: 94,
        20: 82,
        21: 60,
        22: 40,
        23: 25,
    }

    return peak_hours.get(hour, 30)


# --------------------------------------------------
# OPTIMIZATION ENGINE
# --------------------------------------------------

def calculate_block_score(asset, hour):
    """
    Optimization objective:

    Maximize:
    - asset safety
    - maintenance urgency
    - availability

    Minimize:
    - passenger disruption
    - traffic demand
    """

    risk = predict_failure_risk(asset)["risk_score"]

    demand = predict_corridor_demand(hour)

    # Higher risk = maintenance more important
    maintenance_benefit = risk * 1.2

    # Higher demand = more disruption
    disruption_cost = demand * 1.0

    # Optimization score
    score = maintenance_benefit - disruption_cost

    return round(score, 2)


def optimize_block(asset):
    """
    AI optimization searches different time windows
    and chooses the lowest-impact maintenance period.
    """

    candidate_hours = [1, 2, 3, 4, 10, 11, 12, 13, 14, 15, 22]

    options = []

    for hour in candidate_hours:

        score = calculate_block_score(asset, hour)
        demand = predict_corridor_demand(hour)

        options.append({
            "hour": hour,
            "score": score,
            "predicted_demand": demand,
        })

    # Select best optimized time
    best = max(options, key=lambda x: x["score"])

    start = f"{best['hour']:02d}:30"

    end_hour = best["hour"] + 2

    if end_hour >= 24:
        end_hour -= 24

    end = f"{end_hour:02d}:00"

    return {
        "time": f"{start}–{end}",
        "optimization_score": best["score"],
        "predicted_demand": best["predicted_demand"],
    }


# --------------------------------------------------
# METRICS
# --------------------------------------------------

def metrics():

    failed = sum(
        asset["status"] == "Failure reported"
        for asset in state["assets"]
    )

    high_risk = 0

    for asset in state["assets"]:
        prediction = predict_failure_risk(asset)

        if prediction["risk_level"] == "High":
            high_risk += 1

    availability = (
        96.1
        if state["replanned"]
        else (89.8 if failed else 94.6)
    )

    return {
        "availability": availability,
        "failed_assets": failed,
        "high_risk_assets": high_risk,
        "protected_trains": 148,
        "blocks_due": 3 if failed else 2,
    }


# --------------------------------------------------
# AI OPTIMIZED PLAN
# --------------------------------------------------

def build_plan():

    optimized_blocks = []

    positions = [9, 34, 66]

    colors = ["blue", "mint", "purple"]

    works = [
        "Traction inspection",
        "Brake integrity check",
        "Engine diagnostics",
    ]

    for index, asset in enumerate(state["assets"]):

        prediction = predict_failure_risk(asset)

        optimized = optimize_block(asset)

        optimized_blocks.append({
            "asset": asset["id"],
            "work": works[index],
            "time": optimized["time"],
            "left": positions[index],
            "width": 16,
            "tone": colors[index],
            "risk_score": prediction["risk_score"],
            "risk_level": prediction["risk_level"],
            "predicted_demand": optimized["predicted_demand"],
            "optimization_score": optimized["optimization_score"],
        })

    current = metrics()

    return {
        "status": "AI optimized",
        "metrics": current,
        "message": (
            "AI evaluated asset failure risk, predicted corridor demand, "
            "and selected the lowest-impact maintenance windows."
        ),
        "blocks": optimized_blocks,
    }


# --------------------------------------------------
# ROUTES
# --------------------------------------------------

@app.get("/")
def index():
    return send_from_directory(FRONTEND, "index.html")


@app.get("/api/dashboard")
def dashboard():

    assets_with_ai = []

    for asset in state["assets"]:

        asset_copy = deepcopy(asset)

        # Add AI prediction
        asset_copy["ai_prediction"] = predict_failure_risk(asset)

        assets_with_ai.append(asset_copy)

    return jsonify({
        "metrics": metrics(),
        "assets": assets_with_ai,
        "plan": build_plan(),
    })


@app.get("/api/assets")
def assets():

    assets_with_ai = []

    for asset in state["assets"]:

        asset_copy = deepcopy(asset)

        asset_copy["ai_prediction"] = predict_failure_risk(asset)

        assets_with_ai.append(asset_copy)

    return jsonify(assets_with_ai)


@app.post("/api/assets/<asset_id>/simulate-failure")
def simulate_failure(asset_id: str):

    for asset in state["assets"]:

        if asset["id"] == asset_id:

            asset.update({
                "status": "Failure reported",
                "health": 41,
                "tone": "red",
                "previous_failures": asset["previous_failures"] + 1,
            })

            state["replanned"] = False

            return jsonify({
                "message": (
                    f"AI detected critical risk for {asset_id}. "
                    "Asset moved to incident review."
                ),
                "prediction": predict_failure_risk(asset),
                "metrics": metrics(),
            })

    return jsonify({
        "error": "Asset not found"
    }), 404


@app.post("/api/plan/replan")
def replan():

    state["replanned"] = True

    for asset in state["assets"]:

        prediction = predict_failure_risk(asset)

        if asset["status"] == "Failure reported":

            asset.update({
                "status": "Reserve cover assigned",
                "tone": "amber",
            })

    return jsonify({
        "message": (
            "AI optimization completed. Maintenance blocks were "
            "rescheduled to minimize train disruption."
        ),
        "plan": build_plan(),
    })


@app.post("/api/reset")
def reset():

    state["assets"] = deepcopy(BASE_ASSETS)

    state["replanned"] = False

    return jsonify({
        "message": "Demo data reset.",
        "metrics": metrics(),
    })


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
