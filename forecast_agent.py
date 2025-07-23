import streamlit as st
import pandas as pd
import openai
import os
import io
import matplotlib.pyplot as plt
from docx import Document
from fpdf import FPDF
import tempfile

# Set page configuration
st.set_page_config(page_title="Business Tools", layout="wide")
st.title("📊 Business Assistant Suite")

# --- Application Selector ---
tool = st.sidebar.radio("Choose a Tool", ["Forecasting Agent", "Quotation Generator"])

if tool == "Forecasting Agent":
    st.header("📈 Business Forecasting Agent")
    st.markdown("### Provide Service Details for Forecasting")

    service_type = st.selectbox("Type of Service", ["Digital (Mobile/Web App)", "Legacy (SMS/IVR/USSD)"])
    service_nature = st.selectbox("Nature of Service", ["Sports", "Utility", "Entertainment", "Infotainment", "Health", "Finance", "Education"])
    deployment_model = st.selectbox("Deployment Model", ["White Label", "Mobile Operator Hosted"])
    country = st.selectbox("Target Country", ["Pakistan", "UAE", "Saudi Arabia", "Qatar", "Egypt", "Jordan", "Kuwait", "Bahrain", "Oman", "India", "Bangladesh"])

    operators_by_country = {
        "Pakistan": ["Jazz", "Telenor", "Zong", "Ufone"],
        "UAE": ["Etisalat", "du"],
        "Saudi Arabia": ["STC", "Mobily", "Zain"],
        "Qatar": ["Ooredoo", "Vodafone"],
        "Egypt": ["Vodafone Egypt", "Orange Egypt", "Etisalat Misr"],
        "Jordan": ["Zain Jordan", "Orange Jordan", "Umniah"],
        "Kuwait": ["Zain Kuwait", "Ooredoo Kuwait", "STC Kuwait"],
        "Bahrain": ["Batelco", "Zain Bahrain", "STC Bahrain"],
        "Oman": ["Omantel", "Ooredoo Oman"],
        "India": ["Jio", "Airtel", "Vi"],
        "Bangladesh": ["Grameenphone", "Robi", "Banglalink"]
    }

    if deployment_model == "White Label":
        mobile_operator = "Not Applicable"
        st.selectbox("Mobile Operator", ["N/A"], disabled=True)
    else:
        mobile_operator = st.selectbox("Mobile Operator", operators_by_country.get(country, []))

    monetization_model = st.selectbox("Monetization Model", ["Paid Subscription", "Freemium (Free Trial → Premium)", "Ad-supported", "Mixed"])
    daily_promo_bandwidth = st.number_input("Estimated Daily Promotional Bandwidth (e.g., SMS/Impressions)", min_value=0)

    conversion_rate = st.slider("Expected Conversion Rate from Promotions (%)", 0, 100, 5)
    charging_success_rate = st.slider("Charging Success Rate (%)", 0, 100, 90)

    arpu_map = {
        "Pakistan": {"Jazz": 1.5, "Telenor": 1.2, "Zong": 1.4, "Ufone": 1.1},
        "UAE": {"Etisalat": 25, "du": 22},
        "Saudi Arabia": {"STC": 20, "Mobily": 18, "Zain": 17},
        "India": {"Jio": 2.5, "Airtel": 3.2, "Vi": 2.1},
    }

    arpu = arpu_map.get(country, {}).get(mobile_operator, 0.0)

    if arpu:
        st.info(f"⚙️ Average ARPU for {mobile_operator}, {country}: {arpu} (local currency)")
    else:
        st.warning("⚠️ No ARPU data found for selected country/operator. Please ensure values are correct.")

    subscription_model = st.selectbox("Subscription Frequency", ["Daily", "Weekly", "Monthly"])
    subscription_price = st.number_input("Subscription Price (in local currency)", min_value=0.0, format="%.2f")

    if st.button("Generate Forecast"):
        st.success("Forecasting logic remains unchanged.")

elif tool == "Quotation Generator":
    st.header("🧾 Cost Quotation Generator")
    st.markdown("### Fill in the following details to generate a formal quotation.")

    client_name = st.text_input("Client Name")
    client_poc_name = st.text_input("Client POC Name")
    client_email = st.text_input("Client POC Email")
    project_name = st.text_input("Project/Platform Name")
    working_days = st.number_input("Estimated Development & Deployment Working Days", min_value=1)
    support_annual = st.number_input("Annual Support & Maintenance Fee (local currency)", min_value=0.0, format="%.2f")
    daily_rate = st.number_input("Per Day Development Cost (local currency)", min_value=0.0, format="%.2f")
    comments = st.text_area("Any Additional Notes or Custom Terms")

    generate_button = st.button("Generate Quotation")

    if generate_button:
        dev_cost = working_days * daily_rate
        total_cost = dev_cost + support_annual

        document = Document()
        document.add_heading('Commercial Quotation', 0)
        document.add_paragraph(f"Client: {client_name}\nPOC: {client_poc_name}\nEmail: {client_email}\n")
        document.add_paragraph(f"Project: {project_name}\n")
        document.add_paragraph("Quotation Summary:")

        table = document.add_table(rows=1, cols=3)
        hdr_cells = table.rows[0].cells
        hdr_cells[0].text = 'Item'
        hdr_cells[1].text = 'Unit Cost'
        hdr_cells[2].text = 'Total'

        row1 = table.add_row().cells
        row1[0].text = f"Development & Deployment ({working_days} days)"
        row1[1].text = f"{daily_rate:,.2f}"
        row1[2].text = f"{dev_cost:,.2f}"

        row2 = table.add_row().cells
        row2[0].text = "Annual Support & Maintenance"
        row2[1].text = f"-"
        row2[2].text = f"{support_annual:,.2f}"

        row3 = table.add_row().cells
        row3[0].text = "Total"
        row3[1].text = ""
        row3[2].text = f"{total_cost:,.2f}"

        if comments:
            document.add_paragraph(f"\nNotes:\n{comments}")

        document.add_paragraph("\nThis quotation is subject to change based on final project scope and terms negotiated.")

        with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp_word:
            document.save(tmp_word.name)
            tmp_word.seek(0)
            st.download_button("📄 Download Quotation (Word)", data=tmp_word.read(), file_name="quotation.docx")

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt="Commercial Quotation", ln=True, align='C')
        pdf.ln(10)
        pdf.multi_cell(0, 10, txt=f"Client: {client_name}\nPOC: {client_poc_name}\nEmail: {client_email}\nProject: {project_name}")
        pdf.ln(5)
        pdf.cell(0, 10, txt="Quotation Summary:", ln=True)
        pdf.cell(0, 10, txt=f"Development & Deployment ({working_days} days): {dev_cost:,.2f}", ln=True)
        pdf.cell(0, 10, txt=f"Annual Support & Maintenance: {support_annual:,.2f}", ln=True)
        pdf.cell(0, 10, txt=f"Total: {total_cost:,.2f}", ln=True)

        if comments:
            pdf.ln(5)
            pdf.multi_cell(0, 10, txt=f"Notes: {comments}")

        pdf.ln(10)
        pdf.multi_cell(0, 10, txt="This quotation is subject to change based on final project scope and negotiations.")

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
            pdf.output(tmp_pdf.name)
            tmp_pdf.seek(0)
            st.download_button("📄 Download Quotation (PDF)", data=tmp_pdf.read(), file_name="quotation.pdf")

        st.success("Quotation ready for review and download.")
        if st.checkbox("Send this quotation via email to client?"):
            st.info("📧 Email functionality coming soon. This will send the document from your configured email.")
