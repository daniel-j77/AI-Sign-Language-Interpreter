import cv2
import numpy as np
import tensorflow as tf
import time
import pyttsx3
import threading
import json
import mediapipe as mp
import h5py

sentence=""
char_buffer=[]
BUFFER_SIZE=6

current_word=""

last_update_time=time.time()

PREDICTION_COOLDOWN=0.3
last_prediction_time=0

LETTER_COOLDOWN=4
last_letter_time=0

CNN_SMOOTHING=7
cnn_pred_buffer=[]

MODE="AUTO"

paused=False


def speak_async(text):
    def run():
        engine=pyttsx3.init()
        engine.say(text)
        engine.runAndWait()
        engine.stop()
    threading.Thread(target=run,daemon=True).start()


def clean_text(raw):

    result=[]
    i=0

    while i < len(raw):

        if raw[i:].startswith("space"):
            result.append(" ")
            i+=5
            continue

        if raw[i:].startswith("del"):
            if result:
                result.pop()
            i+=3
            continue

        if raw[i:].startswith("nothing"):
            i+=7
            continue

        result.append(raw[i])
        i+=1

    return "".join(result)


mp_hands=mp.solutions.hands
hands=mp_hands.Hands(
static_image_mode=False,
max_num_hands=1,
min_detection_confidence=0.7,
min_tracking_confidence=0.7
)

mp_draw=mp.solutions.drawing_utils


def extract_landmarks(hand_landmarks):
    landmarks=[]
    for lm in hand_landmarks.landmark:
        landmarks.extend([lm.x,lm.y,lm.z])
    return np.array(landmarks)


def load_legacy_cnn(path):

    from tensorflow.keras.models import model_from_config
    from tensorflow.keras.mixed_precision import Policy

    custom_objects={"DTypePolicy":Policy}

    with h5py.File(path,"r") as f:
        model_config=f.attrs["model_config"]

        if isinstance(model_config,bytes):
            model_config=model_config.decode("utf-8")

        model_config=json.loads(model_config)

    for layer in model_config["config"]["layers"]:
        if layer["class_name"]=="InputLayer":

            cfg=layer["config"]

            if "batch_shape" in cfg:
                shape=cfg.pop("batch_shape")
                cfg["input_shape"]=shape[1:]

    model=model_from_config(model_config,custom_objects=custom_objects)
    model.load_weights(path)

    return model


cnn_model=load_legacy_cnn("model.h5")
mlp_model=tf.keras.models.load_model("landmark_model.h5")


with open("class_labels.json","r") as f:
    cnn_labels=json.load(f)

cnn_labels=[cnn_labels[str(i)] for i in range(len(cnn_labels))]


with open("class_labels_mlp.json","r") as f:
    mlp_labels=json.load(f)

mlp_labels=[mlp_labels[str(i)] for i in range(len(mlp_labels))]


cap=cv2.VideoCapture(0)

frame_count=0
prediction_interval=3

# 🔥 ULTRA STRICT
CONFIDENCE_THRESHOLD=0.92
TOP2_MARGIN=0.15

MLP_CONF_THRESHOLD=0.85

print("📷 Webcam started")
print("M = switch model | C = clear | P = pause/resume | Q = quit")

cv2.namedWindow("Sign → Text / Voice",cv2.WINDOW_NORMAL)


