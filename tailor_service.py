import json
import os
import re
import time
import base64
import urllib.request
import urllib.error


def _call_gemini_direct(system_prompt: str, user_prompt: str, gemini_api_key: str) -> str:
    """Call Google Gemini REST API directly using key."""
    clean_key = re.sub(r'[\s\r\n]+', '', (gemini_api_key or '').strip())
    if not clean_key or "Error" in clean_key:
        raise ValueError("A valid Google Gemini API key is required.")

    models_to_try = ["gemini-3.6-flash", "gemini-flash-latest", "gemini-3.1-pro-preview"]
    payload = {
        "systemInstruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
        "generationConfig": {
            "temperature": 0.1,
            "responseMimeType": "application/json"
        }
    }
    
    last_err = None
    for m in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={clean_key}"
        req_data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=req_data, headers={"Content-Type": "application/json"}, method="POST")
        try:
            import ssl
            ssl_ctx = ssl.create_default_context()
            ssl_ctx.check_hostname = False
            ssl_ctx.verify_mode = ssl.CERT_NONE
            with urllib.request.urlopen(req, timeout=45, context=ssl_ctx) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                parts = res["candidates"][0]["content"]["parts"]
                for p in parts:
                    if "text" in p and p["text"].strip():
                        return p["text"].strip()
        except urllib.error.HTTPError as http_err:
            err_body = http_err.read().decode("utf-8", errors="replace")
            last_err = f"HTTP Error {http_err.code} ({m}): {err_body}"
        except Exception as e:
            last_err = f"Gemini Error ({m}): {str(e)}"

    raise ValueError(f"Gemini API call failed across all attempted models. Details: {last_err}")


def load_cv_data():
    with open("cv_data.json", "r", encoding="utf-8") as f:
        return json.load(f)


def _is_header_line(line_str: str) -> bool:
    """Check if a line is a CV section header using keywords and formatting heuristics."""
    s = line_str.strip()
    if not s or len(s.split()) > 5:
        return False
        
    lower_s = s.lower().strip(":-*• ")
    
    known_headers = {
        "profile", "professional profile", "summary", "about me", "objective", "personal statement",
        "education", "academic background", "academic qualifications", "training", "academic history",
        "projects", "selected projects", "key projects", "academic projects", "personal projects",
        "experience", "work experience", "employment", "professional experience", "professional background", "work history", "military service", "research experience", "clinical experience", "internship", "hospitalist",
        "publications", "selected publications", "journal articles", "articles", "papers", "abstracts", "posters", "presentations",
        "skills", "computational skills", "technical skills", "expertise", "core competencies", "skills & experience", "languages", "language proficiency",
        "certifications", "test scores", "awards", "certificates", "board certification", "licenses", "honors", "honors and awards", "awards and honors",
        "teaching", "teaching experience", "courses taught", "mentorship", "hospital affiliations",
        "conferences", "memberships", "professional affiliations", "volunteer experience", "volunteering", "extracurriculars", "interests", "hobbies"
    }
    
    if lower_s in known_headers or s.endswith(':'):
        return True
        
    strong_roots = ["experience", "education", "skills", "projects", "publications", "certifications", "awards", "summary", "profile", "languages", "affiliations"]
    has_root = any(root in lower_s for root in strong_roots)
    
    if has_root:
        alpha_chars = [c for c in s if c.isalpha()]
        is_all_caps = alpha_chars and all(c.isupper() for c in alpha_chars)
        is_title_case = s.istitle()
        if is_all_caps or is_title_case:
            return True

    return False


def stitch_broken_sentences(text: str) -> str:
    """Stitches broken sentences from PDF extraction back together strictly respecting section and header boundaries."""
    lines = text.splitlines()
    stitched_lines = []
    
    bullet_chars = ('-', '•', '*', '')
    list_pattern = re.compile(r"^([0-9]+|[a-zA-Z])[\.\)]\s+")

    for line in lines:
        stripped_line = line.strip()
        if not stripped_line:
            stitched_lines.append(line)
            continue
            
        is_bullet = stripped_line.startswith(bullet_chars) or bool(list_pattern.match(stripped_line))
        current_is_header = _is_header_line(stripped_line)
        
        if stitched_lines and stitched_lines[-1].strip():
            last_line_stripped = stitched_lines[-1].strip()
            last_is_header = _is_header_line(last_line_stripped)
            ends_with_punctuation = last_line_stripped.endswith(('.', '?', '!'))
            
            if not ends_with_punctuation and not last_is_header and not current_is_header and not is_bullet:
                stitched_lines[-1] = stitched_lines[-1] + " " + stripped_line
                continue
                
        stitched_lines.append(line)

    return "\n".join(stitched_lines)


