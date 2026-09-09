#!/usr/bin/env bash
# import-all.sh — Import all nutrition agent tools and agent into watsonx Orchestrate.
# Usage: chmod +x import-all.sh && ./import-all.sh

set -e

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

echo "========================================="
echo " Nutrition Agent — Import to wxO"
echo "========================================="

# --- 1. Import Python tools ---
echo ""
echo "[1/3] Importing Python tools..."
for tool in nutrition_tools.py; do
  echo "  → Importing tool: ${tool}"
  orchestrate tools import -k python -f "${SCRIPT_DIR}/tools/${tool}"
done

# --- 2. Import Flow tools ---
echo ""
echo "[2/3] Importing Flow tools..."
for flow_file in nutrition_flow.py; do
  echo "  → Importing flow: ${flow_file}"
  orchestrate tools import -k flow -f "${SCRIPT_DIR}/tools/${flow_file}"
done

# --- 3. Import Agent ---
echo ""
echo "[3/3] Importing Agent..."
for agent in nutrition_agent.yaml; do
  echo "  → Importing agent: ${agent}"
  orchestrate agents import -f "${SCRIPT_DIR}/agents/${agent}"
done

echo ""
echo "✅  All imports complete!"
echo ""
echo "To start chatting with the agent:"
echo "  orchestrate chat start"
echo "  → Select 'nutrition_agent'"
