"""
Nutrition Agent Tools — IBM watsonx Granite-4 powered nutrition advisor.

All tools are self-contained (no cross-file local imports).

Required environment variables:
    WATSONX_API_KEY     — IBM Cloud API key
    WATSONX_PROJECT_ID  — watsonx project ID
    WATSONX_URL         — generation endpoint (optional, has default)
    MODEL_ID            — model ID (optional, has default)
"""

import os
import json
import requests
from typing import Optional, List
from pydantic import BaseModel, Field
from ibm_watsonx_orchestrate.agent_builder.tools import tool, ToolPermission

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
# Pydantic schemas
# ---------------------------------------------------------------------------


class NutritionPlanInput(BaseModel):
    """Input for generating a personalized nutrition plan."""

    age: int = Field(..., description="User's age in years")
    weight_kg: float = Field(..., description="User's current weight in kilograms")
    height_cm: float = Field(..., description="User's height in centimetres")
    goal: str = Field(
        ...,
        description=(
            "Primary health goal, e.g. 'lose weight', 'build muscle', "
            "'maintain weight', 'improve energy'"
        ),
    )
    dietary_restrictions: Optional[str] = Field(
        default="none",
        description="Any dietary restrictions or allergies (e.g. 'vegan', 'gluten-free', 'nut allergy')",
    )
    activity_level: str = Field(
        default="moderate",
        description="Physical activity level: sedentary, light, moderate, active, very active",
    )


class NutritionPlanOutput(BaseModel):
    """Personalized nutrition plan."""

    plan: str = Field(description="Detailed personalized nutrition plan")
    daily_calories: str = Field(description="Recommended daily calorie intake")
    macros: str = Field(description="Macronutrient breakdown (protein, carbs, fat)")
    meal_suggestions: str = Field(description="Suggested meals for the day")


class FoodAnalysisInput(BaseModel):
    """Input for analysing a food item's nutritional value."""

    food_item: str = Field(
        ..., description="Food item or meal to analyse (e.g. 'grilled chicken breast with brown rice')"
    )
    portion_size: Optional[str] = Field(
        default="standard serving",
        description="Portion size description (e.g. '200g', '1 cup', 'standard serving')",
    )


class FoodAnalysisOutput(BaseModel):
    """Nutritional analysis of a food item."""

    analysis: str = Field(description="Detailed nutritional analysis")
    calories: str = Field(description="Estimated calories per portion")
    nutrients: str = Field(description="Key nutrients and their amounts")
    health_rating: str = Field(description="Health rating out of 10 with explanation")


class HealthyAlternativeInput(BaseModel):
    """Input for suggesting healthy food alternatives."""

    unhealthy_food: str = Field(
        ..., description="The food item the user wants a healthier alternative for"
    )
    preference: Optional[str] = Field(
        default="general",
        description="Dietary preference for alternatives (e.g. 'vegan', 'low-carb', 'high-protein')",
    )


class HealthyAlternativeOutput(BaseModel):
    """Healthy food alternatives."""

    alternatives: str = Field(description="List of healthy alternatives with explanations")
    benefits: str = Field(description="Health benefits of switching to the alternatives")
    tips: str = Field(description="Practical tips for making the switch")


# ---------------------------------------------------------------------------
# Helper: get IAM bearer token
# ---------------------------------------------------------------------------


def _get_iam_token() -> str:
    """Exchange IBM Cloud API key for a short-lived IAM bearer token."""
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


def _call_granite(prompt: str, max_tokens: int = 600) -> str:
    """Send a prompt to the IBM Granite-4-h-small model and return the generated text."""
    token = _get_iam_token()
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
# Tools
# ---------------------------------------------------------------------------


@tool(permission=ToolPermission.READ_ONLY)
def generate_nutrition_plan(input: NutritionPlanInput) -> NutritionPlanOutput:
    """
    Generate a personalized nutrition plan for the user based on their profile.

    Uses IBM Granite-4-h-small to create a tailored daily nutrition plan
    including calorie targets, macronutrient breakdown, and meal suggestions.

    Args:
        input (NutritionPlanInput): User profile including age, weight, height,
            goal, dietary restrictions, and activity level.

    Returns:
        NutritionPlanOutput: A complete personalized nutrition plan with calorie
            targets, macros, and meal suggestions.
    """
    prompt = f"""You are a certified nutritionist. Create a personalized daily nutrition plan.

User Profile:
- Age: {input.age} years
- Weight: {input.weight_kg} kg
- Height: {input.height_cm} cm
- Goal: {input.goal}
- Dietary restrictions: {input.dietary_restrictions}
- Activity level: {input.activity_level}

Provide:
1. PLAN: A brief personalized nutrition strategy (3-4 sentences)
2. DAILY CALORIES: Recommended daily calorie intake with explanation
3. MACROS: Protein/Carbs/Fat breakdown in grams and percentages
4. MEAL SUGGESTIONS: Breakfast, lunch, dinner, and 2 snacks

Keep it practical and evidence-based."""

    raw = _call_granite(prompt, max_tokens=700)

    # Parse sections from generated text
    plan = raw
    calories = "See plan above"
    macros = "See plan above"
    meals = "See plan above"

    lines = raw.split("\n")
    current_section = ""
    section_content: dict = {"plan": [], "calories": [], "macros": [], "meals": []}
    for line in lines:
        ll = line.lower()
        if "plan" in ll and ":" in ll:
            current_section = "plan"
        elif "calori" in ll and ":" in ll:
            current_section = "calories"
        elif "macro" in ll and ":" in ll:
            current_section = "macros"
        elif "meal" in ll and ":" in ll:
            current_section = "meals"
        elif current_section:
            section_content[current_section].append(line)

    if section_content["plan"]:
        plan = "\n".join(section_content["plan"]).strip() or raw
    if section_content["calories"]:
        calories = "\n".join(section_content["calories"]).strip()
    if section_content["macros"]:
        macros = "\n".join(section_content["macros"]).strip()
    if section_content["meals"]:
        meals = "\n".join(section_content["meals"]).strip()

    return NutritionPlanOutput(
        plan=plan,
        daily_calories=calories,
        macros=macros,
        meal_suggestions=meals,
    )


