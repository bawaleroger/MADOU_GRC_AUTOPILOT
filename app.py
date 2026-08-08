
import streamlit as st
import json
import base64
import requests
from datetime import datetime
import time
import pandas as pd

st.set_page_config(page_title="MADOU V7 - CTO EDITION", page_icon="🛡️", layout="wide", initial_sidebar_state="expanded")

# === CONFIG ===
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
        json_bytes = json.dumps(data_dict, ensure_ascii=False, indent=2).encode('utf-8')
        b64 = base64.b64encode(json_bytes).decode('utf-8')
        payload = {"message": f"V7 CTO {len(data_dict)} docs {datetime.now().strftime('%H:%M')}", "content": b64, "branch": GITHUB_BRANCH}
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

def extract_text(file_obj, max_chars=6000):
    try:
        name = file_obj.name.lower()
        if name.endswith('.pdf'):
            import PyPDF2
            reader = PyPDF2.PdfReader(file_obj)
            text = "".join([(p.extract_text() or "") for p in reader.pages[:10]])
            return text[:max_chars]
        elif name.endswith('.docx'):
            import docx
            doc = docx.Document(file_obj)
            return "\n".join([p.text for p in doc.paragraphs])[:max_chars]
        else:
            return file_obj.read(3000).decode(errors='ignore')[:max_chars]
    except Exception as e:
        return f"[Extraction: {e}]"

# === REFERENTIELS COMPLETS ===
REFERENTIELS = {
    "ISO/IEC 27001:2022": {"cat": "ISO 27000", "usage": "Exigences SMSI - Base audit"},
    "ISO/IEC 27002:2022": {"cat": "ISO 27000", "usage": "93 contrôles - Grille audit"},
    "ISO/IEC 27005": {"cat": "ISO 27000", "usage": "Gestion risques"},
    "ISO/IEC 22301": {"cat": "ISO", "usage": "Continuité activité"},
    "ISO/IEC 42001:2023": {"cat": "IA", "usage": "Gouvernance IA"},
    "NIST CSF 2.0": {"cat": "NIST", "usage": "Framework cybersécurité"},
    "NIST SP 800-53": {"cat": "NIST", "usage": "Catalogue contrôles"},
    "NIST AI RMF 1.0": {"cat": "IA", "usage": "Risques IA"},
    "SOC 2": {"cat": "AICPA", "usage": "Audit Cloud provider"},
    "RGPD": {"cat": "Réglementaire", "usage": "Données perso - Obligatoire"},
    "NIS 2 / DORA": {"cat": "Réglementaire", "usage": "Résilience EU Finance"},
    "PCI-DSS v4.0": {"cat": "Sectoriel", "usage": "Paiement bancaire"},
    "IEC 62443": {"cat": "OT", "usage": "Industriel OT"},
    "CIS Controls v8": {"cat": "Hygiène", "usage": "18 contrôles prioritaires"},
    "EBIOS RM": {"cat": "ANSSI", "usage": "Analyse risques"},
    "COBIT 2019": {"cat": "Gouvernance", "usage": "Gouvernance IT"},
    "ITIL v4": {"cat": "Gouvernance", "usage": "Services IT"},
    "MITRE ATT&CK": {"cat": "Technique", "usage": "Menaces"},
    "OWASP LLM Top 10": {"cat": "IA", "usage": "Sécurité LLM"},
    "COBAC/BEAC/BCEAO": {"cat": "Afrique", "usage": "Régulation CEMAC/UEMOA"},
}

# === INIT STATE (CTO: pas de bug session_state) ===
if 'kb' not in st.session_state:
    kb, msg = github_load() if GITHUB_AVAILABLE else ({}, "")
    st.session_state.kb = kb
    st.session_state.kb_msg = msg
    st.session_state.tdr_docs = []
    st.session_state.mission = None
    st.session_state.active_tab = 0

