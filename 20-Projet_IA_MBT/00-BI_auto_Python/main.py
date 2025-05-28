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
    return psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS)

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

def generate_document(intervenant, societe, contact, duree_inter, date_deb, date_fin, obj_presta, contenu_intervention, num_mission):
    doc = Document("template_bon-intervention.docx")
    for p in doc.paragraphs:
        p.text = p.text.replace("[INTERVENANT]", intervenant)\
                       .replace("[SOCIETE]", societe)\
                       .replace("[NOM_CONTACT]", contact)\
                       .replace("[DUREE_INTER]", duree_inter)\
                       .replace("[DATE_DEB]", date_deb)\
                       .replace("[DATE_FIN]", date_fin)\
                       .replace("[OBJ_PRESTA]", obj_presta)\
                       .replace("[CONTENU_INTERVENTION]", contenu_intervention)\
                       .replace("[NUM_MISSION]", num_mission)
    doc_path = f"bon_intervention_{num_mission}.docx"
    doc.save(doc_path)
    pdf_path = doc_path.replace(".docx", ".pdf")
    convert(doc_path, pdf_path)

    conn = connect_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO bon_intervention (intervenant, client_id, contact_id, duree_inter, date_deb, date_fin, obj_presta, contenu_intervention, num_mission)
        VALUES (%s, (SELECT id FROM clients WHERE societe=%s), (SELECT id FROM contact WHERE nom=%s), %s, %s, %s, %s, %s, %s)
    """, (intervenant, societe, contact, duree_inter, date_deb, date_fin, obj_presta, contenu_intervention, num_mission))
    conn.commit()
    cur.close()
    conn.close()

    return pdf_path

def interface():
    with gr.Blocks() as demo:
        clients = get_clients()
        intervenant = gr.Textbox(label="Intervenant")
        societe = gr.Dropdown(label="Société", choices=clients)
        contact = gr.Dropdown(label="Contact", choices=[])
        duree = gr.Textbox(label="Durée")
        date_deb = gr.Textbox(label="Date début")
        date_fin = gr.Textbox(label="Date fin")
        obj = gr.Textbox(label="Objectif")
        contenu = gr.Textbox(label="Contenu")
        mission = gr.Textbox(label="Numéro de mission")

        def update_contacts(soc):
            return gr.update(choices=get_contacts(soc))

        societe.change(update_contacts, inputs=societe, outputs=contact)

        bouton = gr.Button("Générer PDF")
        bouton.click(generate_document, inputs=[
            intervenant, societe, contact, duree, date_deb, date_fin, obj, contenu, mission
        ], outputs="file")

    demo.launch()

if __name__ == "__main__":
    interface()
