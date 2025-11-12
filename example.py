from scipy.io import loadmat

mat = loadmat("data/EEG Data/eeg_record10.mat")
print("Keys in .mat file:")
print(mat.keys())

import numpy as np

mat = loadmat("data/EEG Data/eeg_record10.mat")
obj = mat["o"]

print("Type:", type(obj))
print("Shape:", getattr(obj, "shape", "No shape"))
print("Contents preview:")
print(obj)