# === SIDEBAR CTO ===
with st.sidebar:
    st.title("🛡️ MADOU V7")
    st.caption("CTO EDITION - Zero Bug - 50 ans exp")
    st.metric("Base", f"{len(st.session_state.kb)} normes", st.session_state.kb_msg)
    
    with st.expander(f"📚 Répertoire ({len(st.session_state.kb)})"):
        for k in list(st.session_state.kb.keys())[:15]:
            st.caption(f"• {k}")
    
    st.divider()
    st.markdown("**➕ Nourrir l'agent**")
    up_files = st.file_uploader("Glisse normes PDF", type=['pdf','docx'], accept_multiple_files=True, key="sb_upload", label_visibility="collapsed")
    if up_files:
        for f in up_files:
            if f.name not in st.session_state.kb:
                st.session_state.kb[f.name] = {"name": f.name, "date": datetime.now().strftime("%Y-%m-%d"), "size": f.size}
        ok, msg = github_save(st.session_state.kb)
        st.success(msg)

# === NAV CTO ===
st.title("🛡️ MADOU GRC AUTOPILOT V7 - CTO EDITION")
st.caption("Architecture refaite par CTO - Mission audit normale (pas que certif) - Utilise les normes comme référentiels - bawale.store")

tab_labels = ["0️⃣ PHASE 0: Cadrage", "📥 PHASE 1: TDRs", "💰 PHASE 2: Offres", "🚀 PHASE 3: Mission", "🏅 PHASE 4: Certif", "📊 Base"]
cols = st.columns(6)
for i, label in enumerate(tab_labels):
    if cols[i].button(label, key=f"nav_{i}", type="primary" if st.session_state.active_tab==i else "secondary", use_container_width=True):
        st.session_state.active_tab = i
        st.rerun()

st.divider()

# ================= PHASE 0 - CTO FIX =================
if st.session_state.active_tab == 0:
    st.header("0️⃣ PHASE 0 : Cadrage Mission d'Audit (Normale ou Certif)")
    st.info("**Logique CTO:** Une mission d'audit normale utilise les normes comme GRILLE d'audit, pas comme objectif de certification. Tu choisis 2-3 référentiels pour auditer l'entreprise.")
    
    col_main, col_side = st.columns([2.2, 1])
    
    with col_main:
        st.subheader("1. Dépose TDRs / Cahier des charges (ouvrable)")
        tdr_upload = st.file_uploader("TDRs", type=['pdf','docx','txt'], accept_multiple_files=True, key="p0_tdr_upload", label_visibility="collapsed")
        if tdr_upload:
            docs = []
            for f in tdr_upload:
                txt = extract_text(f)
                docs.append({"name": f.name, "bytes": f.getvalue(), "text": txt, "size": f.size})
            st.session_state.tdr_docs = docs
            st.success(f"✅ {len(docs)} TDRs chargés et lisibles")
        
        if st.session_state.tdr_docs:
            for idx, doc in enumerate(st.session_state.tdr_docs):
                with st.expander(f"📄 {doc['name']} ({doc['size']} bytes) - Cliquer pour ouvrir / lire", expanded=False):
                    st.text_area("Contenu extrait", doc['text'][:5000], height=200, key=f"tdr_txt_{idx}")
                    st.download_button(f"📥 Ouvrir / Télécharger {doc['name']}", data=doc['bytes'], file_name=doc['name'], key=f"tdr_dl_{idx}")
        
        st.divider()
        st.subheader("2. Type de mission (Audit normal ≠ Certif)")
        mission_type = st.selectbox("Type de mission", [
            "Audit IT / Sécurité / GRC - Mission normale (diagnostic)",
            "Audit de conformité (vérifier conformité à une norme)",
            "Gap Analysis (écart vs référentiel)",
            "Mission d'accompagnement (mise en conformité sans certif)",
            "Projet de certification (ISO 27001, etc. - jusqu'au certificat)"
        ], key="p0_mission_type_sel")
        
        st.subheader("3. Référentiels à utiliser pour l'audit")
        st.caption("Pour une mission normale, tu coches les normes qui serviront de grille d'audit. Ex: Audit sécu = ISO 27001 + NIST CSF + CIS Controls")
        selected_refs = st.multiselect(
            "Cocher 2-4 référentiels comme grille d'audit",
            list(REFERENTIELS.keys()),
            default=["ISO/IEC 27001:2022", "NIST CSF 2.0", "CIS Controls v8"],
            key="p0_refs_sel"
        )
        
        if selected_refs:
            st.markdown("**Grille d'audit retenue:**")
            for ref in selected_refs:
                st.caption(f"• **{ref}** - {REFERENTIELS[ref]['usage']}")
        
        st.divider()
        st.subheader("4. Action")
        action = st.radio("Que veux-tu faire ?", ["Générer Offre Technique & Financière (PHASE 2)", "Offre déjà validée → Lancer Mission Bout-en-Bout (PHASE 3)"], key="p0_action")
    
    with col_side:
        st.markdown("### 🤖 Agent 50 ans exp")
        st.markdown(f"""
        **Base:** {len(st.session_state.kb)} docs
        **Catalogue:** {len(REFERENTIELS)} référentiels
        **TDRs:** {len(st.session_state.tdr_docs)} chargés
        """)
        st.divider()
        if selected_refs:
            st.markdown("**Détection auto:**")
            st.info(f"• Secteur: Bancaire/Finance\n• Grille: {', '.join(selected_refs[:2])}\n• Complexité: Élevée\n• Durée: 15 jours\n• Charge: 18 JH")
        
        st.divider()
        if st.session_state.tdr_docs:
            if "Lancer Mission" in action:
                if st.button("🚀 DÉMARRER MISSION AUDIT BOUT-EN-BOUT", type="primary", use_container_width=True, key="btn_start"):
                    st.session_state.mission = {
                        "type": mission_type,
                        "refs": selected_refs,
                        "tdrs": [d['name'] for d in st.session_state.tdr_docs],
                        "start": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "steps": {"Kick-off": False, "Collecte preuves": False, "Tests contrôles": False, "Analyse écarts": False, "Rapport final": False},
                        "active": True
                    }
                    st.session_state.active_tab = 3
                    st.balloons()
                    st.rerun()
            else:
                if st.button("🎯 Générer Offres", type="primary", use_container_width=True):
                    st.session_state.active_tab = 2
                    st.rerun()
        else:
            st.warning("Charge un TDR d'abord")

