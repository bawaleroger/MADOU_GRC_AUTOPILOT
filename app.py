
import streamlit as st
import json
import base64
import requests
from datetime import datetime

st.set_page_config(page_title="MADOU GRC AUTOPILOT", page_icon="🛡️", layout="wide")

GITHUB_AVAILABLE = False
GITHUB_TOKEN = None
GITHUB_REPO = None

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
            "message": f"🧠 update knowledge {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "content": content_b64,
            "branch": GITHUB_BRANCH
        }
        if r.status_code == 200:
            payload["sha"] = r.json()["sha"]
        
        res = requests.put(url, headers=headers, json=payload)
        
        if res.status_code in [200, 201]:
            return True, f"Sauvé sur GitHub {filename} ✅"
        else:
            # Si 404 c'est que repo n'existe pas ou token sans droits
            if res.status_code == 404:
                # Essayer de verifier le repo
                repo_check = requests.get(f"https://api.github.com/repos/{GITHUB_REPO}", headers=headers)
                if repo_check.status_code == 404:
                    return False, f"Repo {GITHUB_REPO} introuvable. Verifie le nom exact sur github.com (casse sensible) et que le token a le droit 'repo'"
            return False, f"GitHub {res.status_code}: {res.text[:500]}"
    except Exception as ex:
        return False, str(ex)

def load_from_github(filename="knowledge_base.json"):
    if not GITHUB_AVAILABLE:
        return None
    try:
        url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{filename}?ref={GITHUB_BRANCH}"
        headers = {"Authorization": f"Bearer {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
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
    # Test connexion
    try:
        headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
        test = requests.get(f"https://api.github.com/repos/{GITHUB_REPO}", headers=headers, timeout=5)
        if test.status_code == 200:
            st.sidebar.caption(f"Repo OK - branch {GITHUB_BRANCH}")
        else:
            st.sidebar.error(f"Repo inaccessible: {test.status_code} - Verifie GITHUB_REPO")
    except Exception as e:
        st.sidebar.caption(f"Test repo: {e}")
else:
    st.sidebar.warning("⚠️ GitHub non connecté")

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
        "size": uploaded_file.size
    }
    st.session_state.knowledge[file_name] = new_entry
    
    if GITHUB_AVAILABLE:
        ok, msg = save_to_github(st.session_state.knowledge)
        if ok:
            st.sidebar.success(f"✅ {file_name} -> {msg}")
        else:
            st.sidebar.error(f"❌ {msg}")
    else:
        st.sidebar.success(f"✅ {file_name} (mode local)")

st.title("🛡️ MADOU GRC AUTOPILOT V3.4.1 - FIX 404")
st.caption("Fix syntaxe DeltaGenerator + GitHub Memory")

if st.session_state.knowledge:
    st.subheader(f"📚 Base ({len(st.session_state.knowledge)} docs)")
    st.json(st.session_state.knowledge)
    if st.button("🔄 Forcer Sync GitHub"):
        ok, msg = save_to_github(st.session_state.knowledge)
        if ok:
            st.success(msg)
            st.balloons()
        else:
            st.error(msg)
else:
    st.info("Glisse un document à gauche pour nourrir l'agent")

st.divider()
st.code(f"Repo configuré: {GITHUB_REPO}\nBranche: {GITHUB_BRANCH if GITHUB_AVAILABLE else 'non configuré'}", language="text")
