import streamlit as st
import json
import os

from tailor_service import tailor_cv, extract_text_from_pdf, parse_cv_text
from pdf_generator import generate_cv_pdf

st.set_page_config(page_title="Academic CV Tailor", layout="centered")

st.title("📄 Academic CV Tailor")
st.markdown(
    "Tailor your academic CV for specific PhD, postdoc, or research assistant positions using AI. "
    "This tool extracts your CV structure, allows you to verify it, and strictly aligns your actual accomplishments "
    "to the job advertisement without fabricating fake skills or degrees."
)

st.info(
    "ℹ️ **How it works:** \n"
    "1. **Upload your CV** (PDF) to build your verified, structured Ground Truth profile.\n"
    "2. **Verify & edit** the parsed JSON structure to ensure 100% accuracy.\n"
    "3. **Paste the job description** and select your model/API key.\n"
    "4. **Generate** a tailored, print-ready PDF CV with optimized, honest framing."
)

# API Key configuration in Sidebar
st.sidebar.header("🔑 API Keys")
st.sidebar.caption(
    "Paste a key from either provider below. Keys stay in this browser session only, "
    "are never written to disk, and are used for both CV parsing and tailoring."
)

# Google Gemini — the box always starts empty. If a GEMINI_API_KEY is present in the
# environment (e.g. from a local .env file) it is used silently as a fallback, but it is
# never rendered into the widget so it cannot leak on a shared or deployed instance.
gemini_key_input = st.sidebar.text_input(
    "Google Gemini API Key",
    value="",
    type="password",
    placeholder="AIza...",
    help="Get a free key at https://aistudio.google.com/apikey",
)
if gemini_key_input:
    os.environ["GEMINI_API_KEY"] = gemini_key_input
gemini_api_key = gemini_key_input or os.environ.get("GEMINI_API_KEY", "")

# OpenRouter — same behaviour: starts empty, env var is a silent fallback.
or_key_input = st.sidebar.text_input(
    "OpenRouter API Key",
    value="",
    type="password",
    placeholder="sk-or-v1-...",
    help="Get a free key at https://openrouter.ai/keys",
)
if or_key_input:
    os.environ["OPENROUTER_API_KEY"] = or_key_input
openrouter_api_key = or_key_input or os.environ.get("OPENROUTER_API_KEY", "")

if gemini_api_key or openrouter_api_key:
    st.sidebar.success("✅ Key detected — AI parsing and tailoring enabled.")
else:
    st.sidebar.warning(
        "⚠️ No API key provided. The app still works using its offline heuristic "
        "parser and tailorer, but results are noticeably better with a key."
    )

# Model selection
model_options = []
if gemini_api_key:
    model_options.append("Direct Google Gemini (gemini-2.0-flash)")
if openrouter_api_key:
    model_options.extend([
        "openrouter/free",
        "google/gemma-2-9b-it:free",
        "google/gemma-4-26b-a4b-it:free",
        "nvidia/nemotron-3-super-120b-a12b:free",
        "openai/gpt-oss-20b:free"
    ])
# If neither key is entered, show a placeholder
if not model_options:
    model_options = ["Offline Fallback Parser & Tailor"]

model_choice = st.sidebar.selectbox(
    "🤖 Select Model / Method:",
    model_options
)

# Manage session state for parsed CV
if "parsed_cv" not in st.session_state:
    st.session_state.parsed_cv = None
if "uploaded_file_name" not in st.session_state:
    st.session_state.uploaded_file_name = None

st.markdown("---")
st.markdown("### 📤 Step 1: Upload Your Academic CV (PDF)")
uploaded_file = st.file_uploader("Select your base CV PDF:", type=["pdf"])

if uploaded_file is not None:
    if st.session_state.uploaded_file_name != uploaded_file.name:
        status_container = st.empty()

        def update_parse_status(msg):
            status_container.info(f"⏳ {msg}")

        with st.spinner("Extracting PDF text..."):
            try:
                raw_text = extract_text_from_pdf(uploaded_file)
            except Exception as e:
                st.error(f"Error reading PDF file: {e}")
                raw_text = None

        if raw_text:
            try:
                # If Offline is selected or no API key, let parse_cv_text handle the fallback
                model_arg = "openrouter/free"
                if "gemini-2.0-flash" in model_choice:
                    model_arg = "gemini-2.0-flash"
                elif model_choice == "Offline Fallback Parser & Tailor":
                    model_arg = "offline"

                parsed_json = parse_cv_text(
                    raw_text, model_arg, status_callback=update_parse_status)
                st.session_state.parsed_cv = parsed_json
                st.session_state.uploaded_file_name = uploaded_file.name
                status_container.empty()
                st.success("CV parsed and structured successfully!")
            except Exception as e:
                status_container.empty()
                st.error(f"An error occurred while parsing your CV: {e}")

if st.session_state.parsed_cv is not None:
    st.markdown("### 📋 Step 2: Verify & Edit your Ground Truth CV Data")
    st.info("💡 You can review or correct the parsed JSON representation of your CV before tailoring.")

    cv_json_str = json.dumps(st.session_state.parsed_cv,
                             indent=2, ensure_ascii=False)
    edited_json_str = st.text_area(
        "Structured CV JSON", value=cv_json_str, height=300)

    try:
        st.session_state.parsed_cv = json.loads(edited_json_str)
    except json.JSONDecodeError:
        st.error(
            "⚠️ Invalid JSON format. Please ensure your edits maintain valid JSON syntax.")

    st.markdown("### 📝 Step 3: Job Advertisement Details")

    # Backing store for the job ad textarea widget
    if "job_ad_text" not in st.session_state:
        st.session_state.job_ad_text = ""

    st.text_area(
        "Paste the full job advertisement text here:",
        height=250,
        key="job_ad_text",
        help="Copy the vacancy text from the job posting page and paste it here."
    )
    st.caption(
        f"{len(st.session_state.job_ad_text)} characters loaded")

    if st.button("✨ Generate Tailored CV", type="primary"):
        if not st.session_state.job_ad_text.strip():
            st.error("Please paste the job advertisement text first.")
        else:
            status_container = st.empty()

            def update_tailor_status(msg):
                status_container.info(f"⏳ {msg}")

            try:
                # Resolve selected model / method
                model_arg = "openrouter/free"
                if "gemini-2.0-flash" in model_choice:
                    model_arg = "gemini-2.0-flash"
                elif model_choice == "Offline Fallback Parser & Tailor":
                    model_arg = "offline"

                # Pass the dynamic parsed CV and status callback
                tailored_data = tailor_cv(
                    st.session_state.job_ad_text, model_arg,
                    st.session_state.parsed_cv, status_callback=update_tailor_status)
                status_container.empty()
                pdf = generate_cv_pdf(tailored_data)
                pdf_output_path = "tailored_cv.pdf"
                pdf.output(pdf_output_path)

                st.success("CV tailored successfully!")

                with open(pdf_output_path, "rb") as f:
                    pdf_bytes = f.read()

                st.download_button(
                    label="📥 Download Tailored CV (PDF)",
                    data=pdf_bytes,
                    file_name="Academic_CV_Tailored.pdf",
                    mime="application/pdf",
                )

                with st.expander("🔍 View Tailored JSON Data (Verification)"):
                    st.json(tailored_data)

            except Exception as e:
                status_container.empty()
                st.error(f"An error occurred during tailoring: {e}")
