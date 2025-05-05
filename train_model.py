import os
import numpy as np
import librosa
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import Dense, Dropout
from sklearn.utils.class_weight import compute_class_weight
import tensorflow as tf
import matplotlib.pyplot as plt

# Path to the dataset
dataset_path = "/Users/samhithpola/Documents/GitHub/Razer-Skibidies#/brainrot_audio"

model = tf.keras.models.load_model("brainrot_detector.h5")

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

# Initialize feature and label lists
X = []
y = []

print(f"number of brainrot samples {np.sum(y == 1)}")
print(f"number of normal samples{np.sum(y == 0)}")

# Load brainrot and normal audio files
for label, class_name in enumerate(["brainrot", "normal"]):  # 0 for normal, 1 for brainrot
    class_path = os.path.join(dataset_path, class_name)
    for file in os.listdir(class_path):
        if file.endswith(".wav"):
            file_path = os.path.join(class_path, file)
            try:
                # Load the audio file
                audio_data, sample_rate = librosa.load(file_path, sr=22050)
                
                # Extract MFCC features
                mfccs = librosa.feature.mfcc(y=audio_data, sr=sample_rate, n_mfcc=13)
                mfccs_mean = np.mean(mfccs.T, axis=0)

                # Append features and label
                X.append(mfccs_mean)
                y.append(label)
            except Exception as e:
                print(f"Error processing {file_path}: {e}")

# Convert to NumPy arrays
X = np.array(X)
y = np.array(y)

print(X)
print(y)

class_weights = compute_class_weight('balanced', classes = np.unique(y), y=y)
class_weights = dict(enumerate(class_weights))

weights, biases = model.layers[0].get_weights()
print("weights of first layer")
print(weights)

print("biases of the first layer")
print(biases)

for i, layer in enumerate(model.layers):
    print(f"Layer {i} - {layer.name}")
    if layer.get_weights():  # Check if the layer has weights
        weights, biases = layer.get_weights()
        print("Weights:")
        print(weights)
        print("Biases:")
        print(biases)
    else:
        print("This layer has no weights or biases.")

# Scale the features
scaler = StandardScaler()
X = scaler.fit_transform(X)

# Save the scaler parameters for inference
np.save("scaler_mean.npy", scaler.mean_)
np.save("scaler_scale.npy", scaler.scale_)

# Split the dataset into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Save the test data for evaluation
np.save("X_test.npy", X_test)
np.save("y_test.npy", y_test)

# Define the model
model = Sequential([
    Dense(256, activation='relu', input_shape=(X_train.shape[1],)),
    Dropout(0.4),
    Dense(128, activation='relu'),
    Dropout(0.4),
    Dense(1, activation='sigmoid')  # Sigmoid for binary classification
])

# Compile the model
model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])

# Print model summary
model.summary()

# Train the model
model.fit(X_train, y_train, validation_data=(X_test, y_test), epochs=200, batch_size=64, class_weight=class_weights)

history = model.fit(X_train, y_train, validation_data=(X_test, y_test), epochs=200, batch_size=64, class_weight=class_weights)
print(history)
plt.plot(history.history['accuracy'], label='Training')
plt.plot(history.history['val_accuracy'], label='Validation Accuracy')
plt.xlabel('Epochs')
plt.ylabel('Accuracy')
plt.legend()
plt.show()

loss, accuracy = model.evaluate(X_test, y_test)
print(f"test loss: {loss}")
print(f"test accuracy {accuracy}")

# Save the trained model
model.save("brainrot_detector.h5")
print("Model saved as brainrot_detector.h5")