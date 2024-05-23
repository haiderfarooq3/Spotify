import os
import numpy as np
import pandas as pd
import librosa
from pymongo import MongoClient
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

# Function to extract audio features
def extract_features(file_path):
    y, sr = librosa.load(file_path, duration=30)  # Load audio file
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)  # Extract MFCC (use 13 coefficients)
    spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)  # Spectral centroid
    zero_crossing_rate = librosa.feature.zero_crossing_rate(y)  # Zero-crossing rate
    
    # Concatenate all features into a single feature vector
    feature_vector = np.hstack((mfcc.mean(axis=1), np.mean(spectral_centroid), np.mean(zero_crossing_rate)))
    return feature_vector

# Function to normalize features
def normalize_features(features):
    scaler = StandardScaler()
    normalized_features = scaler.fit_transform(features)
    return normalized_features

# Function to apply dimensionality reduction
def reduce_dimensionality(features, n_components=10):
    # Ensure n_components does not exceed the minimum of n_samples and n_features
    n_samples, n_features = features.shape
    n_components = min(n_components, n_samples, n_features)
    pca = PCA(n_components=n_components)
    reduced_features = pca.fit_transform(features)
    return reduced_features

# Function to connect to MongoDB and insert data
def insert_to_mongodb(data):
    client = MongoClient('mongodb://localhost:27017/')
    db = client['music_features']
    collection = db['audio_features']
    collection.insert_many(data)

# Path to the root directory containing audio files
root_dir = r'C:\Users\rayya\Desktop\Fourth Semester\BDA\Assignments\PROJECT\sample1'

# Batch size for processing
batch_size = 1000  # Adjust according to system memory and performance

# Lists to store extracted features and track IDs
features_list = []
track_ids = []

# Traverse through all subdirectories and extract features from audio files
for subdir, _, files in os.walk(root_dir):
    for file in files:
        if file.endswith('.mp3'):
            file_path = os.path.join(subdir, file)
            try:
                # Extract features
                feature_vector = extract_features(file_path)
                # Additional information from file path or metadata (example: Track ID)
                track_id = os.path.splitext(file)[0]
                track_ids.append(track_id)
                features_list.append(feature_vector)
                # Batch processing
                if len(features_list) >= batch_size:
                    # Normalize audio features
                    normalized_features = normalize_features(features_list)
                    # Reduce dimensionality of features
                    reduced_features = reduce_dimensionality(normalized_features)
                    # Create a list of dictionaries for MongoDB insertion
                    data_to_insert = [
                        {
                            'track_id': track_ids[i],
                            'audio_features': reduced_features[i].tolist()
                        } for i in range(len(reduced_features))
                    ]
                    # Insert to MongoDB
                    insert_to_mongodb(data_to_insert)
                    # Save to CSV
                    df = pd.DataFrame(data_to_insert)
                    df.to_csv('audio_features_batch.csv', mode='a', header=False, index=False)
                    # Reset lists for next batch
                    features_list = []
                    track_ids = []
            except Exception as e:
                print(f"Error processing {file_path}: {e}")

# Process remaining features
if len(features_list) > 0:
    # Normalize audio features
    normalized_features = normalize_features(features_list)
    # Reduce dimensionality of features
    reduced_features = reduce_dimensionality(normalized_features)
    # Create a list of dictionaries for MongoDB insertion
    data_to_insert = [
        {
            'track_id': track_ids[i],
            'audio_features': reduced_features[i].tolist()
        } for i in range(len(reduced_features))
    ]
    # Insert to MongoDB
    insert_to_mongodb(data_to_insert)
    # Save to CSV
    df = pd.DataFrame(data_to_insert)
    df.to_csv('audio_features_batch.csv', mode='a', header=False, index=False)

print("Data insertion complete.")
