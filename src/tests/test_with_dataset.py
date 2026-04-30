from src.agent.core_agent import run_agent

test_cases = [

    {
        "name": "Stroke Emergency",
        "input": {
            "symptoms": "Patient has slurred speech and weakness on one side",
            "vitals": {
                "heart_rate": 85,
                "systolic_bp": 130,
                "diastolic_bp": 85,
                "oxygen_saturation": 97,
                "body_temperature": 37
            }
        },
        "expected": "High"
    },

    {
        "name": "Cardiac Emergency",
        "input": {
            "symptoms": "Severe chest pain and shortness of breath",
            "vitals": {
                "heart_rate": 130,
                "systolic_bp": 85,
                "diastolic_bp": 55,
                "oxygen_saturation": 88,
                "body_temperature": 38
            }
        },
        "expected": "High"
    },

    {
        "name": "Severe Infection",
        "input": {
            "symptoms": "High fever with cough and difficulty breathing",
            "vitals": {
                "heart_rate": 110,
                "systolic_bp": 95,
                "diastolic_bp": 65,
                "oxygen_saturation": 92,
                "body_temperature": 39.2
            }
        },
        "expected": "High"
    },

    {
        "name": "Moderate Respiratory Case",
        "input": {
            "symptoms": "Cough and mild shortness of breath",
            "vitals": {
                "heart_rate": 95,
                "systolic_bp": 110,
                "diastolic_bp": 70,
                "oxygen_saturation": 93,
                "body_temperature": 37.5
            }
        },
        "expected": "Moderate"
    },

    {
        "name": "Moderate Infection",
        "input": {
            "symptoms": "Fever and fatigue",
            "vitals": {
                "heart_rate": 100,
                "systolic_bp": 115,
                "diastolic_bp": 75,
                "oxygen_saturation": 95,
                "body_temperature": 38.3
            }
        },
        "expected": "Moderate"
    },

    {
        "name": "Trauma Case",
        "input": {
            "symptoms": "Patient fell and has severe pain and bleeding",
            "vitals": {
                "heart_rate": 115,
                "systolic_bp": 90,
                "diastolic_bp": 60,
                "oxygen_saturation": 96,
                "body_temperature": 37
            }
        },
        "expected": "High"
    },

    {
        "name": "Mild Case",
        "input": {
            "symptoms": "Mild headache and fatigue",
            "vitals": {
                "heart_rate": 75,
                "systolic_bp": 120,
                "diastolic_bp": 80,
                "oxygen_saturation": 98,
                "body_temperature": 36.8
            }
        },
        "expected": "Low"
    },

    {
        "name": "Very Mild Case",
        "input": {
            "symptoms": "Patient feels tired",
            "vitals": {
                "heart_rate": 70,
                "systolic_bp": 118,
                "diastolic_bp": 78,
                "oxygen_saturation": 99,
                "body_temperature": 36.7
            }
        },
        "expected": "Low"
    },

    {
        "name": "Mixed Moderate Case",
        "input": {
            "symptoms": "Nausea, cough, and fever",
            "vitals": {
                "heart_rate": 102,
                "systolic_bp": 110,
                "diastolic_bp": 75,
                "oxygen_saturation": 94,
                "body_temperature": 38.5
            }
        },
        "expected": "Moderate"
    },

    {
        "name": "Hidden High Risk",
        "input": {
            "symptoms": "Patient has confusion and altered consciousness",
            "vitals": {
                "heart_rate": 88,
                "systolic_bp": 125,
                "diastolic_bp": 80,
                "oxygen_saturation": 97,
                "body_temperature": 37
            }
        },
        "expected": "High"
    }
]
correct = 0

print("\n===== SYNTHETIC TEST =====\n")

for case in test_cases:
    result = run_agent(case["input"])
    predicted = result["priority"]

    is_correct = predicted.lower() == case["expected"].lower()

    if is_correct:
        correct += 1

    print(f"{case['name']}: Expected={case['expected']} | Predicted={predicted} | {'✅' if is_correct else '❌'}")

accuracy = correct / len(test_cases)
print(f"\nAccuracy: {accuracy * 100:.2f}%")