@tool(permission=ToolPermission.READ_ONLY)
def analyse_food_nutrition(input: FoodAnalysisInput) -> FoodAnalysisOutput:
    """
    Analyse the nutritional content of a food item or meal.

    Uses IBM Granite-4-h-small to provide a detailed breakdown of calories,
    macronutrients, micronutrients, and an overall health rating.

    Args:
        input (FoodAnalysisInput): Food item and portion size to analyse.

    Returns:
        FoodAnalysisOutput: Nutritional analysis including calories, nutrients,
            and a health rating out of 10.
    """
    prompt = f"""You are a nutrition expert. Analyse the nutritional content of the following food.

Food: {input.food_item}
Portion size: {input.portion_size}

Provide:
1. ANALYSIS: Overview of this food's nutritional profile (2-3 sentences)
2. CALORIES: Estimated calorie count with explanation
3. NUTRIENTS: Key macronutrients (protein, carbs, fat) and notable micronutrients
4. HEALTH RATING: Rate this food /10 for health value with a brief explanation

Be specific and evidence-based."""

    raw = _call_granite(prompt, max_tokens=500)

    analysis = raw
    calories = "See analysis above"
    nutrients = "See analysis above"
    rating = "See analysis above"

    lines = raw.split("\n")
    current_section = ""
    section_content: dict = {"analysis": [], "calories": [], "nutrients": [], "rating": []}
    for line in lines:
        ll = line.lower()
        if "analysis" in ll and ":" in ll:
            current_section = "analysis"
        elif "calori" in ll and ":" in ll:
            current_section = "calories"
        elif "nutrient" in ll and ":" in ll:
            current_section = "nutrients"
        elif "rating" in ll and ":" in ll:
            current_section = "rating"
        elif current_section:
            section_content[current_section].append(line)

    if section_content["analysis"]:
        analysis = "\n".join(section_content["analysis"]).strip() or raw
    if section_content["calories"]:
        calories = "\n".join(section_content["calories"]).strip()
    if section_content["nutrients"]:
        nutrients = "\n".join(section_content["nutrients"]).strip()
    if section_content["rating"]:
        rating = "\n".join(section_content["rating"]).strip()

    return FoodAnalysisOutput(
        analysis=analysis,
        calories=calories,
        nutrients=nutrients,
        health_rating=rating,
    )


@tool(permission=ToolPermission.READ_ONLY)
def suggest_healthy_alternatives(input: HealthyAlternativeInput) -> HealthyAlternativeOutput:
    """
    Suggest healthier alternatives for a given food item.

    Uses IBM Granite-4-h-small to recommend nutritious substitutes that match
    the user's dietary preferences while improving their overall diet quality.

    Args:
        input (HealthyAlternativeInput): The unhealthy food item and dietary preference.

    Returns:
        HealthyAlternativeOutput: List of healthy alternatives with benefits
            and practical switching tips.
    """
    prompt = f"""You are a nutrition coach. Suggest healthy alternatives to the following food.

Food to replace: {input.unhealthy_food}
Dietary preference: {input.preference}

Provide:
1. ALTERNATIVES: List 3-5 specific healthier alternatives with brief descriptions
2. BENEFITS: Key health benefits of making these substitutions
3. TIPS: 2-3 practical tips for making the switch successfully

Be specific, practical, and encouraging."""

    raw = _call_granite(prompt, max_tokens=500)

    alternatives = raw
    benefits = "See alternatives above"
    tips = "See alternatives above"

    lines = raw.split("\n")
    current_section = ""
    section_content: dict = {"alternatives": [], "benefits": [], "tips": []}
    for line in lines:
        ll = line.lower()
        if "alternative" in ll and ":" in ll:
            current_section = "alternatives"
        elif "benefit" in ll and ":" in ll:
            current_section = "benefits"
        elif "tip" in ll and ":" in ll:
            current_section = "tips"
        elif current_section:
            section_content[current_section].append(line)

    if section_content["alternatives"]:
        alternatives = "\n".join(section_content["alternatives"]).strip() or raw
    if section_content["benefits"]:
        benefits = "\n".join(section_content["benefits"]).strip()
    if section_content["tips"]:
        tips = "\n".join(section_content["tips"]).strip()

    return HealthyAlternativeOutput(
        alternatives=alternatives,
        benefits=benefits,
        tips=tips,
    )
