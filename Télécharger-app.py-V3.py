
import streamlit as st
import json
import os
from datetime import datetime
from io import BytesIO

# ===================== CONFIG =====================
st.set_page_config(
    page_title="MADOU GRC AUTOPILOT",
    page_icon="🛡️",
    layout="wide"
)

# ===================== GOOGLE DRIVE SYNC =====================
# Tentative de connexion Drive - si secrets présents
DRIVE_AVAILABLE = False
drive_service = None

try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload

    if "GDRIVE_CREDENTIALS_JSON" in st.secrets and "GDRIVE_FOLDER_ID" in st.secrets:
        creds_dict = dict(st.secrets["GDRIVE_CREDENTIALS_JSON"])
        SCOPES = ['https://www.googleapis.com/auth/drive']
        creds = service_account.Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        drive_service = build('drive', 'v3', credentials=creds)
        GDRIVE_FOLDER_ID = st.secrets["GDRIVE_FOLDER_ID"]
        DRIVE_AVAILABLE = True
except Exception as e:
    DRIVE_AVAILABLE = False
    drive_error = str(e)

def save_to_drive(data_dict, filename="knowledge_base.json"):
    """Sauvegarde la base dans Drive"""
    if not DRIVE_AVAILABLE:
        return False, "Drive non configuré"
    try:
        # Chercher si fichier existe déjà
        query = f"name='{filename}' and '{GDRIVE_FOLDER_ID}' in parents and trashed=false"
        results = drive_service.files().list(q=query, fields="files(id, name)").execute()
        files = results.get('files', [])

        json_bytes = json.dumps(data_dict, ensure_ascii=False, indent=2).encode('utf-8')
        media = MediaIoBaseUpload(BytesIO(json_bytes), mimetype='application/json')

        if files:
            # Update
            file_id = files[0]['id']
            drive_service.files().update(fileId=file_id, media_body=media).execute()
            return True, "Mis à jour dans Drive"
        else:
            # Create
            file_metadata = {'name': filename, 'parents': [GDRIVE_FOLDER_ID]}
            drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
            return True, "Créé dans Drive"
    except Exception as ex:
        return False, str(ex)

def load_from_drive(filename="knowledge_base.json"):
    """Charge la base depuis Drive"""
    if not DRIVE_AVAILABLE:
        return None
    try:
        query = f"name='{filename}' and '{GDRIVE_FOLDER_ID}' in parents and trashed=false"
        results = drive_service.files().list(q=query, fields="files(id, name)").execute()
        files = results.get('files', [])
        if not files:
            return None
        file_id = files[0]['id']
        request = drive_service.files().get_media(fileId=file_id)
        fh = BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
        fh.seek(0)
        return json.loads(fh.read().decode('utf-8'))
    except:
        return None

# ===================== SESSION STATE =====================
if 'knowledge' not in st.session_state:
    # Essayer de charger depuis Drive au démarrage
    loaded = load_from_drive() if DRIVE_AVAILABLE else None
    st.session_state.knowledge = loaded if loaded else {}

if 'drive_loaded' not in st.session_state:
    st.session_state.drive_loaded = False
    if DRIVE_AVAILABLE and not st.session_state.knowledge:
        # Si vide, re-essaye une fois
        from_drive = load_from_drive()
        if from_drive:
            st.session_state.knowledge = from_drive

# ===================== UI =====================
st.sidebar.title("🧠 NOURRIR L'AGENT - BOUTON UNIQUE")
st.sidebar.write("L'agent accepte tout et classe tout seul")

# Drive status
if DRIVE_AVAILABLE:
    st.sidebar.success(f"✅ Drive connecté - Sync auto active\n{GDRIVE_FOLDER_ID[:15]}...")
else:
    st.sidebar.warning("⚠️ Drive non connecté - Mode local")
    if 'drive_error' in locals():
        st.sidebar.caption(f"Erreur: {drive_error}")

st.sidebar.divider()

