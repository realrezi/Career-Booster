import os
import io
import json
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import tailor_service
from tailor_service import analyze_fit, tailor_cv
from pdf_generator import generate_cv_pdf
from docx_generator import generate_cv_docx
from cover_letter_service import generate_cover_letter

app = FastAPI(title="Career Booster API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeFitRequest(BaseModel):
    cv_data: Dict[str, Any]
    job_description: str
    gemini_key: Optional[str] = ""


class CoverLetterRequest(BaseModel):
    cv_data: Dict[str, Any]
    job_description: str
    letter_type: Optional[str] = "corporate"
    tone: Optional[str] = "confident_executive"
    length: Optional[str] = "standard"
    custom_focus: Optional[str] = ""
    gemini_key: Optional[str] = None


class PDFRequest(BaseModel):
    cv_data: Dict[str, Any]
    theme: Optional[str] = "modern"


class DOCXRequest(BaseModel):
    cv_data: Dict[str, Any]
    theme: Optional[str] = "modern"


class TailorCVRequest(BaseModel):
    job_description: str
    cv_data: Dict[str, Any]
    gemini_key: Optional[str] = ""


@app.get("/api/health")
def health_check():
    return {"status": "ok", "app": "Career Booster API"}


@app.post("/api/parse-cv")
async def parse_cv(
    file: UploadFile = File(...),
    gemini_key: str = Form(...)
):
    try:
        if not gemini_key or not gemini_key.strip():
            raise ValueError("A Google Gemini API key is strictly required to parse your CV.")

        file_bytes = await file.read()
        if not file_bytes:
            raise ValueError("Uploaded file is empty.")

        parsed_data = tailor_service.parse_cv_pdf(file_bytes, gemini_key=gemini_key)
        return {"parsed_data": parsed_data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/analyze-fit")
def analyze_fit_endpoint(req: AnalyzeFitRequest):
    try:
        result = analyze_fit(req.cv_data, req.job_description, gemini_key=req.gemini_key)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/tailor-cv")
def tailor_cv_endpoint(req: TailorCVRequest):
    try:
        tailored_data = tailor_cv(
            req.job_description, 
            cv_data=req.cv_data,
            gemini_key=req.gemini_key
        )
        return {"tailored_data": tailored_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/generate-cover-letter")
def generate_cover_letter_endpoint(req: CoverLetterRequest):
    try:
        letter_text = generate_cover_letter(
            cv_data=req.cv_data,
            job_description=req.job_description,
            letter_type=req.letter_type or "corporate",
            tone=req.tone or "confident_executive",
            length=req.length or "standard",
            custom_focus=req.custom_focus or "",
            gemini_key=req.gemini_key
        )
        return {"cover_letter": letter_text}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/generate-pdf")
def generate_pdf_endpoint(req: Dict[str, Any]):
    try:
        cv_data = req.get("cv_data") or req
        theme = req.get("theme", "modern")
        pdf = generate_cv_pdf(cv_data, theme=theme)
        pdf_bytes = bytes(pdf.output())
        return Response(content=pdf_bytes, media_type="application/pdf", headers={
            "Content-Disposition": "attachment; filename=Tailored_CV.pdf"
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")


@app.post("/api/generate-docx")
def generate_docx_endpoint(req: Dict[str, Any]):
    try:
        cv_data = req.get("cv_data") or req
        theme = req.get("theme", "modern")
        docx_stream = generate_cv_docx(cv_data, theme=theme)
        return Response(content=docx_stream.getvalue(), media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document", headers={
            "Content-Disposition": "attachment; filename=Tailored_CV.docx"
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DOCX generation failed: {str(e)}")


from fastapi.staticfiles import StaticFiles

frontend_dist = os.path.join(os.path.dirname(__file__), "frontend", "dist")
if os.path.exists(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
