import sys
import os
import win32com.client as win32
import pythoncom
from datetime import datetime
import subprocess

# Dictionnaire des intervenants (à adapter si nécessaire)
intervenants = {
    "Mounir BOUGOUFFA": "mbougouffa@mbt-consulting.com",
    "Yannis CHAZOT": "ychazot@mbt-consulting.com",
}

def enregistrer_email_msg(mail_contact, intervenant, societe, output_pdf):
    pythoncom.CoInitialize()

    cc_emails = ";".join([email for name, email in intervenants.items() if name != intervenant])
    subject = f"MBT/{societe} - Bon d'intervention"
    body = "Bonjour,\n\nVeuillez trouver ci-joint le bon d'intervention à nous retourner signé.\n\n"

    outlook = win32.Dispatch('Outlook.Application')
    mail = outlook.CreateItem(0)
    mail.To = mail_contact
    mail.CC = cc_emails
    mail.Subject = subject
    mail.Body = body
    mail.Attachments.Add(os.path.abspath(output_pdf))

    nom_fichier_msg = f"Mail_{societe}_{datetime.today().strftime('%Y%m%d')}.msg"
    chemin_msg = os.path.abspath(nom_fichier_msg)
    mail.Display()

    pythoncom.CoUninitialize()
    return chemin_msg

if __name__ == "__main__":
    mail_contact = sys.argv[1]
    intervenant = sys.argv[2]
    societe = sys.argv[3]
    output_pdf = sys.argv[4]

    enregistrer_email_msg(mail_contact, intervenant, societe, output_pdf)