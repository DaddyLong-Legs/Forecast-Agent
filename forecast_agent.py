import streamlit as st
import pandas as pd
import openai
import os

# Set page configuration
st.set_page_config(page_title="Business Forecasting Agent", layout="wide")
st.title("📊 Business Forecasting Agent")

# --- User Inputs ---
st.markdown("### Provide Service Details for Forecasting")

service_type = st.selectbox("Type of Service", ["Digital (Mobile/Web App)", "Legacy (SMS/IVR/USSD)"])
service_nature = st.selectbox("Nature of Service", ["Sports", "Utility", "Entertainment", "Infotainment", "Health", "Finance", "Education"])
deployment_model = st.selectbox("Deployment Model", ["White Label", "Mobile Operator Hosted"])
regions = st.text_input("Target Regions (e.g., UAE, Pakistan, MENA)")
monetization_model = st.selectbox("Monetization Model", ["Paid Subscription", "Freemium (Free Trial → Premium)", "Ad-supported", "Mixed"])

# Submit button to run forecast
if st.button("Generate Forecast"):
    with st.spinner("Generating 12-month forecast using AI..."):
        try:
            openai.api_key = os.getenv("OPENAI_API_KEY")

            forecast_prompt = f"""
            You are a business analyst assistant. A user is planning a digital service with the following inputs:

            - Type of Service: {service_type}
            - Nature of Service: {service_nature}
            - Deployment Model: {deployment_model}
            - Target Regions: {regions}
            - Monetization Model: {monetization_model}
            - Forecast Duration: 12 months

            Generate a detailed subscriber forecast including:
            - Total Monthly Active Users
            - Churn Rate (Monthly)
            - Monthly Net Growth
            - Estimated Monthly Revenue

            Use typical conversion rates and churn assumptions based on the monetization model provided.
            Display the output in a 12-row table (1 per month). Base your assumptions on known regional trends.

            If model is freemium, consider trial conversion rate. If paid-only, factor in higher churn at start.
            """

            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert business forecasting assistant."},
                    {"role": "user", "content": forecast_prompt}
                ]
            )

            forecast_result = response.choices[0].message.content
            st.session_state["forecast_output"] = forecast_result
            st.session_state["forecast_done"] = True

            st.markdown("---")
            st.subheader("📈 Forecast Output")
            st.markdown(forecast_result)

        except Exception as e:
            st.error(f"Error generating forecast: {e}")

# --- Refinement Section ---
if st.session_state.get("forecast_done"):
    st.markdown("---")
    st.subheader("🔁 Refine the Forecast")

    ref_input = st.text_area("Optional: Share an example or feedback to refine results")
    example_file = st.file_uploader("Or upload a sample reference (CSV/XLSX)", type=["csv", "xlsx"])

    if st.button("Update Forecast"):
        with st.spinner("Updating forecast based on feedback..."):
            try:
                file_summary = ""
                if example_file is not None:
                    df_example = pd.read_csv(example_file) if example_file.name.endswith(".csv") else pd.read_excel(example_file)
                    file_summary = df_example.head().to_string()

                refine_prompt = f"""
                Revise the following forecast based on this user feedback: '{ref_input}'
                {f"Here is a sample reference:
{file_summary}" if file_summary else ""}

                The original forecast was:
                {st.session_state['forecast_output']}
                """

                refined_response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are an expert business forecasting assistant."},
                        {"role": "user", "content": refine_prompt}
                    ]
                )

                refined_output = refined_response.choices[0].message.content
                st.markdown("### 🔄 Updated Forecast")
                st.markdown(refined_output)

            except Exception as e:
                st.error(f"Error updating forecast: {e}")
