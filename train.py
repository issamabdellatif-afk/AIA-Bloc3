# Entrainement du modèle ML sur fraudtest.csv

import mlflow
import pandas as pd
from dotenv import load_dotenv
from mlflow.models import infer_signature
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

load_dotenv()  # clés AWS du .env

MLFLOW_TRACKING_URI = "http://localhost:4000"
MODEL_NAME = "fraud_detector"
DATA_PATH = "data/fraudTest.csv"

# Colonnes retenues
NUMERIC_COLS = ["amt", "hour"]
CATEGORICAL_COLS = ["category", "gender"]
TARGET = "is_fraud"

df = pd.read_csv(DATA_PATH)

df["hour"] = pd.to_datetime(df["trans_date_trans_time"]).dt.hour

X = df[NUMERIC_COLS + CATEGORICAL_COLS]
y = df[TARGET]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

# Préparation des données et du modèle (sklearn)

preprocessor = ColumnTransformer(
    transformers=[
        ("num", StandardScaler(), NUMERIC_COLS),
        ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_COLS),
    ]
)

model = Pipeline(
    steps=[
        ("preprocessing", preprocessor),
        (
            "classifier",
            RandomForestClassifier(
                n_estimators=100,
                class_weight="balanced", #balanced car moins de 1% de fraudes dans le dataset, met plus de poids aux fraudes
                min_samples_leaf=2,
                random_state=42,
                n_jobs=-1,
            ),
        ),
    ]
)

# Entrainement et suivi dans MLFLOW

mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
mlflow.set_experiment("fraud_detection")

with mlflow.start_run() as run:
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    metrics = {
        "accuracy": accuracy_score(y_test, y_pred),
        "precision_fraud": precision_score(y_test, y_pred),
        "recall_fraud": recall_score(y_test, y_pred),
        "f1_fraud": f1_score(y_test, y_pred),
    }
    mlflow.log_params({"n_estimators": 100, "class_weight": "balanced", "min_samples_leaf": 2})
    mlflow.log_metrics(metrics)
    print("Métriques test :", {k: round(v, 3) for k, v in metrics.items()})

    # Log et enregistrement dans le registry
    mlflow.sklearn.log_model(
        model,
        name="model",
        signature=infer_signature(X_train, y_pred),
        input_example=X_train.head(2),
        registered_model_name=MODEL_NAME,
    )

# Alias Champion sur le dernier modèle entrainé
client = mlflow.MlflowClient()
versions = client.search_model_versions(f"name='{MODEL_NAME}'")
last_version = max(int(v.version) for v in versions)
client.set_registered_model_alias(MODEL_NAME, "champion", last_version)
print(f"Modèle '{MODEL_NAME}' version {last_version} enregistré avec l'alias @champion")
