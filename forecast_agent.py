import streamlit as st
from docx import Document
from fpdf import FPDF
import base64
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import os
import pandas as pd
import requests

# Dynamic churn rates per category (assumed from public benchmarks)
CATEGORY_CHURN_RATES = {
    "Entertainment": 0.15,
    "Religious": 0.05,
    "Informational": 0.08,
    "Games": 0.12,
    "Utility": 0.07,
    "Music": 0.10,
    "Education": 0.06
}

# External datasets for subscriber base and ARPU (fallback if live fetch fails)
EXTERNAL_DATA = {
    "Pakistan": {
        "Telenor": {"base": 47000000, "arpu": 210},
        "Jazz": {"base": 72000000, "arpu": 260},
        "Zong": {"base": 47000000, "arpu": 240},
        "Ufone": {"base": 23000000, "arpu": 180}
    },
    "UAE": {
        "Etisalat": {"base": 12000000, "arpu": 390},
        "Du": {"base": 8500000, "arpu": 360}
    },
    "KSA": {
        "STC": {"base": 27000000, "arpu": 320},
        "Mobily": {"base": 19000000, "arpu": 290},
        "Zain": {"base": 16000000, "arpu": 270}
    },
    "Egypt": {
        "Vodafone Egypt": {"base": 44000000, "arpu": 150},
        "Etisalat Misr": {"base": 25000000, "arpu": 140},
        "Orange Egypt": {"base": 27000000, "arpu": 135}
    },
    "South Africa": {
        "Vodacom": {"base": 43000000, "arpu": 250},
        "MTN": {"base": 35000000, "arpu": 240},
        "Cell C": {"base": 16000000, "arpu": 200}
    }
}

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
    st.header("\U0001F4C4 Quotation Generator")
    st.text_input("Client Name", key="client_name")
    st.text_input("POC Email", key="poc_email")
    logo = st.file_uploader("Upload Company Logo", type=["png", "jpg", "jpeg"], key="logo_file")
    st.text_area("Quotation Description", key="quotation_text")
    
    if st.button("Generate Quotation PDF"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, txt=f"Quotation for {st.session_state.client_name}", ln=True, align='C')
        pdf.ln(10)
        pdf.set_font("Arial", size=12)
        for line in st.session_state.quotation_text.split('\n'):
            pdf.multi_cell(0, 10, txt=line)
        pdf_path = "/tmp/quotation_final.pdf"
        pdf.output(pdf_path)
        with open(pdf_path, "rb") as f:
            st.download_button("\U0001F4E5 Download Quotation PDF", f, file_name="quotation.pdf")

    if st.button("Email Quotation"):
        try:
            sender_email = "your-email@example.com"
            receiver_email = st.session_state.poc_email
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = receiver_email
            msg['Subject'] = f"Quotation from {st.session_state.company_name}"

            body = f"Hi {st.session_state.client_name},\n\nPlease find the attached quotation."
            msg.attach(MIMEText(body, 'plain'))

            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(200, 10, txt=f"Quotation for {st.session_state.client_name}", ln=True, align='C')
            pdf.ln(10)
            pdf.set_font("Arial", size=12)
            for line in st.session_state.quotation_text.split('\n'):
                pdf.multi_cell(0, 10, txt=line)
            pdf_path = "/tmp/quotation_email.pdf"
            pdf.output(pdf_path)

            with open(pdf_path, "rb") as f:
                part = MIMEApplication(f.read(), Name="quotation.pdf")
                part['Content-Disposition'] = 'attachment; filename="quotation.pdf"'
                msg.attach(part)

            with smtplib.SMTP('smtp.example.com', 587) as server:
                server.starttls()
                server.login(sender_email, 'your-password')
                server.sendmail(sender_email, receiver_email, msg.as_string())

            st.success("Quotation emailed successfully.")
        except Exception as e:
            st.error(f"Failed to send email: {e}")

