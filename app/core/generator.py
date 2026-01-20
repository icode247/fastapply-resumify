"""
Resume PDF generation functionality.
"""
import io
from app.constants import FULL_COLUMN_WIDTH
from app.utils.helpers import get_education_element, get_experience_element, get_consulting_experience_element, get_project_element, get_skills_element, get_achievements_element
from app.utils.sections.resume_section import Section
from app.constants.resume_constants import ATS_RESUME_ELEMENTS_ORDER, NAME_PARAGRAPH_STYLE, CONTACT_PARAGRAPH_STYLE, SECTION_PARAGRAPH_STYLE
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle

def generate_resume(output_file_path, author, elements, table_styles) -> None:
    """
    Generate a resume PDF file
    
    Args:
        output_file_path: Path to save the output PDF
        author: Name of the person
        elements: Resume elements (tables, paragraphs, etc.)
        table_styles: Styles for tables
    """
    resume_doc = SimpleDocTemplate(output_file_path, pagesize=A4, showBoundary=0, 
                                   leftMargin=0.5*inch, rightMargin=0.5*inch, 
                                   topMargin=0.2*inch, bottomMargin=0.1*inch, 
                                   title=f"Resume of {author}", author=author)
    table = Table(elements, colWidths=[FULL_COLUMN_WIDTH * 0.7, FULL_COLUMN_WIDTH * 0.3], 
                  spaceBefore=0, spaceAfter=0)
    table.setStyle(TableStyle(table_styles))
    resume_elements = [table]
    resume_doc.build(resume_elements)

# def generate_resume_pdf(author, resume_data):
#     """
#     Generate a PDF resume from the provided author and resume data
    
#     Args:
#         author (str): Name of the person
#         resume_data (dict): Resume data containing education, experience, projects, skills and contact info
        
#     Returns:
#         bytes: The generated PDF content as bytes
#     """
#     # Use provided author or get from resume_data
#     if not author and 'name' in resume_data:
#         author = resume_data.get('name', 'Anonymous')
       
#     # Fallback for direct contact fields
#     email = resume_data.get('email', 'abc@xyz.com')
#     phone = resume_data.get('phone', '00-0000000000')
#     address = resume_data.get('address', 'XXX')

#     # Initialize the table to build the resume
#     table = []
#     running_row_index = [0]
#     table_styles = []
#     table_styles.append(('ALIGN', (0, 0), (0, -1), 'LEFT'))
#     table_styles.append(('ALIGN', (1, 0), (1, -1), 'RIGHT'))
#     table_styles.append(('LEFTPADDING', (0, 0), (-1, -1), 0))
#     table_styles.append(('RIGHTPADDING', (0, 0), (-1, -1), 0))
#     table_styles.append(('BOTTOMPADDING', (0, running_row_index[0]), (1, running_row_index[0]), 6))
    
#     # Process each section of the resume
#     processed_resume_data = {}
    
#     # Process education data
#     education_elements = []
#     if 'education' in resume_data:
#         for element in resume_data['education']:
#             education_elements.append(get_education_element(element))
#     processed_resume_data['education'] = Section('Education', education_elements)
    
#     # Process experience data
#     experience_elements = []
#     if 'experience' in resume_data:
#         for element in resume_data['experience']:
#             experience_elements.append(get_experience_element(element))
#     processed_resume_data['experience'] = Section('Experience', experience_elements)
    
#     # Process projects data
#     project_elements = []
#     if 'projects' in resume_data and resume_data['projects'] and len(resume_data['projects']) > 0:
#         for element in resume_data['projects']:
#             project_elements.append(get_project_element(element))
#         # Only add projects section if there are actual projects
#         processed_resume_data['projects'] = Section('Projects', project_elements)
    
#     # Process skills data - Handle both dictionary and list formats
#     skill_elements = []
#     if 'skills' in resume_data:
#         skills_data = resume_data['skills']
        
#         # Handle when skills is a dictionary with categories
#         if isinstance(skills_data, dict):
#             # Process frameworks/libraries
#             if 'frameworks/libraries' in skills_data:
#                 skill_elements.append(get_skills_element('Frameworks & Libraries', skills_data['frameworks/libraries']))
#             elif 'frameworks' in skills_data:
#                 skill_elements.append(get_skills_element('Frameworks & Libraries', skills_data['frameworks']))
            
