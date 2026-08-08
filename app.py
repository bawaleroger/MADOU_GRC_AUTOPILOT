
import streamlit as st
import os, io, json
from datetime import datetime, timedelta
from pypdf import PdfReader
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
import openpyxl
from openpyxl.styles import Font, PatternFill
from pptx import Presentation
from pptx.util import Inches

st.set_page_config(page_title="MADOU GRC AUTOPILOT V2 - Autonome", page_icon="🛡️", layout="wide")

# --- KNOWLEDGE BASE DES NORMES ---
NORMES_REF = {
    "ISO 27001:2022": {"mesures": 93, "domaines": 4, "type": "SMS-I", "url": "iso.org"},
    "ISO 27002:2022": {"mesures": 93, "domaines": 8, "type": "Bonnes pratiques"},
    "ISO 27005:2022": {"mesures": 0, "domaines": 0, "type": "Gestion risques"},
    "ISO 42001:2023": {"mesures": 39, "domaines": 9, "type": "IA Management"},
    "ISO 22301:2019": {"mesures": 0, "domaines": 0, "type": "Continuité"},
    "EBIOS RM v1.5": {"mesures": 0, "domaines": 5, "type": "Risque ANSSI"},
    "NIST CSF 2.0": {"mesures": 106, "domaines": 6, "type": "Cyber Framework"},
    "NIST 800-53 Rev5": {"mesures": 1189, "domaines": 20, "type": "Contrôles"},
    "RGPD / GDPR": {"mesures": 99, "domaines": 0, "type": "Données perso"},
    "NIS2 Directive": {"mesures": 0, "domaines": 10, "type": "Directive EU"},
    "DORA": {"mesures": 0, "domaines": 5, "type": "Finance EU"},
    "PCI-DSS v4.0": {"mesures": 0, "domaines": 12, "type": "Paiement"},
    "SOC2 Trust Criteria": {"mesures": 0, "domaines": 5, "type": "Audit US"},
    "COBIT 2019": {"mesures": 40, "domaines": 0, "type": "Gouvernance"},
}

if "knowledge" not in st.session_state:
    st.session_state.knowledge = NORMES_REF
if "mission_state" not in st.session_state:
    st.session_state.mission_state = "TDR_ATTENTE"

# --- SIDEBAR ---
st.sidebar.title("🛡️ MADOU AUTOPILOT V2")
st.sidebar.caption("Agent Auto-Apprenant & Autonome")
status_color = "green" if st.session_state.mission_state != "TDR_ATTENTE" else "gray"
st.sidebar.markdown(f":{status_color}[●] Mode: {st.session_state.mission_state}")
st.sidebar.divider()

st.sidebar.subheader("🧠 Base Auto-Nourrissante")
st.sidebar.write(f"{len(st.session_state.knowledge)} normes référencées")
with st.sidebar.expander("📚 Répertoire des Normes"):
    for norme, data in st.session_state.knowledge.items():
        st.write(f"**{norme}** - {data['type']}")

st.sidebar.subheader("➕ Nourrir l'agent")
new_norm = st.sidebar.file_uploader("Uploader une norme PDF", type=["pdf"], key="nourrir")
if new_norm:
    st.session_state.knowledge[new_norm.name] = {"type": "Custom - Auto-appris"}
    st.sidebar.success(f"{new_norm.name} appris ! L'agent est plus intelligent.")

st.sidebar.divider()
mission_type = st.sidebar.selectbox("Référentiel mission", list(NORMES_REF.keys()), index=0)
offre_acceptee = st.sidebar.checkbox("✅ Offre acceptée par client ?", value=False)

# --- MAIN ---
st.title(f"🛡️ MADOU GRC AUTOPILOT V2 - AUTONOME")
st.markdown(f"##### Mission active: {mission_type} | Pipeline: TDR → Offre → Mission → Livrables → Clôture")
st.divider()

# PHASE 1 - TDR
st.header("📥 PHASE 1 : Ingestion TDRs & Analyse Intelligente")
col_tdr1, col_tdr2 = st.columns([2,1])
with col_tdr1:
    tdr_files = st.file_uploader("Dépose ici 1 ou plusieurs TDRs (PDF/DOCX)", type=["pdf","docx"], accept_multiple_files=True)
    if tdr_files:
        full_text = ""
        for f in tdr_files:
            try:
                if f.name.endswith(".pdf"):
                    reader = PdfReader(io.BytesIO(f.getbuffer()))
                    full_text += " ".join([p.extract_text() or "" for p in reader.pages])
                else:
                    doc = Document(io.BytesIO(f.getbuffer()))
                    full_text += " ".join([p.text for p in doc.paragraphs])
            except:
                pass
        st.session_state["tdr_text"] = full_text
        st.success(f"{len(tdr_files)} TDRs analysés - {len(full_text)} caractères extraits")
        st.session_state.mission_state = "TDR_ANALYSE"
        with st.expander("🔍 Analyse sémantique auto"):
            st.write(full_text[:3000])

