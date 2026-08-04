import json
import re
from fpdf import FPDF


class CV_PDF(FPDF):
    def __init__(self, cv_data, theme="modern"):
        super().__init__()
        self.cv_data = cv_data
        self.theme = theme.lower()

        # Fonts & Alignments based on theme
        self.font_family = "Times" if self.theme == "academic" else "Helvetica"
        self.align = "C" if self.theme == "academic" else "L"

        self.margin = 14
        self.set_margins(self.margin, self.margin, self.margin)
        self.set_auto_page_break(auto=True, margin=self.margin)
        
        self.line_h = 5.2
        self.sec_h = 7.5
        
        self.add_page()

    def clean_text(self, text):
        if not isinstance(text, str):
            return "" if text is None else str(text)
        
        text = text.replace("—", "-").replace("–", "-").replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'").replace("•", chr(149)).replace("", chr(149))
        text = text.strip()
        if text.endswith("|"):
            text = text[:-1].strip()
            
        return text.encode("latin-1", "replace").decode("latin-1")

    def check_space(self, required_height):
        """Forces a new page if the remaining space is less than required_height to avoid orphaned headers/items."""
        page_bottom = 297 - self.margin
        if self.get_y() + required_height > page_bottom:
            self.add_page()

    def section_title(self, title):
        self.check_space(25)
        
        self.set_font(self.font_family, 'B', 11)
        if self.theme == "academic":
            self.set_text_color(0, 0, 0)
        elif self.theme == "tech":
            self.set_text_color(13, 148, 136) # Teal #0d9488
        else:
            self.set_text_color(15, 23, 42)  # Dark slate #0f172a
        
        self.cell(0, self.sec_h, self.clean_text(title).upper(), ln=True, align=self.align)
        
        # Divider line
        self.set_line_width(0.3)
        self.set_draw_color(203, 213, 225)
        self.line(self.margin, self.get_y(), 210 - self.margin, self.get_y())
        self.ln(3)

    def body_text(self, text, indent=0):
        self.set_font(self.font_family, '', 10)
        self.set_text_color(30, 41, 59)
        self.set_x(self.get_x() + indent)
        self.multi_cell(0, self.line_h, self.clean_text(text))
        self.ln(1)

    def bullet_point(self, text):
        if not text:
            return
        text = text.lstrip("*•- ").strip()
        if not text:
            return
        
        cleaned = self.clean_text(text)
        
        self.set_font(self.font_family, '', 10)
        self.set_text_color(30, 41, 59)
        
        bullet_indent = self.margin + 3
        text_indent = self.margin + 7
        
        self.set_x(bullet_indent)
        self.cell(4, self.line_h, chr(149))
        self.set_x(text_indent)
        
        try:
            self.multi_cell(0, self.line_h, cleaned, markdown=True)
        except TypeError:
            cleaned = cleaned.replace("**", "")
            self.multi_cell(0, self.line_h, cleaned)


def generate_cv_pdf(cv_data: dict, theme: str = "modern") -> FPDF:
    pdf = CV_PDF(cv_data, theme=theme)

    # --- HEADER ---
    name_str = pdf.clean_text(cv_data.get("name", "Candidate Name"))
    if name_str.endswith("|"): name_str = name_str[:-1].strip()
    
    pdf.set_font(pdf.font_family, 'B', 18)
    if pdf.theme == "tech":
        pdf.set_text_color(15, 23, 42)
    elif pdf.theme == "academic":
        pdf.set_text_color(0, 0, 0)
    else:
        pdf.set_text_color(15, 23, 42)
        
    pdf.cell(0, 8, name_str, ln=True, align=pdf.align)

    title_str = pdf.clean_text(cv_data.get("title"))
    if title_str:
        if title_str.endswith("|"): title_str = title_str[:-1].strip()
        pdf.set_font(pdf.font_family, 'B' if pdf.theme == "modern" else 'I', 10.5)
        pdf.set_text_color(71, 85, 105)
        pdf.cell(0, 5, title_str, ln=True, align=pdf.align)
        
    pdf.ln(1)

    # --- CONTACT BANNER ---
    contact = cv_data.get('contact', {})
    contact_parts = []
    
    if contact.get('location'): contact_parts.append(contact.get('location').strip())
    if contact.get('email'): contact_parts.append(contact.get('email').strip())
    if contact.get('phone'): contact_parts.append(contact.get('phone').strip())

    links = contact.get('links', [])
    if isinstance(links, list):
        for l in links:
            if isinstance(l, str) and l.strip(): contact_parts.append(l.strip())
    elif isinstance(links, str) and links.strip():
        contact_parts.append(links.strip())

    clean_parts = [pdf.clean_text(p).strip(" |") for p in contact_parts if p and pdf.clean_text(p).strip(" |")]

    if clean_parts:
        contact_text = "  |  ".join(clean_parts)
        pdf.set_font(pdf.font_family, '', 9)
        pdf.set_text_color(100, 116, 139)
        pdf.multi_cell(0, 4.5, contact_text, align=pdf.align)

    pdf.ln(5)

    # --- PROFESSIONAL PROFILE ---
    profile = cv_data.get('professional_profile')
    if profile and profile.strip():
        pdf.section_title("Professional Profile")
        pdf.set_font(pdf.font_family, '', 10)
        pdf.set_text_color(30, 41, 59)
        cleaned_prof = pdf.clean_text(profile)
        try:
            pdf.multi_cell(0, pdf.line_h, cleaned_prof, markdown=True)
        except TypeError:
            pdf.multi_cell(0, pdf.line_h, cleaned_prof.replace("**", ""))
        pdf.ln(2)

    # --- DYNAMIC SECTIONS ---
    for section in cv_data.get('sections', []):
        sec_title = pdf.clean_text(section.get('section_title', '')).strip()
        items = section.get('items', [])
        
        if sec_title and items:
            pdf.section_title(sec_title)
            
            norm_sec_title = re.sub(r'[^a-z0-9]', '', sec_title.lower())
            
            for item in items:
                pdf.check_space(12)
                
                if isinstance(item, str):
                    pdf.bullet_point(item)
                elif isinstance(item, dict):
                    title_date = pdf.clean_text(item.get('title_date', '')).strip()
                    norm_title_date = re.sub(r'[^a-z0-9]', '', title_date.lower())
                    
                    if title_date and norm_title_date != norm_sec_title and not norm_sec_title.startswith(norm_title_date):
                        has_bullets = bool(item.get('bullets'))
                        is_short_title = len(title_date) < 80
                        
                        if has_bullets or is_short_title:
                            pdf.set_font(pdf.font_family, 'B', 10)
                            pdf.set_text_color(15, 23, 42)
                        else:
                            pdf.set_font(pdf.font_family, '', 10)
                            pdf.set_text_color(30, 41, 59)
                        
                        try:
                            pdf.multi_cell(0, pdf.line_h, title_date, markdown=True)
                        except TypeError:
                            pdf.multi_cell(0, pdf.line_h, title_date.replace("**", ""))
                    
                    pdf.set_font(pdf.font_family, '', 10)
                    for bullet in item.get('bullets', []):
                        pdf.bullet_point(bullet)
                
                pdf.ln(1)
            
            pdf.ln(3)

    return pdf
