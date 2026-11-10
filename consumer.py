# Lecture des paiements dans Kafka, prédiction, stockage dans Neon et alerte e-mail

import os
import smtplib
from datetime import datetime, timezone
from email.mime.text import MIMEText
from io import StringIO

import mlflow
import pandas as pd
from confluent_kafka import Consumer
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()  #Récupération des mots de passe
GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
ALERT_RECIPIENT = os.getenv("ALERT_RECIPIENT") or GMAIL_USER

# Chargement du modèle MLflow et connexion à Neon
mlflow.set_tracking_uri("http://localhost:4000")
model = mlflow.sklearn.load_model("models:/fraud_detector@champion")
engine = create_engine(os.getenv("DATABASE_URI"))

# Connexion à Kafka
consumer = Consumer({"bootstrap.servers": "localhost:9092", "group.id": "fraud_consumer", "auto.offset.reset": "earliest"})
consumer.subscribe(["transactions"])
print("Kafka OK")

try:
    while True:
        msg = consumer.poll(1.0)  #Attente d'un message pendant 1 seconde
        if msg is None or msg.error():
            continue
        try:
            #Reconstruction du paiement, calcul de l'heure, sélection des 4 colonnes retenues par le model, prediction et proba, et heure de traitement
            df = pd.read_json(StringIO(msg.value().decode("utf-8")), orient="split")
            df["hour"] = pd.to_datetime(df["current_time"]).dt.hour
            features = df[model.feature_names_in_]
            df["fraud_prediction"] = int(model.predict(features)[0])
            df["fraud_proba"] = round(float(model.predict_proba(features)[0][1]), 4)
            df["processed_at"] = datetime.now(timezone.utc)

            # Ajout de la ligne dans la table Neon
            df.to_sql("fraud_predictions", engine, if_exists="append", index=False)
            tx = df.iloc[0]
            print(f"{'FRAUDE' if tx.fraud_prediction == 1 else 'Paiement normal'} | {tx.amt} $ | {tx.category} | proba fraude = {tx.fraud_proba:.0%}")

            # Envoi de l'alerte e-mail si fraude (avec Gmail configuré dans le .env)
            if tx.fraud_prediction == 1 and GMAIL_USER and GMAIL_APP_PASSWORD:
                mail = MIMEText(f"Fraude de {tx.amt} $ chez {tx.merchant} ({tx.category}), carte se terminant par {str(tx.cc_num)[-4:]}, probabilité de fraude : {tx.fraud_proba:.0%}.")
                mail["Subject"] = "Fraude détectée"
                mail["From"] = GMAIL_USER
                mail["To"] = ALERT_RECIPIENT
                with smtplib.SMTP("smtp.gmail.com", 587) as server:
                    server.starttls()
                    server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
                    server.send_message(mail)
                print(f"E-mail d'alerte envoyé à {ALERT_RECIPIENT}")
        except Exception as e:
            print(f"Erreur : {e}")
finally:
    consumer.close()