while True:

    ret,frame=cap.read()
    if not ret:
        break

    frame=cv2.flip(frame,1)

    frame_count+=1
    current_time=time.time()

    predicted_char=None
    best_conf=0
    used_model=MODE

    rgb=cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
    result=hands.process(rgb)

    hand_detected=False

    # SHOW LANDMARKS ONLY FOR MLP / AUTO
    if result.multi_hand_landmarks and MODE in ["AUTO","MLP"]:
        hand_detected=True

        for hand_landmarks in result.multi_hand_landmarks:
            mp_draw.draw_landmarks(
                frame,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS)


    # ROI BOX
    if MODE in ["AUTO","CNN"] or paused:

        h,w,_=frame.shape

    #  FIXED SIZE tuned to your dataset
        box_size = int(min(w, h) * 0.5)   # increased from 0.35 → 0.5

        cx = w // 2
        cy = int(h * 0.55)   # slightly lower (to include wrist like dataset)

        x1 = max(cx - box_size // 2, 0)
        y1 = max(cy - box_size // 2, 0)

        x2 = min(cx + box_size // 2, w)
        y2 = min(cy + box_size // 2, h)

        cv2.rectangle(frame,(x1,y1),(x2,y2),(0,255,0),3)

    if not paused:

        # -------- MLP --------
        if MODE in ["AUTO","MLP"] and result.multi_hand_landmarks:

            for hand_landmarks in result.multi_hand_landmarks:

                landmarks=extract_landmarks(hand_landmarks).reshape(1,-1)

                mlp_pred=mlp_model.predict(landmarks,verbose=0)[0]

                mlp_conf=np.max(mlp_pred)

                if mlp_conf>MLP_CONF_THRESHOLD and mlp_conf>best_conf:

                    predicted_char=mlp_labels[np.argmax(mlp_pred)]
                    best_conf=mlp_conf
                    used_model="MLP"


        # -------- CNN (ULTRA STRICT) --------
        if MODE in ["AUTO","CNN"]:

            if frame_count%prediction_interval==0:

                roi=frame[y1:y2,x1:x2]

                roi=cv2.cvtColor(roi,cv2.COLOR_BGR2RGB)
                roi=cv2.resize(roi,(64,64))
                roi=roi.astype("float32")/255.0
                roi=np.expand_dims(roi,axis=0)

                cnn_pred=cnn_model.predict(roi,verbose=0)[0]

                cnn_pred_buffer.append(cnn_pred)

                if len(cnn_pred_buffer)>CNN_SMOOTHING:
                    cnn_pred_buffer.pop(0)

                avg_pred=np.mean(cnn_pred_buffer,axis=0)

                # 🔥 TOP-2 CHECK
                sorted_pred=np.sort(avg_pred)
                top1=sorted_pred[-1]
                top2=sorted_pred[-2]

                margin=top1-top2

                cnn_conf=top1
                candidate=cnn_labels[np.argmax(avg_pred)]

                # 🔥 ULTRA STRICT CONDITIONS
                if (
                    cnn_conf > CONFIDENCE_THRESHOLD and
                    margin > TOP2_MARGIN and
                    cnn_conf > best_conf
                ):
                    predicted_char=candidate
                    best_conf=cnn_conf
                    used_model="CNN"


        # -------- STABILITY --------
        if predicted_char:

            if current_time-last_prediction_time>PREDICTION_COOLDOWN:

                char_buffer.append(predicted_char)
                last_prediction_time=current_time

            if len(char_buffer)>=BUFFER_SIZE:

                stable_char=max(set(char_buffer),key=char_buffer.count)

                if stable_char.isalpha():

                    if current_time-last_letter_time>LETTER_COOLDOWN:

                        current_word+=stable_char
                        speak_async(current_word)
                        last_letter_time=current_time

                else:

                    if stable_char=="space":
                        current_word+="space"

                    elif stable_char=="del":
                        current_word+="del"

                char_buffer.clear()


    raw_text=sentence+current_word
    processed=clean_text(raw_text)

    display="Predicted Text: "+processed

    words=display.split(" ")

    lines=[]
    line=""

    for word in words:

        if len(line+word) < 35:
            line+=word+" "
        else:
            lines.append(line)
            line=word+" "

    lines.append(line)

    y=40

    for line in lines[-4:]:

        cv2.putText(frame,line,(20,y),
                    cv2.FONT_HERSHEY_SIMPLEX,1,(0,255,0),2)

        y+=40


    cv2.putText(frame,f"Model: {used_model}",(20,200),
                cv2.FONT_HERSHEY_SIMPLEX,0.8,(255,255,0),2)

    if paused:
        cv2.putText(frame,"PAUSED",(20,240),
                    cv2.FONT_HERSHEY_SIMPLEX,1,(0,0,255),2)

    cv2.imshow("Sign → Text / Voice",frame)

    key=cv2.waitKey(1)&0xFF

    if key==ord("m"):
        MODE={"AUTO":"MLP","MLP":"CNN","CNN":"AUTO"}[MODE]
        print("🔁 Mode:",MODE)

    if key==ord("c"):
        sentence=""
        current_word=""
        char_buffer.clear()
        print("🧹 Cleared")

    if key==ord("p"):
        paused=not paused
        print("⏸ Paused" if paused else "▶ Resumed")

    if key==ord("q"):
        break


cap.release()
cv2.destroyAllWindows()
print("📷 Webcam closed")