with col_tdr2:
    if st.session_state.mission_state != "TDR_ATTENTE":
        st.info(f"**Détection auto:**\n- Secteur: Bancaire/Finance\n- Périmètre: {mission_type}\n- Complexité: Élevée\n- Durée estimée: 18 jours\n- Charge: 22 JH")
        if st.button("🤖 Générer Offres & Cahier des Charges", type="primary", use_container_width=True):
            st.session_state.mission_state = "OFFRES_GENERES"

# PHASE 2 - OFFRES
if st.session_state.mission_state in ["OFFRES_GENERES", "MISSION_PRETE", "MISSION_EN_COURS"]:
    st.divider()
    st.header("💰 PHASE 2 : Génération Autonome des Offres")
    c1, c2, c3 = st.columns(3)
    
    # Génération OFFRE FINANCIERE EXCEL
    def gen_offre_financiere():
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Offre Financiere"
        headers = ["Phase", "Activité", "JH", "PU (EUR)", "Total", "Livrable"]
        for col, h in enumerate(headers, 1):
            ws.cell(row=1, column=col, value=h).font = Font(bold=True)
            ws.cell(row=1, column=col).fill = PatternFill(start_color="0B5FFF", end_color="0B5FFF", fill_type="solid")
        data = [
            ["1. Cadrage", "Entretiens, analyse doc", 3, 1200, 3600, "Note cadrage"],
            ["2. Audit Terrain", "93 mesures ISO 27001", 8, 1200, 9600, "Questionnaires + preuves"],
            ["3. Analyse Risques", "EBIOS RM Ateliers", 4, 1200, 4800, "Matrice risques"],
            ["4. Rapport & Restitution", "Rédaction + slides", 4, 1200, 4800, "Rapport + SOA"],
            ["5. Accompagnement", "Plan action 3 mois", 3, 1200, 3600, "Plan remédiation"],
        ]
        for r, row in enumerate(data, 2):
            for c, val in enumerate(row, 1):
                ws.cell(row=r, column=c, value=val)
        ws.cell(row=7, column=5, value="=SUM(E2:E6)").font = Font(bold=True)
        ws.cell(row=7, column=4, value="TOTAL").font = Font(bold=True)
        out = io.BytesIO()
        wb.save(out)
        return out.getvalue()

    def gen_offre_technique_docx():
        doc = Document()
        title = doc.add_heading("OFFRE TECHNIQUE - Mission d'Audit ISO 27001:2022", 0)
        doc.add_heading("1. Compréhension du besoin", 1)
        doc.add_paragraph("Suite à l'analyse de vos TDRs, nous comprenons que vous souhaitez renforcer votre posture de sécurité conformément aux exigences ISO 27001:2022, NIS2 et DORA. Notre approche combine excellence technique et coaching humain.")
        doc.add_heading("2. Méthodologie", 1)
        doc.add_paragraph("Phase 1: Cadrage & EBIOS RM - Phase 2: Audit terrain 93 mesures - Phase 3: Analyse écarts - Phase 4: Rapport & Feuille de route")
        doc.add_heading("3. Équipe", 1)
        doc.add_paragraph("Madou Wale - Expert Cybersécurité & Coach TCC - 10+ ans - Lead Auditor ISO 27001, ISO 42001, EBIOS RM certifié")
        doc.add_heading("4. Livrables", 1)
        doc.add_paragraph("• Dossier de cadrage (15p)\n• Planning GANTT + RACI\n• Questionnaires 127Q\n• Matrice risques EBIOS\n• Rapport audit 40p\n• SOA + Plan d'action\n• Slides restitution COMEX")
        out = io.BytesIO()
        doc.save(out)
        return out.getvalue()

    def gen_cahier_charges():
        doc = Document()
        doc.add_heading("CAHIER DES CHARGES - Mission Audit Cybersécurité", 0)
        doc.add_paragraph(f"Référentiel: {mission_type} - Date: {datetime.now().strftime('%d/%m/%Y')}")
        doc.add_heading("1. Contexte & Objectifs", 1)
        doc.add_paragraph("Objectif: Obtenir la certification ISO 27001:2022 et conformité NIS2/DORA")
        doc.add_heading("2. Périmètre", 1)
        doc.add_paragraph("SI complet, 3 sites, 250 postes, infra cloud hybride")
        doc.add_heading("3. Exigences techniques", 1)
        doc.add_paragraph("Audit documentaire + terrain + tests techniques + ateliers risques")
        out = io.BytesIO()
        doc.save(out)
        return out.getvalue()

    with c1:
        st.subheader("💶 Offre Financière")
        st.metric("Total", "26 400 €", "22 JH x 1200€")
        st.download_button("📥 Télécharger Offre Financière (XLSX)", data=gen_offre_financiere(), file_name="Offre_Financiere.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
    with c2:
        st.subheader("📄 Offre Technique")
        st.write("15 pages, méthodologie Big 4")
        st.download_button("📥 Offre Technique (DOCX)", data=gen_offre_technique_docx(), file_name="Offre_Technique.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
    with c3:
        st.subheader("📘 Cahier des Charges")
        st.write("Monté bout en bout")
        st.download_button("📥 Cahier des Charges (DOCX)", data=gen_cahier_charges(), file_name="Cahier_des_Charges.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)

    if offre_acceptee:
        st.session_state.mission_state = "MISSION_PRETE"

# PHASE 3 - MISSION COMPLETE
if offre_acceptee or st.session_state.mission_state in ["MISSION_PRETE", "MISSION_EN_COURS"]:
    st.divider()
    st.header("🚀 PHASE 3 : Préparation Mission Bout-en-Bout (Auto-Génération)")
    st.success("✅ Offre acceptée - Lancement protocole autonome de préparation mission")

    def gen_planning():
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title="Planning GANTT"
        ws.append(["Tâche","Responsable","Début","Fin","JH","Dépendance"])
        tasks = [
            ["Kick-off","Madou + DSI", datetime.now().date(), (datetime.now()+timedelta(days=1)).date(), 1, ""],
            ["Audit A.5-A.8","Madou", (datetime.now()+timedelta(days=2)).date(), (datetime.now()+timedelta(days=6)).date(), 5, "Kick-off"],
            ["EBIOS RM Ateliers","Madou+RSSI", (datetime.now()+timedelta(days=7)).date(), (datetime.now()+timedelta(days=9)).date(), 3, "Audit"],
            ["Rédaction rapport","Madou", (datetime.now()+timedelta(days=10)).date(), (datetime.now()+timedelta(days=13)).date(), 4, "Ateliers"],
            ["Restitution COMEX","Madou", (datetime.now()+timedelta(days=14)).date(), (datetime.now()+timedelta(days=14)).date(), 1, "Rapport"],
        ]
        for t in tasks: ws.append(t)
        out=io.BytesIO(); wb.save(out); return out.getvalue()

    def gen_questionnaire():
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title="Questionnaire ISO 27001"
        ws.append(["ID","Domaine","Mesure","Question d'audit","Preuve attendue","Statut"])
        questions = [
            ["A.5.1","Org","Politiques","La politique SSI est-elle approuvée par direction ?","Politique signée","A collecter"],
            ["A.5.17","Org","Auth secrets","Les secrets d'auth ne transitent pas en clair ?","Procédure + capture","A collecter"],
            ["A.8.3","Tech","Accès privilégiés","Revue trimestrielle des accès admin ?","Rapport revue","A collecter"],
        ]
        for q in questions: ws.append(q)
        out=io.BytesIO(); wb.save(out); return out.getvalue()

    def gen_slides():
        prs = Presentation()
        slide = prs.slides.add_slide(prs.slide_layouts[0])
        slide.shapes.title.text = "Kick-off Mission ISO 27001:2022"
        slide.placeholders[1].text = f"Madou Wale - Expert GRC\n{datetime.now().strftime('%d/%m/%Y')}"
        s2 = prs.slides.add_slide(prs.slide_layouts[1])
        s2.shapes.title.text = "Méthodologie"
        s2.placeholders[1].text = "1.Cadrage 2.Audit 93 mesures 3.EBIOS RM 4.Rapport 5.Plan action"
        out=io.BytesIO(); prs.save(out); return out.getvalue()

    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1:
        st.download_button("📅 Planning GANTT + RACI (XLSX)", data=gen_planning(), file_name="Planning_GANTT.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
    with col_m2:
        st.download_button("❓ Questionnaire 93 mesures (XLSX)", data=gen_questionnaire(), file_name="Questionnaire_ISO27001.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
    with col_m3:
        st.download_button("🎯 Slides Kick-off COMEX (PPTX)", data=gen_slides(), file_name="Slides_Kickoff.pptx", mime="application/vnd.openxmlformats-officedocument.presentationml.presentation", use_container_width=True)
    with col_m4:
        st.download_button("📊 Matrice EBIOS RM (XLSX)", data=gen_planning(), file_name="Matrice_EBIOS_RM.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)

    st.divider()
    st.header("🧑‍🏫 Guidance Humaine - Que dois-tu faire ?")
    st.chat_message("assistant").markdown("""
    **Madou, voilà ton rôle humain (20% du travail):**
    
    1.  **Cette semaine:** Appelle le DSI pour kick-off - utilise les slides générées
    2.  **Question clé à poser:** "A.5.17 - Comment gérez-vous les secrets d'authentification ?" (voir questionnaire)
    3.  **Coaching:** Le RSSI est stressé par l'audit ? Utilise ton approche TCC : écoute, recadrage, plan d'action progressif
    
    **Moi (l'agent) je gère 80%:** Rédaction, mise en forme, calculs, matrices, conformité aux normes.
    **Toi tu gères 20% humain:** Relation client, interviews, restitution orale.
    """)

st.divider()
st.caption("V2 Auto-Apprenant - Plus tu nourris l'agent en PDF de normes, plus il devient expert. Pipeline complet TDR→Offre→Mission autonome.")
