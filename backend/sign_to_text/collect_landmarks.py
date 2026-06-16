import cv2
import mediapipe as mp
import numpy as np
import os

# ===============================
# CONFIG
# ===============================
LABEL = "A"          # CHANGE LABEL HERE
TARGET_SAMPLES = 500
SAVE_DIR = "landmark_dataset"
DIFF_THRESHOLD = 0.015

os.makedirs(SAVE_DIR, exist_ok=True)
save_path = os.path.join(SAVE_DIR, f"{LABEL}.csv")

# ===============================
# MEDIAPIPE
# ===============================
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)
mp_draw = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)

print(f"📸 Collecting landmarks for '{LABEL}'")
print(f"🎯 Target samples: {TARGET_SAMPLES}")
print("🅿️ Press P = Pause / Resume")
print("⬅️ Press D = Delete last sample")
print("❌ Press Q = Quit")

sample_count = 0
last_saved = None
paused = True

saved_samples = []

# Load existing samples if file already exists
if os.path.exists(save_path):
    with open(save_path, "r") as f:
        for line in f:
            row = np.array(list(map(float, line.strip().split(","))))
            saved_samples.append(row)

    sample_count = len(saved_samples)

    if saved_samples:
        last_saved = saved_samples[-1]

# Rewrite existing samples
with open(save_path, "w") as f:
    for row in saved_samples:
        f.write(",".join(map(str, row)) + "\n")

while sample_count < TARGET_SAMPLES:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb)

    if result.multi_hand_landmarks:
        for hand_landmarks in result.multi_hand_landmarks:
            mp_draw.draw_landmarks(
                frame,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS
            )

            if not paused:
                landmarks = []

                for lm in hand_landmarks.landmark:
                    landmarks.extend([lm.x, lm.y, lm.z])

                landmarks = np.array(landmarks)

                save_flag = False

                if last_saved is None:
                    save_flag = True
                else:
                    diff = np.mean(np.abs(landmarks - last_saved))
                    if diff > DIFF_THRESHOLD:
                        save_flag = True

                if save_flag:
                    saved_samples.append(landmarks)
                    last_saved = landmarks
                    sample_count += 1

                    with open(save_path, "a") as f:
                        f.write(",".join(map(str, landmarks)) + "\n")

                    print(f"✅ Saved {sample_count}/{TARGET_SAMPLES}")

    status = "PAUSED ⏸️" if paused else "SAVING ▶️"

    cv2.putText(
        frame,
        f"Label: {LABEL} | {sample_count}/{TARGET_SAMPLES} | {status}",
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 255, 0),
        2
    )

    cv2.imshow("Collect Landmarks", frame)

    key = cv2.waitKey(1) & 0xFF

    if key == ord("p"):
        paused = not paused
        print("⏸️ Paused" if paused else "▶️ Resumed saving")

    if key == ord("d") and saved_samples:
        saved_samples.pop()
        sample_count -= 1
        last_saved = saved_samples[-1] if saved_samples else None

        with open(save_path, "w") as f:
            for row in saved_samples:
                f.write(",".join(map(str, row)) + "\n")

        print(f"⬅️ Deleted last sample → {sample_count}/{TARGET_SAMPLES}")

    if key == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()

print(f"🎉 Done! Collected {sample_count} samples for '{LABEL}'")