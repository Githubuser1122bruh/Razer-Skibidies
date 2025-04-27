import os
import numpy as np
import librosa
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout

dataset_path = "dataset"

X = []
y = []

for label, class_name in enumerate(["brainrot"]):
    class_path = os.path.join(dataset_path, class_name)
    for file in os.listdir(class_path):
        if file.endswith(".wav"):
            file_path = os.path.join(class_path, file)
            try:
                audio_data, sample_rate = librosa.load(file_path, sr=22050)

                mfccs = librosa.feature.mfcc(y=audio_data, sr=sample_rate, n_mfcc=13)
                mfccs_mean = np.mean(mfccs.T, axis=0)

                X.append(mfccs_mean)
                y.append(1) 
            except Exception as e:
                print(f"Error processing {file_path}: {e}")

X = np.array(X)
Y = np.array(Y)


scaler = StandardScaler()
X = scaler.fit_transform(X)
np.save("scaler_mean.npy", scaler.mean_)
np.save("scaler_mean.npy", scaler.scale_)

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = Sequential([
    Dense(128, activation='relu', input_shape=(X_train.shape[1],)),
    Dropout(0.3),
    Dense(64, activation='relu'),
    Dropout(0.3),
    Dense(1, activation='sigmoid')
])

model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
model.summary()

model.fit(X_train, y_train, validation_data=(X_test, y_test), epochs=20, batch_size=32)

model.save("brainrot_detector.h5")
print("Model saved as brainrot_detector.h5")