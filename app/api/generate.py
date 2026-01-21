"""
Resume generation API endpoints.
"""
from flask import Blueprint, request, jsonify, send_file
import io
import os
import logging
from openai import OpenAI
from app.core.generator import generate_resume_pdf, generate_consulting_resume_pdf, generate_jake_resume_pdf, generate_harvard_resume_pdf
from app.core.docx_generator import generate_resume_docx, generate_jake_resume_docx, generate_harvard_resume_docx

# Create blueprint
bp = Blueprint('generate', __name__)
logger = logging.getLogger(__name__)


def detect_resume_type(title: str) -> str:
    """
    Detect if a resume is technical or consulting based on the job title.

    Args:
        title: The job title from resume_data

    Returns:
        'technical' or 'consulting'
    """
    if not title:
        return 'technical'  # Default to technical if no title

    try:
        client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", ""))

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": f"Is this job title technical or consulting? Title: '{title}'. Reply with only one word: 'technical' or 'consulting'."
                }
            ],
            max_tokens=10,
            temperature=0
        )

        result = response.choices[0].message.content.strip().lower()

        if 'consulting' in result:
            return 'consulting'
        return 'technical'

    except Exception as e:
        logger.error(f"Error detecting resume type: {str(e)}")
        return 'technical'  # Default to technical on error

@bp.route('/generate-resume-pdf', methods=['POST'])
def api_generate_resume_pdf():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Extract user_data and resume_data
        user_data = data.get('user_data')
        resume_data = data.get('resume_data')
        resume_type = data.get('resume_type')
        template = data.get('template', 'jake').lower()  # Default to jake

        if not user_data:
            return jsonify({"error": "Missing user_data"}), 400
        if not resume_data:
            return jsonify({"error": "Missing resume_data"}), 400

        # Validate template
        if template not in ['jake', 'harvard']:
            return jsonify({"error": "template must be 'jake' or 'harvard'"}), 400

        # Auto-detect resume type if not provided
        if not resume_type:
            title = resume_data.get('title', '')
            resume_type = detect_resume_type(title)
            logger.info(f"Auto-detected resume type: {resume_type} for title: {title}")
        elif resume_type not in ['technical', 'consulting']:
            return jsonify({"error": "resume_type must be 'technical' or 'consulting'"}), 400

        # Extract author and years_of_experience from user_data
        author = user_data.get('author', '')
        years_of_experience = user_data.get('yearsOfExperience', 0)
        is_consulting = resume_type == 'consulting'

        # Generate PDF based on template and resume type
        logger.info(f"Generating {template} {resume_type} PDF resume for {author}")

        if template == 'jake':
            pdf_content = generate_jake_resume_pdf(author, resume_data, years_of_experience, is_consulting)
        else:  # harvard
            pdf_content = generate_harvard_resume_pdf(author, resume_data, years_of_experience, is_consulting)

        if not pdf_content:
            return jsonify({"error": "Failed to generate PDF"}), 500

        # Return PDF as file response
        return send_file(
            io.BytesIO(pdf_content),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"{author.lower().replace(' ', '_')}_resume.pdf"
        )

    except Exception as e:
        logger.error(f"Error generating resume: {str(e)}")
        return jsonify({
            "error": "Failed to generate resume",
            "details": str(e)
        }), 500

