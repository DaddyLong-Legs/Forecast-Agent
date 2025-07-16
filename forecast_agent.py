import streamlit as st
import openai
import pandas as pd
import plotly.express as px
from io import BytesIO

# UI Setup
st.set_page_config(page_title="Business Case Forecasting Agent", layout="wide")
st.title("📈 Business Case Forecasting Agent")

# API Key Input (temporary use for local testing)
openai_api_key = st.secrets["OPENAI_API_KEY"]
if not openai_api_key:
    st.warning("Please enter your OpenAI API key to proceed.")
    st.stop()

openai.api_key = openai_api_key

# Step-by-step Inputs
st.header("1. Define Your Service")
service_type = st.selectbox("Type of Service", ["Digital - Mobile App", "Digital - Web App", "Legacy - SMS", "Legacy - IVR", "Legacy - USSD"])
nature = st.selectbox("Nature of Service", ["Entertainment", "Utility", "Infotainment", "Sports", "Religious", "Education", "Others"])
label_type = st.radio("Is this a White-label or Operator-branded service?", ["White-label", "Operator-branded"])
regions = st.multiselect("Target Region(s)", ["Pakistan", "MENA", "South Asia", "Africa", "Europe", "Other"])

if st.button("🔍 Generate Forecast"):
    with st.spinner("Talking to GPT-4..."):
        # Construct prompt
        prompt = f"""
You're a telecom business analyst. Based on the following service inputs, generate a 12-month forecast for:
- Monthly Subscriber Base
- Monthly Growth Rate (%)
- Monthly Churn Rate (%)
- Monthly Revenue (in USD, estimate based on avg ARPU)

Inputs:
- Type of Service: {service_type}
- Nature of Service: {nature}
- Label Type: {label_type}
- Regions: {", ".join(regions)}

Output as a table with columns: Month, Subscribers, Growth Rate, Churn Rate, Revenue
Start with Month 1 and project until Month 12.
"""

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a data analyst specializing in telecom forecasting."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
        )

        raw_output = response['choices'][0]['message']['content']
        st.subheader("📊 Forecast Table (GPT-4 Generated)")

        # Try to parse the response into a DataFrame
        try:
            # Auto-detect markdown or tabular text
            df = pd.read_csv(pd.compat.StringIO(raw_output), sep=",")

        except Exception:
            try:
                # If markdown table
                df = pd.read_fwf(pd.compat.StringIO(raw_output))
            except Exception as e:
                st.error("⚠️ Could not parse GPT output. Please try again or check the response format.")
                st.text_area("Raw Output", raw_output)
                st.stop()

        # Display Table
        st.dataframe(df)

        # Show Charts
        fig = px.line(df, x="Month", y=["Subscribers", "Revenue"], markers=True, title="Subscribers & Revenue Over Time")
        st.plotly_chart(fig, use_container_width=True)

        # Download Excel
        st.subheader("⬇️ Download Forecast")
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Forecast')
        st.download_button("Download Excel", data=output.getvalue(), file_name="forecast.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
