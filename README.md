# Bloc 3 - Issam Abdellatif Détection de fraude en temps réel — Pipeline Kafka et MLflow

Pipeline temps réel : une API envoie des paiements, Kafka les transporte, un modèle MLflow prédit les fraudes, les résultats sont stockés dans Neon, une alerte e-mail part si fraude, et un rapport est envoyé chaque matin.

Données utilisées :
- `fraudTest.csv` : 555 000 paiements étiquetés (fraude ou non frauduleux) pour entraîner le modèle
- API temps réel `https://sdacelo-real-time-fraud-detection.hf.space/current-transactions` pour les nouveaux paiements à analyser

# Structure du dépot

```
fraud-detection-bloc3/
├── requirements.txt        #Environnement Python
├── docker-compose.yml      #Kafka et serveur MLflow en un seul docker compose up
├── mlflow_server/          #Image Docker du serveur MLflow (avec backend dans Neon + artefacts dans S3)
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env.example
├── data/                   #Déposer fraudTest.csv ici (non versionné : trop lourd pour GitHub)
├── train.py                #Entraînement sur CSV et enregistrement du modèle dans MLflow
├── producer.py             #Transmission du paiement de l'API vers Kafka
├── consumer.py             #Prédiction et gestion de l'alerte e-mail si fraude
├── daily_report.py         #Envoi du rapport quotidien (paiements + fraudes de la veille)
└── .env.example            #Variables des scripts Python
```

Deux fichiers `.env` :
- `.env` à la racine : utilisé par les scripts Python (Neon, AWS, Gmail)
- `mlflow_server/.env` : utilisé par le conteneur MLflow (AWS, Neon, S3)

# Modèle ML

- Pipeline scikit-learn : `StandardScaler` (montant, heure), `OneHotEncoder` (catégorie, genre) et `RandomForest`
- 4 informations : **montant**, **heure du paiement**, **type de commerce**, **genre du client**.
- `class_weight="balanced"` car seulement 0,39 % des paiements sont des fraudes
- Préparation des données intégrée au modèle : le script consumer.py appelle uniquement `model.predict()`

# Résultats sur le jeu de test (20% des données)

- Rappel (recall) : 75%
- Précision : 65%
- F1 : 0,70
- Accuracy : 99,7%

# Lancement
1. python -m venv .venv, puis .venv\Scripts\Activate.ps1, puis pip install -r requirements.txt
2. Copier les deux .env.example en .env et les remplir
3. docker compose up --build
4. python train.py
5. python producer.py puis python consumer.py (deux terminaux)
6. python daily_report.py (ou via CRON)

# Lancement automatique de dailyreport.py à 8h
```
0 8 * * * cd /chemin/du/projet && .venv/bin/python daily_report.py
```