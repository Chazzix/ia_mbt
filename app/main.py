import gradio as gr
import psycopg2
from docx import Document
import os
from datetime import datetime
from dotenv import load_dotenv
import sys
import smtplib
from email.message import EmailMessage

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")

def connect_db():
    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )

def get_clients():
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT societe FROM clients")
    clients = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()
    return clients

def get_contacts(societe):
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT nom FROM contact WHERE client_id=(SELECT id FROM clients WHERE societe=%s)", (societe,))
    contacts = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()
    return contacts

def get_intervenants():
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT intervenant FROM intervenants")
    intervenants = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()
    return intervenants

def get_mail_intervenant(nom_intervenant):
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT mail FROM intervenants WHERE intervenant = %s", (nom_intervenant,))
    mail = cur.fetchone()[0]
    cur.close()
    conn.close()
    return mail

def get_all_intervenant_emails(exclude_email=None):
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT mail FROM intervenants")
    mails = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()
    if exclude_email:
        mails = [m for m in mails if m != exclude_email]
    return mails

def get_mail_contact(nom_contact):
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT mail FROM contact WHERE nom = %s", (nom_contact,))
    mail = cur.fetchone()[0]
    cur.close()
    conn.close()
    return mail

def add_client(nomclient):
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO clients (societe) VALUES (%s)", (nomclient,))
    conn.commit()
    cur.close()
    conn.close()
    return f"Client '{nomclient}' ajouté avec succès."

def add_contact(societe, nom, prenom, mail, telephone):
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO contact (nom, prenom, mail, telephone, client_id)
        VALUES (%s, %s, %s, %s, (SELECT id FROM clients WHERE societe=%s))
    """, (nom, prenom, mail, telephone, societe))
    conn.commit()
    cur.close()
    conn.close()
    return f"Contact {nom} ajouté avec succès."

def get_bon_intervention():
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM bon_intervention_view")
    data = cur.fetchall()
    cur.close()
    conn.close()
    return data

def replace_placeholders(text, replacements):
    for key, value in replacements.items():
        text = text.replace(key, value)
    return text

def generate_document(intervenant, societe, contact, mail_contact, duree_inter, date_deb, date_fin, obj_presta, contenu_intervention, num_mission, mail_intervenant):
    doc_path = "template_bon-intervention.docx"
    doc = Document(doc_path)

    replacements = {
        "[INTERVENANT]": intervenant,
        "[MAIL_INTERVENANT]": mail_intervenant,
        "[SOCIETE]": societe,
        "[MAIL_CONTACT]": mail_contact,
        "[NOM_CONTACT]": contact,
        "[DUREE_INTER]": duree_inter,
        "[DATE_DEB]": date_deb,
        "[DATE_FIN]": date_fin,
        "[OBJ_PRESTA]": obj_presta,
        "[CONTENU_INTERVENTION]": contenu_intervention,
        "[NUM_MISSION]": num_mission,
        "[DATE]": datetime.today().strftime("%d/%m/%Y")
    }

    # Remplacement dans les paragraphes
    for p in doc.paragraphs:
        for run in p.runs:
            run.text = replace_placeholders(run.text, replacements)

    # Remplacement dans les tableaux
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    for run in paragraph.runs:
                        run.text = replace_placeholders(run.text, replacements)

    # 🔍 Zones non prises en charge par python-docx :
    # - Zones de texte (formes, SmartArt)
    # - Images et légendes
    # Pour cela, envisager l'utilisation de bibliothèques comme `docxtpl` ou `Aspose.Words`.

    output_docx_path = f"BI_{societe.replace(' ', '_')}.docx"
    doc.save(output_docx_path)

    # Conversion en PDF avec LibreOffice
    os.system(f'libreoffice --headless --convert-to pdf "{output_docx_path}" --outdir .')

    # Suppression du fichier Word généré
    if os.path.exists(output_docx_path):
        os.remove(output_docx_path)

    # Conversion des dates pour la base de données
    date_deb = datetime.strptime(date_deb, "%d/%m/%Y").date()
    date_fin = datetime.strptime(date_fin, "%d/%m/%Y").date()

    # Insertion en base
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO bon_intervention (
            intervenant_id, client_id, contact_id, duree_inter, date_deb, date_fin, obj_presta, contenu_intervention, num_mission
        )
        VALUES (
            (SELECT id FROM intervenants WHERE intervenant=%s),
            (SELECT id FROM clients WHERE societe=%s),
            (SELECT id FROM contact WHERE nom=%s),
            %s, %s, %s, %s, %s, %s
        )
    """, (intervenant, societe, contact, duree_inter, date_deb, date_fin, obj_presta, contenu_intervention, num_mission))
    conn.commit()
    cur.close()
    conn.close()

    return f"BI_{societe.replace(' ', '_')}.pdf"

