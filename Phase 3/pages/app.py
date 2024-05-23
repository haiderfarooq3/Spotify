from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash, session
import os
import re
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
from confluent_kafka import Producer, Consumer, KafkaError

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# Kafka configuration
KAFKA_TOPIC_USER_ACTIVITY = "user-activity"
KAFKA_TOPIC_RECOMMENDATIONS = "recommendations"
KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"

producer = Producer({'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS})

def delivery_report(err, msg):
    if err is not None:
        print('Message delivery failed: {}'.format(err))
    else:
        print('Message delivered to {} [{}]'.format(msg.topic(), msg.partition()))

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['ML']
users_collection = db['Users']

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        birthday = request.form["birthday"]
        password = request.form["password"]
        
        # Validate email format
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            flash("Invalid email address!")
            return render_template("signup.html")

        # Validate password length
        if len(password) < 8:
            flash("Password must be at least 8 characters long!")
            return render_template("signup.html")

        # Check if email already exists
        if users_collection.find_one({"email": email}):
            flash("Email already registered!")
            return render_template("signup.html")

        user_data = {
            "name": name,
            "email": email,
            "birthday": birthday,
            "password": password,
            "music": [],
            "genres": []
        }

        users_collection.insert_one(user_data)
        return redirect(url_for("login"))
    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = users_collection.find_one({"email": email})

        if not user:
            flash("Email not registered!")
            return render_template("login.html")

        if user["password"] != password:
            flash("Incorrect password!")
            return render_template("login.html")

        session['user_email'] = email  # Store user email in session
        return redirect(url_for("profile"))
    return render_template("login.html")

@app.route("/profile")
def profile():
    user_email = session.get('user_email')
    if not user_email:
        return redirect(url_for("login"))
    user = users_collection.find_one({"email": user_email})
    if user:
        return render_template("profile.html", user=user)
    return redirect(url_for("home"))

@app.route("/genres", methods=["GET", "POST"])
def genres():
    if request.method == "POST":
        user_email = session.get('user_email')
        selected_genres = request.form.getlist("genres")
        users_collection.update_one({"email": user_email}, {"$set": {"genres": selected_genres}})
        return redirect(url_for("home"))
    return render_template("genres.html")

@app.route("/your_music")
def your_music():
    user_email = session.get('user_email')
    if not user_email:
        return redirect(url_for("login"))
    user = users_collection.find_one({"email": user_email})
    if user:
        user_music = user["music"]
        return render_template("your_music.html", user_music=user_music, user_email=user_email)
    return redirect(url_for("home"))

@app.route("/recommended_music")
def recommended_music():
    user_email = session.get('user_email')
    if not user_email:
        return redirect(url_for("login"))
    user = users_collection.find_one({"email": user_email})
    if user:
        recommendations = get_recommendations_for_user(user_email)
        return render_template("recommended_music.html", recommended_music=recommendations)
    return redirect(url_for("home"))

@app.route("/all-music")
def all_music():
    audio_folder = "/home/sufyan/Documents/Project/front/pages/Audios"  # Update with the correct path to your audio files folder
    audio_files = os.listdir(audio_folder)
    return render_template("all_music.html", audio_files=audio_files)

@app.route("/audios/<filename>")
def get_audio(filename):
    user_email = session.get('user_email')
    if user_email:
        # Produce message to Kafka topic 'user-activity'
        producer.produce(KAFKA_TOPIC_USER_ACTIVITY, key=user_email, value=filename, callback=delivery_report)
        producer.flush()
        
        # Automatically add the song to the user's music collection
        users_collection.update_one({"email": user_email}, {"$addToSet": {"music": filename}})
        
    return send_from_directory("/home/sufyan/Documents/Project/front/pages/Audios", filename)

@app.route("/add_music", methods=["POST"])
def add_music():
    user_email = session.get('user_email')
    if not user_email:
        return redirect(url_for("login"))
    song = request.form["song"]
    users_collection.update_one({"email": user_email}, {"$push": {"music": song}})
    return redirect(url_for("your_music"))

@app.route("/recommend/<track_id>")
def recommend(track_id):
    recommendations = get_recommendations(int(track_id))
    return render_template("recommended_music.html", recommended_music=recommendations)

def get_recommendations(track_id, num_recommendations=10):
    track = scaled_data.filter(scaled_data.track_id == track_id).select("scaledFeatures").first()
    if track is None:
        # Return an empty list or a default value if the track ID is not found
        return []
    cluster = model.predict(track["scaledFeatures"])
    recommendations = predictions.filter(predictions.prediction == cluster).orderBy(col("track_id")).limit(num_recommendations)
    return [row.track_id for row in recommendations]

def get_recommendations_for_user(user_email):
    user = users_collection.find_one({"email": user_email})
    user_music = user.get("music", [])
    track_ids = []
    for song in user_music:
        try:
            # Assuming song name is formatted as "Song <track_id>"
            track_id = int(song.split()[1])  # Modify this to match your song naming convention
            track_ids.append(track_id)
        except (IndexError, ValueError):
            # Handle the case where the song format is incorrect
            continue

    all_recommendations = []
    for track_id in track_ids:
        recommendations = get_recommendations(track_id)
        if recommendations:
            all_recommendations.extend(recommendations)
    return list(set(all_recommendations) - set(track_ids))

if __name__ == "__main__":
    collection = db['Audio']
    data = list(collection.find())
    df = pd.DataFrame(data)
    df.to_csv("/home/sufyan/Documents/MLaudio3.csv", index=False)

    spark = SparkSession.builder.appName("MusicRecommendationANN").getOrCreate()

    file_path = "/home/sufyan/Documents/MLaudio3.csv"
    df = spark.read.csv(file_path, header=True, inferSchema=True)

    def parse_features(feature_str):
        return [float(x) for x in feature_str.strip("[]").split(",")]

    parse_features_udf = udf(parse_features, ArrayType(FloatType()))
    df = df.withColumn("parsed_features", parse_features_udf(col("audio features")))

    def to_dense_vector(features):
        return DenseVector(features)

    to_dense_vector_udf = udf(lambda x: to_dense_vector(x), VectorUDT())
    df = df.withColumn("features", to_dense_vector_udf(col("parsed_features")))

    scaler = MinMaxScaler(inputCol="features", outputCol="scaledFeatures")
    scaler_model = scaler.fit(df)
    scaled_data = scaler_model.transform(df)

    kmeans = KMeans(featuresCol="scaledFeatures", k=10, seed=1)
    model = kmeans.fit(scaled_data)

    predictions = model.transform(scaled_data)

    evaluator = ClusteringEvaluator(featuresCol="scaledFeatures")
    silhouette = evaluator.evaluate(predictions)
    print(f"Silhouette with squared euclidean distance = {silhouette}")

    app.run(debug=True)
