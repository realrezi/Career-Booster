# 🚀 Career Booster — AI-Powered Academic & Executive Career Engine

[![Live Demo](https://img.shields.io/badge/Live_Demo-Vercel-6366f1?style=for-the-badge&logo=vercel)](https://career-booster-delta.vercel.app)
[![License](https://img.shields.io/badge/License-MIT-10b981?style=for-the-badge)](LICENSE)
[![Python](https://img.shields.io/badge/Backend-FastAPI_/_Python-3776ab?style=for-the-badge&logo=python)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/Frontend-React_/_Vite-61dafb?style=for-the-badge&logo=react)](https://react.dev)

> **Career Booster** is an autonomous, publication-grade career platform designed for academics, researchers, and executives. It parses existing PDF CVs into structured Ground Truth data, evaluates job vacancy alignment in real time, tailors qualifications with zero hallucination, and generates customized Cover & Motivation Letters.

Developed by **[Ahmadreza Shirdel](https://github.com/realrezi)**.

---

## 🌟 Core Features & Capabilities

- 📄 **1. Native Vision CV Parsing**: Upload your academic or corporate CV PDF; Google Gemini Vision extracts degrees, publications, skills, and work history into 100% truthful Ground Truth JSON with zero hallucinated credentials.
- 🎯 **2. Real-Time Semantic Match Scoring**: Paste any job description to evaluate your alignment percentage and see missing domain keywords in real time.
- ⚡ **3. 100% Truthful CV Tailoring**: Re-orders and reframes your profile summary and achievements to highlight job relevance while preserving 100% of candidate history with zero omissions.
- ✉️ **4. Cover & Motivation Letter Studio**: Generates customizable academic motivation letters (Master's / PhD / Postdoc) or corporate cover letters for any position with tailored goals, tones, and length targets.
- 🎨 **5. Multi-Theme PDF & Editable MS Word Exporter**: Download ready-to-submit vector PDFs or editable MS Word (`.docx`) files in 3 visual themes (*Modern Executive*, *Classic Academic*, *Minimalist Tech*).
- 🔒 **6. Privacy-First Session Memory**: User API keys and CV files remain strictly in local browser session memory and are **never saved** to persistent storage or external servers.

---

## 🛠️ Technology Stack

- **Frontend**: React 18, Vite, Lucide Icons, Vanilla Glassmorphism CSS.
- **Backend**: Python 3.11+, FastAPI, Uvicorn, FPDF2, python-docx, PyPDF.
- **AI Models**: Google Gemini 3.6 Flash, Gemini Flash Latest.
- **Deployment**: Vercel Serverless Functions.

---

## 🚀 Quick Start (Local Development)

### 1. Clone the repository
```bash
git clone https://github.com/realrezi/Career-Booster.git
cd Career-Booster
```

### 2. Set up Backend Dependencies
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Set up Frontend Dependencies
```bash
cd frontend
npm install
npm run build
cd ..
```

### 4. Run the Application
```bash
python3 server.py
```
Open [http://localhost:8000](http://localhost:8000) in your browser!

---

## ⚖️ Educational Use Disclaimer

This software is built strictly for **educational, demonstration, and personal career development purposes**. Users provide their own Google Gemini API key which is processed in transient session memory.

---

## 👨‍💻 Author

**Ahmadreza Shirdel**  
- Email: [ahmadrezashirdel@gmail.com](mailto:ahmadrezashirdel@gmail.com)  
- GitHub: [@realrezi](https://github.com/realrezi)
