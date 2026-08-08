
import streamlit as st
import json
from datetime import datetime
from io import BytesIO

st.set_page_config(page_title="MADOU GRC AUTOPILOT", page_icon="🛡️", layout="wide")

DRIVE_AVAILABLE = False
drive_service = None
GDRIVE_FOLDER_ID = None
MY_OWNER_EMAIL = None

try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload

    if "GDRIVE_CREDENTIALS_JSON" in st.secrets and "GDRIVE_FOLDER_ID" in st.secrets:
        creds_dict = dict(st.secrets["GDRIVE_CREDENTIALS_JSON"])
        creds = service_account.Credentials.from_service_account_info(
            creds_dict, 
            scopes=['https://www.googleapis.com/auth/drive']
        )
        drive_service = build('drive', 'v3', credentials=creds)
        GDRIVE_FOLDER_ID = st.secrets["GDRIVE_FOLDER_ID"]
        # Ton Gmail perso qui possede le dossier - OBLIGATOIRE pour fix quota
        MY_OWNER_EMAIL = st.secrets.get("MY_GMAIL", None)
        DRIVE_AVAILABLE = True
except Exception as e:
    DRIVE_AVAILABLE = False
    drive_error = str(e)

def save_to_drive(data_dict, filename="knowledge_base.json"):
    if not DRIVE_AVAILABLE:
        return False, "Drive non configuré"
    try:
        # 1. Chercher fichier existant
        query = f"name='{filename}' and '{GDRIVE_FOLDER_ID}' in parents and trashed=false"
        results = drive_service.files().list(q=query, fields="files(id, name)", supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
        files = results.get('files', [])

        json_bytes = json.dumps(data_dict, ensure_ascii=False, indent=2).encode('utf-8')
        media = MediaIoBaseUpload(BytesIO(json_bytes), mimetype='application/json')

        if files:
            file_id = files[0]['id']
            drive_service.files().update(fileId=file_id, media_body=media, supportsAllDrives=True).execute()
            return True, "Mis à jour dans Drive"
        else:
            # 2. Créer fichier - le SA devient owner temporairement
            file_metadata = {'name': filename, 'parents': [GDRIVE_FOLDER_ID]}
            created = drive_service.files().create(body=file_metadata, media_body=media, fields='id', supportsAllDrives=True).execute()
            file_id = created.get('id')
            
            # 3. TRANSFERT DE PROPRIETE vers ton Gmail perso -> FIX QUOTA
            if MY_OWNER_EMAIL:
                try:
                    drive_service.permissions().create(
                        fileId=file_id,
                        body={'type': 'user', 'role': 'owner', 'emailAddress': MY_OWNER_EMAIL},
                        transferOwnership=True,
                        supportsAllDrives=True
                    ).execute()
                except Exception as perm_err:
                    # Si transfert echoue, on laisse mais on previent
                    return True, f"Créé mais transfert owner échoué (ajoute {MY_OWNER_EMAIL} en owner manuel): {perm_err}"
            
            return True, "Créé dans Drive + transféré à toi"
    except Exception as ex:
        return False, str(ex)

def load_from_drive(filename="knowledge_base.json"):
    if not DRIVE_AVAILABLE:
        return None
    try:
        query = f"name='{filename}' and '{GDRIVE_FOLDER_ID}' in parents and trashed=false"
        results = drive_service.files().list(q=query, fields="files(id, name)", supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
        files = results.get('files', [])
        if not files:
            return None
        file_id = files[0]['id']
        request = drive_service.files().get_media(fileId=file_id, supportsAllDrives=True)
        fh = BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
        fh.seek(0)
        return json.loads(fh.read().decode('utf-8'))
    except:
        return None

if 'knowledge' not in st.session_state:
    loaded = load_from_drive() if DRIVE_AVAILABLE else None
    st.session_state.knowledge = loaded if loaded else {}

st.sidebar.title("🧠 NOURRIR L'AGENT - BOUTON UNIQUE")
st.sidebar.write("L'agent accepte tout et classe tout seul")

if DRIVE_AVAILABLE:
    st.sidebar.success(f"✅ Drive connecté - Sync auto active\n{GDRIVE_FOLDER_ID[:15]}...")
    if MY_OWNER_EMAIL:
        st.sidebar.caption(f"Owner: {MY_OWNER_EMAIL}")
    else:
        st.sidebar.error("⚠️ Ajoute MY_GMAIL dans Secrets pour fix quota Gmail perso")
else:
    st.sidebar.warning("⚠️ Drive non connecté")

st.sidebar.divider()
uploaded_file = st.sidebar.file_uploader("Glisse ici : Normes, Rapports, Modeles, Offres", type=['pdf','docx','xlsx','pptx','txt','json'])

if uploaded_file is not None:
    file_name = uploaded_file.name
    lower = file_name.lower()
    if "norme" in lower or "iso" in lower:
        type_detected = "Norme"
    elif "rapport" in lower or "audit" in lower:
        type_detected = "Rapport Audit"
    else:
        type_detected = "Document"

    new_entry = {
        "name": file_name,
        "type": type_detected,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "size": uploaded_file.size,
    }
    st.session_state.knowledge[file_name] = new_entry
    if DRIVE_AVAILABLE:
        ok, msg = save_to_drive(st.session_state.knowledge)
        if ok:
            st.sidebar.success(f"✅ {file_name} -> {msg}")
        else:
            st.sidebar.error(f"Erreur Drive: {msg}")
            st.sidebar.code(msg)
    else:
        st.sidebar.success(f"✅ {file_name} local")

st.title("🛡️ MADOU GRC AUTOPILOT V3.2.2 - Fix Gmail Perso")
if st.session_state.knowledge:
    st.json(st.session_state.knowledge)
    if st.button("Forcer Sync Drive"):
        ok, msg = save_to_drive(st.session_state.knowledge)
        st.success(msg) if ok else st.error(msg)
else:
    st.info("Glisse un document à gauche")

st.caption("V3.2.2 - Cloud Memory - Fix quota Gmail perso - transfert ownership")
