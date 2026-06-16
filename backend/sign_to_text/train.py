import tensorflow as tf
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
import json

# --------------------
# CONFIG
# --------------------
IMG_SIZE = 64
BATCH_SIZE = 32
EPOCHS = 30
DATASET_PATH = "../../dataset/ASL"

# --------------------
# DATA AUGMENTATION (STRICT + SIZE FLEXIBILITY)
# --------------------
data_gen = ImageDataGenerator(
    rescale=1.0 / 255,
    validation_split=0.2,

    # 🔥 Balanced (still dataset-like but handles size)
    rotation_range=5,
    zoom_range=0.15,   # 🔥 increased for hand size variation

    width_shift_range=0.02,
    height_shift_range=0.02,

    brightness_range=[0.9, 1.1],

    fill_mode="nearest",   # 🔥 prevents edge artifacts

    horizontal_flip=False
)

train_data = data_gen.flow_from_directory(
    DATASET_PATH,
    target_size=(IMG_SIZE, IMG_SIZE),
    batch_size=BATCH_SIZE,
    subset="training",
    class_mode="categorical",
    shuffle=True
)

val_data = data_gen.flow_from_directory(
    DATASET_PATH,
    target_size=(IMG_SIZE, IMG_SIZE),
    batch_size=BATCH_SIZE,
    subset="validation",
    class_mode="categorical",
    shuffle=False
)

# --------------------
# MODEL (UNCHANGED STRUCTURE)
# --------------------
model = tf.keras.Sequential([

    tf.keras.layers.Input(shape=(IMG_SIZE, IMG_SIZE, 3)),

    tf.keras.layers.Conv2D(32,(3,3),padding="same",activation="relu"),
    tf.keras.layers.BatchNormalization(),
    tf.keras.layers.MaxPooling2D(),

    tf.keras.layers.Conv2D(64,(3,3),padding="same",activation="relu"),
    tf.keras.layers.BatchNormalization(),
    tf.keras.layers.MaxPooling2D(),

    tf.keras.layers.Conv2D(128,(3,3),padding="same",activation="relu"),
    tf.keras.layers.BatchNormalization(),
    tf.keras.layers.MaxPooling2D(),

    tf.keras.layers.Conv2D(256,(3,3),padding="same",activation="relu"),
    tf.keras.layers.BatchNormalization(),
    tf.keras.layers.MaxPooling2D(),

    tf.keras.layers.Flatten(),

    tf.keras.layers.Dense(256,activation="relu"),
    tf.keras.layers.BatchNormalization(),
    tf.keras.layers.Dropout(0.5),

    tf.keras.layers.Dense(128,activation="relu"),
    tf.keras.layers.BatchNormalization(),

    tf.keras.layers.Dense(train_data.num_classes,activation="softmax")
])

model.compile(
    optimizer=tf.keras.optimizers.Adam(learning_rate=0.0005),
    loss="categorical_crossentropy",
    metrics=["accuracy"]
)

# --------------------
# CALLBACKS
# --------------------
early_stop = EarlyStopping(
    monitor="val_loss",
    patience=5,
    restore_best_weights=True
)

checkpoint = ModelCheckpoint(
    "model.h5",
    monitor="val_accuracy",
    save_best_only=True,
    verbose=1
)

# --------------------
# TRAIN
# --------------------
model.fit(
    train_data,
    validation_data=val_data,
    epochs=EPOCHS,
    callbacks=[early_stop, checkpoint]
)

# --------------------
# SAVE CLASS ORDER
# --------------------
class_labels = {v: k for k, v in train_data.class_indices.items()}

with open("class_labels.json","w") as f:
    json.dump(class_labels,f)

print("✅ Model trained")
print("✅ class_labels.json saved")