#             # Process languages
#             if 'languages' in skills_data:
#                 skill_elements.append(get_skills_element('Programming Languages', skills_data['languages']))
            
#             # Process technologies
#             if 'technologies' in skills_data:
#                 skill_elements.append(get_skills_element('Technologies', skills_data['technologies']))
            
#             # Process others/soft skills
#             if 'others' in skills_data:
#                 skill_elements.append(get_skills_element('Other Skills', skills_data['others']))
        
#         # Handle when skills is a list of dictionaries
#         elif isinstance(skills_data, list):
#             for skill in skills_data:
#                 if isinstance(skill, dict) and 'title' in skill:
#                     elements = skill.get('elements', [])
#                     skill_elements.append(get_skills_element(skill['title'], elements))
    
#     processed_resume_data['skills'] = Section('Skills', skill_elements)
    
#     # Add the name and contact info to the table
#     table.append([
#         Paragraph(author, NAME_PARAGRAPH_STYLE)
#     ])
#     running_row_index[0] += 1
    
#     # Add job title if available
#     job_title = resume_data.get('title', '')
#     if job_title:
#         table.append([
#             Paragraph(job_title, CONTACT_PARAGRAPH_STYLE)
#         ])
#         table_styles.append(('BOTTOMPADDING', (0, running_row_index[0]), (1, running_row_index[0]), 1))
#         running_row_index[0] += 1
    
#     # Add contact information
#     table.append([
#         Paragraph(f"{email} | {phone} | {address}", CONTACT_PARAGRAPH_STYLE),
#     ])
#     table_styles.append(('BOTTOMPADDING', (0, running_row_index[0]), (1, running_row_index[0]), 1))
#     running_row_index[0] += 1
    
#     # Add each section to the table
#     for element in RESUME_ELEMENTS_ORDER:
#         if element in processed_resume_data:
#             section_table = processed_resume_data[element].get_section_table(running_row_index, table_styles)
#             for entry in section_table:
#                 table.append(entry)
    
#     # Create a BytesIO buffer to hold the PDF content
#     buffer = io.BytesIO()
    
#     # Generate the resume and write to the buffer instead of a file
#     generate_resume_to_buffer(buffer, author, table, table_styles)
    
#     # Get the PDF content from the buffer
#     buffer.seek(0)
#     pdf_content = buffer.getvalue()
    
