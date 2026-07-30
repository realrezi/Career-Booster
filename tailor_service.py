import json
import os
import re
import time
import concurrent.futures
from openai import OpenAI


def _call_gemini_direct(system_prompt: str, user_prompt: str, gemini_api_key: str) -> str:
    """Call Google Gemini directly using the OpenAI-compatible API endpoint."""
    client = OpenAI(
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        api_key=gemini_api_key
    )
    response = client.chat.completions.create(
        model="gemini-2.0-flash",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.1
    )
    return response.choices[0].message.content


def load_cv_data():
    with open("cv_data.json", "r", encoding="utf-8") as f:
        return json.load(f)


def extract_text_from_pdf(pdf_file) -> str:
    from pypdf import PdfReader
    reader = PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text


def parse_cv_text(raw_text: str, model: str = "openrouter/free", status_callback=None) -> dict:
    if model == "offline":
        if status_callback:
            status_callback("Using offline fallback heuristic parser...")
        return parse_cv_text_offline(raw_text)

    system_prompt = (
        "You are an expert academic CV parsing assistant specializing in medicine, science, and research applications. "
        "Your task is to parse unstructured text from an academic CV and organize it into a structured JSON format following the schema below exactly:\n\n"
        "{\n"
        "  \"name\": \"Full Name (include academic titles or degrees like MD, PhD if present in the text)\",\n"
        "  \"title\": \"Academic/Professional Title (e.g., Postdoctoral Researcher, PhD Candidate, Medical Doctor)\",\n"
        "  \"contact\": {\n"
        "    \"location\": \"Location (City, Country)\",\n"
        "    \"email\": \"email@address.com\",\n"
        "    \"phone\": \"Phone number (or empty if not present)\",\n"
        "    \"links\": [\n"
        "      \"Professional links (e.g., ResearchGate, LinkedIn, GitHub, Google Scholar, ORCID)\"\n"
        "    ]\n"
        "  },\n"
        "  \"professional_profile\": \"A brief, professional summary paragraph highlighting research interests, expertise, and academic goals.\",\n"
        "  \"education\": [\n"
        "    {\n"
        "      \"degree\": \"Degree Name (e.g., Doctor of Medicine (MD), PhD in Biology, MSc in Computer Science)\",\n"
        "      \"institution_date\": \"Institution Name | Date Range (e.g., 2017 to 2025)\",\n"
        "      \"details\": [\n"
        "        \"GPA, honours, national ranks, or key coursework details (if present)\"\n"
        "      ]\n"
        "    }\n"
        "  ],\n"
        "  \"research_experience\": [\n"
        "    {\n"
        "      \"title_date\": \"Role Title, Institution/University Name (Year to Year)\",\n"
        "      \"bullets\": [\n"
        "        \"Description of research tasks, methodologies used, or pipeline development\"\n"
        "      ]\n"
        "    }\n"
        "  ],\n"
        "  \"selected_publications\": [\n"
        "    {\n"
        "      \"text\": \"Full academic citation text\",\n"
        "      \"is_bold\": true or false (set to true if the candidate is a first author or co-first author, otherwise false)\n"
        "    }\n"
        "  ],\n"
        "  \"skills\": [\n"
        "    \"Category Name: specific methods, programming languages, or laboratory skills (e.g., Programming: Python, R; Lab: PCR, Flow Cytometry)\"\n"
        "  ],\n"
        "  \"clinical_experience\": [\n"
        "    {\n"
        "      \"title_date\": \"Role Title, Hospital/Clinic, Location (Date Range)\",\n"
        "      \"bullets\": [\n"
        "        \"Clinical duties, rotations, oncology/medicine experience\"\n"
        "      ]\n"
        "    }\n"
        "  ],\n"
        "  \"certifications\": [\n"
        "    \"Specific certifications, training courses, or licenses\"\n"
        "  ],\n"
        "  \"teaching\": [\n"
        "    \"Teaching assistant roles, mentoring students, delivering lectures, or workshops\"\n"
        "  ],\n"
        "  \"conferences_memberships\": [\n"
        "    \"Details of conference presentations, memberships, or club participations\"\n"
        "  ],\n"
        "  \"languages\": [\n"
        "    \"Language proficiency levels (e.g., English (fluent), Persian (native))\"\n"
        "  ]\n"
        "}\n\n"
        "RULES:\n"
        "1. STRICT TRUTHFULNESS: Only populate sections and fields using details that are explicitly present or directly derivable from the input CV text. DO NOT invent, assume, or hallucinate any dates, titles, degrees, or publications.\n"
        "2. COMPLETENESS MANDATE: You MUST extract and parse EVERY SINGLE educational degree, research position, clinical role, publication, skill, certification, teaching experience, and conference/membership listed in the raw CV text. Do not summarize, skip, or omit any item, especially from the latter pages of the CV.\n"
        "3. MISSING SECTIONS: If a section (like publications, clinical experience, certifications, teaching, conferences_memberships, or languages) is completely missing from the raw CV text, populate it as an empty list [] or empty string/object fields for that section. Do not omit the keys from the output JSON.\n"
        "4. FORMAT: You MUST return a single, valid JSON object with the exact keys specified above."
    )

    user_prompt = (
        f"Here is the raw text of the academic CV to parse:\n---\n{raw_text}\n---\n\n"
        "Return the parsed CV as a valid JSON object."
    )

    # Check if a direct Google Gemini API Key is available
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if gemini_key:
        if status_callback:
            status_callback(
                "Structuring CV using Google Gemini API directly...")
        try:
            response_text = _call_gemini_direct(
                system_prompt, user_prompt, gemini_key)
            parsed_json = json.loads(response_text.strip())
            return parsed_json
        except Exception as e:
            if status_callback:
                status_callback(
                    f"⚠️ Direct Gemini call failed: {e}. Falling back to OpenRouter...")

    # Without a key the OpenAI client raises at construction time, which would
    # skip the offline fallback below. Go straight to the heuristic parser.
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        if status_callback:
            status_callback(
                "⚠️ No OPENROUTER_API_KEY set. Using offline heuristic parser...")
        return parse_cv_text_offline(raw_text)

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
        default_headers={
            "HTTP-Referer": "http://localhost:8501",
            "X-Title": "CV Tailor"
        }
    )

    # Build fallback models list (trying chosen model first, then switching to others if congested)
    models_to_try = [model]
    free_fallbacks = [
        "google/gemma-2-9b-it:free",
        "google/gemma-4-31b-it:free",
        "google/gemma-4-26b-a4b-it:free",
        "nvidia/nemotron-3-super-120b-a12b:free",
        "nvidia/nemotron-3-nano-30b-a3b:free",
        "openai/gpt-oss-20b:free",
        "openrouter/free"
    ]
    for fallback in free_fallbacks:
        if fallback not in models_to_try:
            models_to_try.append(fallback)

    # Let's add paid models if we specify paid model or want robust fallbacks, but keep it free-oriented.
    # Actually, the user's API key has 0 credits ("Insufficient credits. This account never purchased credits.")
    # This means the user CANNOT use ANY paid models!
    # ANY model call that is not free (i.e. does not end in :free or is not openrouter/free) will fail with 402!
    # This is a critical insight: Since the user has 0 credits and hasn't purchased credits,
    # the model "google/gemini-2.5-flash" (which is a paid model) will ALWAYS fail with 402.
    # Therefore, the base model choice MUST be a free model, or we must fallback only to free models.
    # Let's inspect the active free models list from curl:
    # "inclusionai/ling-3.0-flash:free",
    # "poolside/laguna-s-2.1:free",
    # "poolside/laguna-xs-2.1:free",
    # "cohere/north-mini-code:free",
    # "nvidia/nemotron-3.5-content-safety:free",
    # "nvidia/nemotron-3-ultra-550b-a55b:free",
    # "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
    # "google/gemma-4-26b-a4b-it:free",
    # "google/gemma-4-31b-it:free",
    # "nvidia/nemotron-3-super-120b-a12b:free",
    # "nvidia/nemotron-3-nano-30b-a3b:free",
    # "nvidia/nemotron-nano-12b-v2-vl:free",
    # "nvidia/nemotron-nano-9b-v2:free",
    # "openai/gpt-oss-20b:free"
    # Note: openrouter/free itself routes to a free model, but it is heavily rate limited (429) if requested too much.
    # The active free models include:
    # "google/gemma-4-31b-it:free"
    # "google/gemma-4-26b-a4b-it:free"
    # "nvidia/nemotron-3-super-120b-a12b:free"
    # "nvidia/nemotron-nano-9b-v2:free"
    # "openai/gpt-oss-20b:free"
    # "poolside/laguna-s-2.1:free"
    # Let's refine the free fallbacks to include exactly these models.
    # Wait, the 429 error says: 'Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day'
    # Wait, the limit is "free-models-per-day" across ALL free models?
    # Ah! "Rate limit exceeded: free-models-per-day" means the free-tier daily request limit for the USER key has been reached.
    # "X-RateLimit-Limit: 50, X-RateLimit-Remaining: 0"
    # This means the user has made 50 requests to free models today, and they have 0 free requests remaining!
    # Under OpenRouter's policy, a completely free key with 0 credits has a daily limit of 50 requests for free models.
    # Since X-RateLimit-Remaining is 0, ALL free models will return 429 until the daily reset!
    # And paid models will return 402 because the user has 0 credits.
    # Oh! That explains the issue.
    # The user key is completely locked out of OpenRouter today because:
    # 1. Free models -> 429 (50/50 requests used up today)
    # 2. Paid models -> 402 (0 credits in account)
    # Wait, is there another way?
    # Let's check the date of reset: X-RateLimit-Reset: 1785369600000.
    # What timestamp is 1785369600000? Let's check with python.

    last_error = None
    for attempt, current_model in enumerate(models_to_try):
        if status_callback:
            status_callback(
                f"Structuring CV using model: `{current_model}` (Model {attempt+1}/{len(models_to_try)})...")

        executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        try:
            future = executor.submit(
                client.chat.completions.create,
                model=current_model,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1
            )
            response = future.result(timeout=25.0)
            executor.shutdown(wait=False)
            response_text = response.choices[0].message.content

            # Clean potential markdown formatting
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]

            parsed_json = json.loads(response_text.strip())
            return parsed_json

        except Exception as e:
            executor.shutdown(wait=False)
            import traceback
            tb_str = traceback.format_exc()
            last_error = f"{str(e)}\n{tb_str}"
            if status_callback:
                status_callback(
                    f"⚠️ Model `{current_model}` failed/timed out: {str(e)}. Detailed error:\n{tb_str}\nTrying next fallback...")
            time.sleep(1)

    if status_callback:
        status_callback(
            "⚠️ All AI models failed/rate-limited. Falling back to offline heuristic parser...")
    try:
        return parse_cv_text_offline(raw_text)
    except Exception as offline_err:
        raise Exception(
            f"All available models failed to parse CV (Last error: {last_error}), "
            f"and offline parser failed: {offline_err}"
        )


