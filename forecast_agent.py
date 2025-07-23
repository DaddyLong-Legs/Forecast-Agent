import streamlit as st
import pandas as pd
import openai
import os
import io
import matplotlib.pyplot as plt

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
                Respond ONLY with a CSV-formatted table enclosed in triple backticks, with columns strictly in the following order: 'Month', 'Paying Users', 'Estimated Churn', 'Monthly Revenue (local currency)'. Use month names only (e.g., January) for the 'Month' column. Ensure the CSV is parsable and values are comma-separated.
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

                try:
                    df.columns = [col.strip() for col in df.columns]
                    df = df.rename(columns={
                        df.columns[1]: "Paying Users",
                        df.columns[2]: "Estimated Churn",
                        df.columns[3]: "Monthly Revenue (local currency)"
                    })

                    for col in ["Paying Users", "Estimated Churn", "Monthly Revenue (local currency)"]:
                        df[col] = pd.to_numeric(df[col], errors='coerce')

                    df = df.dropna()

                    if not df.empty:
                        fig, ax = plt.subplots(figsize=(10, 5))
                        ax.plot(df[df.columns[0]], df["Paying Users"], label="Paying Users", marker='o')
                        ax.plot(df[df.columns[0]], df["Estimated Churn"], label="Estimated Churn", marker='x')
                        ax.plot(df[df.columns[0]], df["Monthly Revenue (local currency)"], label="Revenue", marker='s')
                        ax.set_title("📊 Forecast Overview", fontsize=14)
                        ax.set_xlabel("Month")
                        ax.set_ylabel("Value")
                        ax.grid(True, linestyle='--', alpha=0.5)
                        ax.legend()
                        st.pyplot(fig)
                    else:
                        st.warning("⚠️ Not enough data to plot forecast. Please check the forecast format.")

                except Exception as e:
                    st.error(f"❌ Error during plotting: {e}")

                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df.to_excel(writer, index=False, sheet_name='Forecast')
                st.download_button("📥 Download Forecast as Excel", data=output.getvalue(), file_name="forecast_output.xlsx")

            except Exception as e:
                st.error(f"Error generating forecast: {e}")

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

elif tool == "Quotation Generator":
    st.header("🧾 Cost Quotation Generator")
    st.markdown("### Fill in the following details to generate a commercial quotation.")

    client_name = st.text_input("Client Name")
    service_description = st.text_area("Brief Description of the Service")
    country = st.selectbox("Country", ["Pakistan", "UAE", "Saudi Arabia", "Qatar", "Egypt", "Jordan", "Kuwait", "Bahrain", "Oman", "India", "Bangladesh"])
    operator = st.text_input("Mobile Operator (if applicable)")
    subscription_price = st.number_input("Subscription Price (local currency)", min_value=0.0, format="%.2f")
    revenue_share = st.slider("Proposed Revenue Share (our %)", 0, 100, 50)
    expected_subscribers = st.number_input("Expected Subscriber Base", min_value=0)

    if st.button("Generate Quotation"):
        with st.spinner("Generating quotation..."):
            try:
                openai.api_key = os.getenv("OPENAI_API_KEY")

                quote_prompt = f"""
                You are a business consultant preparing a quotation. Based on the following:
                - Client Name: {client_name}
                - Country: {country}
                - Mobile Operator: {operator}
                - Service Description: {service_description}
                - Subscription Price: {subscription_price} (local currency)
                - Revenue Share (our side): {revenue_share}%
                - Expected Subscribers: {expected_subscribers}

                Prepare a professional commercial quotation in business English, including:
                - A brief intro
                - Summary of the service
                - Commercial proposal (revenue share, price point)
                - Disclaimer for custom terms and actual negotiations
                """

                response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are an experienced commercial proposals specialist."},
                        {"role": "user", "content": quote_prompt}
                    ]
                )

                quotation_text = response.choices[0].message.content
                st.markdown("### 🧾 Generated Quotation")
                st.markdown(quotation_text)

                st.download_button("📄 Download Quotation (TXT)", quotation_text.encode(), file_name="quotation.txt")

            except Exception as e:
                st.error(f"❌ Error generating quotation: {e}")
