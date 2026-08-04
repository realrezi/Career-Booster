import json
import os
import re
import urllib.request
import urllib.error


def generate_cover_letter(
    cv_data: dict,
    job_description: str,
    letter_type: str = "corporate",
    tone: str = "confident_executive",
    length: str = "standard",
    custom_focus: str = "",
    gemini_key: str = None
) -> str:
    """Generates a highly tailored cover or motivation letter using Google Gemini."""
    
    cv_json_str = json.dumps(cv_data, indent=2, ensure_ascii=False)
    
    type_prompts = {
        "academic_phd": "Write an Academic Motivation Letter / Statement of Purpose suitable for Master's, PhD, Postdoc, or Research applications. Emphasize relevant methodology, academic background, key skills, and alignment with the program/position requirements.",
        "corporate": "Write a professional Corporate Cover Letter tailored for an industry or enterprise position. Highlight relevant achievements, leadership, analytical problem solving, and strategic value.",
        "executive": "Write a high-level Executive Leadership Letter. Focus on strategic vision, cross-functional leadership, revenue/impact growth, and organizational transformation.",
        "career_change": "Write a persuasive Career Transition Letter. Focus on transferable skills, adaptability, domain cross-over potential, and strong passion for the new field."
    }
    
    tone_prompts = {
        "academic_formal": "Use a formal, rigorous, and scholarly academic tone.",
        "confident_executive": "Use a confident, results-oriented, and decisive executive tone.",
        "passionate": "Use an enthusiastic, highly engaged, and mission-aligned tone.",
        "direct": "Use a direct, concise, and no-nonsense professional tone."
    }
    
    length_prompts = {
        "short": "Keep the letter concise and punchy (approximately 250-300 words, 3 structured paragraphs).",
        "standard": "Provide a well-developed standard letter (approximately 400-450 words, 4 structured paragraphs).",
        "comprehensive": "Provide a thorough and detailed academic/motivation letter (approximately 550-650 words, 5 structured paragraphs)."
    }
    
    type_instr = type_prompts.get(letter_type, type_prompts["corporate"])
    tone_instr = tone_prompts.get(tone, tone_prompts["confident_executive"])
    length_instr = length_prompts.get(length, length_prompts["standard"])
    
    custom_instr = f"ADDITIONAL USER HIGHLIGHT INSTRUCTION: Ensure you explicitly highlight: {custom_focus}" if custom_focus and custom_focus.strip() else ""
    
    system_prompt = (
        "You are an expert executive career strategist and academic advisor. "
        "Your task is to write a compelling, tailored cover letter or motivation letter connecting a candidate's ground truth CV to a target job description.\n\n"
        "RULES:\n"
        "1. STRICT TRUTHFULNESS: Only mention degrees, roles, skills, and publications present in the candidate's CV data. Do NOT invent achievements or qualifications.\n"
        f"2. TYPE & GOAL: {type_instr}\n"
        f"3. TONE: {tone_instr}\n"
        f"4. LENGTH: {length_instr}\n"
        "5. HUMAN TONE: Avoid generic AI clichés like 'spearheaded', 'leveraged', 'testament', or 'seamlessly'. Write naturally as an accomplished professional.\n"
        f"{custom_instr}\n\n"
        "OUTPUT FORMAT:\n"
        "Return ONLY the complete letter text in clean Markdown format with standard letter headers (Date, Recipient, Salutation, Body Paragraphs, Sign-off)."
    )

    user_prompt = (
        f"TARGET JOB DESCRIPTION:\n---\n{job_description}\n---\n\n"
        f"CANDIDATE GROUND TRUTH CV DATA:\n---\n{cv_json_str}\n---\n\n"
        "Generate the custom letter now in clean Markdown."
    )

    clean_gemini_key = re.sub(r'[\s\r\n]+', '', (gemini_key or os.environ.get("GEMINI_API_KEY") or '').strip())
    if not clean_gemini_key or "Error" in clean_gemini_key:
        raise ValueError("A valid Google Gemini API key is strictly required to generate cover letters.")

    models_to_try = ["gemini-3.6-flash", "gemini-flash-latest", "gemini-3.1-pro-preview"]
    payload = {
        "systemInstruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
        "generationConfig": {"temperature": 0.3}
    }
    
    last_err = None
    for m in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={clean_gemini_key}"
        req_data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=req_data, headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=45) as resp:
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

    raise ValueError(f"Failed to generate cover letter using Google Gemini API. Details: {last_err}")
