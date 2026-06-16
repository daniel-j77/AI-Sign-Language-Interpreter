import numpy as np
import os
import tensorflow as tf
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

DATA_DIR = "landmark_dataset"

X = []
y = []

for file in os.listdir(DATA_DIR):
    if file.endswith(".csv"):
        label = file.replace(".csv", "")
        path = os.path.join(DATA_DIR, file)
        data = np.loadtxt(path, delimiter=",")
        X.append(data)
        y += [label] * len(data)

X = np.vstack(X)
y = np.array(y)

encoder = LabelEncoder()
y = encoder.fit_transform(y)
y = tf.keras.utils.to_categorical(y)

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

model = tf.keras.Sequential([
    tf.keras.layers.Dense(128, activation="relu", input_shape=(63,)),
    tf.keras.layers.Dense(64, activation="relu"),
    tf.keras.layers.Dense(y.shape[1], activation="softmax")
])

model.compile(
    optimizer="adam",
    loss="categorical_crossentropy",
    metrics=["accuracy"]
)

model.fit(X_train, y_train, epochs=30, validation_data=(X_test, y_test))

model.save("landmark_model.h5")
print("✅ Landmark MLP model trained & saved")
import json
# 🔤 Save MLP class labels
class_labels_mlp = {
    str(i): label for i, label in enumerate(encoder.classes_)
}

with open("class_labels_mlp.json", "w") as f:
    json.dump(class_labels_mlp, f, indent=2)

print("✅ class_labels_mlp.json saved")