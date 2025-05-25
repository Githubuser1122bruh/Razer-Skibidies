import os
import numpy as np
import librosa
import tensorflow as tf
from sklearn.model_selection import train_test_split
from sklearn.utils.class_weight import compute_class_weight
from sklearn.preprocessing import StandardScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout, Bidirectional
from tensorflow.keras.callbacks import EarlyStopping


DATA_DIR = "dataset"
SAMPLE_RATE = 22050
DURATION = 3
N_MFCC = 13
AUGMENT = True
MODEL_PATH = "brainrot_lstm_model.h5"

def extract_features(file_path):
    y, sr = librosa.load(file_path, sr=SAMPLE_RATE, duration=DURATION)
    if len(y) < sr * DURATION:
        y = np.pad(y, (0, sr * DURATION - len(y)))

    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=N_MFCC)
    delta = librosa.feature.delta(mfcc)
    delta2 = librosa.feature.delta(mfcc, order=2)
    combined = np.vstack([mfcc, delta, delta2])
    return combined.T 
    
def augment_audio(y):
    noise = y + 0.005 * np.random.randn(len(y))
    stretch = librosa.effects.time_stretch(y, rate=np.random.uniform(0.8, 1.2))
    pitch = librosa.effects.pitch_shift(y, sr=SAMPLE_RATE, n_steps=np.random.randint(-2, 2))
    return [noise[:len(y)], stretch[:len(y)], pitch[:len(y)]]


features, labels = [], []

for label_dir, label_value in [("brainrot", 1), ("no_brainrot", 0)]:
    full_dir = os.path.join(DATA_DIR, label_dir)
    for filename in os.listdir(full_dir):
        if filename.endswith(".wav"):
            path = os.path.join(full_dir, filename)
            try:
                y, _ = librosa.load(path, sr=SAMPLE_RATE, duration=DURATION)
                feats = extract_features(path)
                features.append(feats)
                labels.append(label_value)

                if AUGMENT and label_value == 1:
                    for aug_y in augment_audio(y):
                        mfcc = librosa.feature.mfcc(y=aug_y, sr=SAMPLE_RATE, n_mfcc=N_MFCC)
                        delta = librosa.feature.delta(mfcc)
                        delta2 = librosa.feature.delta(mfcc, order=2)
                        combined = np.vstack([mfcc, delta, delta2])
                        features.append(combined.T)
                        labels.append(label_value)
            except Exception as e:
                print(f"Error processing {filename}: {e}")


X = tf.keras.preprocessing.sequence.pad_sequences(features, padding='post', dtype='float32')
y = np.array(labels)


scaler = StandardScaler()
X_flat = X.reshape(-1, X.shape[-1])
scaler.fit(X_flat)


np.save("scaler_mean.npy", scaler.mean_)
np.save("scaler_scale.npy", scaler.scale_)

X_scaled = ((X_flat - scaler.mean_) / scaler.scale_).reshape(X.shape)


X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, stratify=y, random_state=42)


class_weights = compute_class_weight(class_weight='balanced', classes=np.unique(y_train), y=y_train)
class_weights = {i: w for i, w in enumerate(class_weights)}


model = Sequential([
    Bidirectional(LSTM(64, return_sequences=False), input_shape=(X.shape[1], X.shape[2])),
    Dropout(0.3),
    Dense(64, activation='relu'),
    Dropout(0.3),
    Dense(1, activation='sigmoid')
])

model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
early_stop = EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True)

model.fit(X_train, y_train, validation_split=0.2, epochs=100, batch_size=16,
          class_weight=class_weights, callbacks=[early_stop])

loss, acc = model.evaluate(X_test, y_test)
model.save(MODEL_PATH)
