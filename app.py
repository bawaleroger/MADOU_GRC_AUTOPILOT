
import streamlit as st
import json
import base64
import requests
from datetime import datetime, timedelta
import time
import pandas as pd

st.set_page_config(page_title="MADOU V8 - MISSION MEF", page_icon="🛡️", layout="wide")

# === GITHUB ===
GITHUB_TOKEN = st.secrets.get("GITHUB_TOKEN", "")
GITHUB_REPO = st.secrets.get("GITHUB_REPO", "bawaleroger/MADOU_GRC_AUTOPILOT")
GITHUB_BRANCH = st.secrets.get("GITHUB_BRANCH", "main")
GITHUB_AVAILABLE = bool(GITHUB_TOKEN)

def github_save(data_dict, filename="knowledge_base.json"):
    if not GITHUB_AVAILABLE:
        return False, "Non configuré"
    try:
        url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{filename}"
        headers = {"Authorization": f"Bearer {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
        r = requests.get(url, headers=headers)
        b64 = base64.b64encode(json.dumps(data_dict, ensure_ascii=False, indent=2).encode('utf-8')).decode('utf-8')
        payload = {"message": f"V8 MEF {len(data_dict)} docs {datetime.now().strftime('%H:%M')}", "content": b64, "branch": GITHUB_BRANCH}
        if r.status_code == 200:
            payload["sha"] = r.json()["sha"]
        res = requests.put(url, headers=headers, json=payload)
        return (True, f"Sauvé ({len(data_dict)} docs) ✅") if res.status_code in [200,201] else (False, f"Erreur {res.status_code}")
    except Exception as e:
        return False, str(e)

def github_load(filename="knowledge_base.json"):
    if not GITHUB_AVAILABLE:
        return {}, "Non configuré"
    try:
        url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{filename}?ref={GITHUB_BRANCH}&t={int(time.time())}"
        headers = {"Authorization": f"Bearer {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json", "Cache-Control": "no-cache"}
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code == 200:
            data = json.loads(base64.b64decode(r.json()["content"]).decode('utf-8'))
            return data, f"API fraîche ({len(data)} docs) ✅"
        return {}, "Base vide"
    except Exception as e:
        return {}, str(e)

def extract_text(file_obj, max_chars=8000):
    try:
        name = file_obj.name.lower()
        if name.endswith('.pdf'):
            import PyPDF2
            reader = PyPDF2.PdfReader(file_obj)
            text = "".join([(p.extract_text() or "") for p in reader.pages[:12]])
            return text[:max_chars]
        elif name.endswith('.docx'):
            import docx
            doc = docx.Document(file_obj)
            return "\n".join([p.text for p in doc.paragraphs])[:max_chars]
        else:
            return file_obj.read(4000).decode(errors='ignore')[:max_chars]
    except:
        return ""

# === MISSION MEF REELLE ===
LIVRABLES_MEF = [
    {
        "id": "cadrage",
        "nom": "Rapport de cadrage",
        "format": "Word, PDF et Physique",
        "delai": "2 jours après cadrage",
        "delai_jours": 2,
        "dest": "Comité de suivi autorité contractante",
        "contenu": [
            "Harmoniser points de vue maître ouvrage et DORIANNE IS",
            "Présenter périmètre fonctionnel et organisationnel",
            "Rappeler et finaliser principes de communication",
            "Lancer officiellement le projet",
            "Responsabiliser parties prenantes",
            "Finaliser Planning et méthodologie (base modèle proposé)",
            "Présentation outils de collecte et données"
        ]
    },
    {
        "id": "existant",
        "nom": "Rapport d'étude de l'existant",
        "format": "Word, PDF et Physique",
        "delai": "15 jours après cadrage",
        "delai_jours": 15,
        "dest": "Comité de suivi",
        "contenu": [
            "Etude de l'existant - Inventaire global SI MEF",
            "Analyse des risques (EBIOS RM / ISO 27005)",
            "Cartographie fonctionnelle et technique",
            "Entretiens avec parties prenantes"
        ]
    },
    {
        "id": "orga",
        "nom": "Rapport d'audit organisationnel",
        "format": "Word, PDF et Physique",
        "delai": "20 jours après étude existant",
        "delai_jours": 20,
        "dest": "Comité de suivi",
        "contenu": [
            "Audit organisationnel - Gouvernance, processus, rôles",
            "Audit physique - Locaux, contrôle accès, Datacenter",
            "Matrice RACI et organisation cible"
        ]
    },
    {
        "id": "technique",
        "nom": "Rapport d'audit technique et test d'intrusion",
        "format": "Word, PDF et Physique",
        "delai": "60 jours après audit orga",
        "delai_jours": 60,
        "dest": "Comité de suivi",
        "contenu": [
            "Audit Réseau informatique - Inventaire actifs informationnels MEF",
            "Bilan et état des lieux transparent global SI + interactions services MEF",
            "Audit Sécurité Applicative Plateformes MEF - Pertinence parc logiciel vs besoins fonctionnels",
            "Tests d'Intrusion interne et externe Applications Web Plateformes MEF - Vulnérabilités équipements, apps, réseau",
            "Audit Code Source Applications Web Plateformes MEF",
            "Évaluation objective maturité numérique services MEF (0 à 5)"
        ]
    },
    {
        "id": "synthese",
        "nom": "Rapport de synthèse et plan d'actions",
        "format": "Word, PDF et Physique",
        "delai": "22 jours après audit technique",
        "delai_jours": 22,
        "dest": "Autorité contractante",
        "contenu": [
            "Recommandations réorganisation SI global (tech, métier, humain, stratégie)",
            "Propositions améliorations stratégie développement plateformes",
            "Proposition organisation et missions correspondantes",
            "Recommandations + plan d'action correction vulnérabilités et réduction risques",
            "Plan d'action court et moyen terme + coûts",
            "Estimation coûts, délais, tâches prioritaires",
            "Schéma directeur sur 3 ans - Feuille de Route Investissements SI/Cyber (Plan Directeur Recommandations chiffrées) - NB: pas vrai plan directeur mais feuille route chiffrée"
        ]
    }
]

REFERENTIELS = ["ISO/IEC 27001:2022","ISO/IEC 27002","ISO/IEC 27005","EBIOS RM","NIST CSF 2.0","NIST SP 800-53","OWASP Top 10","MITRE ATT&CK","CIS Controls v8","COBIT 2019","ITIL v4","COBAC/BEAC","RGPD"]

# INIT
if 'kb' not in st.session_state:
    kb, msg = github_load() if GITHUB_AVAILABLE else ({}, "")
    st.session_state.kb = kb
    st.session_state.kb_msg = msg
    st.session_state.tdr_docs = []
    st.session_state.mission_mef = None
    st.session_state.active_tab = 0
    st.session_state.mef_start_date = datetime.now().date()

# SIDEBAR
with st.sidebar:
    st.title("🛡️ MADOU V8")
    st.caption("MISSION MEF - DORIANNE IS")
    st.metric("Base", f"{len(st.session_state.kb)} docs", st.session_state.kb_msg)
    st.divider()
    st.markdown("**➕ Nourrir l'agent**")
    up = st.file_uploader("Normes", type=['pdf','docx'], accept_multiple_files=True, key="sb_up", label_visibility="collapsed")
    if up:
        for f in up:
            if f.name not in st.session_state.kb:
                st.session_state.kb[f.name] = {"name": f.name, "date": datetime.now().strftime("%Y-%m-%d"), "size": f.size}
        github_save(st.session_state.kb)
        st.success("Ajouté")
    st.divider()
    if st.session_state.mission_mef:
        m = st.session_state.mission_mef
        st.markdown("### 📅 Planning contractuel")
        for liv in LIVRABLES_MEF:
            done = m['livrables'].get(liv['id'], {}).get('done', False)
            icon = "✅" if done else "⏳"
            st.caption(f"{icon} {liv['nom']} - {liv['delai']}")

# NAV
st.title("🛡️ MADOU GRC AUTOPILOT V8 - MISSION MEF")
st.caption("Mission réelle: Audit SI MEF - DORIANNE IS - 5 rapports contractuels - bawale.store")

tabs = ["0️⃣ PHASE 0: Cadrage MEF", "📥 TDRs & Périmètre", "📑 Les 5 Rapports", "🚀 Exécution Mission", "💰 Offres", "📊 Base"]
cols = st.columns(6)
for i, label in enumerate(tabs):
    if cols[i].button(label, key=f"nav_{i}", type="primary" if st.session_state.active_tab==i else "secondary", use_container_width=True):
        st.session_state.active_tab = i
        st.rerun()
st.divider()

# PHASE 0
if st.session_state.active_tab == 0:
    st.header("0️⃣ PHASE 0 : Cadrage Mission MEF - DORIANNE IS")
    st.info("**Mission future:** Audit global SI du MEF - 5 livrables contractuels avec délais. Cette PHASE 0 correspond exactement à ton Rapport de cadrage (2 jours).")
    
    c1, c2 = st.columns([2,1])
    with c1:
        st.subheader("1. TDRs MEF (ouvrables)")
        tdr_up = st.file_uploader("Dépose TDRs MEF", type=['pdf','docx'], accept_multiple_files=True, key="p0_tdr_mef", label_visibility="collapsed")
        if tdr_up:
            docs = []
            for f in tdr_up:
                txt = extract_text(f)
                docs.append({"name": f.name, "bytes": f.getvalue(), "text": txt})
            st.session_state.tdr_docs = docs
            st.success(f"✅ {len(docs)} TDRs MEF chargés")
        
        if st.session_state.tdr_docs:
            for idx, doc in enumerate(st.session_state.tdr_docs):
                with st.expander(f"📄 {doc['name']} - Ouvrir"):
                    st.text_area("Aperçu", doc['text'][:5000], height=180, key=f"mef_txt_{idx}")
                    st.download_button(f"📥 Ouvrir {doc['name']}", data=doc['bytes'], file_name=doc['name'], key=f"mef_dl_{idx}")
        
        st.divider()
        st.subheader("2. Paramètres mission MEF")
        start_date = st.date_input("Date de démarrage mission (cadrage)", value=st.session_state.mef_start_date, key="mef_start")
        st.session_state.mef_start_date = start_date
        
        refs = st.multiselect("Référentiels pour la mission MEF", REFERENTIELS, default=["ISO/IEC 27001:2022","EBIOS RM","NIST CSF 2.0","OWASP Top 10"], key="mef_refs")
        
        # Calcul planning automatique
        st.subheader("3. Planning contractuel auto-calculé")
        planning = []
        current = start_date
        for liv in LIVRABLES_MEF:
            current = current + timedelta(days=liv['delai_jours'])
            planning.append({"Rapport": liv['nom'], "Échéance": current, "Délai": liv['delai'], "Destinataire": liv['dest']})
        df_plan = pd.DataFrame(planning)
        st.dataframe(df_plan, use_container_width=True)
    
    with c2:
        st.markdown("### 🎯 Mission MEF")
        st.markdown("""
        **Client:** MEF (Ministère Éco & Finances)  
        **Prestataire:** DORIANNE IS  
        **Type:** Audit global SI + Pentest + Code Source  
        **Durée:** ~119 jours (2+15+20+60+22)
        """)
        st.divider()
        if st.session_state.tdr_docs:
            if st.button("🚀 DÉMARRER MISSION MEF - 5 RAPPORTS", type="primary", use_container_width=True):
                st.session_state.mission_mef = {
                    "start": start_date.strftime("%Y-%m-%d"),
                    "refs": refs,
                    "tdrs": [d['name'] for d in st.session_state.tdr_docs],
                    "livrables": {liv['id']: {"done": False, "date": None, "file": None} for liv in LIVRABLES_MEF},
                    "active": True
                }
                st.session_state.active_tab = 3
                st.balloons()
                st.rerun()
        else:
            st.warning("Charge TDRs MEF d'abord")

# PHASE 1 - TDRs
elif st.session_state.active_tab == 1:
    st.header("📥 PHASE 1 : Périmètre fonctionnel & organisationnel")
    if not st.session_state.tdr_docs:
        st.warning("Pas de TDRs")
    else:
        st.success(f"{len(st.session_state.tdr_docs)} TDRs - Périmètre MEF")
        for doc in st.session_state.tdr_docs:
            st.markdown(f"**{doc['name']}** - {len(doc['text'])} chars")

# PHASE 2 - Les 5 Rapports (NOUVEAU COEUR)
elif st.session_state.active_tab == 2:
    st.header("📑 Les 5 Rapports Contractuels - Mission MEF")
    st.caption("Tableau officiel de ta mission future - Délais contractuels")
    
    # Tableau récap comme tu as donné
    df = pd.DataFrame([
        {"Rapport": liv["nom"], "Format": liv["format"], "Contenu (résumé)": "\n".join(liv["contenu"][:2]) + "...", "Délai": liv["delai"], "Destinataire": liv["dest"]}
        for liv in LIVRABLES_MEF
    ])
    st.dataframe(df, use_container_width=True, height=300)
    
    st.divider()
    for liv in LIVRABLES_MEF:
        with st.expander(f"📄 {liv['nom']} - {liv['delai']} - {liv['format']}"):
            st.markdown(f"**Destinataire:** {liv['dest']}")
            st.markdown(f"**Délai:** {liv['delai']} ({liv['delai_jours']} jours)")
            st.markdown("**Contenu détaillé:**")
            for c in liv['contenu']:
                st.markdown(f"• {c}")
            
            # Génération
            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"🤖 Générer {liv['nom']} (Agent 50 ans exp)", key=f"gen_{liv['id']}"):
                    # Simuler génération
                    content = f"Rapport {liv['nom']} - MEF - DORIANNE IS - Basé sur {', '.join(st.session_state.get('mef_refs',[]))} - {datetime.now()}\n\n" + "\n".join([f"- {x}" for x in liv['contenu']])
                    st.session_state[f"doc_{liv['id']}"] = content
                    st.success(f"{liv['nom']} généré !")
            with col2:
                if f"doc_{liv['id']}" in st.session_state:
                    st.download_button(f"📥 Télécharger {liv['nom']} (Word)", data=st.session_state[f"doc_{liv['id']}"].encode(), file_name=f"{liv['nom'].replace(' ','_')}.docx", key=f"dl_{liv['id']}")

