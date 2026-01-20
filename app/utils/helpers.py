# app/utils/helpers.py
"""
Miscellaneous helper functions.
"""
import re
from app.utils.elements.resume_education import Education
from app.utils.elements.resume_experience import Experience
from app.utils.elements.consulting_experience import ConsultingExperience
from app.utils.elements.resume_project import Project
from app.utils.elements.resume_skill import Skill
from app.utils.elements.resume_achievement import Achievement

ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_input(text):
    if not text or len(text.strip()) < 10:
        return False
    if len(text) > 5000:  # Limit text length
        return False
    # Basic XSS prevention
    if re.search(r'<script|javascript:|data:', text, re.I):
        return False
    return True

def get_education_element(element) -> Education:
    e = Education()
    e.set_institution(element.get('institution', ''))
    e.set_course(element.get('course', '') or element.get('degree', ''))
    e.set_location(element.get('location', ''))
    
    # Handle different date formats
    if 'start_date' in element and 'end_date' in element:
        e.set_start_date(element.get('start_date', ''))
        e.set_end_date(element.get('end_date', ''))
    elif 'year' in element:
        # Try to parse year field which might contain both start and end dates
        year_text = element.get('year', '')
        if '–' in year_text or '-' in year_text:
            parts = year_text.replace('–', '-').split('-')
            if len(parts) == 2:
                e.set_start_date(parts[0].strip())
                e.set_end_date(parts[1].strip())
            else:
                e.set_end_date(year_text)
        else:
            e.set_end_date(year_text)
    
    return e

def get_experience_element(element) -> Experience:
    e = Experience()
    e.set_company(element.get('company', ''))
    e.set_title(element.get('title', ''))
    e.set_location(element.get('location', ''))
    
    # Handle different date formats
    if 'start_date' in element and 'end_date' in element:
        e.set_start_date(element.get('start_date', ''))
        e.set_end_date(element.get('end_date', ''))
    elif 'period' in element:
        # Try to parse period field which might contain both start and end dates
        period_text = element.get('period', '')
        if '–' in period_text or '-' in period_text:
            parts = period_text.replace('–', '-').split('-')
            if len(parts) == 2:
                e.set_start_date(parts[0].strip())
                e.set_end_date(parts[1].strip())
            else:
                e.set_end_date(period_text)
        else:
            e.set_end_date(period_text)
    
    # Handle description field
    description = element.get('description', [])
    if isinstance(description, list):
        e.set_description(description)
    elif isinstance(description, str):
        e.set_description([description])
    else:
        e.set_description([])
    
    return e

def get_consulting_experience_element(element) -> ConsultingExperience:
    """Get consulting experience element with skill-header format."""
    e = ConsultingExperience()
    e.set_company(element.get('company', ''))
    e.set_title(element.get('title', ''))
    e.set_location(element.get('location', ''))

    # Handle different date formats
    if 'start_date' in element and 'end_date' in element:
        e.set_start_date(element.get('start_date', ''))
        e.set_end_date(element.get('end_date', ''))
    elif 'period' in element:
        # Try to parse period field which might contain both start and end dates
        period_text = element.get('period', '')
        if '–' in period_text or '-' in period_text:
            parts = period_text.replace('–', '-').split('-')
            if len(parts) == 2:
                e.set_start_date(parts[0].strip())
                e.set_end_date(parts[1].strip())
            else:
                e.set_end_date(period_text)
        else:
            e.set_end_date(period_text)

    # Handle description field - expecting list of dicts with skillHeader and bullet
    description = element.get('description', [])
    if isinstance(description, list):
        e.set_description(description)
    else:
        e.set_description([])

    return e

def get_project_element(element) -> Project:
    e = Project()
    e.set_title(element.get('title', ''))
    e.set_description(element.get('description', ''))
    e.set_link(element.get('link', ''))
    return e

def get_skills_element(title, elements) -> Skill:
    e = Skill()
    e.set_title(title)
    e.set_elements(elements if isinstance(elements, list) else [])
    return e

def get_achievements_element(elements) -> Achievement:
    """Create an Achievement element from a list of achievements"""
    e = Achievement()
    e.set_elements(elements if isinstance(elements, list) else [])
    return e

def process_for_json(result):
    """Convert sets to lists for JSON serialization"""
    if isinstance(result, dict):
        return {k: process_for_json(v) for k, v in result.items()}
    if isinstance(result, set):
        return list(result)
    return result

def latex_to_html_elements(latex: str) -> str:
    replacements = {
        r'\textbf{([^}]*)}': r'<strong>\1</strong>',
        r'\textit{([^}]*)}': r'<em>\1</em>',
        r'\begin{itemize}': r'<ul>',
        r'\end{itemize}': r'</ul>',
        r'\item\s+([^\\]*)': r'<li>\1</li>',
        r'\\section\*{([^}]*)}': r'<h2>\1</h2>',
        r'\\\\': '<br>',
        r'\hfill': '<span style="float:right">',
        r'\\vspace{\d+em}': '',
        r'\$\\bullet\$': '•'
    }
    
    html = latex
    for pattern, replacement in replacements.items():
        html = re.sub(pattern, replacement, html)
    return html

