
import streamlit as st
import json
import base64
import requests
from datetime import datetime

st.set_page_config(page_title="MADOU GRC AUTOPILOT", page_icon="🛡️", layout="wide")

GITHUB_AVAILABLE = False
GITHUB_TOKEN = None
GITHUB_REPO = None
GITHUB_BRANCH = "main"

try:
    if "GITHUB_TOKEN" in st.secrets and "GITHUB_REPO" in st.secrets:
        GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
        GITHUB_REPO = st.secrets["GITHUB_REPO"]
        GITHUB_BRANCH = st.secrets.get("GITHUB_BRANCH", "main")
        GITHUB_AVAILABLE = True
except:
    GITHUB_AVAILABLE = False

def save_to_github(data_dict, filename="knowledge_base.json"):
    if not GITHUB_AVAILABLE:
        return False, "GitHub non configuré"
    try:
        url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{filename}"
        headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
        r = requests.get(url, headers=headers)
        json_bytes = json.dumps(data_dict, ensure_ascii=False, indent=2).encode('utf-8')
        content_b64 = base64.b64encode(json_bytes).decode('utf-8')
        payload = {"message": f"brain update {datetime.now().strftime('%Y-%m-%d %H:%M')}", "content": content_b64, "branch": GITHUB_BRANCH}
        if r.status_code == 200:
            payload["sha"] = r.json()["sha"]
        res = requests.put(url, headers=headers, json=payload)
        if res.status_code in [200, 201]:
            return True, f"Sauvé sur GitHub {filename}"
        else:
            return False, f"GitHub {res.status_code}: {res.text[:300]}"
    except Exception as ex:
        return False, str(ex)

def load_from_github(filename="knowledge_base.json"):
    if not GITHUB_AVAILABLE:
        return None
    try:
        url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{filename}?ref={GITHUB_BRANCH}"
        headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            data = r.json()
            content = base64.b64decode(data["content"]).decode('utf-8')
            return json.loads(content)
        return None
    except:
        return None

if 'knowledge' not in st.session_state:
    loaded = load_from_github() if GITHUB_AVAILABLE else None
    st.session_state.knowledge = loaded if loaded else {}

st.sidebar.title("🧠 NOURRIR L'AGENT - BOUTON UNIQUE")
if GITHUB_AVAILABLE:
    st.sidebar.success(f"✅ GitHub Memory active\n{GITHUB_REPO}")
else:
    st.sidebar.warning("⚠️ GitHub non connecté")
    st.sidebar.info("Ajoute GITHUB_TOKEN dans Secrets")

st.sidebar.divider()
uploaded_file = st.sidebar.file_uploader("Glisse ici : Normes, Rapports, Modeles, Offres", type=['pdf','docx','xlsx','pptx','txt','json'])

if uploaded_file is not None:
    file_name = uploaded_file.name
    lower = file_name.lower()
    type_detected = "Rapport Audit" if "audit" in lower else "Norme" if "norme" in lower or "iso" in lower else "Document"
    new_entry = {"name": file_name, "type": type_detected, "date": datetime.now().strftime("%Y-%m-%d %H:%M"), "size": uploaded_file.size}
    st.session_state.knowledge[file_name] = new_entry
    if GITHUB_AVAILABLE:
        ok, msg = save_to_github(st.session_state.knowledge)
        st.sidebar.success(f"✅ {file_name} -> {msg}") if ok else st.sidebar.error(msg)
    else:
        st.sidebar.success(f"✅ {file_name} local")

st.title("🛡️ MADOU GRC AUTOPILOT V3.4 - GitHub Memory")
if st.session_state.knowledge:
    st.json(st.session_state.knowledge)
    if st.button("🔄 Forcer Sync GitHub"):
        ok, msg = save_to_github(st.session_state.knowledge)
        st.success(msg) if ok else st.error(msg)
else:
    st.info("Glisse un document à gauche")

st.caption("V3.4 - GitHub Memory - Sans carte - bawale.store")
