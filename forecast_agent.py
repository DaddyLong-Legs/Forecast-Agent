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
    st.session_state.logo_file = None
    st.session_state.company_name = "Planet Beyond Pakistan (Pvt.) Ltd."

# Tab layout
tab1, tab2 = st.tabs(["Forecasting Agent", "Quotation Generator"])

with tab2:
    st.header("\U0001F4B0 Quotation Generator")

    st.subheader("Company Branding")
    company_name = st.text_input("Company Name", value=st.session_state.company_name)
    logo_file = st.file_uploader("Upload Company Logo (PNG or JPG)", type=["png", "jpg", "jpeg"])
    if logo_file:
        st.session_state.logo_file = logo_file
    st.session_state.company_name = company_name

    # Sample quotation data generator (replace with real logic)
    def generate_quotation(client_name, poc_name, poc_email, project_days, daily_rate, support_cost):
        development_cost = project_days * daily_rate
        deployment_cost = round(development_cost * 0.2)
        total_cost = development_cost + deployment_cost + support_cost

        quotation_text = f"""
{st.session_state.company_name}

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

        if "logo_file" in st.session_state and st.session_state.logo_file:
            logo_path = "/tmp/company_logo.png"
            with open(logo_path, "wb") as f:
                f.write(st.session_state.logo_file.read())
            pdf.image(logo_path, x=10, y=8, w=40)
            pdf.ln(30)

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
            if file_path.endswith(".pdf"):
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
        st.subheader("\U0001F4C4 Generated Quotation")
        st.code(st.session_state.quotation_text, language='text')

        word_path = create_word_doc(st.session_state.quotation_text)
        with open(word_path, "rb") as f:
            st.download_button("\U0001F4E5 Download Word File", f, file_name="quotation.docx")

        pdf_path = create_pdf_doc(st.session_state.quotation_text)
        with open(pdf_path, "rb") as f:
            st.download_button("\U0001F4E5 Download PDF File", f, file_name="quotation.pdf")

        if st.button("✉️ Send Quotation to Client"):
            try:
                send_email(
                    receiver_email=st.session_state.poc_email,
                    subject=f"Quotation from {st.session_state.company_name} - {st.session_state.client_name}",
                    body=st.session_state.quotation_text,
                    attachments=[pdf_path]
                )
                st.success(f"Quotation emailed to {st.session_state.poc_email} successfully!")
            except Exception as e:
                st.error(f"Failed to send email: {e}")

with tab1:
    st.header("\U0001F4C8 Forecasting Agent")

    st.subheader("Service Configuration")
    service_type = st.selectbox("Type of Service", ["Legacy", "New"])
    operator_type = st.selectbox("Operator Type", ["Operator", "Aggregator"])
    country = st.text_input("Country", value="Pakistan")
    operator = st.text_input("Operator Name", value="Telenor")

    st.subheader("Conversion & Revenue Inputs")
    charging_success = st.slider("Charging Success Rate (%)", 0, 100, 8)
    onboarding_success = st.slider("Onboarding Success from Promotions (%)", 0, 100, 2)
    promotional_bandwidth = st.number_input("Daily Promotional Bandwidth", min_value=0, value=1_000_000)

    subscription_model = st.selectbox("Subscription Model", ["Daily", "Weekly", "Monthly"])
    price_per_day = st.number_input("Price per Subscription Day", min_value=0, value=3)

    if st.button("Generate Forecast"):
        try:
            subscribers = int(promotional_bandwidth * (onboarding_success / 100))
            churn = int(subscribers * 0.1)
            net_subs = subscribers - churn
            revenue = net_subs * price_per_day

            forecast_data = {
                "Month": ["Month 1"],
                "Subscribers": [subscribers],
                "Churn": [churn],
                "Revenue": [revenue]
            }

            st.subheader("Forecast Summary")
            st.write(forecast_data)

            st.bar_chart({"Revenue": forecast_data["Revenue"]})
        except Exception as e:
            st.error(f"Forecast generation failed: {e}")
