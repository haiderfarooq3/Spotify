# Project Report: Developing a Streamlined Music Recommendation System

## Introduction

Spotify, a renowned digital music streaming service, revolutionized the way people discover and listen to music. With its extensive library of songs, podcasts, and videos, Spotify offers users personalized recommendations based on their preferences and listening habits. In this project, our objective is to develop a streamlined alternative to Spotify, featuring a music recommendation system, playback, and streaming capabilities, alongside real-time suggestions derived from user activity.

## Phase #1: Extract, Transform, Load (ETL) Pipeline

### Dataset Selection and Preparation
For our project, we initially encountered challenges dealing with the size of the FMA dataset, totaling 93 GiB when compressed. To address this, we decided to extract a smaller sample from the dataset for experimentation and development purposes. This sample subset allowed us to efficiently work with the data without compromising the integrity of the project.

### Feature Extraction and Transformation
Once we had the sample dataset in hand, we proceeded with feature extraction using Python. Techniques such as Mel-Frequency Cepstral Coefficients (MFCC), spectral centroid, and zero-crossing rate were employed to convert the audio files into numerical and vector formats. Despite the reduced dataset size, the feature extraction process remained computationally intensive but manageable.

### Data Storage
Storing the extracted audio features posed no significant challenges thanks to MongoDB's scalability and accessibility. The database seamlessly accommodated the sample dataset, ensuring efficient storage and retrieval for subsequent phases of the project.

## Phase #2: Music Recommendation Model

### Model Selection and Training
In Phase 2, significant time and effort were invested in selecting the appropriate machine learning model for the music recommendation task. After extensive testing and trial attempts, we concluded that a K-means clustering algorithm, specifically applied as an Approximate Nearest Neighbors (ANN) model, was best suited for our dataset and objectives. The iterative process of model selection and training involved fine-tuning parameters and evaluating performance to ensure optimal results.

### Evaluation and Validation
While the chosen K-means ANN model showed promise, we encountered some challenges in achieving desired performance metrics. Despite our efforts in hyperparameter tuning and model optimization, the results were not initially as robust as anticipated. However, ongoing refinement and iteration were necessary to address these limitations and enhance the model's effectiveness.

## Phase #3: Deployment

### Web Application Development
In Phase 3, our focus shifted towards deploying the trained model onto a web application, transforming it into an interactive music streaming service. Leveraging frameworks like Flask and Django, we developed a user-friendly web interface that encapsulated the core features of our music recommendation system. Implementing Apache Kafka enabled us to dynamically generate music recommendations based on user activity and historical playback data, ensuring personalized suggestions in real-time. Continuous monitoring of user interactions and feedback channels allowed us to refine the system iteratively, gauging satisfaction and making necessary improvements. This phase culminated in the successful deployment of an interactive music streaming web application with real-time recommendation capabilities, showcasing the transformative potential of our alternative to Spotify.

## Conclusion

Our project successfully developed a streamlined music recommendation system, offering a compelling alternative to existing platforms like Spotify. By leveraging big data technologies and machine learning algorithms, we demonstrated the transformative potential of personalized music recommendations and real-time streaming capabilities. We look forward to further refining and enhancing the system to meet the evolving needs of music enthusiasts worldwide.