#     return pdf_content
def generate_resume_pdf(author, resume_data):
    """
    Generate a PDF resume from the provided author and resume data

    Args:
        author (str): Name of the person
        resume_data (dict): Resume data containing education, experience, projects, skills and contact info

    Returns:
        bytes: The generated PDF content as bytes
    """
    # Use name from resume_data first, then fallback to author parameter
    author = resume_data.get('name', '') or author or ''

    # Extract contact information from nested contact object
    contact = resume_data.get('contact', {})
    email = contact.get('email', '')
    phone = contact.get('phone', '')
    location = contact.get('location', '')
    linkedin = contact.get('linkedin', '')
    github = contact.get('github', '')
    portfolio = contact.get('portfolio', '')

    # Get job title if available
    job_title = resume_data.get('title', '')
        
    # Initialize the table to build the resume
    table = []
    running_row_index = [0]
    table_styles = []
    table_styles.append(('ALIGN', (0, 0), (0, -1), 'LEFT'))
    table_styles.append(('ALIGN', (1, 0), (1, -1), 'RIGHT'))
    table_styles.append(('LEFTPADDING', (0, 0), (-1, -1), 0))
    table_styles.append(('RIGHTPADDING', (0, 0), (-1, -1), 0))
    table_styles.append(('BOTTOMPADDING', (0, running_row_index[0]), (1, running_row_index[0]), 6))
    
    # Process each section of the resume
    processed_resume_data = {}
    
    # Process experience data
    experience_elements = []
    if 'experience' in resume_data and resume_data['experience']:
        for element in resume_data['experience']:
            experience_elements.append(get_experience_element(element))
        if experience_elements:  # Only add section if there are elements
            processed_resume_data['experience'] = Section('EXPERIENCE', experience_elements)
    
    # Process education data
    education_elements = []
    if 'education' in resume_data and resume_data['education']:
        for element in resume_data['education']:
            education_elements.append(get_education_element(element))
        if education_elements:  # Only add section if there are elements
            processed_resume_data['education'] = Section('EDUCATION', education_elements)
    
    # Process projects data
    project_elements = []
    if 'projects' in resume_data and resume_data['projects'] and len(resume_data['projects']) > 0:
        for element in resume_data['projects']:
            # Map 'name' field to 'title' if needed for compatibility
            if 'name' in element and 'title' not in element:
                element['title'] = element['name']
            project_elements.append(get_project_element(element))
        # Only add projects section if there are actual projects
        processed_resume_data['projects'] = Section('PROJECTS', project_elements)
    
    # Process skills data - Handle both dictionary and list formats
    skill_elements = []
    if 'skills' in resume_data:
        skills_data = resume_data['skills']

        # Handle when skills is a dictionary with categories
        if isinstance(skills_data, dict):
            # Process technical skills
            if 'technical' in skills_data and skills_data['technical']:
                skill_elements.append(get_skills_element('Technical Skills', skills_data['technical']))

            # Process programming languages
            if 'languages' in skills_data and skills_data['languages']:
                skill_elements.append(get_skills_element('Programming Languages', skills_data['languages']))

            # Process frameworks
            if 'frameworks' in skills_data and skills_data['frameworks']:
                skill_elements.append(get_skills_element('Frameworks & Libraries', skills_data['frameworks']))
            elif 'frameworks/libraries' in skills_data and skills_data['frameworks/libraries']:
                skill_elements.append(get_skills_element('Frameworks & Libraries', skills_data['frameworks/libraries']))

            # Process tools
            if 'tools' in skills_data and skills_data['tools']:
                skill_elements.append(get_skills_element('Tools', skills_data['tools']))

            # Process technologies (legacy field)
            if 'technologies' in skills_data and skills_data['technologies']:
                skill_elements.append(get_skills_element('Technologies', skills_data['technologies']))

            # Process methodologies
            if 'methodologies' in skills_data and skills_data['methodologies']:
                skill_elements.append(get_skills_element('Methodologies', skills_data['methodologies']))

            # Process soft skills
            if 'soft_skills' in skills_data and skills_data['soft_skills']:
                skill_elements.append(get_skills_element('Soft Skills', skills_data['soft_skills']))

            # Process others (legacy field)
            if 'others' in skills_data and skills_data['others']:
                skill_elements.append(get_skills_element('Other Skills', skills_data['others']))

        # Handle when skills is a list of dictionaries
        elif isinstance(skills_data, list):
            for skill in skills_data:
                if isinstance(skill, dict) and 'title' in skill:
                    elements = skill.get('elements', [])
                    if elements:
                        skill_elements.append(get_skills_element(skill['title'], elements))

    # Only add skills section if there are skill elements
    if skill_elements:
        processed_resume_data['skills'] = Section('SKILLS', skill_elements)

    # Process certifications data
    if 'certifications' in resume_data and resume_data['certifications']:
        certifications = resume_data['certifications']
        if isinstance(certifications, list) and certifications:
            cert_elements = []
            cert_elements.append(get_achievements_element(certifications))
            processed_resume_data['certifications'] = Section('CERTIFICATIONS', cert_elements)

    # Process languages data (add as separate section if present)
    if 'languages' in resume_data and resume_data['languages']:
        language_list = resume_data['languages']
        if isinstance(language_list, list) and language_list:
            lang_elements = []
            lang_elements.append(get_skills_element('Languages', language_list))
            processed_resume_data['languages'] = Section('LANGUAGES', lang_elements)

    # Process achievements data
    if 'achievements' in resume_data and resume_data['achievements']:
        achievements_list = resume_data['achievements']
        if isinstance(achievements_list, list) and achievements_list:
            achievement_elements = []
            achievement_elements.append(get_achievements_element(achievements_list))
            processed_resume_data['achievements'] = Section('ACHIEVEMENTS', achievement_elements)

    # Add the name to the table (span both columns for full width)
    table.append([
        Paragraph(author, NAME_PARAGRAPH_STYLE), ''
    ])
    table_styles.append(('SPAN', (0, running_row_index[0]), (1, running_row_index[0])))
    running_row_index[0] += 1

    # If job title exists, add it on the next line with appropriate spacing (span both columns)
    if job_title:
        table.append([
            Paragraph(job_title, CONTACT_PARAGRAPH_STYLE), ''
        ])
        table_styles.append(('SPAN', (0, running_row_index[0]), (1, running_row_index[0])))
        # Set padding between name and title to create proper separation
        table_styles.append(('BOTTOMPADDING', (0, running_row_index[0]-1), (1, running_row_index[0]-1), 4))
        table_styles.append(('TOPPADDING', (0, running_row_index[0]), (1, running_row_index[0]), 2))
        running_row_index[0] += 1

    # Add contact information (span both columns for full width)
    # Build contact string with available fields
    contact_parts = []
    if email:
        contact_parts.append(email)
    if phone:
        contact_parts.append(phone)
    if location:
        contact_parts.append(location)
    if github:
        contact_parts.append(f'<a href="{github}" color="blue">Github</a>')
    if linkedin:
        contact_parts.append(f'<a href="{linkedin}" color="blue">Linkedin</a>')
    if portfolio:
        contact_parts.append(portfolio)

    contact_string = " | ".join(contact_parts)

    table.append([
        Paragraph(contact_string, CONTACT_PARAGRAPH_STYLE), ''
    ])
    table_styles.append(('SPAN', (0, running_row_index[0]), (1, running_row_index[0])))
    table_styles.append(('BOTTOMPADDING', (0, running_row_index[0]), (1, running_row_index[0]), 1))
    running_row_index[0] += 1

    # Add Professional Summary (use the one from resume_data if available)
    summary_text = resume_data.get('summary', '')
    if summary_text:
        # Add summary section header
        table.append([
            Paragraph('SUMMARY', SECTION_PARAGRAPH_STYLE), ''
        ])
        table_styles.append(('TOPPADDING', (0, running_row_index[0]), (1, running_row_index[0]), 5))
        table_styles.append(('BOTTOMPADDING', (0, running_row_index[0]), (1, running_row_index[0]), 5))
        table_styles.append(('SPAN', (0, running_row_index[0]), (1, running_row_index[0])))
        running_row_index[0] += 1
        
        # Add summary content
        table.append([
            Paragraph(summary_text, CONTACT_PARAGRAPH_STYLE), ''
        ])
        table_styles.append(('TOPPADDING', (0, running_row_index[0]), (1, running_row_index[0]), 2))
        table_styles.append(('BOTTOMPADDING', (0, running_row_index[0]), (1, running_row_index[0]), 8))
        table_styles.append(('SPAN', (0, running_row_index[0]), (1, running_row_index[0])))
        running_row_index[0] += 1
    
    # Add each section to the table in ATS-optimized order
    for element in ATS_RESUME_ELEMENTS_ORDER:
        if element in processed_resume_data:
            section_table = processed_resume_data[element].get_section_table(running_row_index, table_styles)
            for entry in section_table:
                table.append(entry)
    
    # Create a BytesIO buffer to hold the PDF content
    buffer = io.BytesIO()
    
    # Generate the resume and write to the buffer instead of a file
    generate_resume_to_buffer(buffer, author, table, table_styles)
    
    # Get the PDF content from the buffer
    buffer.seek(0)
    pdf_content = buffer.getvalue()
    
    return pdf_content
