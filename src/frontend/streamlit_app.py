import streamlit as st
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.agent.core_agent import run_agent


SAMPLE_PATIENT = {
    "symptoms": "Severe chest pain with shortness of breath and dizziness.",
    "vitals": {
        "heart_rate": 125,
        "systolic_bp": 85,
        "diastolic_bp": 55,
        "oxygen_saturation": 89,
        "body_temperature": 38.2,
    },
}


def build_patient_payload() -> dict:
    return {
        "symptoms": st.session_state.symptoms.strip(),
        "vitals": {
            "heart_rate": st.session_state.heart_rate,
            "systolic_bp": st.session_state.systolic_bp,
            "diastolic_bp": st.session_state.diastolic_bp,
            "oxygen_saturation": st.session_state.oxygen_saturation,
            "body_temperature": st.session_state.body_temperature,
        },
    }


def load_sample() -> None:
    st.session_state.symptoms = SAMPLE_PATIENT["symptoms"]
    st.session_state.heart_rate = SAMPLE_PATIENT["vitals"]["heart_rate"]
    st.session_state.systolic_bp = SAMPLE_PATIENT["vitals"]["systolic_bp"]
    st.session_state.diastolic_bp = SAMPLE_PATIENT["vitals"]["diastolic_bp"]
    st.session_state.oxygen_saturation = SAMPLE_PATIENT["vitals"]["oxygen_saturation"]
    st.session_state.body_temperature = SAMPLE_PATIENT["vitals"]["body_temperature"]


def render_result(result: dict) -> None:
    priority = result.get("priority", "Unknown")
    department = result.get("department", "Unknown")
    explanation = result.get("explanation", "No explanation returned.")

    st.subheader("Triage Result")

    col1, col2 = st.columns(2)
    col1.metric("Priority", priority)
    col2.metric("Recommended Department", department)

    st.markdown("#### Clinical Explanation")
    st.write(explanation)

    trace = result.get("agent_trace", [])
    if trace:
        st.markdown("#### Agent Trace")
        for index, step in enumerate(trace, start=1):
            tool = step.get("tool", "agent_step")
            reason = step.get("reason", "No reason provided")

            with st.expander(f"{index}. {tool}"):
                st.caption(reason)
                st.json(step.get("result", {}))


st.set_page_config(
    page_title="ER Triage Agent",
    page_icon="ER",
    layout="wide",
)

if "symptoms" not in st.session_state:
    load_sample()

st.title("ER Triage Agent")

left, right = st.columns([0.95, 1.05], gap="large")

with left:
    st.subheader("Patient Input")

    with st.form("triage_form"):
        st.text_area(
            "Symptoms",
            key="symptoms",
            height=170,
            placeholder="Describe the patient's symptoms.",
        )

        vitals_col1, vitals_col2 = st.columns(2)
        with vitals_col1:
            st.number_input("Heart Rate (bpm)", min_value=0.0, step=1.0, key="heart_rate")
            st.number_input("Systolic BP (mmHg)", min_value=0.0, step=1.0, key="systolic_bp")
            st.number_input("SpO2 (%)", min_value=0.0, max_value=100.0, step=1.0, key="oxygen_saturation")

        with vitals_col2:
            st.number_input("Diastolic BP (mmHg)", min_value=0.0, step=1.0, key="diastolic_bp")
            st.number_input(
                "Body Temperature (C)",
                min_value=20.0,
                max_value=45.0,
                step=0.1,
                key="body_temperature",
            )

        submit = st.form_submit_button("Run Triage", type="primary")

    st.button("Load Sample Patient", on_click=load_sample)

with right:
    if submit:
        patient_payload = build_patient_payload()

        if not patient_payload["symptoms"]:
            st.error("Symptoms are required.")
        else:
            with st.spinner("Running agent triage..."):
                try:
                    render_result(run_agent(patient_payload))
                except Exception as exc:
                    st.error(f"Triage failed: {exc}")
    else:
        st.info("Enter patient symptoms and vitals, then run triage.")
