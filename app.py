
import streamlit as st
import json
from datetime import datetime
from io import BytesIO
import uuid

st.set_page_config(page_title="MADOU GRC AUTOPILOT", page_icon="🛡️", layout="wide")

DRIVE_AVAILABLE = False
drive_service = None
GDRIVE_FOLDER_ID = None
MY_OWNER_EMAIL = None
SHARED_DRIVE_ID = None

try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload

    if "GDRIVE_CREDENTIALS_JSON" in st.secrets:
        creds_dict = dict(st.secrets["GDRIVE_CREDENTIALS_JSON"])
        creds = service_account.Credentials.from_service_account_info(
            creds_dict, 
            scopes=['https://www.googleapis.com/auth/drive']
        )
        drive_service = build('drive', 'v3', credentials=creds)
        GDRIVE_FOLDER_ID = st.secrets.get("GDRIVE_FOLDER_ID", None)
        MY_OWNER_EMAIL = st.secrets.get("MY_GMAIL", "bawaleroger@gmail.com")
        DRIVE_AVAILABLE = True
except Exception as e:
    DRIVE_AVAILABLE = False
    drive_error = str(e)

def get_or_create_shared_drive():
    """Cree ou recupere un Shared Drive pour contourner quota Gmail perso"""
    global SHARED_DRIVE_ID
    try:
        # 1. Lister les shared drives existants
        drives = drive_service.drives().list(pageSize=20).execute()
        for d in drives.get('drives', []):
            if "MADOU_GRC" in d.get('name',''):
                SHARED_DRIVE_ID = d['id']
                return SHARED_DRIVE_ID
        
        # 2. Creer un nouveau Shared Drive (seule facon pour SA d'avoir du quota)
        request_id = str(uuid.uuid4())
        body = {"name": "MADOU_GRC_AUTOPILOT_SHARED"}
        created = drive_service.drives().create(body=body, requestId=request_id).execute()
        SHARED_DRIVE_ID = created.get('id')
        
        # 3. Ajouter ton Gmail comme manager du Shared Drive
        if MY_OWNER_EMAIL and SHARED_DRIVE_ID:
            try:
                drive_service.permissions().create(
                    fileId=SHARED_DRIVE_ID,
                    body={'type': 'user', 'role': 'organizer', 'emailAddress': MY_OWNER_EMAIL},
                    supportsAllDrives=True,
                    useDomainAdminAccess=False
                ).execute()
            except:
                pass
        
        return SHARED_DRIVE_ID
    except Exception as ex:
        st.sidebar.error(f"Erreur creation Shared Drive: {ex}")
        return None

