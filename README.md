# ER Triage System Using Agentic AI
## A Single-Agent Approach with Tools

### 1. Introduction
This project proposes an agentic AI system for Emergency Room (ER) triage using a single intelligent agent equipped with specialized tools. The agent processes both structured vital signs and unstructured symptom descriptions to autonomously generate triage decisions. Unlike traditional rule-based pipelines, our approach demonstrates core agentic AI principles: the agent reasons over available tools, decides which ones to use, and generates decisions autonomously. This architecture simplifies complexity while maintaining interpretability.

### 2. The Problem & Solution
Emergency rooms need fast, consistent patient prioritization. Traditional systems are rigid and rule-based. Clinicians need reasoning combined with data analysis. Both structured (vitals) and unstructured (symptoms) data must be considered. 

**Our Solution:** A single intelligent agent with access to specialized tools. The agent receives patient data (vitals + symptoms), decides which tools to use, reasons over results, and outputs a triage decision. Simple, interpretable, agentic.

### 3. System Architecture
**Single Agent + Three Tools**
ER Triage Agent has access to three specialized tools:

**1️⃣ Vital Signs Analysis Tool**
* **Input:** Structured vital data (heart rate, SpO₂, blood pressure, temperature)
* **Function:** Detects abnormal values using predefined medical thresholds
* **Output:** Risk assessment (Normal / At-Risk / Critical)

**2️⃣ Symptom Understanding Tool**
* **Input:** Free-text symptom descriptions
* **Function:** Extracts key medical concepts from unstructured patient descriptions
* **Output:** Structured symptom categories and severity indicators

**3️⃣ Decision Tool**
* **Input:** Combined outputs from vital and symptom tools
* **Function:** Applies triage logic to determine priority and department
* **Output:** Priority (High / Moderate / Low), Department, Recommendation

### 4. Data Flow
Patient Input
↓
[Structured Vitals] + [Unstructured Symptoms]
↓
Agent Decision Point
↓
Calls Symptom Understanding Tool → Extracts medical meaning
↓
Calls Vital Signs Analysis Tool → Detects abnormalities
↓
Calls Decision Tool → Combines results
↓
Output
→ Triage Priority
→ Recommended Department
→ Clinical Explanation

### 5. Datasets
We use two carefully selected, publicly available datasets (both included in `data/raw/` for easy evaluation):

* **Dataset 1 (Structured):** Human Vital Signs Dataset (Kaggle). Features: Heart rate, BP, SpO₂, temperature. Defines abnormal thresholds.
* **Dataset 2 (Unstructured):** Open Patients Dataset (Hugging Face). Patient narratives & symptom descriptions. Tests symptom extraction.

### 6. Deployment Architecture
* **Frontend:** Web form for patient data entry (vitals + symptoms)
* **Backend:** FastAPI service hosting the agent
* **Agent Runtime:** LLM (e.g., Claude) + tool access
* **Output:** Triage recommendation displayed to medical staff

Simple. No multi-agent orchestration. Just one agent, clear tools, one job.



---

## 🚀 Local Setup & Cloning Instructions

We use `uv` for dependency management.

### 1. Clone the Repository
`git clone <https://github.com/omarfarhoud/er-triage-agent>`
`cd er_triage_agent`

### 2. Install uv
If you don't have it installed:
* **Mac/Linux:** `curl -LsSf https://astral.sh/uv/install.sh | sh`
* **Windows:** `powershell -c "irm https://astral.sh/uv/install.ps1 | iex"`

### 3. Sync the Environment
This instantly installs all libraries (FastAPI, Anthropic, Jupyter, Pandas, etc.):
`uv sync`

