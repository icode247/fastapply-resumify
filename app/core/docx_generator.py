"""
DOCX resume generation functionality for ATS compatibility.
"""
import io
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from app.constants.resume_constants import ATS_RESUME_ELEMENTS_ORDER
from app.utils.helpers import get_education_element, get_experience_element, get_project_element, get_skills_element
from app.utils.sections.resume_section import Section


def generate_resume_docx(author, resume_data):
    """
    Generate a DOCX resume optimized for ATS systems
    
    Args:
        author (str): Name of the person
        resume_data (dict): Resume data containing education, experience, projects, skills and contact info
        
    Returns:
        bytes: The generated DOCX content as bytes
    """
    # Create new document
    doc = Document()
    
    # Set up document margins (1 inch on all sides)
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin = Inches(1)
        section.right_margin = Inches(1)
    
    # Use provided author or get from resume_data
    if not author and 'name' in resume_data:
        author = resume_data.get('name', '')
    
    # Extract contact information
    email = resume_data.get('email', '')
    phone = resume_data.get('phone', '')
    address = resume_data.get('address', '')
    job_title = resume_data.get('title', '')
    
    # Add name (header)
    name_paragraph = doc.add_paragraph()
    name_run = name_paragraph.add_run(author)
    name_run.font.size = Pt(16)
    name_run.font.bold = True
    name_run.font.name = 'Calibri'
    name_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Add job title if available
    if job_title:
        title_paragraph = doc.add_paragraph()
        title_run = title_paragraph.add_run(job_title)
        title_run.font.size = Pt(12)
        title_run.font.name = 'Calibri'
        title_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Add contact information
    contact_paragraph = doc.add_paragraph()
    contact_text = f"{email} | {phone} | {address}"
    contact_run = contact_paragraph.add_run(contact_text)
    contact_run.font.size = Pt(11)
    contact_run.font.name = 'Calibri'
    contact_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Add some space after contact info
    doc.add_paragraph()

    # Add Professional Summary (use the one from resume_data if available)
    summary_text = resume_data.get('summary', '')
    if summary_text:
        add_section_header(doc, "PROFESSIONAL SUMMARY")
        summary_paragraph = doc.add_paragraph()
        summary_run = summary_paragraph.add_run(summary_text)
        summary_run.font.size = Pt(11)
        summary_run.font.name = 'Calibri'
        doc.add_paragraph()
    
    # Process resume sections in ATS-optimized order
    processed_resume_data = process_resume_sections(resume_data)
    
    # Add sections in proper ATS order
    for element in ATS_RESUME_ELEMENTS_ORDER:
        if element in processed_resume_data:
            section = processed_resume_data[element]
            add_resume_section_to_doc(doc, section)
    
    # Save to buffer
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    
    return buffer.getvalue()


def process_resume_sections(resume_data):
    """Process resume data into sections"""
    processed_resume_data = {}
    
    # Process experience data
    experience_elements = []
    if 'experience' in resume_data and resume_data['experience']:
        for element in resume_data['experience']:
            experience_elements.append(get_experience_element(element))
        processed_resume_data['experience'] = Section('PROFESSIONAL EXPERIENCE', experience_elements)
    
    # Process skills data
    skill_elements = []
    if 'skills' in resume_data:
        skills_data = resume_data['skills']
        
        if isinstance(skills_data, dict):
            # Process different skill categories
            if 'frameworks/libraries' in skills_data:
                skill_elements.append(get_skills_element('Frameworks & Libraries', skills_data['frameworks/libraries']))
            elif 'frameworks' in skills_data:
                skill_elements.append(get_skills_element('Frameworks & Libraries', skills_data['frameworks']))
            
            if 'languages' in skills_data:
                skill_elements.append(get_skills_element('Programming Languages', skills_data['languages']))
            
            if 'technologies' in skills_data:
                skill_elements.append(get_skills_element('Technologies', skills_data['technologies']))
            
            if 'others' in skills_data:
                skill_elements.append(get_skills_element('Other Skills', skills_data['others']))
        
        elif isinstance(skills_data, list):
            for skill in skills_data:
                if isinstance(skill, dict) and 'title' in skill:
                    elements = skill.get('elements', [])
                    skill_elements.append(get_skills_element(skill['title'], elements))
    
    if skill_elements:
        processed_resume_data['skills'] = Section('CORE COMPETENCIES', skill_elements)
    
    # Process education data
    education_elements = []
    if 'education' in resume_data and resume_data['education']:
        for element in resume_data['education']:
            education_elements.append(get_education_element(element))
        processed_resume_data['education'] = Section('EDUCATION', education_elements)
    
    # Process projects data
    project_elements = []
    if 'projects' in resume_data and resume_data['projects'] and len(resume_data['projects']) > 0:
        for element in resume_data['projects']:
            project_elements.append(get_project_element(element))
        processed_resume_data['projects'] = Section('PROJECTS', project_elements)
    
    return processed_resume_data


def add_section_header(doc, header_text):
    """Add a section header with proper formatting"""
    header_paragraph = doc.add_paragraph()
    header_run = header_paragraph.add_run(header_text)
    header_run.font.size = Pt(12)
    header_run.font.bold = True
    header_run.font.name = 'Calibri'
    header_paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT


def add_resume_section_to_doc(doc, section):
    """Add a resume section to the document"""
    # Add section header
    add_section_header(doc, section.heading)
    
    # Add section content
    for element in section.elements:
        if hasattr(element, 'get_docx_content'):
            element.get_docx_content(doc)
        else:
            # Fallback for elements without docx support
            add_generic_element_to_doc(doc, element)
    
    # Add space after section
    doc.add_paragraph()


def add_generic_element_to_doc(doc, element):
    """Add a generic element to the document"""
    if hasattr(element, 'title') and element.title:
        # Add element title
        title_paragraph = doc.add_paragraph()
        title_run = title_paragraph.add_run(element.title)
        title_run.font.size = Pt(11)
        title_run.font.bold = True
        title_run.font.name = 'Calibri'
    
    if hasattr(element, 'description') and element.description:
        # Add description
        if isinstance(element.description, list):
            for desc in element.description:
                desc_paragraph = doc.add_paragraph()
                desc_run = desc_paragraph.add_run(f"• {desc}")
                desc_run.font.size = Pt(11)
                desc_run.font.name = 'Calibri'
        else:
            desc_paragraph = doc.add_paragraph()
            desc_run = desc_paragraph.add_run(element.description)
            desc_run.font.size = Pt(11)
            desc_run.font.name = 'Calibri'