import gradio as gr
import psycopg2
from docx import Document
from docx2pdf import convert
import os
from datetime import datetime
from dotenv import load_dotenv

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

def generate_document(intervenant, societe, contact, duree_inter, date_deb, date_fin, obj_presta, contenu_intervention, num_mission, mail_intervenant):
    doc = Document("template_bon-intervention.docx")
    for p in doc.paragraphs:
        p.text = p.text.replace("[INTERVENANT]", intervenant)\
                       .replace("[MAIL_INTERVENANT]", mail_intervenant)\
                       .replace("[SOCIETE]", societe)\
                       .replace("[NOM_CONTACT]", contact)\
                       .replace("[DUREE_INTER]", duree_inter)\
                       .replace("[DATE_DEB]", date_deb)\
                       .replace("[DATE_FIN]", date_fin)\
                       .replace("[OBJ_PRESTA]", obj_presta)\
                       .replace("[CONTENU_INTERVENTION]", contenu_intervention)\
                       .replace("[NUM_MISSION]", num_mission)\
                       .replace("[DATE]", datetime.today().strftime("%d/%m/%Y"))
    doc_path = f"bon_intervention_{num_mission}.docx"
    doc.save(doc_path)
    pdf_path = doc_path.replace(".docx", ".pdf")
    convert(doc_path, pdf_path)

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
    return pdf_path

def generate_with_mail(intervenant, societe, contact, duree, date_deb, date_fin, obj, contenu, mission):
    mail = get_mail_intervenant(intervenant)
    return generate_document(intervenant, societe, contact, duree, date_deb, date_fin, obj, contenu, mission, mail)

def interface():
    clients = get_clients()
    intervenants = get_intervenants()

    with gr.Blocks() as demo:
        # Onglet 1 : Génération de bon d'intervention
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

        # Onglet 2 : Ajouter un client
        with gr.Tab("Ajouter Client"):
            new_client = gr.Textbox(label="Société")
            msg_client = gr.Textbox(label="Message", interactive=False)
            gr.Button("Ajouter Client").click(add_client, inputs=new_client, outputs=msg_client)

        # Onglet 3 : Ajouter un contact
        with gr.Tab("Ajouter Contact"):
            societe_contact = gr.Dropdown(label="Société", choices=clients)
            nom = gr.Textbox(label="Nom")
            prenom = gr.Textbox(label="Prénom")
            mail = gr.Textbox(label="Email")
            tel = gr.Textbox(label="Téléphone")
            msg_contact = gr.Textbox(label="Message", interactive=False)
            gr.Button("Ajouter Contact").click(add_contact, 
                inputs=[societe_contact, nom, prenom, mail, tel], outputs=msg_contact)

        # Onglet 4 : Tableau de bord
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
