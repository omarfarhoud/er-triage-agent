from dataclasses import asdict, is_dataclass
import json

from litellm import completion

from src.tools.decision_tool import make_decision
from src.tools.symptom_tool import analyze_symptoms
from src.tools.vital_signs_tool import analyze_vitals


MODEL = "ollama/mistral"

SYMPTOM_TOOL = "symptom_tool"
VITALS_TOOL = "vital_signs_tool"
DECISION_TOOL = "decision_tool"
FINAL_ANSWER = "final_answer"

PRIORITY_LABELS = {
    "HIGH": "High",
    "MODERATE": "Moderate",
    "LOW": "Low",
}

SYSTEM_PROMPT = f"""
You are an intelligent ER triage agent with access to three tools:
- {SYMPTOM_TOOL}: extracts medical meaning from free-text symptoms.
- {VITALS_TOOL}: detects abnormalities in structured vital signs.
- {DECISION_TOOL}: combines symptom and vital results into a triage decision.

You control the workflow one step at a time.
You do not write prose, markdown, bullets, code fences, or explanations outside JSON.

At each step, return ONLY valid JSON in one of these formats:

To request a tool:
{{
  "action": "tool",
  "tool": "{SYMPTOM_TOOL} | {VITALS_TOOL} | {DECISION_TOOL}",
  "reason": "short reason"
}}

To return the final answer:
{{
  "action": "{FINAL_ANSWER}",
  "priority": "High | Moderate | Low",
  "department": "...",
  "explanation": "brief clinical explanation"
}}

Rules:
- The first response should usually request {SYMPTOM_TOOL}.
- Do not request {DECISION_TOOL} until you have seen results from both {SYMPTOM_TOOL} and {VITALS_TOOL}.
- Do not return {FINAL_ANSWER} until you have seen the result from {DECISION_TOOL}.
- Use exactly one of these action values: "tool" or "{FINAL_ANSWER}".
- Use exactly one of these tool values: "{SYMPTOM_TOOL}", "{VITALS_TOOL}", "{DECISION_TOOL}".
- Your entire response must be parseable by json.loads().

Recommended order for complete ER triage:
1. {SYMPTOM_TOOL}
2. {VITALS_TOOL}
3. {DECISION_TOOL}
4. {FINAL_ANSWER}

Valid first response example:
{{"action":"tool","tool":"{SYMPTOM_TOOL}","reason":"extract medical concepts from symptoms"}}

Valid final response example:
{{"action":"{FINAL_ANSWER}","priority":"High","department":"Cardiology","explanation":"Critical vital signs and severe cardiac symptoms require immediate attention."}}
"""


def call_llm(messages):
    response = completion(
        model=MODEL,
        messages=messages,
        temperature=0,
    )
    return response["choices"][0]["message"]["content"]


def _to_jsonable(value):
    if is_dataclass(value):
        return asdict(value)

    if isinstance(value, list):
        return [_to_jsonable(item) for item in value]

    if isinstance(value, dict):
        return {key: _to_jsonable(item) for key, item in value.items()}

    return value


def _parse_json(raw_response: str) -> dict:
    try:
        return json.loads(raw_response)
    except json.JSONDecodeError:
        start = raw_response.find("{")
        end = raw_response.rfind("}")
        if start == -1 or end == -1 or start >= end:
            raise
        return json.loads(raw_response[start:end + 1])


def _validate_agent_step(agent_step: dict) -> None:
    action = agent_step.get("action")

    if action == FINAL_ANSWER:
        required = ["priority", "department", "explanation"]
        missing = [field for field in required if not agent_step.get(field)]
        if missing:
            raise ValueError(f"Final answer missing fields: {', '.join(missing)}")
        return

    if action != "tool":
        raise ValueError('Agent response must use action "tool" or "final_answer"')

    tool_name = agent_step.get("tool")
    if tool_name not in {SYMPTOM_TOOL, VITALS_TOOL, DECISION_TOOL}:
        raise ValueError(
            f"Tool must be one of: {SYMPTOM_TOOL}, {VITALS_TOOL}, {DECISION_TOOL}"
        )


