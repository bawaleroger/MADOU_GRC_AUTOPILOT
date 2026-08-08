
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
            "message": f"🧠 update {datetime.now().strftime('%Y-%m-%d %H:%M')} - {len(data_dict)} docs",
            "content": content_b64,
            "branch": GITHUB_BRANCH
        }
        if r.status_code == 200:
            payload["sha"] = r.json()["sha"]
        
        res = requests.put(url, headers=headers, json=payload)
        
        if res.status_code in [200, 201]:
            # Attendre que GitHub indexe (evite le vide au refresh)
            time.sleep(1)
            return True, f"Sauvé sur GitHub ✅ ({len(data_dict)} docs)"
        else:
            return False, f"GitHub {res.status_code}: {res.text[:500]}"
    except Exception as ex:
        return False, str(ex)

def load_from_github(filename="knowledge_base.json"):
    """Charge avec 2 methodes: API + RAW (RAW marche meme sans token et plus rapide)"""
    if not GITHUB_AVAILABLE:
        return None, "GitHub non configuré"
    
    # Methode 1: RAW github (public, instantané, pas de cache)
    try:
        raw_url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/{GITHUB_BRANCH}/{filename}"
        # Ajouter timestamp pour eviter cache
        raw_url += f"?t={int(time.time())}"
        r = requests.get(raw_url, timeout=10)
        if r.status_code == 200 and r.text.strip():
            data = json.loads(r.text)
            return data, f"Chargé via RAW ({len(data)} docs)"
    except Exception as e:
        raw_error = str(e)
    else:
        raw_error = "RAW 404"
    
    # Methode 2: API GitHub (avec token)
    try:
        url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{filename}?ref={GITHUB_BRANCH}"
        headers = {"Authorization": f"Bearer {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            content_data = r.json()
            content = base64.b64decode(content_data["content"]).decode('utf-8')
            data = json.loads(content)
            return data, f"Chargé via API ({len(data)} docs)"
        else:
            return None, f"API {r.status_code} + RAW {raw_error}"
    except Exception as ex:
        return None, f"Erreur load: {ex} + RAW {raw_error}"

# --- SESSION STATE ROBUSTE ---
if 'knowledge' not in st.session_state:
    st.session_state.knowledge = {}
    st.session_state.load_msg = ""

    if GITHUB_AVAILABLE:
        with st.spinner("🧠 Chargement de la base GitHub..."):
            loaded, msg = load_from_github()
            st.session_state.load_msg = msg
            if loaded is not None:
                st.session_state.knowledge = loaded
                st.session_state.last_load_ok = True
            else:
                st.session_state.last_load_ok = False
                # Si c'est le premier lancement, c'est normal que le fichier n'existe pas
                if "404" in msg:
                    st.session_state.load_msg = "Base vide - premier lancement, glisse un doc"
                    st.session_state.knowledge = {}

# UI
st.sidebar.title("🧠 NOURRIR L'AGENT - BOUTON UNIQUE")

if GITHUB_AVAILABLE:
    st.sidebar.success(f"✅ GitHub Memory active\n{GITHUB_REPO}")
    if st.session_state.get('load_msg'):
        if st.session_state.get('last_load_ok'):
            st.sidebar.caption(f"✅ {st.session_state.load_msg}")
        else:
            st.sidebar.caption(f"ℹ️ {st.session_state.load_msg}")
else:
    st.sidebar.warning("⚠️ GitHub non connecté")

st.sidebar.divider()
uploaded_file = st.sidebar.file_uploader("Glisse ici : Normes, Rapports, Modeles, Offres", type=['pdf','docx','xlsx','pptx','txt','json'])

if uploaded_file is not None:
    # Eviter de re-sauver le meme fichier à chaque rerun
    if 'last_uploaded' not in st.session_state or st.session_state.last_uploaded != uploaded_file.name + str(uploaded_file.size):
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
            "size": uploaded_file.size
        }
        st.session_state.knowledge[file_name] = new_entry
        st.session_state.last_uploaded = file_name + str(uploaded_file.size)
        
        if GITHUB_AVAILABLE:
            ok, msg = save_to_github(st.session_state.knowledge)
            if ok:
                st.sidebar.success(f"✅ {file_name} -> {msg}")
                st.sidebar.balloons = True
            else:
                st.sidebar.error(f"❌ {msg}")
        else:
            st.sidebar.success(f"✅ {file_name} (local)")

st.title("🛡️ MADOU GRC AUTOPILOT V3.5 - PERSISTANCE")
st.caption("V3.5 - La base reste après actualisation - Chargement RAW + API")

if st.session_state.knowledge:
    st.subheader(f"📚 Base persistante ({len(st.session_state.knowledge)} docs) - Cette base reste après F5")
    st.json(st.session_state.knowledge)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🔄 Forcer Sync GitHub"):
            ok, msg = save_to_github(st.session_state.knowledge)
            if ok:
                st.success(msg)
                st.balloons()
            else:
                st.error(msg)
    with col2:
        if st.button("🔄 Recharger depuis GitHub"):
            loaded, msg = load_from_github()
            if loaded is not None:
                st.session_state.knowledge = loaded
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)
    with col3:
        st.download_button("📥 Télécharger JSON", data=json.dumps(st.session_state.knowledge, indent=2, ensure_ascii=False), file_name="knowledge_base.json", mime="application/json")

else:
    st.info("Aucun document en memoire. Si tu viens d'actualiser et que c'est vide, clique sur 'Recharger depuis GitHub'")
    if GITHUB_AVAILABLE:
        if st.button("🔄 Recharger maintenant"):
            loaded, msg = load_from_github()
            if loaded is not None:
                st.session_state.knowledge = loaded
                st.success(f"✅ {msg}")
                time.sleep(1)
                st.rerun()
            else:
                st.warning(f"{msg} - C'est normal si c'est la premiere fois")

st.divider()
st.code(f"Repo: {GITHUB_REPO}\nBranche: {GITHUB_BRANCH}\nDernier chargement: {st.session_state.get('load_msg','')}", language="text")
st.caption("Astuce: Va sur github.com/bawaleroger/MADOU_GRC_AUTOPILOT/blob/main/knowledge_base.json pour voir ta base directement")
