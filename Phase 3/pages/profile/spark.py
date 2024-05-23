from pyspark.sql.functions import col
from pymongo import MongoClient
import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, udf
from pyspark.sql.types import ArrayType, FloatType
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.linalg import Vectors, DenseVector, VectorUDT
from pyspark.ml.feature import MinMaxScaler
from pyspark.ml.clustering import KMeans
from pyspark.ml.evaluation import ClusteringEvaluator
# Initialize SparkSession
spark = SparkSession.builder.appName("MongoDB-Spark Connector").getOrCreate()

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['ML']
collection = db['Audio']

# Fetch data using PyMongo
data = list(collection.find())

# Convert the data to a Pandas DataFrame
df = pd.DataFrame(data)

# Write the DataFrame to a CSV file
df.to_csv("/home/sufyan/Documents/MLaudio3.csv", index=False)


# Initialize Spark session
spark = SparkSession.builder.appName("MusicRecommendationANN").getOrCreate()

# Load the dataset
file_path = "MLaudio3.csv"
df = spark.read.csv(file_path, header=True, inferSchema=True)

# Convert the audio features from string to list of floats
def parse_features(feature_str):
    return [float(x) for x in feature_str.strip("[]").split(",")]

parse_features_udf = udf(parse_features, ArrayType(FloatType()))

df = df.withColumn("parsed_features", parse_features_udf(col("audio features")))

# Convert the parsed features to DenseVector
def to_dense_vector(features):
    return DenseVector(features)

to_dense_vector_udf = udf(lambda x: to_dense_vector(x), VectorUDT())

df = df.withColumn("features", to_dense_vector_udf(col("parsed_features")))

# Scale the features
scaler = MinMaxScaler(inputCol="features", outputCol="scaledFeatures")
scaler_model = scaler.fit(df)
scaled_data = scaler_model.transform(df)

# Train the KMeans model for ANN
kmeans = KMeans(featuresCol="scaledFeatures", k=10, seed=1)
model = kmeans.fit(scaled_data)

# Make predictions
predictions = model.transform(scaled_data)

# Evaluate clustering by computing Silhouette score
evaluator = ClusteringEvaluator(featuresCol="scaledFeatures")
silhouette = evaluator.evaluate(predictions)
print(f"Silhouette with squared euclidean distance = {silhouette}")


# Function to get recommendations
def get_recommendations(track_id, num_recommendations=10):
    track = scaled_data.filter(scaled_data.track_id == track_id).select("scaledFeatures").first()
    cluster = model.predict(track["scaledFeatures"])
    recommendations = predictions.filter(predictions.prediction == cluster).orderBy(col("track_id")).limit(num_recommendations)
    return recommendations.select("track_id").collect()

# Example usage
track_id = 3  # Replace with an actual track ID
recommendations = get_recommendations(track_id)
print([row.track_id for row in recommendations])

# Stop the Spark session
spark.stop()
