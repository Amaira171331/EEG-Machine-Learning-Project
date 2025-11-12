import joblib

feature_names = joblib.load('models/eeg_features_Logistic Regression.pkl')
print(feature_names)