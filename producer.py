# Appel de l'API de paiement et transmission à Kafka

import time

import requests
from confluent_kafka import Producer
from confluent_kafka.admin import AdminClient, NewTopic

API_URL = "https://sdacelo-real-time-fraud-detection.hf.space/current-transactions"
TOPIC = "transactions"
KAFKA_CONF = {"bootstrap.servers": "localhost:9092"} #localement

# Création du topic si il n'existe pas
admin = AdminClient(KAFKA_CONF)
if TOPIC not in admin.list_topics(timeout=10).topics:
    admin.create_topics([NewTopic(TOPIC, num_partitions=1, replication_factor=1)])

producer = Producer(KAFKA_CONF) #Création du producer
last_record = None #Initialisation variable dernier paiement

#Récupération toutes les 15 secondes du paiement et envoi à Kafka
while True:
    try:
        response = requests.get(API_URL, timeout=30)
        record = response.json()
        if response.status_code == 200 and record != last_record: #Pour éviter les doublons
            producer.produce(TOPIC, value=record, on_delivery=lambda err, msg: print(f"Paiement envoyé dans Kafka (offset {msg.offset()})")) #Dépôt du paiement dans le topic kafka
            producer.flush() #Attente de l'envoi
            last_record = record #Sauvegarde en tant que précédent paiement
    except Exception as e:
        print(f"Erreur : {e}")
    time.sleep(15) #Pause 15 sec
