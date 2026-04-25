from litellm import completion
import json

# import your tools
from src.tools.vital_signs_tool import analyze_vitals
from src.tools.symptom_tool import analyze_symptoms
from src.tools.decision_tool import make_decision


SYSTEM_PROMPT = """
You are an intelligent ER triage agent.

You have access to:
- Vital Signs Tool
- Symptom Tool
- Decision Tool

Your job:
1. Understand the patient input
2. Decide which tools to use
3. Combine results
4. Return final triage decision

Output format:
{
  "priority": "High / Moderate / Low",
  "department": "...",
  "explanation": "..."
}
"""


def call_llm(messages):
    response = completion(
        model="ollama/mistral",   # or phi3
        messages=messages
    )
    return response["choices"][0]["message"]["content"]


def run_agent(patient_input: dict):

    messages = [
        {"role": "system", "content": """
You are an ER triage agent.

Given patient input, decide which tools to use.

Return ONLY JSON in this format:
{
  "use_vitals": true/false,
  "use_symptoms": true/false,
  "reason": "short explanation"
}
"""},

        {"role": "user", "content": json.dumps(patient_input)}
    ]

    decision_raw = call_llm(messages)

    try:
        decision = json.loads(decision_raw)
    except:
        decision = {
            "use_vitals": True,
            "use_symptoms": True,
            "reason": "fallback decision"
        }

    vital_result = None
    symptom_result = None

    if decision.get("use_vitals") and patient_input.get("vitals"):
        vital_result = analyze_vitals(patient_input["vitals"])

    if decision.get("use_symptoms") and patient_input.get("symptoms"):
        symptom_result = analyze_symptoms(patient_input["symptoms"])

    final_result = make_decision(vital_result, symptom_result)

    return {
        "agent_decision": decision,
        "vital_analysis": vital_result,
        "symptom_analysis": symptom_result,
        "final_output": final_result
    }