import streamlit as st
from docx import Document
from fpdf import FPDF
import base64
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import os

# Session state initialization
if "quotation_text" not in st.session_state:
    st.session_state.quotation_text = ""
    st.session_state.poc_email = ""
    st.session_state.client_name = ""

# Sample quotation data generator (replace with real logic)
def generate_quotation(client_name, poc_name, poc_email, project_days, daily_rate, support_cost):
    development_cost = project_days * daily_rate
    deployment_cost = round(development_cost * 0.2)  # Example 20% of dev cost
    total_cost = development_cost + deployment_cost + support_cost

    quotation_text = f"""
Quotation for {client_name}

Point of Contact: {poc_name} ({poc_email})

Itemized Cost:
+-----------------------------+--------------------------+
| Item                       | Cost (in local currency) |
+-----------------------------+--------------------------+
| Development                | {development_cost:<24} |
| Deployment                 | {deployment_cost:<24} |
| Annual Support & Maintenance | {support_cost:<24} |
+-----------------------------+--------------------------+
| Total                      | {total_cost:<24} |
+-----------------------------+--------------------------+
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

# Helper to send email
def send_email(receiver_email, subject, body, attachments=[]):
    sender_email = "awais@planetbeyond.co.uk"
    sender_password = "rzzk qtxh hraq kdeu"
    smtp_server = "smtp.gmail.com"
    smtp_port = 587

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    for file_path in attachments:
        if file_path.endswith(".pdf"):  # only attach PDF
            with open(file_path, "rb") as f:
                part = MIMEApplication(f.read(), Name=os.path.basename(file_path))
                part['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
                msg.attach(part)

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.ehlo()
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
    except smtplib.SMTPAuthenticationError as auth_err:
        raise RuntimeError("Authentication failed. Please check your SMTP credentials.") from auth_err

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
    st.session_state.quotation_text = quotation_text
    st.session_state.poc_email = poc_email
    st.session_state.client_name = client_name

if st.session_state.quotation_text:
    st.subheader("📄 Generated Quotation")
    st.code(st.session_state.quotation_text, language='text')

    word_path = create_word_doc(st.session_state.quotation_text)
    with open(word_path, "rb") as f:
        st.download_button("📥 Download Word File", f, file_name="quotation.docx")

    pdf_path = create_pdf_doc(st.session_state.quotation_text)
    with open(pdf_path, "rb") as f:
        st.download_button("📥 Download PDF File", f, file_name="quotation.pdf")

    if st.button("✉️ Send Quotation to Client"):
        try:
            send_email(
                receiver_email=st.session_state.poc_email,
                subject=f"Quotation from Business Assistant Suite - {st.session_state.client_name}",
                body=st.session_state.quotation_text,
                attachments=[pdf_path]  # Only PDF is emailed
            )
            st.success(f"Quotation emailed to {st.session_state.poc_email} successfully!")
        except Exception as e:
            st.error(f"Failed to send email: {e}")
