"""
Local proxy server for Nutrition Agent frontend.
Handles CORS by forwarding IBM IAM + watsonx Granite API calls server-side.

Usage:
    1. Copy .env.example to .env and fill in your credentials.
    2. python server.py
    3. Open: http://localhost:5000

Required environment variables:
    WATSONX_API_KEY      — IBM Cloud API key
    WATSONX_PROJECT_ID   — watsonx project ID
    WATSONX_URL          — watsonx generation endpoint (optional, has default)
    MODEL_ID             — Granite model ID (optional, has default)
"""

import os
import sys
import requests
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# Load .env file if python-dotenv is available (optional convenience)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

app = Flask(__name__, static_folder="frontend")
CORS(app)

# ── Credentials from environment variables ────────────────────────────────────
API_KEY    = os.getenv("WATSONX_API_KEY", "")
PROJECT_ID = os.getenv("WATSONX_PROJECT_ID", "")
IAM_URL    = "https://iam.cloud.ibm.com/identity/token"
WX_GEN_URL = os.getenv(
    "WATSONX_URL",
    "https://us-south.ml.cloud.ibm.com/ml/v1/text/generation?version=2023-05-29",
)
MODEL_ID   = os.getenv("MODEL_ID", "ibm/granite-4-h-small")

# Fail fast with a clear message if required credentials are missing
_missing = [name for name, val in [("WATSONX_API_KEY", API_KEY), ("WATSONX_PROJECT_ID", PROJECT_ID)] if not val]
if _missing:
    print(f"\n[ERROR] Missing required environment variable(s): {', '.join(_missing)}")
    print("  → Copy .env.example to .env and fill in your credentials.")
    print("  → Or export the variables before running this script.\n")
    sys.exit(1)

_iam_token  = None
_token_exp  = 0


def get_iam_token():
    """Get (or refresh) IBM IAM bearer token."""
    import time
    global _iam_token, _token_exp
    if _iam_token and time.time() < _token_exp:
        return _iam_token
    resp = requests.post(
        IAM_URL,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
            "apikey": API_KEY,
        },
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    _iam_token = data["access_token"]
    _token_exp = time.time() + data.get("expires_in", 3600) - 60
    return _iam_token


# ── Serve frontend ──────────────────────────────────────────────────────────

@app.route("/")
def index():
    return send_from_directory("frontend", "index.html")


@app.route("/<path:filename>")
def static_files(filename):
    return send_from_directory("frontend", filename)


# ── Proxy: IAM token (called by frontend) ──────────────────────────────────

@app.route("/api/token", methods=["GET"])
def token():
    try:
        tok = get_iam_token()
        return jsonify({"access_token": tok})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── Proxy: Granite generation ──────────────────────────────────────────────

@app.route("/api/generate", methods=["POST"])
def generate():
    try:
        body = request.get_json(force=True)
        message = body.get("message", "")
        if not message:
            return jsonify({"error": "No message provided"}), 400

        system_prompt = (
            "You are a friendly, knowledgeable, and motivating nutrition advisor "
            "powered by IBM Granite AI.\n"
            "Your mission is to help users achieve their health and wellness goals "
            "through personalised nutrition guidance.\n"
            "You provide personalised nutrition plans, food nutritional analysis, "
            "and healthy food alternatives.\n"
            "Always be warm, encouraging, and evidence-based. "
            "Keep medical disclaimers brief.\n"
            "Format your responses clearly with sections and bullet points where helpful."
        )

        full_prompt = f"{system_prompt}\n\nUser: {message}\n\nNutrition Advisor:"

        tok = get_iam_token()
        resp = requests.post(
            WX_GEN_URL,
            headers={
                "Authorization": f"Bearer {tok}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            json={
                "model_id": MODEL_ID,
                "project_id": PROJECT_ID,
                "input": full_prompt,
                "parameters": {
                    "decoding_method": "greedy",
                    "max_new_tokens": 800,
                    "min_new_tokens": 10,
                    "stop_sequences": ["User:", "Human:"],
                },
            },
            timeout=60,
        )
        resp.raise_for_status()
        data    = resp.json()
        results = data.get("results", [])
        text    = (results[0].get("generated_text", "") if results else "").strip()
        return jsonify({"response": text or "No response generated."})

    except requests.HTTPError as e:
        return jsonify({"error": f"Granite API error {e.response.status_code}: {e.response.text}"}), 502
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    print("=" * 50)
    print("  Nutrition Advisor — Local Proxy Server")
    print("  Open: http://localhost:5000")
    print("=" * 50)
    app.run(host="0.0.0.0", port=5000, debug=False)
