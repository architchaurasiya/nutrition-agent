<div align="center">

<img src="https://img.shields.io/badge/IBM%20watsonx-Orchestrate-1a6dcc?style=for-the-badge&logo=ibm&logoColor=white" alt="IBM watsonx Orchestrate"/>
<img src="https://img.shields.io/badge/Model-Granite--4--h--small-6c3483?style=for-the-badge&logo=ibm&logoColor=white" alt="Granite Model"/>
<img src="https://img.shields.io/badge/Python-3.10%2B-3776ab?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
<img src="https://img.shields.io/badge/Flask-Proxy%20Server-000000?style=for-the-badge&logo=flask&logoColor=white" alt="Flask"/>
<img src="https://img.shields.io/badge/License-Educational-22c55e?style=for-the-badge" alt="License"/>

# 🥗 Nutrition Advisor Agent

**A personalised AI nutrition advisor powered by IBM Granite-4-h-small and deployed on IBM watsonx Orchestrate.**  
Get tailored nutrition plans, deep food analysis, and smart healthy-swap recommendations — all from a single conversational agent.

[Features](#-features) · [Architecture](#-architecture) · [Project Structure](#-project-structure) · [Setup](#-environment-setup) · [Usage](#-usage) · [Tools](#-tools)

</div>

---

## ✨ Features

| 🎯 Feature | Description |
|---|---|
| **Personalised Nutrition Plans** | Full daily meal plan built around your age, weight, height, goal, and activity level |
| **Food Analysis** | Calories, macros, micros, and a health rating for any food or meal |
| **Healthy Swaps** | Smart food-substitution suggestions aligned to your dietary preferences |
| **End-to-End Report Flow** | One-shot flow from user profile → IBM Granite → complete formatted nutrition report |
| **Web Chat UI** | Standalone browser-based chat powered by a lightweight Flask proxy |
| **watsonx Orchestrate Native** | Import directly into Orchestrate for a production-ready AI agent experience |

---

## 🏗️ Architecture

```mermaid
graph TB
    User[👤 User] -->|Web UI| Frontend[Frontend — index.html]
    User -->|Chat| WxO[watsonx Orchestrate Chat UI]

    Frontend -->|HTTP proxy| Server[server.py — Flask proxy]
    Server -->|IBM IAM + Granite API| Granite[IBM Granite-4-h-small\nus-south.ml.cloud.ibm.com]
    WxO -->|Routes requests| Agent[nutrition_agent]

    Agent -->|Calls| T1[generate_nutrition_plan]
    Agent -->|Calls| T2[analyse_food_nutrition]
    Agent -->|Calls| T3[suggest_healthy_alternatives]
    Agent -->|Executes| Flow[nutrition_advisory_flow]

    T1 -->|IBM Granite API| Granite
    T2 -->|IBM Granite API| Granite
    T3 -->|IBM Granite API| Granite
    Flow -->|build_nutrition_report tool| Granite

    style Agent fill:#1a6dcc,stroke:#145099,color:#fff
    style Flow fill:#1a8c5e,stroke:#14694a,color:#fff
    style T1 fill:#e67e22,stroke:#ca6f1e,color:#fff
    style T2 fill:#e67e22,stroke:#ca6f1e,color:#fff
    style T3 fill:#e67e22,stroke:#ca6f1e,color:#fff
    style Granite fill:#6c3483,stroke:#4a235a,color:#fff
    style Frontend fill:#2e86c1,stroke:#1a5276,color:#fff
    style Server fill:#16a085,stroke:#0e6655,color:#fff
```

### Nutrition Advisory Flow

```mermaid
flowchart TD
    Start([▶ START]) --> Input[NutritionFlowInput\nage · weight · height\ngoal · activity · restrictions]
    Input --> Report[build_nutrition_report\n🤖 IBM Granite-4-h-small]
    Report --> Output[NutritionFlowOutput\n• Calorie target\n• Macro breakdown\n• Meal plan\n• Health tips]
    Output --> End([⏹ END])

    style Start fill:#22c55e,stroke:#16a34a,color:#fff
    style End fill:#ef4444,stroke:#dc2626,color:#fff
    style Report fill:#1a6dcc,stroke:#145099,color:#fff
    style Input fill:#f39c12,stroke:#d68910,color:#fff
    style Output fill:#1a8c5e,stroke:#14694a,color:#fff
```

---

## 📁 Project Structure

```
nutrition_agent/
├── 📄 __init__.py
├── 🚀 main_flow.py              # Programmatic flow test script
├── 🌐 server.py                 # Flask proxy (serves UI + proxies API calls)
├── 🔧 import-all.sh             # CLI import script for watsonx Orchestrate
├── 📦 requirements.txt          # Python dependencies
├── 🔑 .env.example              # Credentials template (copy → .env, never commit .env)
├── 📖 README.md
│
├── tools/
│   ├── __init__.py
│   ├── 🍎 nutrition_tools.py    # Core tools: generate plan, analyse food, suggest swaps
│   └── 🔄 nutrition_flow.py     # Nutrition advisory flow definition
│
├── agents/
│   └── 🤖 nutrition_agent.yaml  # Agent configuration (LLM, tools, starter prompts)
│
├── generated/                   # Compiled flow specs (auto-generated, git-ignored)
│
└── frontend/
    └── 💬 index.html            # Standalone web chat UI
```

---

## 🛠️ Tools

| Tool | Input | What it does |
|------|-------|-------------|
| `generate_nutrition_plan` | age, weight, height, goal, activity, restrictions | Generates a full personalised daily nutrition plan with meals and macros |
| `analyse_food_nutrition` | food name / description | Returns calories, protein, carbs, fat, micros, and a health rating |
| `suggest_healthy_alternatives` | food item, dietary preferences | Recommends healthier substitutes that still match taste profile |
| `nutrition_advisory_flow` | complete user profile | End-to-end flow: profile → Granite → formatted comprehensive report |

---

## ⚙️ Configuration

| Setting | Value |
|---------|-------|
| **Model** | `ibm/granite-4-h-small` |
| **Inference Endpoint** | `https://us-south.ml.cloud.ibm.com/ml/v1/text/generation?version=2023-05-29` |
| **Agent LLM** | `groq/openai/gpt-oss-120b` |
| **Agent Style** | `react_core` |

> 🔒 **Credentials are never stored in code.** All secrets are loaded from environment variables. See [Environment Setup](#-environment-setup) below.

---

## 🔑 Environment Setup

> ⚠️ **Never commit your `.env` file or real credentials to version control.**

### Step 1 — Copy the example file

```bash
cp .env.example .env
```

### Step 2 — Fill in your credentials

```env
# Required
WATSONX_API_KEY=your_ibm_cloud_api_key_here
WATSONX_PROJECT_ID=your_watsonx_project_id_here

# Optional — sensible defaults are used if omitted
WATSONX_URL=https://us-south.ml.cloud.ibm.com/ml/v1/text/generation?version=2023-05-29
MODEL_ID=ibm/granite-4-h-small
```

### Where to find each credential

| Variable | Where to get it |
|---|---|
| `WATSONX_API_KEY` | [IBM Cloud → IAM → API keys](https://cloud.ibm.com/iam/apikeys) |
| `WATSONX_PROJECT_ID` | watsonx.ai project → **Manage** tab → Project ID |
| `WATSONX_URL` | Regional endpoint — default is `us-south`; change if your project is in another region |
| `MODEL_ID` | Granite model to use — default is `ibm/granite-4-h-small` |

---

## 🚀 Usage

### Option 1 — Web UI _(recommended for quick testing)_

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure credentials
cp .env.example .env
# Edit .env with your IBM credentials

# 3. Start the Flask proxy server
python server.py

# 4. Open your browser at:
#    http://localhost:5000
```

### Option 2 — Import to watsonx Orchestrate

```bash
# Log in to the Orchestrate CLI first, then:
chmod +x import-all.sh
./import-all.sh

# Start a chat session and select 'nutrition_agent'
orchestrate chat start
```

### Option 3 — Programmatic flow test

```bash
export PYTHONPATH=/path/to/adk/src:/path/to/adk
python main_flow.py
```

---

## 📦 Dependencies

```bash
pip install -r requirements.txt
```

| Package | Purpose |
|---------|---------|
| `flask` | Lightweight web server and API proxy backend |
| `flask-cors` | Cross-origin request handling for the browser UI |
| `requests` | HTTP calls to the IBM watsonx Inference API |
| `pydantic` | Schema validation for tool inputs and flow I/O |
| `python-dotenv` | Loads `.env` credentials at runtime |
| `ibm-watsonx-orchestrate` | ADK — tools, flows, and agent authoring |

---

## 💬 Starter Prompts

The agent ships with four ready-to-use conversation starters:

> 🟢 **"Create my nutrition plan"** — Generate a full personalised daily plan  
> 🔵 **"Analyse a food item"** — Get a detailed nutritional breakdown of any meal  
> 🟡 **"Healthy Swaps"** — Discover healthier alternatives to your favourite foods  
> 🟣 **"Full Report"** — Get a comprehensive nutrition report with a complete meal plan  

---

## 🔐 Security

- All IBM credentials are loaded exclusively from **environment variables** — zero hardcoding.
- The Flask server acts as a **secure proxy** — API keys are never exposed to the browser.
- `.env` is listed in `.gitignore` and will **never** be committed to source control.
- Only `.env.example` (with safe placeholder values) is tracked by git.

---

## 📄 License

This project is provided as-is for **educational and demonstration purposes**.  
> ⚕️ Always consult a qualified healthcare professional for personalised medical or dietary advice.

---

<div align="center">
  <sub>Built with ❤️ using <strong>IBM watsonx Orchestrate</strong> · <strong>IBM Granite-4-h-small</strong> · <strong>Python</strong></sub>
</div>