def generate_resume_to_buffer(buffer, author, table, table_styles):
    """
    Generate a resume PDF and write it to a buffer
    
    Args:
        buffer (io.BytesIO): Buffer to write the PDF to
        author (str): Name of the person
        table (list): Table containing resume content
        table_styles (list): Styles for the table
    """
    # Create the PDF document
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.5 * 72,  # 0.5 inch
        leftMargin=0.5 * 72,   # 0.5 inch
        topMargin=0.5 * 72,    # 0.5 inch
        bottomMargin=0.5 * 72  # 0.5 inch
    )
    
    # Build the PDF
    elements = []
    t = Table(table, colWidths=['*', '*'])
    t.setStyle(TableStyle(table_styles))
    elements.append(t)
    
    # Build the document
    doc.build(elements)


def generate_consulting_resume_pdf(author, resume_data):
    """
    Generate a PDF resume for consulting roles with skill-header format.

    The consulting format has experience descriptions with 'skillHeader' and 'bullet' fields
    instead of plain string descriptions.

    Args:
        author (str): Name of the person
        resume_data (dict): Resume data containing education, experience, projects, skills and contact info

    Returns:
        bytes: The generated PDF content as bytes
    """
    # Use name from resume_data first, then fallback to author parameter
    author = resume_data.get('name', '') or author or ''

    # Extract contact information from nested contact object
    contact = resume_data.get('contact', {})
    email = contact.get('email', '')
    phone = contact.get('phone', '')
    location = contact.get('location', '')
    linkedin = contact.get('linkedin', '')
    github = contact.get('github', '')
    portfolio = contact.get('portfolio', '')

    # Get job title if available
    job_title = resume_data.get('title', '')

    # Initialize the table to build the resume
    table = []
    running_row_index = [0]
    table_styles = []
    table_styles.append(('ALIGN', (0, 0), (0, -1), 'LEFT'))
    table_styles.append(('ALIGN', (1, 0), (1, -1), 'RIGHT'))
    table_styles.append(('LEFTPADDING', (0, 0), (-1, -1), 0))
    table_styles.append(('RIGHTPADDING', (0, 0), (-1, -1), 0))
    table_styles.append(('BOTTOMPADDING', (0, running_row_index[0]), (1, running_row_index[0]), 6))

    # Process each section of the resume
    processed_resume_data = {}

    # Process experience data using consulting format
    experience_elements = []
    if 'experience' in resume_data and resume_data['experience']:
        for element in resume_data['experience']:
            experience_elements.append(get_consulting_experience_element(element))
        if experience_elements:
            processed_resume_data['experience'] = Section('EXPERIENCE', experience_elements)

    # Process education data
    education_elements = []
    if 'education' in resume_data and resume_data['education']:
        for element in resume_data['education']:
            education_elements.append(get_education_element(element))
        if education_elements:
            processed_resume_data['education'] = Section('EDUCATION', education_elements)

    # Process projects data
    project_elements = []
    if 'projects' in resume_data and resume_data['projects'] and len(resume_data['projects']) > 0:
        for element in resume_data['projects']:
            if 'name' in element and 'title' not in element:
                element['title'] = element['name']
            project_elements.append(get_project_element(element))
        processed_resume_data['projects'] = Section('PROJECTS', project_elements)

    # Process skills data - Handle both dictionary and list formats
    skill_elements = []
    if 'skills' in resume_data:
        skills_data = resume_data['skills']

        if isinstance(skills_data, dict):
            # Process technical skills
            if 'technical' in skills_data and skills_data['technical']:
                skill_elements.append(get_skills_element('Technical Skills', skills_data['technical']))

            # Process programming languages
            if 'languages' in skills_data and skills_data['languages']:
                skill_elements.append(get_skills_element('Programming Languages', skills_data['languages']))

            # Process frameworks
            if 'frameworks' in skills_data and skills_data['frameworks']:
                skill_elements.append(get_skills_element('Frameworks & Libraries', skills_data['frameworks']))
            elif 'frameworks/libraries' in skills_data and skills_data['frameworks/libraries']:
                skill_elements.append(get_skills_element('Frameworks & Libraries', skills_data['frameworks/libraries']))

            # Process tools
            if 'tools' in skills_data and skills_data['tools']:
                skill_elements.append(get_skills_element('Tools', skills_data['tools']))

            # Process technologies
            if 'technologies' in skills_data and skills_data['technologies']:
                skill_elements.append(get_skills_element('Technologies', skills_data['technologies']))

            # Process methodologies
            if 'methodologies' in skills_data and skills_data['methodologies']:
                skill_elements.append(get_skills_element('Methodologies', skills_data['methodologies']))

            # Process soft skills
            if 'soft_skills' in skills_data and skills_data['soft_skills']:
                skill_elements.append(get_skills_element('Soft Skills', skills_data['soft_skills']))

            # Process others
            if 'others' in skills_data and skills_data['others']:
                skill_elements.append(get_skills_element('Other Skills', skills_data['others']))

        elif isinstance(skills_data, list):
            for skill in skills_data:
                if isinstance(skill, dict) and 'title' in skill:
                    elements = skill.get('elements', [])
                    if elements:
                        skill_elements.append(get_skills_element(skill['title'], elements))

    if skill_elements:
        processed_resume_data['skills'] = Section('SKILLS', skill_elements)

    # Process certifications data
    if 'certifications' in resume_data and resume_data['certifications']:
        certifications = resume_data['certifications']
        if isinstance(certifications, list) and certifications:
            cert_elements = []
            cert_elements.append(get_achievements_element(certifications))
            processed_resume_data['certifications'] = Section('CERTIFICATIONS', cert_elements)

    # Process languages data
    if 'languages' in resume_data and resume_data['languages']:
        language_list = resume_data['languages']
        if isinstance(language_list, list) and language_list:
            lang_elements = []
            lang_elements.append(get_skills_element('Languages', language_list))
            processed_resume_data['languages'] = Section('LANGUAGES', lang_elements)

    # Process achievements data
    if 'achievements' in resume_data and resume_data['achievements']:
        achievements_list = resume_data['achievements']
        if isinstance(achievements_list, list) and achievements_list:
            achievement_elements = []
            achievement_elements.append(get_achievements_element(achievements_list))
            processed_resume_data['achievements'] = Section('ACHIEVEMENTS', achievement_elements)

    # Add the name to the table
    table.append([
        Paragraph(author, NAME_PARAGRAPH_STYLE), ''
    ])
    table_styles.append(('SPAN', (0, running_row_index[0]), (1, running_row_index[0])))
    running_row_index[0] += 1

    # Add job title if available
    if job_title:
        table.append([
            Paragraph(job_title, CONTACT_PARAGRAPH_STYLE), ''
        ])
        table_styles.append(('SPAN', (0, running_row_index[0]), (1, running_row_index[0])))
        table_styles.append(('BOTTOMPADDING', (0, running_row_index[0]-1), (1, running_row_index[0]-1), 4))
        table_styles.append(('TOPPADDING', (0, running_row_index[0]), (1, running_row_index[0]), 2))
        running_row_index[0] += 1

    # Add contact information
    contact_parts = []
    if email:
        contact_parts.append(email)
    if phone:
        contact_parts.append(phone)
    if location:
        contact_parts.append(location)
    if github:
        contact_parts.append(f'<a href="{github}" color="blue">Github</a>')
    if linkedin:
        contact_parts.append(f'<a href="{linkedin}" color="blue">Linkedin</a>')
    if portfolio:
        contact_parts.append(portfolio)

    contact_string = " | ".join(contact_parts)

    table.append([
        Paragraph(contact_string, CONTACT_PARAGRAPH_STYLE), ''
    ])
    table_styles.append(('SPAN', (0, running_row_index[0]), (1, running_row_index[0])))
    table_styles.append(('BOTTOMPADDING', (0, running_row_index[0]), (1, running_row_index[0]), 1))
    running_row_index[0] += 1

    # Add Professional Summary
    summary_text = resume_data.get('summary', '')
    if summary_text:
        table.append([
            Paragraph('SUMMARY', SECTION_PARAGRAPH_STYLE), ''
        ])
        table_styles.append(('TOPPADDING', (0, running_row_index[0]), (1, running_row_index[0]), 5))
        table_styles.append(('BOTTOMPADDING', (0, running_row_index[0]), (1, running_row_index[0]), 5))
        table_styles.append(('SPAN', (0, running_row_index[0]), (1, running_row_index[0])))
        running_row_index[0] += 1

        table.append([
            Paragraph(summary_text, CONTACT_PARAGRAPH_STYLE), ''
        ])
        table_styles.append(('TOPPADDING', (0, running_row_index[0]), (1, running_row_index[0]), 2))
        table_styles.append(('BOTTOMPADDING', (0, running_row_index[0]), (1, running_row_index[0]), 8))
        table_styles.append(('SPAN', (0, running_row_index[0]), (1, running_row_index[0])))
        running_row_index[0] += 1

    # Add each section to the table in ATS-optimized order
    for element in ATS_RESUME_ELEMENTS_ORDER:
        if element in processed_resume_data:
            section_table = processed_resume_data[element].get_section_table(running_row_index, table_styles)
            for entry in section_table:
                table.append(entry)

    # Create a BytesIO buffer
    buffer = io.BytesIO()

    # Generate the resume
    generate_resume_to_buffer(buffer, author, table, table_styles)

    # Get the PDF content
    buffer.seek(0)
    pdf_content = buffer.getvalue()

    return pdf_content