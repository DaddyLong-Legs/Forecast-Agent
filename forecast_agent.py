import streamlit as st
from docx import Document
from fpdf import FPDF
import base64

# Sample quotation data generator (replace with real logic)
def generate_quotation(client_name, poc_name, poc_email, project_days, daily_rate, support_cost):
    total_cost = project_days * daily_rate + support_cost
    quotation_text = f"""
    Quotation for {client_name}

    Point of Contact: {poc_name} ({poc_email})

    Itemized Cost:
    - Development Days: {project_days} days @ {daily_rate}/day = {project_days * daily_rate}
    - Annual Support and Maintenance: {support_cost}

    Total Quotation: {total_cost}
    """
    return quotation_text, total_cost

# Helper to download Word file
def create_word_doc(text):
    doc = Document()
    for line in text.split('\n'):
        doc.add_paragraph(line)
    file_path = "/tmp/quotation.docx"
    doc.save(file_path)
    return file_path

# Helper to download PDF file
def create_pdf_doc(text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    for line in text.split('\n'):
        pdf.cell(200, 10, txt=line, ln=True)
    file_path = "/tmp/quotation.pdf"
    pdf.output(file_path)
    return file_path

# UI Layout
st.title("📊 Business Assistant Suite")
st.header("💰 Quotation Generator")

with st.form("quotation_form"):
    client_name = st.text_input("Client Name")
    poc_name = st.text_input("POC Name")
    poc_email = st.text_input("POC Email")
    project_days = st.number_input("Estimated Development + Deployment Days", min_value=1)
    daily_rate = st.number_input("Daily Rate (in local currency)", min_value=1)
    support_cost = st.number_input("Annual Support & Maintenance (in local currency)", min_value=0)
    submit = st.form_submit_button("Generate Quotation")

if submit:
    quotation_text, total = generate_quotation(client_name, poc_name, poc_email, project_days, daily_rate, support_cost)
    st.subheader("📄 Generated Quotation")
    st.code(quotation_text, language='text')

    word_path = create_word_doc(quotation_text)
    with open(word_path, "rb") as f:
        st.download_button("📥 Download Word File", f, file_name="quotation.docx")

    pdf_path = create_pdf_doc(quotation_text)
    with open(pdf_path, "rb") as f:
        st.download_button("📥 Download PDF File", f, file_name="quotation.pdf")

    if st.button("✉️ Send Quotation to Client"):
        # Add email sending logic here, e.g., using smtplib or an external API
        st.success(f"Quotation emailed to {poc_email} successfully!")
