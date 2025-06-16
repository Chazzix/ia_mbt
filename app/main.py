import gradio as gr
import psycopg2
from docxtpl import DocxTemplate
import os
from datetime import datetime
from dotenv import load_dotenv
from email.message import EmailMessage
import mimetypes
import requests
import json
from msal import ConfidentialClientApplication

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

def get_graph_token():
    client_id = os.getenv("MS_CLIENT_ID")
    client_secret = os.getenv("MS_CLIENT_SECRET")
    tenant_id = os.getenv("MS_TENANT_ID")
    scope = [os.getenv("MS_SCOPE")]

    app = ConfidentialClientApplication(
        client_id,
        authority=f"https://login.microsoftonline.com/{tenant_id}",
        client_credential=client_secret
    )

    result = app.acquire_token_silent(scope, account=None)
    if not result:
        result = app.acquire_token_for_client(scopes=scope)

    if "access_token" in result:
        return result["access_token"]
    else:
        raise Exception(f"Erreur d'authentification : {result.get('error_description')}")

def generate_docxtpl(intervenant, mail_intervenant, societe, contact, mail_contact, duree_inter, date_deb, date_fin, obj_presta, contenu_intervention, num_mission):
    template_path = "template_bon-intervention.docx"
    doc = DocxTemplate(template_path)

    context = {
        "INTERVENANT": intervenant,
        "MAIL_INTERVENANT": mail_intervenant,
        "SOCIETE": societe,
        "NOM_CONTACT": contact,
        "MAIL_CONTACT": mail_contact,
        "DUREE_INTER": duree_inter,
        "DATE_DEB": date_deb,
        "DATE_FIN": date_fin,
        "OBJ_PRESTA": obj_presta,
        "CONTENU_INTERVENTION": contenu_intervention,
        "NUM_MISSION": num_mission if num_mission.strip() else "PRXXXX-XX",
        "DATE": datetime.today().strftime("%d/%m/%Y")
    }

    output_dir = "./shared_files"
    output_docx = f"{output_dir}/BI_{societe.replace(' ', '_')}.docx"
    doc.render(context)
    doc.save(output_docx)

    os.system(f'libreoffice --headless --convert-to pdf "{output_docx}" --outdir {output_dir}')
    os.remove(output_docx)

    return output_docx.replace(".docx", ".pdf")

def check_onedrive_folder_exists(folder_path):
    access_token = get_graph_token()
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    url = f"https://graph.microsoft.com/v1.0/me/drive/root:/{folder_path}"
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        print(f"📁 Dossier trouvé : {folder_path}")
        return True
    elif response.status_code == 404:
        print(f"⚠️ Dossier introuvable : {folder_path}")
        return False
    else:
        print(f"❌ Erreur lors de la vérification du dossier : {response.status_code} - {response.text}")
        return False


def upload_to_onedrive(file_path, societe):
    access_token = get_graph_token()
    file_name = os.path.basename(file_path)
    folder_path = f"01-Clients/{societe}"
    upload_url = f"https://graph.microsoft.com/v1.0/me/drive/root:/{folder_path}/{file_name}:/content"

    with open(file_path, "rb") as f:
        response = requests.put(
            upload_url,
            headers={"Authorization": f"Bearer {access_token}"},
            data=f
        )

    if response.status_code in [200, 201]:
        print(f"✅ Fichier uploadé sur OneDrive : {file_name}")
    else:
        print(f"❌ Échec de l'upload : {response.status_code} - {response.text}")

def prepare_outlook_email(mail_contact, mail_intervenant, pdf_path, societe):
    cc_list = get_all_intervenant_emails(exclude_email=mail_intervenant)

    msg = EmailMessage()
    msg["Subject"] = f"MBT/{societe} - Bon d'intervention"
    msg["From"] = mail_intervenant
    msg["To"] = mail_contact
    if cc_list:
        msg["Cc"] = ", ".join(cc_list)
    msg["X-Unsent"] = "1"   # Indique à Outlook que c'est un brouillon

    # Corps du message
    text_body = "Bonjour,\n\nVeuillez trouver ci-joint le bon d'intervention.\n\n"
    html_body = """\
    <html>
        <body>
            <p>Bonjour,<br><br>
                Veuillez trouver ci-joint le bon d'intervention.<br><br>
            </p>
        </body>
    <html>
    """
    msg.set_content(text_body)
    msg.add_attachment(html_body, subtype='html')

    # Ajout du PDF
    with open(pdf_path, "rb") as f:
        file_data = f.read()
        file_name = os.path.basename(pdf_path)
        mime_type, _ = mimetypes.guess_type(file_name)
        if mime_type:
            maintype, subtype = mime_type.split("/")
        else:
                maintype, subtype = "application", "octet-stream"
        msg.add_attachment(file_data, maintype=maintype, subtype=subtype, filename=file_name)
    
    # Save du fichier EML
    output_dir = "./shared_files"
    os.makedirs(output_dir, exist_ok=True)
    eml_path = os.path.join(output_dir, f"email_{file_name.replace('.pdf', '.eml')}")

    with open(eml_path, "wb") as f:
        f.write(bytes(msg))

    print(f"Fichier .eml généré : {eml_path}")
    return eml_path

def generate_with_mail(intervenant, societe, contact, duree, date_deb, date_fin, obj, contenu, mission):
    mail_intervenant = get_mail_intervenant(intervenant)
    mail_contact = get_mail_contact(contact)
    pdf_path = generate_docxtpl(intervenant, mail_intervenant, societe, contact, mail_contact, duree, date_deb, date_fin, obj, contenu, mission)
    eml_path = prepare_outlook_email(mail_contact, mail_intervenant, pdf_path, societe)
    upload_to_onedrive(pdf_path, societe)
    upload_to_onedrive(eml_path, societe)
    return pdf_path, eml_path

def interface():
    clients = get_clients()
    intervenants = get_intervenants()

    with gr.Blocks() as demo:
        with gr.Tab("Générer Bon d'Intervention"):
            intervenant = gr.Dropdown(label="Intervenant", choices=intervenants)
            societe = gr.Dropdown(label="Société", choices=clients)
            contact = gr.Dropdown(label="Contact", choices=[])
            duree = gr.Textbox(label="Durée (uniquement les chiffres)")
            date_deb = gr.Textbox(label="Date début (dd/mm/YYYY)")
            date_fin = gr.Textbox(label="Date fin (dd/mm/YYYY)")
            obj = gr.Textbox(label="Objectif")
            contenu = gr.Textbox(label="Contenu")
            mission = gr.Textbox(label="Numéro de mission")
            fichier_pdf = gr.File(label="Bon d'intervention (PDF)")
            fichier_eml = gr.File(label="Email prêt à envoyer (.eml)")


            def update_contacts(soc):
                return gr.update(choices=get_contacts(soc))
            societe.change(update_contacts, inputs=societe, outputs=contact)

            gr.Button("Générer PDF").click(generate_with_mail, 
                inputs=[intervenant, societe, contact, duree, date_deb, date_fin, obj, contenu, mission],
                outputs=[fichier_pdf, fichier_eml])

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
