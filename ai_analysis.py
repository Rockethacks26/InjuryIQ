import os
import google.generativeai as genai
from data_loader import get_injury_context

# Load .env (GEMENI_API_KEY - note spelling used in .env)
api_key = os.getenv("GEMENI_API_KEY")
if not api_key:
    try:
        from dotenv import load_dotenv
        load_dotenv()
        api_key = os.getenv("GEMENI_API_KEY")
    except ImportError:
        env_path = os.path.join(os.path.dirname(__file__), ".env")
        if os.path.exists(env_path):
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("GEMENI_API_KEY="):
                        api_key = line.split("=", 1)[1].strip().strip('"').strip("'")
                        break
api_key = api_key or ""
genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-2.5-flash")

def analyze_injury_risk(left_knee, right_knee, left_hip_y=None, right_hip_y=None,
                         trunk_lean=None, minutes_played=90, position="Center Forward", age=25):

    knee_diff = abs(left_knee - right_knee)
    hip_drop = abs(left_hip_y - right_hip_y) if left_hip_y and right_hip_y else 0

    # Only skip AI when knees are nearly identical (avoid skipping on real asymmetry)
    if knee_diff < 1 and hip_drop < 2:
        return {
            "risk": "LOW",
            "injury_type": "None detected",
            "reason": "Movement looks symmetric and normal.",
            "action": "Player can continue.",
            "confidence": "90%"
        }

    # Get real Premier League injury context
    real_data_context = get_injury_context(position=position, age=age)

    prompt = f"""
    You are an elite sports physiotherapist analyzing a live soccer player's movement.
    
    REAL PREMIER LEAGUE INJURY DATA FOR CONTEXT:
    {real_data_context}
    
    CURRENT PLAYER DATA (live camera analysis):
    - Position: {position}
    - Age: {age}
    - Left knee angle: {left_knee}°
    - Right knee angle: {right_knee}°
    - Knee asymmetry: {knee_diff}° (normal <10°, concerning >15°, serious >25°)
    - Hip drop: {hip_drop} pixels (concerning if >20)
    - Trunk lean: {trunk_lean}° (concerning if >8°)
    - Minutes played: {minutes_played}
    
    IMPORTANT:
    - A bent knee alone is NOT injury risk
    - Only flag risk based on ASYMMETRY and compensation patterns
    - Use the real Premier League data above to identify likely injury type
    - Be conservative — only flag MEDIUM/HIGH if clearly warranted
    
    Reply in EXACT format:
    RISK: [LOW/MEDIUM/HIGH]
    INJURY_TYPE: [specific risk based on real data e.g. "Hamstring strain - left side"]
    REASON: [one sentence referencing the asymmetry pattern]
    ACTION: [one specific coaching action]
    CONFIDENCE: [percentage]
    """

    response = model.generate_content(prompt)
    return parse_response(response.text)

def parse_response(text):
    lines = text.strip().split('\n')
    result = {
        "risk": "LOW",
        "injury_type": "None detected",
        "reason": "",
        "action": "",
        "confidence": "0%"
    }
    for line in lines:
        if line.startswith("RISK:"):
            result["risk"] = line.replace("RISK:", "").strip()
        elif line.startswith("INJURY_TYPE:"):
            result["injury_type"] = line.replace("INJURY_TYPE:", "").strip()
        elif line.startswith("REASON:"):
            result["reason"] = line.replace("REASON:", "").strip()
        elif line.startswith("ACTION:"):
            result["action"] = line.replace("ACTION:", "").strip()
        elif line.startswith("CONFIDENCE:"):
            result["confidence"] = line.replace("CONFIDENCE:", "").strip()
    return result