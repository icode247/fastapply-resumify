from app.constants import GARAMOND_REGULAR, GARAMOND_SEMIBOLD
from reportlab.lib.enums import TA_RIGHT, TA_JUSTIFY, TA_CENTER, TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors

RESUME_ELEMENTS_ORDER = [
    'skills',
    'projects',
    'experience',
    'education',
    'achievements',
    'certifications'
]

# ATS-optimized section order (Professional Summary added separately in generator)
ATS_RESUME_ELEMENTS_ORDER = [
    'experience',
    'skills',
    'education',
    'projects',
    'achievements',
    'certifications',
    'languages'
]

# Jake's template section orders based on years of experience
# For new grads (<3 years): Education first to highlight recent education
JAKE_SECTION_ORDER_NEW_GRAD = [
    'education',
    'experience',
    'projects',
    'skills',
    'achievements',
    'certifications',
    'languages'
]

# For experienced professionals (3+ years): Experience first
JAKE_SECTION_ORDER_EXPERIENCED = [
    'experience',
    'skills',
    'education',
    'projects',
    'achievements',
    'certifications',
    'languages'
]

# Harvard template section order: Summary (if present) -> Experience -> Skills -> Education -> Projects
HARVARD_SECTION_ORDER = [
    'experience',
    'skills',
    'education',
    'projects',
    'achievements',
    'certifications',
    'languages'
]

# Jake's template specific styles (centered header)
JAKE_NAME_PARAGRAPH_STYLE = ParagraphStyle('jake_name_paragraph', fontName = GARAMOND_SEMIBOLD, fontSize=16, alignment=TA_CENTER)
JAKE_CONTACT_PARAGRAPH_STYLE = ParagraphStyle('jake_contact_paragraph', fontName = GARAMOND_REGULAR, fontSize=12, alignment=TA_CENTER)

JOB_DETAILS_PARAGRAPH_STYLE = ParagraphStyle('job_details_paragraph', leftIndent=12, fontName = GARAMOND_REGULAR, fontSize = 12, leading = 13, alignment = TA_JUSTIFY)
NAME_PARAGRAPH_STYLE = ParagraphStyle('name_paragraph', fontName = GARAMOND_SEMIBOLD, fontSize=16)
CONTACT_PARAGRAPH_STYLE = ParagraphStyle('contact_paragraph', fontName = GARAMOND_REGULAR, fontSize=12)
SECTION_PARAGRAPH_STYLE = ParagraphStyle('section_paragraph', fontName = GARAMOND_SEMIBOLD, fontSize=13, textTransform = 'uppercase')
COMPANY_HEADING_PARAGRAPH_STYLE = ParagraphStyle('company_heading_paragraph', fontName = GARAMOND_SEMIBOLD, fontSize=12)
COMPANY_TITLE_PARAGRAPH_STYLE = ParagraphStyle('company_title_paragraph', fontName = GARAMOND_REGULAR, fontSize=12)
COMPANY_DURATION_PARAGRAPH_STYLE = ParagraphStyle('company_duration_paragraph', fontName = GARAMOND_SEMIBOLD, fontSize=12, alignment = TA_RIGHT)
COMPANY_LOCATION_PARAGRAPH_STYLE = ParagraphStyle('company_location_paragraph', fontName = GARAMOND_REGULAR, fontSize=12, alignment = TA_RIGHT)

# Harvard template specific styles (left-aligned header, more whitespace)
HARVARD_NAME_PARAGRAPH_STYLE = ParagraphStyle('harvard_name_paragraph', fontName = GARAMOND_SEMIBOLD, fontSize=18)
HARVARD_CONTACT_PARAGRAPH_STYLE = ParagraphStyle('harvard_contact_paragraph', fontName = GARAMOND_REGULAR, fontSize=11)
HARVARD_SECTION_PARAGRAPH_STYLE = ParagraphStyle('harvard_section_paragraph', fontName = GARAMOND_SEMIBOLD, fontSize=12, textTransform = 'uppercase')
HARVARD_COMPANY_NAME_PARAGRAPH_STYLE = ParagraphStyle('harvard_company_name_paragraph', fontName = GARAMOND_SEMIBOLD, fontSize=12)

def appendSectionTableStyle(table_styles : list, running_row_index : list) -> None:
    table_styles.append(('TOPPADDING', (0, running_row_index[0]), (1, running_row_index[0]), 8))
    table_styles.append(('BOTTOMPADDING', (0, running_row_index[0]), (1, running_row_index[0]), 2))