def prepare_outlook_email(mail_contact, mail_intervenant, pdf_path, societe):
    from email.message import EmailMessage

    cc_list = get_all_intervenant_emails(exclude_email=mail_intervenant)

    msg = EmailMessage()
    msg["Subject"] = f"MBT/{societe} - Bon d'intervention"
    msg["From"] = mail_intervenant
    msg["To"] = mail_contact
    if cc_list:
        msg["Cc"] = ", ".join(cc_list)
    msg.set_content("Bonjour,\n\nVeuillez trouver ci-joint le bon d'intervention.\n\n")

    with open(pdf_path, "rb") as f:
        file_data = f.read()
        file_name = os.path.basename(pdf_path)
        msg.add_attachment(file_data, maintype="application", subtype="pdf", filename=file_name)
    
    output_dir = "./emails"
    os.makedirs(output_dir, exist_ok=True)
    eml_path = os.path.join(output_dir, f"email_{file_name.replace('.pdf', '.eml')}")

    with open(eml_path, "wb") as f:
        f.write(msg.as_bytes())

    print(f"Fichier .eml généré : {eml_path}")

def generate_with_mail(intervenant, societe, contact, duree, date_deb, date_fin, obj, contenu, mission):
    mail_intervenant = get_mail_intervenant(intervenant)
    pdf_path = generate_document(intervenant, societe, contact, duree, date_deb, date_fin, obj, contenu, mission, mail_intervenant)
    mail_contact = get_mail_contact(contact)
    prepare_outlook_email(mail_contact, mail_intervenant, pdf_path, societe)
    return pdf_path

def interface():
    clients = get_clients()
    intervenants = get_intervenants()

    with gr.Blocks() as demo:
        with gr.Tab("Générer Bon d'Intervention"):
            intervenant = gr.Dropdown(label="Intervenant", choices=intervenants)
            societe = gr.Dropdown(label="Société", choices=clients)
            contact = gr.Dropdown(label="Contact", choices=[])
            duree = gr.Textbox(label="Durée")
            date_deb = gr.Textbox(label="Date début")
            date_fin = gr.Textbox(label="Date fin")
            obj = gr.Textbox(label="Objectif")
            contenu = gr.Textbox(label="Contenu")
            mission = gr.Textbox(label="Numéro de mission")
            fichier_pdf = gr.File(label="Bon d'intervention (PDF)")

            def update_contacts(soc):
                return gr.update(choices=get_contacts(soc))
            societe.change(update_contacts, inputs=societe, outputs=contact)

            gr.Button("Générer PDF").click(generate_with_mail, 
                inputs=[intervenant, societe, contact, duree, date_deb, date_fin, obj, contenu, mission],
                outputs=fichier_pdf)

        with gr.Tab("Ajouter Client"):
            new_client = gr.Textbox(label="Société")
            msg_client = gr.Textbox(label="Message", interactive=False)
            gr.Button("Ajouter Client").click(add_client, inputs=new_client, outputs=msg_client)

        with gr.Tab("Ajouter Contact"):
            societe_contact = gr.Dropdown(label="Société", choices=clients)
            nom = gr.Textbox(label="Nom")
            prenom = gr.Textbox(label="Prénom")
            mail = gr.Textbox(label="Email")
            tel = gr.Textbox(label="Téléphone")
            msg_contact = gr.Textbox(label="Message", interactive=False)
            gr.Button("Ajouter Contact").click(add_contact, 
                inputs=[societe_contact, nom, prenom, mail, tel], outputs=msg_contact)

        with gr.Tab("Tableau de Bord"):
            data = get_bon_intervention()
            gr.DataFrame(data, headers=[
                "ID", "Intervenant", "Société", "Nom Contact", "Email Contact",
                "Durée", "Date Début", "Date Fin", "Objectif", "Contenu",
                "Numéro de Mission", "Date Création"
            ])

    return demo

if __name__ == "__main__":
    demo = interface()
    demo.launch(server_name="0.0.0.0", server_port=7860)
