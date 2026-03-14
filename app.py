import cv2
import mediapipe as mp
import numpy as np

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

def get_risk_level(left_knee, right_knee):
    diff = abs(left_knee - right_knee)
    if diff > 20:
        return "HIGH RISK", (0, 0, 255)
    elif diff > 10:
        return "MEDIUM RISK", (0, 165, 255)
    else:
        return "LOW RISK", (0, 255, 0)

def is_visible(landmark, threshold=0.6):
    """Check if a landmark is actually visible on screen"""
    return landmark.visibility > threshold

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

        # Check if legs are actually visible
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
            left_knee   = get_point(mp_pose.PoseLandmark.LEFT_KNEE)
            left_ankle  = get_point(mp_pose.PoseLandmark.LEFT_ANKLE)
            right_hip   = get_point(mp_pose.PoseLandmark.RIGHT_HIP)
            right_knee  = get_point(mp_pose.PoseLandmark.RIGHT_KNEE)
            right_ankle = get_point(mp_pose.PoseLandmark.RIGHT_ANKLE)

            left_knee_angle  = calculate_angle(left_hip, left_knee, left_ankle)
            right_knee_angle = calculate_angle(right_hip, right_knee, right_ankle)
            risk, color = get_risk_level(left_knee_angle, right_knee_angle)

            cv2.putText(frame, f"L Knee: {left_knee_angle}°", (10, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            cv2.putText(frame, f"R Knee: {right_knee_angle}°", (10, 80),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            cv2.putText(frame, risk, (10, 130),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.2, color, 3)
        else:
            # Show message when legs aren't visible
            cv2.putText(frame, "Step back so full body is visible", (10, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

    cv2.imshow("InjuryIQ - Pose Detection", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()