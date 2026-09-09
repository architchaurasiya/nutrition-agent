"""
main_flow.py — Programmatic test script for the nutrition advisory flow.

Usage:
    export PYTHONPATH=<ADK>/src:<ADK>
    python3 nutrition_agent/main_flow.py
"""

import asyncio
from pathlib import Path

from tools.nutrition_flow import build_nutrition_advisory_flow


async def main() -> None:
    """Compile, deploy, and test the nutrition advisory flow."""
    print("Compiling and deploying nutrition advisory flow...")
    flow_def = await build_nutrition_advisory_flow().compile_deploy()

    generated_folder = Path(__file__).resolve().parent / "generated"
    generated_folder.mkdir(parents=True, exist_ok=True)
    flow_def.dump_spec(str(generated_folder / "nutrition_advisory_flow.json"))
    print(f"Flow spec saved to: {generated_folder}/nutrition_advisory_flow.json")

    print("\nRunning test invocation...")
    result = await flow_def.invoke(
        {
            "age": 30,
            "weight_kg": 75.0,
            "height_cm": 175.0,
            "goal": "lose weight",
            "dietary_restrictions": "none",
            "activity_level": "moderate",
        },
        debug=True,
    )
    print("\n=== NUTRITION REPORT ===")
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
