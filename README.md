# 📄 Academic CV Tailor

An open-access, AI-powered Streamlit web application designed to tailor academic CVs for PhD, postdoc, and research assistant positions. 

This app extracts text from an uploaded CV, organizes it into a structured JSON representation (the "Ground Truth"), allows the user to review and correct the parsed data, and then tailors it to match a pasted academic job advertisement using direct Google Gemini (Gemini 2.0 Flash) or fallback OpenRouter models.

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

1. **Clone the repository:**
   ```bash
   git clone <your-repository-url>
   cd <repository-folder>
   ```

2. **Install dependencies:**
   ```bash
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
* `requirements.txt`: Pinned Python package requirements.
* `.env.example`: Template for optional local key storage. Copy to `.env` (git-ignored).
* `run.sh`: Loads `.env` if present, then launches Streamlit.

