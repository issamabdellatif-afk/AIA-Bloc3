# Rapport du matin : bilan des paiements et des fraudes de la veille envoyé par e-mail

import os
import smtplib
from datetime import datetime, timedelta, timezone
from email.mime.text import MIMEText

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()  #lit les mots de passe du fichier .env
GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
ALERT_RECIPIENT = os.getenv("ALERT_RECIPIENT") or GMAIL_USER

#Date de la veille
day = datetime.now(timezone.utc).date() - timedelta(days=1)

#Lecture dans Neon des paiements traités 
engine = create_engine(os.getenv("DATABASE_URI"))
df = pd.read_sql(text("SELECT * FROM fraud_predictions WHERE DATE(processed_at) = :day"), engine, params={"day": day})
frauds = df[df["fraud_prediction"] == 1]

# Construction du rapport
report = (
    f"Rapport du {day}\n\n"
    f"Nombre de paiements : {len(df)}\n"
    f"Fraudes détectées : {len(frauds)}\n"
    f"Montant total des paiements : {df['amt'].sum():.2f} $\n"
    f"Montant total des fraudes : {frauds['amt'].sum():.2f} $\n\n"
)
if len(frauds) > 0:
    report += frauds[["processed_at", "amt", "merchant", "category", "fraud_proba"]].to_string(index=False)
print(report)

# Envoi par e-mail si Gmail est configuré dans le .env
if GMAIL_USER and GMAIL_APP_PASSWORD:
    mail = MIMEText(report)
    mail["Subject"] = f"Rapport fraude du {day}"
    mail["From"] = GMAIL_USER
    mail["To"] = ALERT_RECIPIENT
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        server.send_message(mail)
    print("Rapport envoyé par e-mail")