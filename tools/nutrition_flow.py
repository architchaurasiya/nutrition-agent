"""
Nutrition Advisor Flow — orchestrates the nutrition tools in sequence.

Flow function signature MUST follow: def build_<name>(aflow: Flow) -> Flow:

Required environment variables:
    WATSONX_API_KEY     — IBM Cloud API key
    WATSONX_PROJECT_ID  — watsonx project ID
    WATSONX_URL         — generation endpoint (optional, has default)
    MODEL_ID            — model ID (optional, has default)
"""

import os
from pydantic import BaseModel, Field
from typing import Optional

from ibm_watsonx_orchestrate.flow_builder.flows import Flow, flow, START, END
from ibm_watsonx_orchestrate.agent_builder.tools import tool, ToolPermission


# ---------------------------------------------------------------------------
# Inline tool re-definitions (self-contained — no cross-file local imports)
# ---------------------------------------------------------------------------

import json
import requests

# Load .env file if python-dotenv is available (optional convenience)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ---------------------------------------------------------------------------
# Configuration — read from environment variables
# ---------------------------------------------------------------------------
WATSONX_URL = os.getenv(
    "WATSONX_URL",
    "https://us-south.ml.cloud.ibm.com/ml/v1/text/generation?version=2023-05-29",
)
MODEL_ID   = os.getenv("MODEL_ID", "ibm/granite-4-h-small")
PROJECT_ID = os.getenv("WATSONX_PROJECT_ID", "")
API_KEY    = os.getenv("WATSONX_API_KEY", "")
IAM_TOKEN_URL = "https://iam.cloud.ibm.com/identity/token"


# ---------------------------------------------------------------------------
# Flow Input / Output schemas
# ---------------------------------------------------------------------------


class NutritionFlowInput(BaseModel):
    """Input schema for the full nutrition advisory flow."""

    age: int = Field(..., description="User's age in years")
    weight_kg: float = Field(..., description="User's current weight in kilograms")
    height_cm: float = Field(..., description="User's height in centimetres")
    goal: str = Field(
        ...,
        description=(
            "Primary health goal: 'lose weight', 'build muscle', "
            "'maintain weight', or 'improve energy'"
        ),
    )
    dietary_restrictions: Optional[str] = Field(
        default="none",
        description="Any dietary restrictions or allergies",
    )
    activity_level: str = Field(
        default="moderate",
        description="Activity level: sedentary, light, moderate, active, very active",
    )


class NutritionFlowOutput(BaseModel):
    """Output schema for the full nutrition advisory flow."""

    nutrition_report: str = Field(
        description="Complete personalised nutrition report including plan, calories, macros, and meal suggestions"
    )


# ---------------------------------------------------------------------------
# Helper (inline, self-contained)
# ---------------------------------------------------------------------------


def _get_iam_token_flow() -> str:
    resp = requests.post(
        IAM_TOKEN_URL,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
            "apikey": API_KEY,
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def _call_granite_flow(prompt: str, max_tokens: int = 800) -> str:
    token = _get_iam_token_flow()
    payload = {
        "model_id": MODEL_ID,
        "project_id": PROJECT_ID,
        "input": prompt,
        "parameters": {
            "decoding_method": "greedy",
            "max_new_tokens": max_tokens,
            "min_new_tokens": 10,
            "stop_sequences": [],
        },
    }
    resp = requests.post(
        WATSONX_URL,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        json=payload,
        timeout=60,
    )
    resp.raise_for_status()
    results = resp.json().get("results", [])
    return results[0].get("generated_text", "").strip() if results else ""


# ---------------------------------------------------------------------------
# Flow tool (generates the full report in one pass)
# ---------------------------------------------------------------------------


@tool(permission=ToolPermission.READ_ONLY)
def build_nutrition_report(input: NutritionFlowInput) -> NutritionFlowOutput:
    """
    Build a comprehensive personalised nutrition report.

    Calls IBM Granite-4-h-small to generate a complete nutrition advisory
    report covering daily calorie target, macro breakdown, and meal plan.

    Args:
        input (NutritionFlowInput): User profile data.

    Returns:
        NutritionFlowOutput: Full nutrition report as a single formatted string.
    """
    prompt = f"""You are a certified nutritionist and dietitian. Create a comprehensive personalised nutrition report.

## User Profile
- Age: {input.age} years
- Weight: {input.weight_kg} kg
- Height: {input.height_cm} cm
- Goal: {input.goal}
- Dietary restrictions: {input.dietary_restrictions}
- Activity level: {input.activity_level}

## Report Structure

### 1. Personalised Nutrition Strategy
Write 3-4 sentences summarising the ideal nutritional approach for this user.

### 2. Daily Calorie Target
State the recommended daily calorie intake with a brief rationale.

### 3. Macronutrient Breakdown
Provide protein, carbohydrates, and fat targets in grams and as a percentage of total calories.

### 4. Daily Meal Plan
- Breakfast: (with approximate calories)
- Mid-morning snack: (with approximate calories)
- Lunch: (with approximate calories)
- Afternoon snack: (with approximate calories)
- Dinner: (with approximate calories)

### 5. Key Nutritional Tips
List 3 evidence-based tips tailored to the user's goal.

Keep the tone friendly, motivating, and practical."""

    report = _call_granite_flow(prompt, max_tokens=900)
    return NutritionFlowOutput(nutrition_report=report)


# ---------------------------------------------------------------------------
# Flow definition
# ---------------------------------------------------------------------------


@flow(
    name="nutrition_advisory_flow",
    display_name="Nutrition Advisory Flow",
    description=(
        "End-to-end nutrition advisory flow: accepts user profile data, "
        "calls IBM Granite-4-h-small, and returns a complete personalised "
        "nutrition report with calorie targets, macros, and meal suggestions."
    ),
    input_schema=NutritionFlowInput,
)
def build_nutrition_advisory_flow(aflow: Flow) -> Flow:
    """
    Build the nutrition advisory flow.

    Executes build_nutrition_report tool and returns the result.
    """
    report_node = aflow.tool(build_nutrition_report)
    aflow.sequence(START, report_node, END)
    return aflow