@bp.route('/generate-resume-docx', methods=['POST'])
def api_generate_resume_docx():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Extract user_data and resume_data
        user_data = data.get('user_data')
        resume_data = data.get('resume_data')
        resume_type = data.get('resume_type')
        template = data.get('template', 'jake').lower()  # Default to jake

        if not user_data:
            return jsonify({"error": "Missing user_data"}), 400
        if not resume_data:
            return jsonify({"error": "Missing resume_data"}), 400

        # Validate template
        if template not in ['jake', 'harvard']:
            return jsonify({"error": "template must be 'jake' or 'harvard'"}), 400

        # Auto-detect resume type if not provided
        if not resume_type:
            title = resume_data.get('title', '')
            resume_type = detect_resume_type(title)
            logger.info(f"Auto-detected resume type: {resume_type} for title: {title}")
        elif resume_type not in ['technical', 'consulting']:
            return jsonify({"error": "resume_type must be 'technical' or 'consulting'"}), 400

        # Extract author and years_of_experience from user_data
        author = user_data.get('author', '')
        years_of_experience = user_data.get('yearsOfExperience', 0)
        is_consulting = resume_type == 'consulting'

        # Generate DOCX based on template
        logger.info(f"Generating {template} {resume_type} DOCX resume for {author}")

        if template == 'jake':
            docx_content = generate_jake_resume_docx(author, resume_data, years_of_experience, is_consulting)
        else:  # harvard
            docx_content = generate_harvard_resume_docx(author, resume_data, years_of_experience, is_consulting)

        if not docx_content:
            return jsonify({"error": "Failed to generate DOCX"}), 500

        # Return DOCX as file response
        return send_file(
            io.BytesIO(docx_content),
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            as_attachment=True,
            download_name=f"{author.lower().replace(' ', '_')}_resume.docx"
        )

    except Exception as e:
        logger.error(f"Error generating DOCX resume: {str(e)}")
        return jsonify({
            "error": "Failed to generate resume",
            "details": str(e)
        }), 500

@bp.route('/generate-resume', methods=['POST'])
def api_generate_resume():
    """Generate resume in specified format (PDF or DOCX)"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Extract user_data and resume_data
        user_data = data.get('user_data')
        resume_data = data.get('resume_data')
        format_type = data.get('format', 'docx').lower()  # Default to DOCX for ATS compatibility
        resume_type = data.get('resume_type')  # 'technical' or 'consulting' (auto-detect if not provided)
        template = data.get('template', 'jake').lower()  # Default to jake

        if not user_data:
            return jsonify({"error": "Missing user_data"}), 400
        if not resume_data:
            return jsonify({"error": "Missing resume_data"}), 400
        if format_type not in ['pdf', 'docx']:
            return jsonify({"error": "Format must be 'pdf' or 'docx'"}), 400

        # Validate template
        if template not in ['jake', 'harvard']:
            return jsonify({"error": "template must be 'jake' or 'harvard'"}), 400

        # Auto-detect resume type if not provided
        if not resume_type:
            title = resume_data.get('title', '')
            resume_type = detect_resume_type(title)
            logger.info(f"Auto-detected resume type: {resume_type} for title: {title}")
        elif resume_type not in ['technical', 'consulting']:
            return jsonify({"error": "resume_type must be 'technical' or 'consulting'"}), 400

        # Extract author and years_of_experience from user_data
        author = user_data.get('author', '')
        years_of_experience = user_data.get('yearsOfExperience', 0)
        is_consulting = resume_type == 'consulting'

        logger.info(f"Generating {template} {resume_type} {format_type.upper()} resume for {author}")

        if format_type == 'docx':
            # Generate DOCX based on template
            if template == 'jake':
                content = generate_jake_resume_docx(author, resume_data, years_of_experience, is_consulting)
            else:  # harvard
                content = generate_harvard_resume_docx(author, resume_data, years_of_experience, is_consulting)
            mimetype = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            filename = f"{author.lower().replace(' ', '_')}_resume.docx"
        else:
            # Generate PDF based on template
            if template == 'jake':
                content = generate_jake_resume_pdf(author, resume_data, years_of_experience, is_consulting)
            else:  # harvard
                content = generate_harvard_resume_pdf(author, resume_data, years_of_experience, is_consulting)
            mimetype = 'application/pdf'
            filename = f"{author.lower().replace(' ', '_')}_resume.pdf"

        if not content:
            return jsonify({"error": f"Failed to generate {format_type.upper()}"}), 500

        # Return file response
        return send_file(
            io.BytesIO(content),
            mimetype=mimetype,
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        logger.error(f"Error generating resume: {str(e)}")
        return jsonify({
            "error": "Failed to generate resume",
            "details": str(e)
        }), 500