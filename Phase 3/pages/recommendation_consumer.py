from confluent_kafka import Consumer, KafkaError
from pymongo import MongoClient

KAFKA_TOPIC_USER_ACTIVITY = "topic1"
KAFKA_TOPIC_RECOMMENDATIONS = "recommendations"
KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"

consumer = Consumer({
    'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
    'group.id': 'recommendation-consumer-group',
    'auto.offset.reset': 'earliest'
})

consumer.subscribe([KAFKA_TOPIC_USER_ACTIVITY])

client = MongoClient('mongodb://localhost:27017/')
db = client['ML']
users_collection = db['Users']

def update_recommendations(user_email, song):
    # Placeholder for recommendation logic
    # For simplicity, just return the song as the recommendation
    recommendations = [song]
    users_collection.update_one({"email": user_email}, {"$set": {"recommendations": recommendations}})

while True:
    msg = consumer.poll(1.0)
    if msg is None:
        continue
    if msg.error():
        if msg.error().code() == KafkaError._PARTITION_EOF:
            continue
        else:
            print(msg.error())
            break

    user_email = msg.key().decode('utf-8')
    song = msg.value().decode('utf-8')
    update_recommendations(user_email, song)

consumer.close()
