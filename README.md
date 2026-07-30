# 📄 Career Booster — Academic CV Tailor

[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/built%20with-Streamlit-FF4B4B.svg)](https://streamlit.io)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

> Tailor your academic CV to any PhD, postdoc, or research vacancy — without inventing a single credential.

An open-access, AI-powered Streamlit web application designed to tailor academic CVs for PhD, postdoc, and research assistant positions.

This app extracts text from an uploaded CV, organizes it into a structured JSON representation (the "Ground Truth"), lets you review and correct the parsed data, then tailors it to match a pasted academic job advertisement using Google Gemini 2.0 Flash directly or fallback OpenRouter models.

**Why the Ground Truth step matters:** most AI CV tools happily invent a publication or a skill to match a job ad, which is career-ending in academia. Here the structured JSON is the hard boundary. The model may filter, reorder, and rephrase what is in it, but it cannot add to it, and you get to inspect and correct that JSON before anything is generated.


## 🚀 Key Features

* **📤 Upload Any PDF CV:** Instantly extract text from your own CV.
* **⚡ Direct Google Gemini API Support:** Uses `gemini-2.0-flash` directly via Google AI Studio API for ultra-fast, structured JSON parsing and tailoring.
* **📝 Paste the Job Ad:** Drop the vacancy text straight into the app, no formatting cleanup needed.
* **🔌 Offline Fallback Parser & Tailor:** If API keys are missing, rate-limited, or blocked by local geographic firewalls, the app seamlessly switches to a highly optimized regex & heuristic-based offline engine. No crashes, 100% reliability.
* **📋 Interactive Verification:** Edit the parsed JSON directly inside the web interface to verify and correct your "Ground Truth" before any tailoring happens.
* **🧠 Anti-Hallucination Tailoring:** Implements a strict "Transferable Skills Framing" prompt that optimizes CV bullet points, aligns keywords, and rewrites the professional profile *without* hallucinating or fabricating degrees, projects, or skills.
* **📥 Dynamic PDF Compilation:** Programmatic, professional A4 PDF generation using FPDF with safety checks to skip empty sections and prevent orphaned headers.

---

## 🛠️ Installation & Local Running

Requires Python 3.9 or newer.

1. **Clone the repository:**
   ```bash
   git clone https://github.com/realrezi/Career-Booster.git
   cd Career-Booster
   ```

2. **Install dependencies** (a virtual environment is recommended):
   ```bash
   python3 -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   ```


3. **Launch the application:**
   ```bash
   streamlit run app.py
   ```

4. **Paste an API key into the sidebar.**
   The two key boxes in the sidebar are the primary way to supply credentials. Grab a free key from:
   * Google Gemini: [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
   * OpenRouter: [openrouter.ai/keys](https://openrouter.ai/keys)

   Either one is enough. With no key at all the app still runs on its offline heuristic engines.

### Optional: keep a key on your machine

If you would rather not retype your key every session, copy `.env.example` to `.env`, fill in your
key, and start the app with `./run.sh`. The env var is picked up as a silent fallback and is **never**
rendered back into the sidebar boxes, so a deployed instance always shows empty fields to visitors.

`.env` is listed in `.gitignore` and will not be committed.

---

## 🔒 A note on API keys

* Keys typed into the sidebar live in the Streamlit session only. They are not written to disk, not logged, and not persisted between runs.
* Never commit a key. Git history keeps deleted secrets recoverable forever, so a leaked key must be revoked at the provider, not just removed from a file.
* If you deploy publicly, leave the secrets empty and let each visitor bring their own key.

---


## 🌐 Deploying to Streamlit Community Cloud

Deploying this app is completely free and takes just a few steps:

1. Push your code to a public GitHub repository.
2. Visit [Streamlit Share](https://share.streamlit.io/) and log in with your GitHub account.
3. Click **New app** and select your repository, branch, and `app.py` as the entrypoint.
4. **Leave Secrets empty.** Each visitor pastes their own key into the sidebar, so the app costs you nothing and exposes no credentials. Only add a key under **Advanced settings → Secrets** if the deployment is private and you intend to pay for everyone's usage.
5. Click **Deploy!**

---

## 📂 Project Structure

* `app.py`: Streamlit frontend interface, sidebar key entry, and model selection.
* `tailor_service.py`: Text extraction (`pypdf`), CV parsing, anti-hallucination tailoring prompt, Gemini/OpenRouter clients with retry and offline fallback.
* `pdf_generator.py`: Generates the print-ready A4 PDF CV programmatically from structured JSON.
* `cv_data.json`: Anonymized sample profile, used only as a fallback when no CV has been uploaded.
* `requirements.txt`: Pinned Python package requirements.
* `.streamlit/config.toml`: Theme, 5 MB upload cap, telemetry disabled.
* `.env.example`: Template for optional local key storage. Copy to `.env` (git-ignored).
* `run.sh`: Loads `.env` if present, then launches Streamlit.
* `LICENSE`: MIT.

---

## ⚠️ Known limitations

* **Text-based PDFs only.** Extraction uses `pypdf`, so a scanned or image-only CV yields no text. There is no OCR step.
* **Parsing is best-effort.** Unusual CV layouts (multi-column, heavy tables) can confuse both the LLM and the offline parser. This is exactly why Step 2 lets you correct the JSON by hand.
* **The offline engine is a safety net, not a peer.** Regex heuristics keep the app functional without a key, but the output is noticeably weaker than an LLM pass.
* **Free-tier models are rate-limited.** OpenRouter free models return 429s under load. The app retries and falls back, but a Gemini key is the smoother path.
* **PDF output is capped at two pages** by design, matching typical academic application limits.

---

## 🤝 Contributing

Issues and pull requests are welcome. Two ground rules:

1. Never commit an API key, a real CV, or any generated PDF. `.gitignore` covers the usual cases, so check `git status` before committing.
2. Changes to the tailoring prompt in `tailor_service.py` must preserve the anti-hallucination constraint. The model filters and rephrases the Ground Truth; it never adds to it.