def tailor_cv(job_ad_text: str, model: str = "openrouter/free", cv_data: dict = None, status_callback=None) -> dict:
    if cv_data is None:
        cv_data = load_cv_data()
    cv_json_str = json.dumps(cv_data, indent=2, ensure_ascii=False)

    system_prompt = (
        "You are an expert CV optimization assistant specializing in academic and medical research applications. "
        "Your task is to tailor a CV to perfectly match a specific job advertisement. You MUST follow these rules exactly:\n\n"
        "1. GROUND TRUTH CONSTRAINT (NEVER BREAK THIS): You MUST ONLY use the degrees, skills, experiences, publications, certifications, and dates provided in the input JSON. You are ABSOLUTELY FORBIDDEN from adding, inventing, hallucinating, or assuming ANY information not strictly present in the input data. If the job ad asks for a specific medical or research field the candidate has not worked in (e.g., cognitive neuroscience, brain stimulation), DO NOT claim they have past expertise in it.\n\n"
        "2. WHAT YOU MUST CHANGE (TAILORING):\n"
        "   - REWRITE THE PROFILE: You MUST completely rewrite the 'professional_profile' paragraph to highlight the specific themes, clinical areas, or methodologies requested in the job ad.\n"
        "   - TRANSFERABLE SKILLS FRAMING: To bridge the gap between their actual experience and the job's needs, you MUST emphasize adaptability. You may add phrases highlighting their 'potential to adapt', 'readiness to apply robust computational data science skills to [New Field]', or 'strong clinical foundation applicable to [New Field/Population]'. Emphasize transferability without fabricating history.\n"
        "   - REORDERING: You MUST reorder the bullet points in 'research_experience', 'clinical_experience', 'skills', and 'selected_publications' to put the most relevant items at the very top.\n"
        "   - KEYWORD MIRRORING: You MUST subtly rephrase bullet points to adopt the specific vocabulary and keywords used in the job ad (e.g., changing 'data extraction' to 'data mining' if the ad uses that term), while keeping the underlying truth identical.\n\n"
        "3. TONE (STRICTLY HUMAN): Keep the tone direct, academic, and purely human. DO NOT use typical AI buzzwords like 'spearheaded', 'leveraged', 'seamlessly', 'fostered', 'delved', 'a testament to', or 'unwavering'. Write exactly like a serious medical researcher.\n\n"
        "4. OUTPUT FORMAT: Return your response as a single valid JSON object with the EXACT same structure (same keys, same fields) as the input JSON. Keep section titles identical."
    )

    user_prompt = (
        f"Here is the job advertisement to tailor the CV for:\n---\n{job_ad_text}\n---\n\n"
        f"Here is the strict Ground Truth CV data in JSON format. Modify this JSON to align with the job ad according to the system rules:\n---\n{cv_json_str}\n---\n\n"
        "Return the tailored CV as a valid JSON object."
    )

    # Check if a direct Google Gemini API Key is available
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if gemini_key:
        if status_callback:
            status_callback("Tailoring CV using Google Gemini API directly...")
        try:
            response_text = _call_gemini_direct(
                system_prompt, user_prompt, gemini_key)
            tailored_json = json.loads(response_text.strip())
            return tailored_json
        except Exception as e:
            if status_callback:
                status_callback(
                    f"⚠️ Direct Gemini call failed: {e}. Falling back to OpenRouter...")

    # Without a key the OpenAI client raises at construction time, which would
    # skip the offline fallback below. Go straight to the heuristic tailorer.
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        if status_callback:
            status_callback(
                "⚠️ No OPENROUTER_API_KEY set. Using offline heuristic tailoring...")
        return tailor_cv_offline(job_ad_text, cv_data)

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
        default_headers={
            "HTTP-Referer": "http://localhost:8501",  # Required by OpenRouter
            "X-Title": "CV Tailor"
        }
    )

    # Build fallback models list
    models_to_try = [model]
    free_fallbacks = [
        "google/gemma-2-9b-it:free",
        "google/gemma-4-31b-it:free",
        "google/gemma-4-26b-a4b-it:free",
        "nvidia/nemotron-3-super-120b-a12b:free",
        "nvidia/nemotron-3-nano-30b-a3b:free",
        "openai/gpt-oss-20b:free",
        "openrouter/free"
    ]
    for fallback in free_fallbacks:
        if fallback not in models_to_try:
            models_to_try.append(fallback)

    last_error = None
    for attempt, current_model in enumerate(models_to_try):
        if status_callback:
            status_callback(
                f"Tailoring CV content using model: `{current_model}` (Model {attempt+1}/{len(models_to_try)})...")

        executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        try:
            future = executor.submit(
                client.chat.completions.create,
                model=current_model,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2
            )
            response = future.result(timeout=30.0)
            executor.shutdown(wait=False)
            response_text = response.choices[0].message.content

            # Clean up potential markdown formatting from free models
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]

            tailored_json = json.loads(response_text.strip())
            return tailored_json

        except Exception as e:
            executor.shutdown(wait=False)
            last_error = e
            if status_callback:
                status_callback(
                    f"⚠️ Model `{current_model}` failed/timed out: {str(e)[:80]}. Trying next fallback...")
            time.sleep(1)

    if status_callback:
        status_callback(
            "⚠️ All AI models failed/rate-limited. Falling back to offline heuristic tailoring...")
    try:
        return tailor_cv_offline(job_ad_text, cv_data)
    except Exception as offline_err:
        raise Exception(
            f"All available models failed to tailor CV (Last error: {last_error}), "
            f"and offline tailor failed: {offline_err}"
        )