def parse_cv_pdf(file_bytes: bytes, gemini_key: str = None) -> dict:
    """Parses a CV PDF into structured JSON using Google Gemini API."""
    import io
    import pypdf
    
    clean_gemini = re.sub(r'[\s\r\n]+', '', (gemini_key or os.environ.get("GEMINI_API_KEY") or '').strip())
    if not clean_gemini or "Error" in clean_gemini:
        raise ValueError("A Google Gemini API key is strictly required to parse your CV. Please enter your Gemini API key.")

    extracted_text = ""
    try:
        pdf_reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        for page in pdf_reader.pages:
            t = page.extract_text()
            if t:
                extracted_text += t + "\n"
    except Exception:
        pass

    system_prompt = (
        "You are an expert ATS (Applicant Tracking System) parser. "
        "Your job is to read the candidate's CV and extract it into a strictly structured JSON format. "
        "You MUST return ONLY a raw JSON object with NO markdown codeblocks, NO formatting, and NO extra text.\n\n"
        "EXPECTED JSON SCHEMA:\n"
        "{\n"
        "  \"name\": \"Full Name (or empty string)\",\n"
        "  \"title\": \"Professional Title (or empty string)\",\n"
        "  \"contact\": {\n"
        "    \"location\": \"City, State (or empty)\",\n"
        "    \"email\": \"email address (or empty)\",\n"
        "    \"phone\": \"phone number (or empty)\",\n"
        "    \"links\": [\"URL 1\", \"URL 2\"]\n"
        "  },\n"
        "  \"professional_profile\": \"A brief professional summary paragraph highlighting expertise and goals.\",\n"
        "  \"sections\": [\n"
        "    {\n"
        "      \"section_title\": \"Name of the section (e.g., EDUCATION, EXPERIENCE, SKILLS)\",\n"
        "      \"items\": [\n"
        "        {\n"
        "          \"title_date\": \"The title of the item, role, company, and date (e.g., 'Software Engineer, Google (2020-2023)')\",\n"
        "          \"bullets\": [\"Bullet point 1\", \"Bullet point 2\"]\n"
        "        }\n"
        "      ]\n"
        "    }\n"
        "  ]\n"
        "}\n\n"
        "RULES:\n"
        "1. STRICT TRUTHFULNESS & ANTI-HALLUCINATION: You MUST ONLY use the details provided in the input CV.\n"
        "2. PRESERVE ORIGINAL SECTIONS: Dynamically extract sections as they appear in the original CV.\n"
        "3. COMPLETENESS MANDATE: You MUST extract EVERY SINGLE item in the CV. Do not summarize or skip."
    )

    pdf_base64 = base64.b64encode(file_bytes).decode("utf-8")
    parts = []
    if extracted_text.strip():
        parts.append({"text": f"Here is the extracted text of the CV to parse into JSON:\n---\n{extracted_text.strip()}\n---"})
    else:
        parts.append({"text": "Extract the structured JSON data from this attached CV document."})
        parts.append({
            "inlineData": {
                "mimeType": "application/pdf",
                "data": pdf_base64
            }
        })

    user_prompt = json.dumps(parts) if len(parts) == 1 else parts[0]["text"]
    response_text = _call_gemini_direct(system_prompt, user_prompt, clean_gemini)
    
    text = response_text.strip()
    if text.startswith("```json"): text = text[7:]
    if text.startswith("```"): text = text[3:]
    if text.endswith("```"): text = text[:-3]
    
    return json.loads(text.strip())