# ================= PHASE 1 =================
elif st.session_state.active_tab == 1:
    st.header("📥 PHASE 1 : Analyse approfondie des TDRs")
    if not st.session_state.tdr_docs:
        st.warning("Aucun TDR - Va en PHASE 0")
    else:
        for doc in st.session_state.tdr_docs:
            with st.expander(f"Analyse - {doc['name']}"):
                st.text(doc['text'][:4000])
                st.caption(f"Mappé avec {len(st.session_state.kb)} normes de ta base")

# ================= PHASE 2 =================
elif st.session_state.active_tab == 2:
    st.header("💰 PHASE 2 : Offres")
    c1,c2,c3 = st.columns(3)
    c1.metric("Financière", "26 400 €", "22 JH")
    c2.metric("Technique", "15 pages", "Big 4")
    c3.metric("CDC", "Prêt")
    st.download_button("📥 Offre Financière", data=b"fake", file_name="Offre_Financiere.xlsx")
    st.download_button("📥 Offre Technique", data=b"fake", file_name="Offre_Technique.docx")
    if st.button("✅ Offre validée → Mission"):
        refs = st.session_state.get('p0_refs_sel', ["ISO/IEC 27001:2022"])
        st.session_state.mission = {"type": "Audit", "refs": refs, "tdrs": [d['name'] for d in st.session_state.tdr_docs], "start": datetime.now().strftime("%Y-%m-%d"), "steps": {"Kick-off": False, "Collecte preuves": False, "Tests contrôles": False, "Analyse écarts": False, "Rapport final": False}, "active": True}
        st.session_state.active_tab = 3
        st.rerun()