with tab1:
    st.header("\U0001F4C8 Forecasting Agent")

    st.subheader("Service Configuration")
    service_group = st.selectbox("Service Group", ["Legacy (SMS, IVR, USSD)", "Digital (Web, Mobile App)"])
    is_telco_branded = st.radio("Branding Type", ["Telco-branded", "White-label"])

    region = st.selectbox("Country/Region", list(EXTERNAL_DATA.keys()))
    operator_options = {k: list(v.keys()) for k, v in EXTERNAL_DATA.items()}

    if is_telco_branded == "Telco-branded":
        operator = st.selectbox("Operator Name", operator_options.get(region, []))
    else:
        st.selectbox("Operator Name", ["Not Applicable"], disabled=True)
        operator = None

    nature_of_service = st.selectbox("Nature of Service", ["Subscription Based", "One-time", "Freemium", "Ad Supported"])
    category = st.selectbox("Category", list(CATEGORY_CHURN_RATES.keys()))

    st.subheader("Conversion & Revenue Inputs")
    opt_in_percentage = st.slider("Opt In Percentage (%)", 0, 100, 2)
    charging_success = st.slider("Charging Success Rate (%)", 0, 100, 8)
    promotional_bandwidth = st.number_input("Daily Promotional Bandwidth", min_value=0, value=1_000_000)

    subscription_model = st.selectbox("Subscription Model", ["Daily", "Weekly", "Monthly"])
    price_per_day = st.number_input("Price per Subscription Day", min_value=0, value=3)

    if operator:
        operator_total_base = EXTERNAL_DATA[region][operator]["base"]
        estimated_arpu = EXTERNAL_DATA[region][operator]["arpu"]
    else:
        operator_total_base = 0
        estimated_arpu = 0

    st.markdown(f"**Total Subscriber Base:** {operator_total_base:,}")
    st.markdown(f"**ARPU (Monthly):** {estimated_arpu}")

    if st.button("Generate Forecast"):
        try:
            forecast_data = []
            churn_rate = CATEGORY_CHURN_RATES.get(category, 0.1)
            retention_window = 3  # months
            daily_new_users = int(promotional_bandwidth * (opt_in_percentage / 100))
            cumulative_users = []
            active_users = 0
            retained_by_month = [0] * 12

            for month in range(1, 13):
                potential_new_users = operator_total_base - active_users
                monthly_acquired = min(daily_new_users * 30, potential_new_users)

                # More realistic retention modeling
                if month > retention_window:
                    churned_users = retained_by_month[month - retention_window - 1] * churn_rate
                else:
                    churned_users = 0

                active_users += monthly_acquired - churned_users
                retained_by_month[month - 1] = monthly_acquired

                revenue = active_users * price_per_day * 30 * charging_success / 100

                forecast_data.append({
                    "Month": f"Month {month}",
                    "MonthNumber": month,
                    "New Users": int(monthly_acquired),
                    "Churned Users": int(churned_users),
                    "Total Subscribers": int(active_users),
                    "Revenue": round(revenue, 2)
                })

            df_forecast = pd.DataFrame(forecast_data)
            df_forecast = df_forecast.sort_values("MonthNumber")

            st.subheader("12-Month Forecast Summary")
            st.line_chart(data=df_forecast.set_index("MonthNumber")["Revenue"])
            st.dataframe(df_forecast.drop(columns=["MonthNumber"]))

            st.markdown(f"""
            **Daily New Users:** {daily_new_users:,}  
            **Monthly Churn Rate (Category: {category}):** {int(churn_rate * 100)}%  
            **Charging Success Rate:** {charging_success}%  
            **Operator Base Considered:** {operator_total_base:,}  
            **Retention Window:** {retention_window} months  
            **Operator ARPU:** {estimated_arpu}
            """)

            csv = df_forecast.drop(columns=["MonthNumber"]).to_csv(index=False).encode('utf-8')
            st.download_button("\U0001F4E5 Download Forecast CSV", csv, "forecast_12_months.csv", "text/csv")

            excel_path = "/tmp/forecast_12_months.xlsx"
            with pd.ExcelWriter(excel_path, engine='xlsxwriter') as writer:
                df_forecast.drop(columns=["MonthNumber"]).to_excel(writer, index=False, sheet_name="Forecast")

            with open(excel_path, "rb") as f:
                st.download_button("\U0001F4E5 Download Forecast Excel", f, "forecast_12_months.xlsx")

        except Exception as e:
            st.error(f"Forecast generation failed: {e}")