# PHASE 3 - Exécution
elif st.session_state.active_tab == 3:
    st.header("🚀 Exécution Mission MEF - Suivi des 5 Rapports")
    m = st.session_state.get('mission_mef')
    if not m or not m.get('active'):
        st.info("Aucune mission MEF active → Va en PHASE 0 et clique DÉMARRER MISSION MEF")
    else:
        st.success(f"Mission MEF active - Démarrée {m['start']} - Référentiels: {', '.join(m['refs'])}")
        
        # Timeline
        current_date = st.session_state.mef_start_date
        for idx, liv in enumerate(LIVRABLES_MEF):
            current_date = current_date + timedelta(days=liv['delai_jours'])
            is_done = m['livrables'].get(liv['id'], {}).get('done', False)
            icon = "✅" if is_done else "⏳" if idx==0 else "⭕"
            
            with st.expander(f"{icon} {idx+1}. {liv['nom']} - Échéance: {current_date} - {liv['delai']}", expanded=(idx==0)):
                st.markdown(f"**Format:** {liv['format']} | **Dest:** {liv['dest']}")
                for c in liv['contenu']:
                    st.markdown(f"• {c}")
                
                c1, c2 = st.columns(2)
                with c1:
                    if not is_done:
                        if st.button(f"✅ Valider {liv['nom']}", key=f"val_{liv['id']}"):
                            st.session_state.mission_mef['livrables'][liv['id']]['done'] = True
                            st.session_state.mission_mef['livrables'][liv['id']]['date'] = datetime.now().strftime("%Y-%m-%d")
                            st.rerun()
                    else:
                        st.success(f"Validé le {m['livrables'][liv['id']].get('date')}")
                with c2:
                    # Générer doc
                    if st.button(f"📄 Générer document", key=f"gen2_{liv['id']}"):
                        content = f"{liv['nom']} - MEF\n" + "\n".join(liv['contenu'])
                        st.download_button(f"📥 Télécharger {liv['nom']}", data=content.encode(), file_name=f"{liv['id']}.docx", key=f"dld_{liv['id']}_2")

# PHASE 4 - Offres
elif st.session_state.active_tab == 4:
    st.header("💰 Offres - MEF")
    st.metric("Offre Financière", "À chiffrer selon 119 jours")
    st.download_button("📥 Offre Technique MEF", data=b"fake", file_name="Offre_Technique_MEF.docx")

# PHASE 5 - Base
else:
    st.header("📊 Base & Catalogue MEF")
    st.dataframe([{"Nom": k} for k in st.session_state.kb.keys()], use_container_width=True)
    st.markdown("### Référentiels pour MEF")
    for r in REFERENTIELS:
        st.caption(f"• {r}")

st.caption("V8 MISSION MEF - 5 Rapports contractuels - Planning 119 jours - DORIANNE IS - bawale.store")
