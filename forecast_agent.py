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
country = st.selectbox(
    "Target Country",
    ["Pakistan", "UAE", "Saudi Arabia", "Qatar", "Egypt", "Jordan", "Kuwait", "Bahrain", "Oman", "India", "Bangladesh"]
)

# Country to operators mapping
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

mobile_operator = st.selectbox("Mobile Operator", operators_by_country.get(country, []))
monetization_model = st.selectbox("Monetization Model", ["Paid Subscription", "Freemium (Free Trial → Premium)", "Ad-supported", "Mixed"])
daily_promo_bandwidth = st.number_input("Estimated Daily Promotional Bandwidth (e.g., SMS/Impressions)", min_value=0)

conversion_rate = st.slider(
    "Expected Conversion Rate from Promotions (%)",
    0, 100, 5,
    help="Estimated % of users who respond to promotional messages and subscribe"
)

charging_success_rate = st.slider(
    "Charging Success Rate (%)",
    0, 100, 90,
    help="Estimated % of subscription attempts that are successfully charged"
)

# Subscription model details
subscription_model = st.selectbox("Subscription Frequency", ["Daily", "Weekly", "Monthly"])
subscription_price = st.number_input("Subscription Price (in local currency)", min_value=0.0, format="%.2f")

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
            - Target Country: {country}
            - Mobile Operator: {mobile_operator}
            - Monetization Model: {monetization_model}
            - Daily Promotional Bandwidth: {daily_promo_bandwidth}
            - Conversion Rate from Promotions: {conversion_rate}%
            - Charging Success Rate: {charging_success_rate}%
            - Subscription Model: {subscription_model}
            - Subscription Price: {subscription_price} (local currency)
            - Forecast Duration: 12 months

            Generate a detailed subscriber forecast including:
            - Total Monthly Active Users
            - Churn Rate (Monthly)
            - Monthly Net Growth
            - Estimated Monthly Revenue (in local currency of {country})

            Assume that daily promotional bandwidth reflects the maximum number of new potential users who can be reached each day.
            Multiply the bandwidth with the conversion rate to estimate new users, then apply charging success rate to compute paying users.
            For subscription model:
            - Daily: users are charged {subscription_price} every day
            - Weekly: users are charged {subscription_price} every week
            - Monthly: users are charged {subscription_price} every month

            Incorporate this charging model and charging success rate into the monthly revenue forecasts.

            Use public ARPU benchmarks of the selected mobile operator in the given country to improve estimate reliability.
            Factor in the impact of promotional reach, price sensitivity, user churn/conversion, and monetization effectiveness.

            Display the output in a 12-row table (1 per month). Base your assumptions on known telecom trends and available public operator data.
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
                {f"Here is a sample reference:\n{file_summary}" if file_summary else ""}

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
