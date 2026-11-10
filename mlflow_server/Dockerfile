# Création du conteneur MLFLow
FROM python:3.11

WORKDIR /home/app

# Installation MLflow, Postgres (Neon) et boto3
COPY requirements.txt /dependencies/requirements.txt
RUN pip install -r /dependencies/requirements.txt

# Les variables (clés AWS, URI Neon, URI S3, PORT) viennent de .env de mlflow
CMD mlflow server -p $PORT \
    --host 0.0.0.0 \
    --backend-store-uri $BACKEND_STORE_URI \
    --default-artifact-root $ARTIFACT_ROOT \
    --allowed-hosts "*"