def _get_agent_step(messages: list[dict]) -> dict:
    last_error = None

    for _ in range(2):
        raw_response = call_llm(messages)

        try:
            agent_step = _parse_json(raw_response)
            _validate_agent_step(agent_step)
            return agent_step
        except Exception as exc:
            last_error = exc
            messages.append({
                "role": "assistant",
                "content": raw_response,
            })
            messages.append({
                "role": "user",
                "content": (
                    f"Your previous response was invalid: {exc}. "
                    "Return ONLY one valid JSON object with no prose. "
                    f'To call a tool use {{"action":"tool","tool":"{SYMPTOM_TOOL}","reason":"..."}}. '
                    f'To finish use {{"action":"{FINAL_ANSWER}","priority":"High","department":"...","explanation":"..."}}.'
                ),
            })

    raise ValueError(f"Could not get a valid agent step: {last_error}")


def _validate_patient_input(patient_input: dict) -> dict:
    if not isinstance(patient_input, dict):
        raise ValueError("Patient input must be a dictionary")

    symptoms = patient_input.get("symptoms")
    vitals = patient_input.get("vitals")

    if not isinstance(symptoms, str) or not symptoms.strip():
        raise ValueError("Patient input must include symptom text")

    if not isinstance(vitals, dict) or not vitals:
        raise ValueError("Patient input must include structured vitals")

    return {
        "symptoms": symptoms.strip(),
        "vitals": vitals,
    }


def _normalize_decision_result(decision_result) -> dict:
    return {
        "priority": PRIORITY_LABELS.get(
            decision_result.final_priority,
            decision_result.final_priority,
        ),
        "department": decision_result.department,
        "explanation": decision_result.explanation,
    }


def _fallback_pipeline(patient_data: dict, trace: list[dict]) -> dict:
    symptom_result = analyze_symptoms(patient_data["symptoms"])
    trace.append({
        "tool": SYMPTOM_TOOL,
        "reason": "fallback execution",
        "result": _to_jsonable(symptom_result),
    })

    vital_result = analyze_vitals(patient_data["vitals"])
    trace.append({
        "tool": VITALS_TOOL,
        "reason": "fallback execution",
        "result": _to_jsonable(vital_result),
    })

    decision_result = make_decision(vital_result, symptom_result)
    trace.append({
        "tool": DECISION_TOOL,
        "reason": "fallback execution",
        "result": _to_jsonable(decision_result),
    })

    final_output = _normalize_decision_result(decision_result)
    final_output["agent_trace"] = trace
    return final_output


def run_agent(patient_input: dict):
    patient_data = _validate_patient_input(patient_input)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                "Patient input:\n"
                f"{json.dumps(patient_data)}\n\n"
                "Choose the next tool or return the final answer."
            ),
        },
    ]

    trace = []
    symptom_result = None
    vital_result = None
    decision_result = None

    try:
        for _ in range(6):
            agent_step = _get_agent_step(messages)

            if agent_step.get("action") == FINAL_ANSWER:
                return {
                    "priority": agent_step["priority"],
                    "department": agent_step["department"],
                    "explanation": agent_step["explanation"],
                    "agent_trace": trace,
                }

            tool_name = agent_step.get("tool")
            reason = agent_step.get("reason", "")

            if tool_name == SYMPTOM_TOOL:
                symptom_result = analyze_symptoms(patient_data["symptoms"])
                tool_result = symptom_result

            elif tool_name == VITALS_TOOL:
                vital_result = analyze_vitals(patient_data["vitals"])
                tool_result = vital_result

            elif tool_name == DECISION_TOOL:
                if symptom_result is None or vital_result is None:
                    raise ValueError("Decision tool requires symptom and vital results")
                decision_result = make_decision(vital_result, symptom_result)
                tool_result = decision_result

            else:
                raise ValueError(f"Unknown tool requested: {tool_name}")

            jsonable_result = _to_jsonable(tool_result)
            trace.append({
                "tool": tool_name,
                "reason": reason,
                "result": jsonable_result,
            })

            messages.append({
                "role": "assistant",
                "content": json.dumps(agent_step),
            })
            messages.append({
                "role": "user",
                "content": (
                    f"Tool result from {tool_name}:\n"
                    f"{json.dumps(jsonable_result)}\n\n"
                    "Choose the next tool or return the final answer."
                ),
            })

        if decision_result is None:
            raise ValueError("Agent did not complete triage within the step limit")

        final_output = _normalize_decision_result(decision_result)
        final_output["agent_trace"] = trace
        return final_output

    except Exception as exc:
        trace.append({
            "tool": "fallback",
            "reason": f"agent loop failed: {exc}",
        })
        return _fallback_pipeline(patient_data, trace)
