import google.generativeai as genai

genai.configure(api_key="AIzaSyCw3Lg6D56HwX01DPbweN0QcjtrdWFJtvw")
model = genai.GenerativeModel("gemini-2.5-flash")

def analyze_road_conditions(potholes):
    if len(potholes) == 0:
        return {
            "summary": "No potholes detected yet.",
            "severity_assessment": "N/A",
            "likely_cause": "N/A",
            "recommendation": "Continue monitoring.",
            "priority": "LOW",
            "estimated_repair_cost": "N/A"
        }

    high = len([p for p in potholes if p['severity'] == 'HIGH'])
    medium = len([p for p in potholes if p['severity'] == 'MEDIUM'])
    low = len([p for p in potholes if p['severity'] == 'LOW'])
    avg_impact = sum(p['impact'] for p in potholes) / len(potholes)
    max_impact = max(p['impact'] for p in potholes)

    prompt = f"""
    You are a senior city road infrastructure engineer analyzing pothole sensor data.

    POTHOLE DETECTION REPORT:
    - Total potholes detected: {len(potholes)}
    - High severity: {high}
    - Medium severity: {medium}
    - Low severity: {low}
    - Average impact force: {avg_impact:.2f} m/s²
    - Maximum impact force: {max_impact:.2f} m/s²
    - Latest detection: {potholes[-1]['timestamp']}

    Reply in EXACT format, nothing else:
    SUMMARY: [2 sentence overview]
    SEVERITY_ASSESSMENT: [one sentence]
    LIKELY_CAUSE: [most likely cause]
    RECOMMENDATION: [specific repair recommendation]
    PRIORITY: [IMMEDIATE/HIGH/MEDIUM/LOW]
    ESTIMATED_REPAIR_COST: [rough cost estimate]
    """

    response = model.generate_content(prompt)
    return parse_response(response.text)

def parse_response(text):
    lines = text.strip().split('\n')
    result = {
        "summary": "",
        "severity_assessment": "",
        "likely_cause": "",
        "recommendation": "",
        "priority": "LOW",
        "estimated_repair_cost": ""
    }
    for line in lines:
        if line.startswith("SUMMARY:"):
            result["summary"] = line.replace("SUMMARY:", "").strip()
        elif line.startswith("SEVERITY_ASSESSMENT:"):
            result["severity_assessment"] = line.replace("SEVERITY_ASSESSMENT:", "").strip()
        elif line.startswith("LIKELY_CAUSE:"):
            result["likely_cause"] = line.replace("LIKELY_CAUSE:", "").strip()
        elif line.startswith("RECOMMENDATION:"):
            result["recommendation"] = line.replace("RECOMMENDATION:", "").strip()
        elif line.startswith("PRIORITY:"):
            result["priority"] = line.replace("PRIORITY:", "").strip()
        elif line.startswith("ESTIMATED_REPAIR_COST:"):
            result["estimated_repair_cost"] = line.replace("ESTIMATED_REPAIR_COST:", "").strip()
    return result