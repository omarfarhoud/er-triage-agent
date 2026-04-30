from src.agent.core_agent import run_agent
test_cases = [

    {
        "name": "Stroke Emergency",
        "symptoms": "slurred speech and weakness on one side",
        "vitals": {"heart_rate": 85, "systolic_bp": 130, "diastolic_bp": 85, "oxygen_saturation": 97, "body_temperature": 37},
        "expected": "high"
    },
    {
        "name": "Cardiac Emergency",
        "symptoms": "severe chest pain and shortness of breath",
        "vitals": {"heart_rate": 130, "systolic_bp": 85, "diastolic_bp": 55, "oxygen_saturation": 88, "body_temperature": 38},
        "expected": "high"
    },
    {
        "name": "Severe Infection",
        "symptoms": "high fever and difficulty breathing",
        "vitals": {"heart_rate": 110, "systolic_bp": 95, "diastolic_bp": 65, "oxygen_saturation": 92, "body_temperature": 39.2},
        "expected": "high"
    },
    {
        "name": "Severe Trauma",
        "symptoms": "heavy bleeding and unconsciousness after accident",
        "vitals": {"heart_rate": 120, "systolic_bp": 80, "diastolic_bp": 50, "oxygen_saturation": 94, "body_temperature": 36.5},
        "expected": "high"
    },

    {
        "name": "Moderate Infection",
        "symptoms": "fever and fatigue",
        "vitals": {"heart_rate": 100, "systolic_bp": 115, "diastolic_bp": 75, "oxygen_saturation": 95, "body_temperature": 38.3},
        "expected": "moderate"
    },
    {
        "name": "Respiratory Issue",
        "symptoms": "cough and mild breathing difficulty",
        "vitals": {"heart_rate": 95, "systolic_bp": 110, "diastolic_bp": 70, "oxygen_saturation": 93, "body_temperature": 37.5},
        "expected": "moderate"
    },
    {
        "name": "Abdominal Pain",
        "symptoms": "moderate abdominal pain and nausea",
        "vitals": {"heart_rate": 90, "systolic_bp": 118, "diastolic_bp": 78, "oxygen_saturation": 96, "body_temperature": 37.2},
        "expected": "moderate"
    },
    {
        "name": "Headache Case",
        "symptoms": "persistent headache and dizziness",
        "vitals": {"heart_rate": 88, "systolic_bp": 118, "diastolic_bp": 76, "oxygen_saturation": 97, "body_temperature": 37.3},
        "expected": "moderate"
    },

    {
        "name": "Mild Case",
        "symptoms": "mild headache",
        "vitals": {"heart_rate": 75, "systolic_bp": 120, "diastolic_bp": 80, "oxygen_saturation": 98, "body_temperature": 36.8},
        "expected": "low"
    },
    {
        "name": "Very Mild Case",
        "symptoms": "feeling tired",
        "vitals": {"heart_rate": 70, "systolic_bp": 118, "diastolic_bp": 78, "oxygen_saturation": 99, "body_temperature": 36.7},
        "expected": "low"
    },

    {
        "name": "Hidden High Risk",
        "symptoms": "confusion and altered consciousness",
        "vitals": {"heart_rate": 88, "systolic_bp": 125, "diastolic_bp": 80, "oxygen_saturation": 97, "body_temperature": 37},
        "expected": "high"
    },
    {
        "name": "Borderline Case",
        "symptoms": "fatigue and slight fever",
        "vitals": {"heart_rate": 92, "systolic_bp": 118, "diastolic_bp": 76, "oxygen_saturation": 96, "body_temperature": 37.8},
        "expected": "moderate"
    }
]
def evaluate(test_cases, mode="full"):
    correct = 0

    for case in test_cases:

        if mode == "full":
            patient_input = {
                "symptoms": case["symptoms"],
                "vitals": case["vitals"]
            }

        elif mode == "no_symptoms":
            patient_input = {
                "symptoms": "no significant symptoms",
                "vitals": case["vitals"]
            }

        elif mode == "no_vitals":
            patient_input = {
                "symptoms": case["symptoms"],
                "vitals": {
                    "heart_rate": 75,
                    "systolic_bp": 120,
                    "diastolic_bp": 80,
                    "oxygen_saturation": 98,
                    "body_temperature": 36.8
                }
            }

        result = run_agent(patient_input)
        predicted = result["priority"].lower()

        if predicted == case["expected"]:
            correct += 1

        print(f"{case['name']} ({mode}): {predicted}")

    return correct / len(test_cases)


print("\n===== FULL AGENT ABLATION =====\n")

full_acc = evaluate(test_cases, "full")
no_symptoms_acc = evaluate(test_cases, "no_symptoms")
no_vitals_acc = evaluate(test_cases, "no_vitals")

print("\nRESULTS:")
print(f"Full System: {full_acc * 100:.2f}%")
print(f"No Symptoms: {no_symptoms_acc * 100:.2f}%")
print(f"No Vitals: {no_vitals_acc * 100:.2f}%")