def tailor_cv(job_ad_text: str, cv_data: dict = None, status_callback=None, gemini_key: str = None) -> dict:
    """Tailors CV content to match job requirements strictly using Google Gemini."""
    if cv_data is None:
        cv_data = load_cv_data()
    cv_json_str = json.dumps(cv_data, indent=2, ensure_ascii=False)

    clean_gemini = re.sub(r'[\s\r\n]+', '', (gemini_key or os.environ.get("GEMINI_API_KEY") or '').strip())
    if not clean_gemini or "Error" in clean_gemini:
        raise ValueError("A valid Google Gemini API key is strictly required to tailor your CV. Please enter your Gemini API key.")

    system_prompt = (
        "You are an expert CV optimization assistant. "
        "Your task is to tailor a CV to perfectly match a specific job advertisement. You MUST follow these rules exactly:\n\n"
        "1. GROUND TRUTH CONSTRAINT (NEVER BREAK THIS): You MUST ONLY use the education, skills, experiences, and details provided in the input JSON. You are ABSOLUTELY FORBIDDEN from adding, inventing, hallucinating, or assuming ANY information not strictly present in the input data.\n\n"
        "2. ZERO OMISSIONS MANDATE: You MUST preserve 100% of the candidate's history. DO NOT delete, drop, or omit any section, job role, degree, publication, award, or bullet point from the original CV.\n\n"
        "3. WHAT YOU MUST CHANGE (TAILORING & HIGHLIGHTING):\n"
        "   - REWRITE THE PROFILE: Adapt the 'professional_profile' paragraph to highlight the specific themes and requirements requested in the job ad.\n"
        "   - REORDERING: Reorder items within each section to put the most job-relevant items at the top.\n"
        "   - KEYWORD & IMPACT REPHRASING: Sharpen bullet points using industry vocabulary from the job description while keeping all underlying facts 100% true.\n\n"
        "4. TONE (STRICTLY HUMAN): Keep the tone direct, professional, and purely human. DO NOT use AI buzzwords.\n\n"
        "5. OUTPUT FORMAT: Return your response as a single valid JSON object with the EXACT same structure as the input JSON."
    )

    user_prompt = (
        f"JOB ADVERTISEMENT:\n---\n{job_ad_text}\n---\n\n"
        f"GROUND TRUTH CV DATA (JSON):\n---\n{cv_json_str}\n---\n\n"
        "Return the tailored CV as a valid JSON object."
    )

    response_text = _call_gemini_direct(system_prompt, user_prompt, clean_gemini)
    text = response_text.strip()
    if text.startswith("```json"): text = text[7:]
    if text.startswith("```"): text = text[3:]
    if text.endswith("```"): text = text[:-3]
    return json.loads(text.strip())


def analyze_fit(cv_json: dict, job_description: str, gemini_key: str = None) -> dict:
    """Calculates a semantic Fit Score strictly using Google Gemini API."""
    clean_gemini = re.sub(r'[\s\r\n]+', '', (gemini_key or os.environ.get("GEMINI_API_KEY") or '').strip())
    if not clean_gemini or "Error" in clean_gemini:
        raise ValueError("A Google Gemini API key is strictly required to perform a semantic fit analysis.")

    system_prompt = (
        "You are an expert technical recruiter and ATS algorithm. "
        "Analyze how well a candidate's CV matches a provided Job Description. "
        "Perform a deep semantic analysis of the required skills, experience, and domain knowledge.\n\n"
        "Return ONLY a valid JSON object with EXACTLY two keys:\n"
        "1. \"fit_percentage\": An integer from 0 to 100 representing match score.\n"
        "2. \"missing_keywords\": An array of strings containing up to 6 critical missing skills or requirements.\n\n"
        "IMPORTANT: Strictly valid JSON only."
    )

    user_prompt = (
        f"JOB DESCRIPTION:\n{job_description}\n\n"
        f"CANDIDATE CV (JSON):\n{json.dumps(cv_json, indent=2)}\n\n"
        "Return the JSON evaluation."
    )

    response_text = _call_gemini_direct(system_prompt, user_prompt, clean_gemini)
    text = response_text.strip()
    if text.startswith("```json"): text = text[7:]
    if text.startswith("```"): text = text[3:]
    if text.endswith("```"): text = text[:-3]
    return json.loads(text.strip())
