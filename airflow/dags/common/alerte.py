from datetime import datetime, timezone
import os
import smtplib
import ssl
from email.message import EmailMessage


SERVEUR = "smtp.gmail.com"
PORT = 465


def envoyer(sujet, corps):
    utilisateur = os.environ.get("MBDA_SMTP_USER")
    motdepasse = os.environ.get("MBDA_SMTP_PASSWORD")
    destinataires = os.environ.get("MBDA_SMTP_TO", "")

    if not (utilisateur and motdepasse and destinataires):
        print("alerte non envoyee : MBDA_SMTP_* absent de l'environnement")
        return False

    message = EmailMessage()
    message["Subject"] = sujet
    message["From"] = utilisateur
    message["To"] = destinataires
    message.set_content(corps)

    with smtplib.SMTP_SSL(SERVEUR, PORT, context=ssl.create_default_context()) as smtp:
        smtp.login(utilisateur, motdepasse)
        smtp.send_message(message)
    return True


def sur_echec(contexte):
    tache = contexte["task_instance"]
    envoyer(
        f"Echec {tache.dag_id} / {tache.task_id}",
        f"Tache   : {tache.task_id}\n"
        f"DAG     : {tache.dag_id}\n"
        f"Essai   : {tache.try_number}\n"
        f"Date    : {datetime.now(timezone.utc).isoformat()}\n\n"
        f"Journal : {tache.log_url}\n",
    )