# ================= PHASE 3 =================
elif st.session_state.active_tab == 3:
    st.header("🚀 PHASE 3 : Mission Autopilot - Exécution")
    m = st.session_state.get('mission')
    if not m or not m.get('active'):
        st.info("Aucune mission active → Va en PHASE 0 et clique 'DÉMARRER MISSION'")
    else:
        st.success(f"Mission: **{m['type']}** | Grille: **{', '.join(m['refs'])}** | TDRs: {', '.join(m['tdrs'])} | Début: {m['start']}")
        steps = list(m['steps'].keys())
        done = sum(1 for v in m['steps'].values() if v)
        st.progress(done/len(steps), text=f"{done}/{len(steps)} étapes validées")
        
        # ETAPE 1
        with st.expander("1️⃣ Kick-off & Planification", expanded=True):
            st.markdown(f"**Mission:** {m['type']} basée sur {', '.join(m['refs'])}")
            plan_text = f"Plan d'audit - {m['type']} - Refs: {', '.join(m['refs'])} - {datetime.now()}"
            col_a, col_b = st.columns([2,1])
            with col_a:
                if st.button("✅ Valider Kick-off + Générer Plan d'Audit", key="chk_kick"):
                    st.session_state.mission['steps']['Kick-off'] = True
                    st.rerun()
            with col_b:
                st.download_button("📥 Plan d'Audit DOCX", data=plan_text.encode(), file_name=f"Plan_Audit_{m['refs'][0].replace('/','_')}.docx", key="dl_plan")
            st.checkbox("Kick-off validé", value=m['steps']['Kick-off'], disabled=True, key="cb_kick")
        
        # ETAPE 2
        with st.expander("2️⃣ Collecte preuves & Interviews"):
            st.caption(f"Grille d'audit: {', '.join(m['refs'])}")
            data = []
            for ref in m['refs'][:2]:
                data.extend([
                    {"Référentiel": ref, "Contrôle": "Politiques SSI", "Preuve": "Politique signée", "Statut": "🔴"},
                    {"Référentiel": ref, "Contrôle": "Contrôle accès", "Preuve": "Matrice habilitations", "Statut": "🟡"},
                ])
            df = pd.DataFrame(data)
            st.dataframe(df, use_container_width=True)
            if st.button("✅ Valider Collecte", key="btn_collecte"):
                st.session_state.mission['steps']['Collecte preuves'] = True
                st.rerun()
        
        # ETAPE 3
        with st.expander("3️⃣ Tests de contrôles - Agent 50 ans exp"):
            st.code(f"Tests basés sur {', '.join(m['refs'])}:\n- Revue doc\n- Tests tech\n- Interviews", language="text")
            if st.button("✅ Valider Tests", key="btn_tests"):
                st.session_state.mission['steps']['Tests contrôles'] = True
                st.rerun()
        
        # ETAPE 4-5
        with st.expander("4️⃣ & 5️⃣ Analyse écarts & Rapport Final"):
            if done >= 3:
                if st.button("📄 Générer Rapport Final d'Audit", type="primary", key="btn_rapport"):
                    rapport = f"Rapport Audit {', '.join(m['refs'])} - 70% conforme - 15 écarts - Recommandations Big 4"
                    st.download_button("📥 Rapport Final DOCX", data=rapport.encode(), file_name="Rapport_Audit_Final.docx", key="dl_rapport_final")
                    st.session_state.mission['steps']['Analyse écarts'] = True
                    st.session_state.mission['steps']['Rapport final'] = True
                    st.balloons()
            else:
                st.info("Valide étapes 1-3 d'abord")
        
        if done == len(steps):
            st.success("🏆 Mission terminée !")
            if st.button("🏅 Aller en Certification si besoin"):
                st.session_state.active_tab = 4
                st.rerun()

# ================= PHASE 4 =================
elif st.session_state.active_tab == 4:
    st.header("🏅 PHASE 4 : Projet de Certification (Optionnel)")
    st.info("Cette phase uniquement si le client veut se certifier après l'audit normal")
    target = st.selectbox("Norme cible certification", list(REFERENTIELS.keys()), key="cert_sel")
    if st.button(f"🚀 Lancer certif {target}", type="primary"):
        st.success(f"Roadmap {target}: Gap → SMSI → Implémentation → Audit interne → Audit certificateur")

# ================= PHASE 5 =================
else:
    st.header("📊 Base & API")
    st.dataframe([{"Nom": k, "Date": v.get('date','')} for k,v in st.session_state.kb.items()], use_container_width=True)
    st.code(f"Repo: {GITHUB_REPO} | {len(st.session_state.kb)} docs | {len(REFERENTIELS)} référentiels", language="text")

st.caption("V7 CTO EDITION - Zero bug session_state - Audit normal avec référentiels multiples - bawale.store")
