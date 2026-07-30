import json
from fpdf import FPDF


class CV_PDF(FPDF):
    def __init__(self, cv_data):
        super().__init__()
        self.cv_data = cv_data
        self.set_auto_page_break(auto=False)
        self.set_margins(15, 15, 15)
        self.add_page()

    def check_space(self, required_height):
        if self.get_y() + required_height > 275:
            self.add_page()

    def section_title(self, title):
        self.check_space(15)
        # Draw vertical accent line (3mm wide, 5.5mm high)
        self.set_fill_color(0, 51, 102)  # Dark blue
        self.rect(self.get_x(), self.get_y(), 3, 5.5, style="F")

        # Draw title text shifted to the right
        self.set_x(self.get_x() + 5)
        self.set_font("Helvetica", 'B', 10.5)
        self.set_text_color(0, 51, 102)
        self.cell(0, 5.5, title.upper(), ln=True)

        # Bottom thin horizontal divider line
        self.set_line_width(0.2)
        self.set_draw_color(220, 220, 220)
        self.line(15, self.get_y(), 195, self.get_y())

        self.set_text_color(0, 0, 0)
        self.ln(2.5)

    def body_text(self, text, indent=0):
        self.set_font("Helvetica", '', 10)
        self.set_x(self.get_x() + indent)
        lines = (len(text) // 90) + 1
        self.check_space((lines * 5.5) + 2)
        self.multi_cell(0, 5.5, text)
        self.ln(2)

    def bullet_point(self, text):
        self.set_font("Helvetica", '', 10)
        lines = (len(text) // 85) + 1
        self.check_space((lines * 5.5) + 2)
        self.set_x(18)
        self.multi_cell(0, 5.5, f"{chr(149)}  {text}")
        self.ln(1.5)


def clean_data(data):
    if isinstance(data, dict):
        return {k: clean_data(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [clean_data(item) for item in data]
    elif isinstance(data, str):
        replacements = {
            "’": "'",
            "‘": "'",
            "”": '"',
            "“": '"',
            "—": "-",
            "–": "-",
            "•": "*",
            "…": "...",
            "\u2013": "-",
            "\u2014": "-",
            "\u2018": "'",
            "\u2019": "'",
            "\u201c": '"',
            "\u201d": '"',
            "\u2022": "*",
            "\u2026": "...",
            "\u00a0": " ",
        }
        for uni_char, ascii_char in replacements.items():
            data = data.replace(uni_char, ascii_char)
        return data.encode('latin-1', 'replace').decode('latin-1')
    return data


def generate_cv_pdf(cv_data):
    cv_data = clean_data(cv_data)
    pdf = CV_PDF(cv_data)

    # Header (LaTeX-like Left-Aligned Name/Title, Right-Aligned Contact Details)
    pdf.set_y(15)

    # Left-side: Name
    pdf.set_text_color(0, 51, 102)  # Deep blue
    pdf.set_font("Helvetica", 'B', 22)
    pdf.cell(100, 10, cv_data.get('name', 'Your Name'), ln=False, align='L')

    # Right-side: Contact info formatting
    pdf.set_font("Helvetica", '', 9)
    pdf.set_text_color(80, 80, 80)

    contact = cv_data.get('contact', {})
    contact_lines = []

    line1_parts = []
    if contact.get('location'):
        line1_parts.append(contact.get('location'))
    if contact.get('email'):
        line1_parts.append(contact.get('email'))
    if contact.get('phone'):
        line1_parts.append(contact.get('phone'))
    if line1_parts:
        contact_lines.append(" | ".join(line1_parts))

    links = contact.get('links', [])
    if isinstance(links, list) and links:
        valid_links = [l for l in links if l.strip()]
        if valid_links:
            contact_lines.append(" | ".join(valid_links))
    elif isinstance(links, str) and links.strip():
        contact_lines.append(links)

    # Print first line of contact on the right, aligned with name
    pdf.set_x(115)
    if len(contact_lines) > 0:
        pdf.cell(80, 5, contact_lines[0], ln=True, align='R')
    else:
        pdf.ln(5)

    # Left-side: Subtitle (Title)
    pdf.set_font("Helvetica", 'I', 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(100, 5, cv_data.get('title', ''), ln=False, align='L')

    # Print second line of contact on the right, aligned with subtitle
    pdf.set_font("Helvetica", '', 9)
    pdf.set_text_color(80, 80, 80)
    pdf.set_x(115)
    if len(contact_lines) > 1:
        pdf.cell(80, 5, contact_lines[1], ln=True, align='R')
    else:
        pdf.ln(5)

    pdf.set_text_color(0, 0, 0)
    pdf.ln(5)

    # Professional Profile
    if cv_data.get('professional_profile'):
        pdf.section_title("Professional Profile")
        pdf.body_text(cv_data['professional_profile'])

    # Education
    if cv_data.get('education'):
        pdf.section_title("Education")
        edu_list = cv_data['education']
        if isinstance(edu_list, dict):
            edu_list = [edu_list]
        for edu in edu_list:
            pdf.set_font("Helvetica", 'B', 10)
            if edu.get('degree'):
                pdf.cell(0, 5.5, edu.get('degree'), ln=True)
            pdf.set_font("Helvetica", '', 10)
            if edu.get('institution_date'):
                pdf.cell(0, 5.5, edu.get('institution_date'), ln=True)
            for detail in edu.get('details', []):
                pdf.cell(0, 5.5, detail, ln=True)
            pdf.ln(1.5)
        pdf.ln(1)

    # Research Experience
    if cv_data.get('research_experience'):
        exp_list = cv_data['research_experience']
        if isinstance(exp_list, dict):
            exp_list = [exp_list]

        valid_exp = [e for e in exp_list if e.get(
            'title_date') or e.get('bullets')]
        if valid_exp:
            pdf.section_title("Research Experience")
            for exp in valid_exp:
                if exp.get('title_date'):
                    pdf.set_font("Helvetica", 'B', 10)
                    pdf.cell(0, 5.5, exp.get('title_date'), ln=True)
                pdf.set_font("Helvetica", '', 10)
                for bullet in exp.get('bullets', []):
                    pdf.bullet_point(bullet)
                pdf.ln(1.5)
            pdf.ln(1)

    # Selected Publications
    if cv_data.get('selected_publications'):
        pdf.section_title("Selected Publications")
        for pub in cv_data['selected_publications']:
            if not pub.get('text'):
                continue
            pdf.set_font("Helvetica", 'B', 10) if pub.get(
                'is_bold') else pdf.set_font("Helvetica", '', 10)
            lines = (len(pub['text']) // 85) + 1
            pdf.check_space((lines * 5.5) + 2)
            pdf.set_x(18)
            pdf.multi_cell(0, 5.5, f"{chr(149)}  {pub['text']}")
            pdf.ln(1.5)
        pdf.ln(2)

    # Skills
    if cv_data.get('skills'):
        pdf.section_title("Skills and Experience")
        for skill in cv_data['skills']:
            pdf.bullet_point(skill)
        pdf.ln(2)

    # Clinical Experience
    if cv_data.get('clinical_experience'):
        # Filter out empty items
        valid_clinical = [c for c in cv_data['clinical_experience'] if c.get(
            'title_date') or c.get('bullets')]
        if valid_clinical:
            pdf.section_title("Clinical Experience")
            for clinical in valid_clinical:
                if clinical.get('title_date'):
                    pdf.set_font("Helvetica", 'B', 10)
                    pdf.cell(0, 5.5, clinical.get('title_date'), ln=True)
                pdf.set_font("Helvetica", '', 10)
                for bullet in clinical.get('bullets', []):
                    pdf.bullet_point(bullet)
                pdf.ln(2)

    # Certifications
    if cv_data.get('certifications'):
        # Filter out empty strings/items
        valid_certs = [c for c in cv_data['certifications'] if c.strip()]
        if valid_certs:
            pdf.section_title("Certifications")
            for cert in valid_certs:
                pdf.bullet_point(cert)
            pdf.ln(2)

    # Teaching
    if cv_data.get('teaching'):
        # Filter out empty strings/items
        valid_teach = [t for t in cv_data['teaching'] if t.strip()]
        if valid_teach:
            pdf.section_title("Teaching Experience")
            for teach in valid_teach:
                pdf.bullet_point(teach)
            pdf.ln(2)

    # Conferences and Memberships
    if cv_data.get('conferences_memberships'):
        valid_conf = [
            c for c in cv_data['conferences_memberships'] if c.strip()]
        if valid_conf:
            pdf.section_title("Conferences and Memberships")
            for conf in valid_conf:
                pdf.bullet_point(conf)
            pdf.ln(2)

    # Languages
    if cv_data.get('languages'):
        valid_lang = [l for l in cv_data['languages'] if l.strip()]
        if valid_lang:
            pdf.section_title("Languages")
            for lang in valid_lang:
                pdf.bullet_point(lang)

    return pdf
