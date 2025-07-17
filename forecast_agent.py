import streamlit as st
import pandas as pd
import openai
import os
import io
import matplotlib.pyplot as plt

# Set page configuration
st.set_page_config(page_title="Business Forecasting Agent", layout="wide")
st.title("\U0001F4CA Business Forecasting Agent")

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

# Conditionally enable/disable mobile operator
if deployment_model == "White Label":
    mobile_operator = "Not Applicable"
    st.selectbox("Mobile Operator", ["N/A"], disabled=True)
else:
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

# ARPU mapping per operator per country
arpu_map = {
    "Pakistan": {"Jazz": 1.5, "Telenor": 1.2, "Zong": 1.4, "Ufone": 1.1},
    "UAE": {"Etisalat": 25, "du": 22},
    "Saudi Arabia": {"STC": 20, "Mobily": 18, "Zain": 17},
    "India": {"Jio": 2.5, "Airtel": 3.2, "Vi": 2.1},
    # Add more country-operator ARPUs here...
}

arpu = arpu_map.get(country, {}).get(mobile_operator, 0.0)

if arpu:
    st.info(f"⚙️ Average ARPU for {mobile_operator}, {country}: {arpu} (local currency)")
else:
    st.warning("⚠️ No ARPU data found for selected country/operator. Please ensure values are correct.")

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
            - Average Monthly ARPU: {arpu} (local currency)
            - Forecast Duration: 12 months

            Respond ONLY with a CSV-formatted table enclosed in triple backticks, with a first column called 'Month' listing the 12 months and then including at minimum: 'Monthly Revenue (local currency)', 'Paying Users', and 'Estimated Churn'.
            Ensure the CSV is parsable and values are comma-separated.
            """

            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert business forecasting assistant."},
                    {"role": "user", "content": forecast_prompt}
                ]
            )

            forecast_text = response.choices[0].message.content
            st.session_state["forecast_output"] = forecast_text
            st.session_state["forecast_done"] = True

            from io import StringIO
            import re

            csv_like = re.findall(r"(?<=```)([\s\S]*?)(?=```)", forecast_text)
            data = csv_like[0] if csv_like else forecast_text

            st.text_area("📄 Raw Forecast Output (Debug)", data, height=200)

            try:
                df = pd.read_csv(StringIO(data), sep="," if "," in data else "\t", engine="python", on_bad_lines='warn')
            except Exception as parse_error:
                st.error("❌ Failed to parse forecast data. Please check the format returned by GPT.")
                raise parse_error

            st.session_state["forecast_df"] = df

            st.markdown("---")
            st.subheader("📈 Forecast Output")
            st.dataframe(df)

            expected_cols = {
                "Monthly Revenue (local currency)": None,
                "Paying Users": None,
                "Estimated Churn": None
            }

            for col in df.columns:
                col_norm = col.strip().lower()
                if "revenue" in col_norm and expected_cols["Monthly Revenue (local currency)"] is None:
                    expected_cols["Monthly Revenue (local currency)"] = col
                elif ("paying" in col_norm or "subscribers" in col_norm) and expected_cols["Paying Users"] is None:
                    expected_cols["Paying Users"] = col
                elif "churn" in col_norm and expected_cols["Estimated Churn"] is None:
                    expected_cols["Estimated Churn"] = col

            plot_columns = [col for col in expected_cols.values() if col is not None]
            time_col = df.columns[0]

            if len(plot_columns) >= 2 and time_col in df.columns:
                try:
                    for col in plot_columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                    df[time_col] = df[time_col].astype(str)
                    df_plot = df[[time_col] + plot_columns].dropna()

                    if df_plot.empty:
                        st.warning("⚠️ Forecast data is empty after cleaning. Cannot plot.")
                    else:
                        fig, ax = plt.subplots(figsize=(10, 5))
                        for col in plot_columns:
                            ax.plot(df_plot[time_col], df_plot[col], label=col, marker='o')

                        ax.set_title("📊 Forecast Overview", fontsize=14)
                        ax.set_xlabel(time_col)
                        ax.set_ylabel("Value")
                        ax.grid(True, linestyle='--', alpha=0.5)
                        ax.legend()
                        st.pyplot(fig)
                except Exception as e:
                    st.error(f"❌ Error during plotting: {e}")
            else:
                st.warning("⚠️ Not enough data to plot forecast. Please check the forecast format.")

            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Forecast')
            st.download_button("📥 Download Forecast as Excel", data=output.getvalue(), file_name="forecast_output.xlsx")

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
