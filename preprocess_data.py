"""
EEG Preprocessing Script (CSV version)
- Loads .mat files
- Extracts EEG features and labels
- Splits into windows
- Saves processed features as CSV
"""

import os
import numpy as np
import pandas as pd
from scipy.io import loadmat

# Folder containing .mat EEG files
DATA_FOLDER = "data/EEG Data"
OUTPUT_FILE = "data/processed_features.csv"

# Parameters
WINDOW_SIZE = 128  # samples per window
STEP_SIZE = 64     # overlap

def extract_features_from_eeg(eeg_data):
    """
    Simple feature extraction from EEG window:
    - Mean, Std, Min, Max for each channel
    """
    features = []
    # eeg_data shape: (window_size, n_channels)
    for ch in range(eeg_data.shape[1]):
        window = eeg_data[:, ch]
        features.extend([
            np.mean(window),
            np.std(window),
            np.min(window),
            np.max(window)
        ])
    return features

def load_mat_file(file_path):
    """
    Load a single .mat file and extract features/labels
    """
    try:
        mat = loadmat(file_path)
        o = mat['o'][0,0]  # adjust if needed

        eeg = o[4]          # EEG data: (n_samples, n_channels)
        labels = o[3].flatten()  # 0/1 labels per sample

        windows = []
        window_labels = []

        # Sliding windows
        for start in range(0, len(eeg)-WINDOW_SIZE+1, STEP_SIZE):
            end = start + WINDOW_SIZE
            eeg_win = eeg[start:end, :]
            label_win = labels[start:end]
            # Majority label in window
            label = 1 if np.sum(label_win) > (WINDOW_SIZE/2) else 0
            feat = extract_features_from_eeg(eeg_win)
            windows.append(feat)
            window_labels.append(label)

        return np.array(windows), np.array(window_labels)

    except Exception as e:
        print(f"⚠ Could not extract EEG from {file_path}: {e}")
        return None, None

def load_all_mat_files(folder):
    """
    Load all .mat files and combine into one DataFrame
    """
    all_features = []
    all_labels = []

    files = sorted([f for f in os.listdir(folder) if f.endswith(".mat")])
    for f in files:
        path = os.path.join(folder, f)
        feats, labs = load_mat_file(path)
        if feats is not None:
            all_features.append(feats)
            all_labels.append(labs)
            print(f"✓ Loaded {feats.shape[0]} windows from {f}")

    if not all_features:
        raise ValueError("No valid .mat data loaded.")

    X = np.vstack(all_features)
    y = np.concatenate(all_labels)

    df = pd.DataFrame(X)
    df['label'] = y
    print(f"\n✅ Successfully loaded {len(df)} total windows from {len(files)} files.")
    return df

def main():
    df = load_all_mat_files(DATA_FOLDER)
    os.makedirs("data", exist_ok=True)
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"✓ Processed data saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