uploaded_file = st.sidebar.file_uploader(
    "Glisse ici : Normes, Rapports d'audit, Modèles CC, Offres Tech/Fin, Templates",
    type=['pdf','docx','xlsx','pptx','txt','json'],
    help="200MB par fichier"
)

st.sidebar.markdown("---")
doc_count = len(st.session_state.knowledge)
st.sidebar.markdown(f"📚 **Base de connaissances ({doc_count} docs)**")

# Liste des docs
if st.session_state.knowledge:
    for name, data in st.session_state.knowledge.items():
        with st.sidebar.expander(f"{name} - {data.get('type','doc')}"):
            st.json(data)

# Upload logic
if uploaded_file is not None:
    try:
        file_name = uploaded_file.name
        # Détection simple du type
        lower = file_name.lower()
        if "norme" in lower or "iso" in lower or "nca" in lower:
            type_detected = "Norme"
        elif "rapport" in lower or "audit" in lower:
            type_detected = "Rapport Audit"
        elif "offre" in lower:
            type_detected = "Offre"
        elif "modele" in lower or "template" in lower:
            type_detected = "Modèle"
        else:
            type_detected = "Document"

        new_entry = {
            "name": file_name,
            "type": type_detected,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "size": uploaded_file.size,
            "content_preview": f"Fichier {file_name} - {uploaded_file.size} bytes"
        }

        st.session_state.knowledge[file_name] = new_entry
        
        # Sauvegarde auto Drive
        if DRIVE_AVAILABLE:
            ok, msg = save_to_drive(st.session_state.knowledge)
            if ok:
                st.sidebar.success(f"✅ {file_name} classé en {type_detected} + Sauvé dans Drive")
            else:
                st.sidebar.error(f"Sauvé local mais erreur Drive: {msg}")
        else:
            st.sidebar.success(f"✅ {file_name} classé en {type_detected} (local)")

    except Exception as e:
        st.sidebar.error(f"Erreur: {e}")

st.sidebar.divider()
st.sidebar.subheader("🔌 API Externes (Optionnel)")
openai_key = st.sidebar.text_input("OpenAI / Groq API (pour IA générative)", type="password", placeholder="sk-...")
shodan_key = st.sidebar.text_input("Shodan / VirusTotal API", type="password", placeholder="API Key...")
jira_webhook = st.sidebar.text_input("Jira / Notion Webhook", placeholder="https://...")

# ===================== MAIN =====================
st.title("🛡️ MADOU GRC AUTOPILOT")

if not st.session_state.knowledge:
    st.info("👈 Commence par nourrir l'agent à gauche. Glisse un document, il sera auto-classé et sauvegardé dans ton Drive.")
    if DRIVE_AVAILABLE:
        st.success(f"Drive connecté: https://drive.google.com/drive/folders/{GDRIVE_FOLDER_ID}")
else:
    st.success(f"Agent nourri avec {len(st.session_state.knowledge)} documents")

    col1, col2, col3 = st.columns(3)
    col1.metric("Documents", len(st.session_state.knowledge))
    col2.metric("Drive", "Connecté ✅" if DRIVE_AVAILABLE else "Local")
    col3.metric("Dernier ajout", list(st.session_state.knowledge.values())[-1]['date'] if st.session_state.knowledge else "-")

    st.subheader("📊 Base de connaissances")
    st.json(st.session_state.knowledge)

    if st.button("🗑️ Vider la base (local + Drive)"):
        st.session_state.knowledge = {}
        if DRIVE_AVAILABLE:
            save_to_drive({})
        st.rerun()

    if st.button("🔄 Forcer Sync Drive"):
        if DRIVE_AVAILABLE:
            ok, msg = save_to_drive(st.session_state.knowledge)
            st.success(msg) if ok else st.error(msg)
            reloaded = load_from_drive()
            if reloaded:
                st.session_state.knowledge = reloaded
                st.success("Rechargé depuis Drive")
        else:
            st.warning("Drive non configuré")

st.markdown("---")
st.caption("V3.2 - Cloud Memory - MADOU AUTOPILOT - Drive auto-sync actif")