def save_to_drive(data_dict, filename="knowledge_base.json"):
    if not DRIVE_AVAILABLE:
        return False, "Drive non configuré"
    
    # D'abord essayer le folder classique
    target_folder = GDRIVE_FOLDER_ID
    
    try:
        # Tenter sauvegarde normale
        if target_folder:
            query = f"name='{filename}' and '{target_folder}' in parents and trashed=false"
            try:
                results = drive_service.files().list(q=query, fields="files(id, name)", supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
                files = results.get('files', [])
                json_bytes = json.dumps(data_dict, ensure_ascii=False, indent=2).encode('utf-8')
                media = MediaIoBaseUpload(BytesIO(json_bytes), mimetype='application/json')

                if files:
                    file_id = files[0]['id']
                    drive_service.files().update(fileId=file_id, media_body=media, supportsAllDrives=True).execute()
                    return True, f"Mis à jour dans {target_folder[:10]}..."

                file_metadata = {'name': filename, 'parents': [target_folder]}
                created = drive_service.files().create(body=file_metadata, media_body=media, fields='id', supportsAllDrives=True).execute()
                file_id = created.get('id')
                
                # Transfert ownership vers toi
                if MY_OWNER_EMAIL:
                    try:
                        drive_service.permissions().create(
                            fileId=file_id,
                            body={'type': 'user', 'role': 'owner', 'emailAddress': MY_OWNER_EMAIL},
                            transferOwnership=True,
                            supportsAllDrives=True
                        ).execute()
                    except:
                        pass
                return True, "Créé dans Mon Drive (quota perso contourné)"
            except Exception as ex:
                if "storageQuotaExceeded" in str(ex) or "Service Accounts do not have storage quota" in str(ex):
                    # FALLBACK : passer en Shared Drive
                    st.warning("Quota Gmail perso detecte -> bascule auto vers Drive partagé...")
                    shared_id = get_or_create_shared_drive()
                    if not shared_id:
                        return False, f"Echec Shared Drive: {ex}"
                    target_folder = shared_id
                else:
                    return False, str(ex)
        
        # Fallback Shared Drive
        if not target_folder:
            target_folder = get_or_create_shared_drive()
        
        if not target_folder:
            return False, "Pas de dossier cible"
            
        query = f"name='{filename}' and '{target_folder}' in parents and trashed=false"
        results = drive_service.files().list(q=query, fields="files(id, name)", supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
        files = results.get('files', [])
        json_bytes = json.dumps(data_dict, ensure_ascii=False, indent=2).encode('utf-8')
        media = MediaIoBaseUpload(BytesIO(json_bytes), mimetype='application/json')

        if files:
            file_id = files[0]['id']
            drive_service.files().update(fileId=file_id, media_body=media, supportsAllDrives=True).execute()
            return True, f"Mis à jour dans Shared Drive {target_folder[:8]}..."
        else:
            file_metadata = {'name': filename, 'parents': [target_folder]}
            drive_service.files().create(body=file_metadata, media_body=media, fields='id', supportsAllDrives=True).execute()
            return True, f"Créé dans Shared Drive - FINI ! Visible dans drive.google.com > Drives partagés"
            
    except Exception as ex:
        return False, str(ex)

def load_from_drive(filename="knowledge_base.json"):
    if not DRIVE_AVAILABLE:
        return None
    try:
        # Essayer d'abord Mon Drive
        if GDRIVE_FOLDER_ID:
            query = f"name='{filename}' and '{GDRIVE_FOLDER_ID}' in parents and trashed=false"
            results = drive_service.files().list(q=query, fields="files(id, name)", supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
            files = results.get('files', [])
            if files:
                file_id = files[0]['id']
                request = drive_service.files().get_media(fileId=file_id, supportsAllDrives=True)
                fh = BytesIO()
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while not done:
                    status, done = downloader.next_chunk()
                fh.seek(0)
                return json.loads(fh.read().decode('utf-8'))
        # Essayer Shared Drives
        drives = drive_service.drives().list(pageSize=20).execute()
        for d in drives.get('drives', []):
            if "MADOU_GRC" in d.get('name',''):
                sd_id = d['id']
                query = f"name='{filename}' and '{sd_id}' in parents and trashed=false"
                results = drive_service.files().list(q=query, fields="files(id, name)", supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
                files = results.get('files', [])
                if files:
                    file_id = files[0]['id']
                    request = drive_service.files().get_media(fileId=file_id, supportsAllDrives=True)
                    fh = BytesIO()
                    downloader = MediaIoBaseDownload(fh, request)
                    done = False
                    while not done:
                        status, done = downloader.next_chunk()
                    fh.seek(0)
                    return json.loads(fh.read().decode('utf-8'))
        return None
    except:
        return None

if 'knowledge' not in st.session_state:
    loaded = load_from_drive() if DRIVE_AVAILABLE else None
    st.session_state.knowledge = loaded if loaded else {}

st.sidebar.title("🧠 NOURRIR L'AGENT - BOUTON UNIQUE")
if DRIVE_AVAILABLE:
    st.sidebar.success(f"✅ Drive connecté - Sync auto active")
    st.sidebar.caption(f"Owner: {MY_OWNER_EMAIL}")
    # Afficher shared drive si existe
    try:
        drives = drive_service.drives().list(pageSize=5).execute()
        for d in drives.get('drives', []):
            if "MADOU_GRC" in d.get('name',''):
                st.sidebar.info(f"📁 Shared Drive: {d['name']}")
    except:
        pass
else:
    st.sidebar.warning("⚠️ Drive non connecté")

st.sidebar.divider()
uploaded_file = st.sidebar.file_uploader("Glisse ici : Normes, Rapports, Modeles, Offres", type=['pdf','docx','xlsx','pptx','txt','json'])

if uploaded_file is not None:
    file_name = uploaded_file.name
    lower = file_name.lower()
    type_detected = "Rapport Audit" if "audit" in lower else "Norme" if "norme" in lower or "iso" in lower else "Document"
    new_entry = {"name": file_name, "type": type_detected, "date": datetime.now().strftime("%Y-%m-%d %H:%M"), "size": uploaded_file.size}
    st.session_state.knowledge[file_name] = new_entry
    if DRIVE_AVAILABLE:
        ok, msg = save_to_drive(st.session_state.knowledge)
        if ok:
            st.sidebar.success(f"✅ {file_name} -> {msg}")
        else:
            st.sidebar.error(f"Erreur Drive: {msg}")
            st.sidebar.code(msg[:500])
    else:
        st.sidebar.success(f"✅ {file_name} local")

st.title("🛡️ MADOU GRC AUTOPILOT V3.3 - Fix Definitif Gmail Perso")
if st.session_state.knowledge:
    st.json(st.session_state.knowledge)
    if st.button("🔄 Forcer Sync Drive (vers Shared Drive)"):
        ok, msg = save_to_drive(st.session_state.knowledge)
        if ok:
            st.success(msg)
            st.balloons()
        else:
            st.error(msg)
else:
    st.info("Glisse un document à gauche - il sera sauvé dans Drive partagé auto-créé")

st.caption("V3.3 - Cloud Memory - Shared Drive auto-creation - Fix quota SA Gmail perso")
