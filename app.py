
import streamlit as st
import json
import base64
import requests
from datetime import datetime
import time

st.set_page_config(page_title="MADOU GRC AUTOPILOT", page_icon="🛡️", layout="wide")

GITHUB_AVAILABLE = False
GITHUB_TOKEN = None
GITHUB_REPO = None
GITHUB_BRANCH = "main"

try:
    if "GITHUB_TOKEN" in st.secrets:
        GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
        GITHUB_REPO = st.secrets.get("GITHUB_REPO", "bawaleroger/MADOU_GRC_AUTOPILOT")
        GITHUB_BRANCH = st.secrets.get("GITHUB_BRANCH", "main")
        if GITHUB_TOKEN and GITHUB_REPO:
            GITHUB_AVAILABLE = True
except Exception as e:
    st.sidebar.error(f"Erreur secrets: {e}")

def save_to_github(data_dict, filename="knowledge_base.json"):
    if not GITHUB_AVAILABLE:
        return False, "GitHub non configuré"
    try:
        url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{filename}"
        headers = {"Authorization": f"Bearer {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
        r = requests.get(url, headers=headers)
        
        json_bytes = json.dumps(data_dict, ensure_ascii=False, indent=2).encode('utf-8')
        content_b64 = base64.b64encode(json_bytes).decode('utf-8')
        
        payload = {
            "message": f"brain: {len(data_dict)} docs {datetime.now().strftime('%H:%M:%S')}",
            "content": content_b64,
            "branch": GITHUB_BRANCH
        }
        if r.status_code == 200:
            payload["sha"] = r.json()["sha"]
        
        res = requests.put(url, headers=headers, json=payload)
        
        if res.status_code in [200, 201]:
            return True, f"Sauvé sur GitHub ✅ ({len(data_dict)} docs) - Fichier mis à jour"
        else:
            return False, f"GitHub {res.status_code}: {res.text[:500]}"
    except Exception as ex:
        return False, str(ex)

def load_from_github(filename="knowledge_base.json"):
    """V3.6: API FIRST (toujours frais) puis RAW en fallback"""
    if not GITHUB_AVAILABLE:
        return None, "GitHub non configuré"
    
    # Methode 1 PRIORITAIRE: API GitHub (toujours à jour, pas de cache)
    try:
        url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{filename}?ref={GITHUB_BRANCH}&t={int(time.time())}"
        headers = {"Authorization": f"Bearer {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json", "Cache-Control": "no-cache"}
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code == 200:
            content_data = r.json()
            # Gerer le cas ou fichier vide
            if "content" not in content_data:
                return {}, "Fichier vide"
            content = base64.b64decode(content_data["content"]).decode('utf-8')
            if not content.strip():
                return {}, "Fichier vide"
            data = json.loads(content)
            return data, f"Chargé via API fraîche ({len(data)} docs) ✅"
        elif r.status_code == 404:
            api_404 = True
        else:
            api_error = f"API {r.status_code}"
    except Exception as ex:
        api_error = str(ex)
        api_404 = False

    # Methode 2 FALLBACK: RAW (peut etre en cache 5 min)
    try:
        raw_url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/{GITHUB_BRANCH}/{filename}?t={int(time.time())}"
        r = requests.get(raw_url, timeout=10)
        if r.status_code == 200 and r.text.strip():
            data = json.loads(r.text)
            return data, f"Chargé via RAW cache ({len(data)} docs) - peut etre en retard de 5min"
        else:
            return {}, "Base vide - premier lancement"
    except Exception as e:
        return None, f"Erreur API:{api_error} RAW:{e}"

# --- INIT ---
if 'knowledge' not in st.session_state:
    st.session_state.knowledge = {}
    st.session_state.load_msg = "Initialisation..."
    st.session_state.last_load_ok = False
    
    if GITHUB_AVAILABLE:
        loaded, msg = load_from_github()
        st.session_state.load_msg = msg
        if loaded is not None:
            st.session_state.knowledge = loaded
            st.session_state.last_load_ok = True
            if len(loaded) == 0:
                st.session_state.load_msg = "Base vide - glisse tes docs"

# UI
st.sidebar.title("🧠 NOURRIR L'AGENT - BOUTON UNIQUE")

if GITHUB_AVAILABLE:
    st.sidebar.success(f"✅ GitHub Memory active\n{GITHUB_REPO}")
    st.sidebar.caption(f"✅ {st.session_state.get('load_msg','')}")
else:
    st.sidebar.warning("⚠️ GitHub non connecté")

st.sidebar.divider()
uploaded_files = st.sidebar.file_uploader("Glisse ici : Normes, Rapports, Modeles, Offres", type=['pdf','docx','xlsx','pptx','txt','json'], accept_multiple_files=True)

if uploaded_files:
    for uploaded_file in uploaded_files:
        key = f"{uploaded_file.name}_{uploaded_file.size}"
        if 'processed_files' not in st.session_state:
            st.session_state.processed_files = set()
        if key in st.session_state.processed_files:
            continue
            
        file_name = uploaded_file.name
        lower = file_name.lower()
        type_detected = "Rapport Audit" if "audit" in lower else "Norme" if "norme" in lower or "iso" in lower else "Document"
        
        st.session_state.knowledge[file_name] = {
            "name": file_name,
            "type": type_detected,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "size": uploaded_file.size
        }
        st.session_state.processed_files.add(key)
    
    # Sauvegarde une seule fois apres avoir ajouté tous les fichiers
    if GITHUB_AVAILABLE:
        ok, msg = save_to_github(st.session_state.knowledge)
        if ok:
            st.sidebar.success(f"✅ {len(uploaded_files)} fichier(s) -> {msg}")
        else:
            st.sidebar.error(f"❌ {msg}")

st.title("🛡️ MADOU GRC AUTOPILOT V3.6 - API FIRST")
st.caption("V3.6 - Persistance 100% - Charge via API fraîche, pas de cache")

if st.session_state.knowledge:
    st.subheader(f"📚 Base persistante ({len(st.session_state.knowledge)} docs) - Reste après F5 ✅")
    st.json(st.session_state.knowledge)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Forcer Sync GitHub"):
            ok, msg = save_to_github(st.session_state.knowledge)
            if ok:
                st.success(msg)
                st.balloons()
            else:
                st.error(msg)
    with col2:
        if st.button("🔄 Recharger depuis GitHub (API fraîche)"):
            loaded, msg = load_from_github()
            if loaded is not None:
                st.session_state.knowledge = loaded
                st.success(f"✅ {msg}")
                time.sleep(0.5)
                st.rerun()
            else:
                st.error(msg)
else:
    st.warning("Base vide après F5 ? Clique sur 'Recharger depuis GitHub' - Le cache RAW met 5 min, l'API est instantanée")
    if GITHUB_AVAILABLE:
        if st.button("🔄 Recharger maintenant (API)"):
            loaded, msg = load_from_github()
            if loaded is not None:
                st.session_state.knowledge = loaded
                st.success(msg)
                st.rerun()

st.divider()
st.caption("V3.6 - Fix cache GitHub - Utilise API, pas RAW")
