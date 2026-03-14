import cv2
import mediapipe as mp
import numpy as np
from ai_analysis import analyze_injury_risk
import time
import threading

mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils
pose = mp_pose.Pose(min_detection_confidence=0.7, min_tracking_confidence=0.7)

def calculate_angle(a, b, c):
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)
    radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
    angle = np.abs(radians * 180.0 / np.pi)
    if angle > 180.0:
        angle = 360 - angle
    return round(angle, 1)

def is_visible(landmark, threshold=0.6):
    return landmark.visibility > threshold

# Shared state
analysis_result = {"risk": "WAITING", "reason": "Stand in frame...", "action": ""}
is_analyzing = False
last_analysis_time = 0
minutes_played = 87

def run_analysis(left_knee, right_knee):
    global analysis_result, is_analyzing
    is_analyzing = True
    try:
        result = analyze_injury_risk(left_knee, right_knee, minutes_played)
        analysis_result = result
    except Exception as e:
        print(f"Analysis error: {e}")
    is_analyzing = False

cap = cv2.VideoCapture(0)
print("InjuryIQ running! Press Q to quit.")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = pose.process(rgb_frame)

    if results.pose_landmarks:
        mp_drawing.draw_landmarks(frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

        lm = results.pose_landmarks.landmark
        h, w = frame.shape[:2]

        legs_visible = (
            is_visible(lm[mp_pose.PoseLandmark.LEFT_KNEE]) and
            is_visible(lm[mp_pose.PoseLandmark.RIGHT_KNEE]) and
            is_visible(lm[mp_pose.PoseLandmark.LEFT_ANKLE]) and
            is_visible(lm[mp_pose.PoseLandmark.RIGHT_ANKLE])
        )

        if legs_visible:
            def get_point(landmark):
                return [lm[landmark].x * w, lm[landmark].y * h]

            left_hip    = get_point(mp_pose.PoseLandmark.LEFT_HIP)
            left_knee_p = get_point(mp_pose.PoseLandmark.LEFT_KNEE)
            left_ankle  = get_point(mp_pose.PoseLandmark.LEFT_ANKLE)
            right_hip   = get_point(mp_pose.PoseLandmark.RIGHT_HIP)
            right_knee_p = get_point(mp_pose.PoseLandmark.RIGHT_KNEE)
            right_ankle = get_point(mp_pose.PoseLandmark.RIGHT_ANKLE)

            left_knee_angle  = calculate_angle(left_hip, left_knee_p, left_ankle)
            right_knee_angle = calculate_angle(right_hip, right_knee_p, right_ankle)

            # Trigger AI in background every 10 seconds
            current_time = time.time()
            if current_time - last_analysis_time > 10 and not is_analyzing:
                last_analysis_time = current_time
                thread = threading.Thread(
                    target=run_analysis,
                    args=(left_knee_angle, right_knee_angle)
                )
                thread.daemon = True
                thread.start()

            # Pick color based on risk
            risk = analysis_result["risk"].upper()
            if "HIGH" in risk:
                color = (0, 0, 255)
            elif "MEDIUM" in risk:
                color = (0, 165, 255)
            else:
                color = (0, 255, 0)

            # Show analyzing indicator
            status = "🔄 Analyzing..." if is_analyzing else f"RISK: {risk}"

            cv2.putText(frame, f"L Knee: {left_knee_angle}", (10, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,255), 2)
            cv2.putText(frame, f"R Knee: {right_knee_angle}", (10, 80),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,255), 2)
            cv2.putText(frame, status, (10, 130),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, color, 3)
            cv2.putText(frame, analysis_result["reason"][:60], (10, 170),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1)
            cv2.putText(frame, analysis_result["action"][:60], (10, 200),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        else:
            cv2.putText(frame, "Step back so full body is visible", (10, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,255), 2)

    cv2.imshow("InjuryIQ - Live Analysis", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()