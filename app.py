import streamlit as st
from fpdf import FPDF
import datetime
import streamlit.components.v1 as components

# Injection du mode PWA
pwa_code = """
<link rel="manifest" href="/manifest.json">
<script>
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/sw.js');
  }
</script>
"""
components.html(pwa_code, height=0)
# --- CONFIGURATION ---
st.set_page_config(page_title="Facturation Expert", page_icon="💼", layout="wide")

class PDF(FPDF):
    def header(self):
        try:
            self.image('logo.png', 10, 8, 33)
        except:
            pass 
        self.set_font("helvetica", "B", 20)
        self.set_text_color(40, 40, 110)
        self.cell(0, 10, "FACTURE", border=False, ln=True, align="R")
        self.ln(20)

    def footer(self):
        self.set_y(-25)
        self.set_font("helvetica", "I", 8)
        self.cell(0, 5, "Indemnite forfaitaire pour frais de recouvrement de 40 euros due en cas de retard.", ln=True, align="C")

def generate_pdf(client, liste_prods, invoice_no, tva_rate, my_info, iban_bic):
    pdf = PDF()
    pdf.add_page()
    euro = chr(128)
    
    # --- ZONE ADRESSES (CORRIGÉE) ---
    pdf.set_font("helvetica", "B", 11)
    
    # Colonne GAUCHE (Ma Société)
    pdf.set_xy(10, 40)
    pdf.cell(90, 7, my_info['nom'].upper(), ln=0)
    
    # Colonne DROITE (Destinaire)
    pdf.set_xy(110, 40)
    pdf.cell(90, 7, "DESTINATAIRE :", ln=1)
    
    pdf.set_font("helvetica", size=10)
    
    # Texte GAUCHE
    pdf.set_xy(10, 47)
    pdf.multi_cell(90, 5, f"{my_info['adresse']}\nSIRET : {my_info['siret']}")
    
    # Texte DROITE (On s'aligne sur la même hauteur que la gauche)
    pdf.set_xy(110, 47)
    pdf.multi_cell(0, 5, f"{client['nom']}\n{client['adresse']}")
    
    # On descend le curseur après les adresses pour la suite
    pdf.set_y(80)

    # --- INFOS FACTURE ---
    pdf.set_fill_color(230, 230, 230)
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(0, 10, f"FACTURE N : {invoice_no}  |  Date : {datetime.date.today()}  |  Echeance : {datetime.date.today() + datetime.timedelta(days=30)}", fill=True, ln=True, align="C")
    pdf.ln(5)

    # --- TABLEAU ---
    pdf.set_fill_color(40, 40, 110)
    pdf.set_text_color(255)
    pdf.cell(90, 10, " Description", border=1, fill=True)
    pdf.cell(25, 10, "Qte", border=1, fill=True, align="C")
    pdf.cell(35, 10, "Prix Unit. HT", border=1, fill=True, align="C")
    pdf.cell(40, 10, "Total HT", border=1, fill=True, ln=True, align="C")

    pdf.set_text_color(0)
    pdf.set_font("helvetica", size=10)
    total_ht = 0
    for p in liste_prods:
        total_ht += p['qte'] * p['prix']
        pdf.cell(90, 10, f" {p['desc']}", border=1)
        pdf.cell(25, 10, str(p['qte']), border=1, align="C")
        pdf.cell(35, 10, f"{p['prix']:.2f} {euro}", border=1, align="R")
        pdf.cell(40, 10, f"{p['qte']*p['prix']:.2f} {euro}", border=1, ln=True, align="R")

    # --- TOTAUX ---
    tva_m = total_ht * (tva_rate / 100)
    pdf.ln(5)
    pdf.set_x(130)
    pdf.cell(35, 8, "Total HT", border=0)
    pdf.cell(35, 8, f"{total_ht:.2f} {euro}", border=1, ln=True, align="R")
    pdf.set_x(130)
    pdf.cell(35, 8, f"TVA ({tva_rate}%)", border=0)
    pdf.cell(35, 8, f"{tva_m:.2f} {euro}", border=1, ln=True, align="R")
    pdf.set_font("helvetica", "B", 12)
    pdf.set_x(130)
    pdf.set_fill_color(40, 40, 110)
    pdf.set_text_color(255)
    pdf.cell(35, 10, "TOTAL TTC", border=1, fill=True)
    pdf.cell(35, 10, f"{total_ht + tva_m:.2f} {euro}", border=1, fill=True, align="R", ln=True)

    # --- BANQUE ---
    pdf.ln(10)
    pdf.set_text_color(0)
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(0, 5, "COORDONNEES BANCAIRES", ln=True)
    pdf.set_font("helvetica", size=9)
    pdf.cell(0, 5, f"IBAN : {iban_bic['iban']}", ln=True)
    pdf.cell(0, 5, f"BIC : {iban_bic['bic']}", ln=True)

    return pdf.output()

# --- APP STREAMLIT ---
if 'mes_produits' not in st.session_state:
    st.session_state.mes_produits = []

with st.sidebar:
    st.header("⚙️ Ma Societe")
    ma_soc = st.text_input("Nom", "Mon Entreprise")
    mon_adr = st.text_area("Adresse", "123 Rue de l'Exemple, 75001 Paris")
    mon_sir = st.text_input("SIRET", "123 456 789 00001")
    m_iban = st.text_input("IBAN", "FR76...")
    m_bic = st.text_input("BIC", "XXXX")
    tva_v = st.number_input("TVA %", 20)

c_cl, c_prod = st.columns([1, 2])

with c_cl:
    st.subheader("👤 Client")
    n_cli = st.text_input("Nom Client")
    a_cli = st.text_area("Adresse Client")
    num_f = st.text_input("N Facture", "FAC-001")

with c_prod:
    st.subheader("📝 Articles")
    with st.form("form_ajout", clear_on_submit=True):
        col1, col2, col3 = st.columns([3,1,1])
        d = col1.text_input("Description")
        q = col2.number_input("Qté", min_value=1)
        p = col3.number_input("Prix Unit. HT", min_value=0.0)
        submitted = st.form_submit_button("Ajouter l'article")
        
        if submitted and d:
            st.session_state.mes_produits.append({"desc": d, "qte": q, "prix": p})
            st.rerun()

    if st.session_state.mes_produits:
        st.table(st.session_state.mes_produits)
        if st.button("🗑️ Vider la liste"):
            st.session_state.mes_produits = []
            st.rerun()

if st.session_state.mes_produits and n_cli:
    st.divider()
    try:
        pdf_bytes = generate_pdf({"nom": n_cli, "adresse": a_cli}, st.session_state.mes_produits, num_f, tva_v, {"nom": ma_soc, "adresse": mon_adr, "siret": mon_sir}, {"iban": m_iban, "bic": m_bic})
        st.download_button("📥 TELECHARGER LA FACTURE (PDF)", data=bytes(pdf_bytes), file_name=f"{num_f}.pdf", mime="application/pdf", use_container_width=True)
    except Exception as e:
        st.error(f"Erreur : {e}")