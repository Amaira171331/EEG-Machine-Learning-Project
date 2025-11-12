import numpy as np
import joblib

# 1️⃣ Load your trained model and scaler
model = joblib.load('models/eeg_model_Logistic Regression.pkl')
scaler = joblib.load('models/eeg_scaler_Logistic Regression.pkl')
feature_names = joblib.load('models/eeg_features_Logistic Regression.pkl')

# 2️⃣ Collect or simulate a window of EEG data (alpha + beta)
# Example: shape must match the features used in training
alpha_beta_window = np.array([...])  # your 128-sample EEG window

# 3️⃣ Extract features (mean, std, min, max)
mean = np.mean(alpha_beta_window)
std = np.std(alpha_beta_window)
min_val = np.min(alpha_beta_window)
max_val = np.max(alpha_beta_window)

features = np.array([[mean, std, min_val, max_val]])

# 4️⃣ Scale features
features_scaled = scaler.transform(features)

# 5️⃣ Predict concentration
prediction = model.predict(features_scaled)

if prediction[0] == 1:
    print("Concentrated")
else:
    print("Not Concentrated")