def parse_cv_text_offline(raw_text: str) -> dict:
    """Offline heuristic fallback parser that extracts CV details using regex & heuristics."""
    import re

    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]

    cv = {
        "name": "",
        "title": "Researcher",
        "contact": {
            "location": "",
            "email": "",
            "phone": "",
            "links": []
        },
        "professional_profile": "",
        "education": [],
        "research_experience": [],
        "selected_publications": [],
        "skills": [],
        "clinical_experience": [],
        "certifications": [],
        "teaching": [],
        "conferences_memberships": [],
        "languages": []
    }

    # Extract name (heuristic: first line that doesn't look like contact/header)
    for line in lines[:5]:
        if "@" not in line and "http" not in line and not line.startswith(("+", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9")):
            cv["name"] = line
            break
    if not cv["name"]:
        cv["name"] = "Candidate Name"

    # Extract email
    email_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", raw_text)
    if email_match:
        cv["contact"]["email"] = email_match.group(0)

    # Simple phone regex
    phone_match = re.search(
        r"(\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", raw_text)
    if phone_match:
        cv["contact"]["phone"] = phone_match.group(0)

    # Location heuristic
    location_keywords = ["Turkey", "Netherlands", "UK", "USA", "Germany", "France",
                         "Canada", "Izmir", "Urla", "Ankara", "Eindhoven", "Amsterdam", "Rotterdam", "London"]
    for line in lines[:10]:
        if any(keyword in line for keyword in location_keywords) and "@" not in line:
            cv["contact"]["location"] = line
            break

    # Extract links
    urls = re.findall(r"https?://[^\s()<>]+", raw_text)
    cv["contact"]["links"] = list(set(urls))

    # Segment CV by sections
    sections = {}
    current_section = "profile"
    section_mapping = {
        "education": ["education", "academic background", "studies"],
        "experience": ["work experience", "experience", "employment", "research experience", "professional experience"],
        "skills": ["skills", "expertise", "technical skills"],
        "publications": ["publications", "selected publications", "journal articles", "articles"],
        "teaching": ["teaching", "lectures", "courses taught"],
        "conferences": ["conferences", "presentations", "conference presentations", "conferences & summer schools", "conferences & workshops"],
        "awards": ["awards", "certificates", "certificates & awards", "achievements", "honors"],
        "languages": ["languages", "language proficiency"]
    }

    for line in lines:
        lower_line = line.lower().strip("*-\"': ")
        is_header = False
        for sec_name, keywords in section_mapping.items():
            if lower_line in keywords or any(lower_line == kw for kw in keywords):
                current_section = sec_name
                sections[current_section] = []
                is_header = True
                break
        if not is_header and current_section:
            if current_section not in sections:
                sections[current_section] = []
            sections[current_section].append(line)

    # Process Education
    edu_lines = sections.get("education", [])
    current_edu = None
    for line in edu_lines:
        degree_keywords = ["Ph.D.", "PhD", "M.Sc.", "MSc",
                           "B.Sc.", "BSc", "Doctor of", "Master of", "Bachelor of"]
        has_degree = any(dk in line for dk in degree_keywords)

        if has_degree:
            if current_edu:
                cv["education"].append(current_edu)

            parts = line.split(":", 1)
            degree_name = parts[0].strip("* ")
            inst_date = parts[1].strip() if len(parts) > 1 else "University"

            current_edu = {
                "degree": degree_name,
                "institution_date": inst_date,
                "details": []
            }
        elif current_edu:
            current_edu["details"].append(line.strip("* "))

    if current_edu:
        cv["education"].append(current_edu)

    # Process Experience
    exp_lines = sections.get("experience", [])
    current_exp = None
    for line in exp_lines:
        year_range_match = re.search(
            r"\b(19|20)\d{2}\b.*(Present|\b(19|20)\d{2}\b)", line)
        if year_range_match or line.startswith("20") or line.startswith("19"):
            if current_exp:
                cv["research_experience"].append(current_exp)

            role_text = line.strip("* ")
            current_exp = {
                "title_date": role_text,
                "bullets": []
            }
        elif current_exp:
            current_exp["bullets"].append(line.strip("* "))

    if current_exp:
        cv["research_experience"].append(current_exp)

    # Process Publications
    pub_lines = sections.get("publications", [])
    for line in pub_lines:
        if len(line) > 15:
            is_first = False
            last_name = cv["name"].split()[-1] if cv["name"] else ""
            if last_name and last_name.lower() in line.lower()[:30]:
                is_first = True
            cv["selected_publications"].append({
                "text": line.strip("* "),
                "is_bold": is_first
            })

    # Process Skills
    skills_lines = sections.get("skills", [])
    for line in skills_lines:
        cv["skills"].append(line.strip("* "))

    # Process Teaching
    teaching_lines = sections.get("teaching", [])
    for line in teaching_lines:
        cv["teaching"].append(line.strip("* "))

    # Process Conferences
    conf_lines = sections.get("conferences", [])
    for line in conf_lines:
        cv["conferences_memberships"].append(line.strip("* "))

    # Process Awards / Certifications
    award_lines = sections.get("awards", [])
    for line in award_lines:
        cv["certifications"].append(line.strip("* "))

    # Process Languages
    lang_lines = sections.get("languages", [])
    for line in lang_lines:
        cv["languages"].append(line.strip("* "))

    # Clean profile or set default
    profile_lines = sections.get("profile", [])
    if profile_lines:
        cv["professional_profile"] = " ".join(profile_lines[:3])
    else:
        cv["professional_profile"] = f"Experienced researcher in {cv.get('title', 'research')} with a strong academic background."

    return cv


def tailor_cv_offline(job_ad_text: str, cv_data: dict) -> dict:
    """Offline heuristic fallback tailor that aligns CV details using simple keyword ranking."""
    import re
    import copy

    tailored = copy.deepcopy(cv_data)

    # Tokenize job ad to find keywords
    words = re.findall(r"\b\w{4,15}\b", job_ad_text.lower())
    stop_words = {"with", "that", "this", "from", "have", "about",
                  "your", "their", "will", "development", "research", "project"}
    keywords = [w for w in words if w not in stop_words]

    # Rank and reorder lists helper
    def rank_key(item_text):
        if not isinstance(item_text, str):
            return 0
        score = 0
        for kw in keywords:
            if kw in item_text.lower():
                score += 1
        return score

    # Reorder skills
    if "skills" in tailored and isinstance(tailored["skills"], list):
        tailored["skills"].sort(key=rank_key, reverse=True)

    # Reorder research experience bullet points
    if "research_experience" in tailored and isinstance(tailored["research_experience"], list):
        for role in tailored["research_experience"]:
            if "bullets" in role and isinstance(role["bullets"], list):
                role["bullets"].sort(key=rank_key, reverse=True)

    # Reorder clinical experience bullet points
    if "clinical_experience" in tailored and isinstance(tailored["clinical_experience"], list):
        for role in tailored["clinical_experience"]:
            if "bullets" in role and isinstance(role["bullets"], list):
                role["bullets"].sort(key=rank_key, reverse=True)

    # Reorder publications
    if "selected_publications" in tailored and isinstance(tailored["selected_publications"], list):
        tailored["selected_publications"].sort(
            key=lambda p: rank_key(p.get("text", "")), reverse=True)

    # Generate tailored professional profile paragraph
    job_title = "Research Position"
    title_matches = re.findall(
        r"(phd\s+candidate|postdoc|postdoctoral|research\s+assistant|researcher)", job_ad_text.lower())
    if title_matches:
        job_title = title_matches[0].title()

    # Extract 3 main terms from keywords
    top_keywords = []
    for kw in keywords:
        if kw not in top_keywords and len(kw) > 4:
            top_keywords.append(kw)
        if len(top_keywords) >= 3:
            break
    kw_str = ", ".join(
        top_keywords) if top_keywords else "advanced methodologies"

    name_str = tailored.get("name", "Candidate")
    dept_str = tailored.get("department", "Science")

    tailored["professional_profile"] = (
        f"{name_str} is an experienced researcher specializing in fields related to {dept_str}. "
        f"Highly motivated to transition skills and apply advanced expertise to the {job_title} role, "
        f"with specific interest in {kw_str}. Demonstrates a proven track record of adaptability, "
        f"academic excellence, and strong collaboration skills."
    )

    return tailored
