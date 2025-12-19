# app/core/cover_letter.py
"""
Cover Letter Generator functionality.
"""
import io
import logging
import json
import re
from typing import Dict, Any
from openai import OpenAI
import os
from datetime import datetime

logger = logging.getLogger(__name__)

class CoverLetterGenerator:
    """
    Generate professional cover letters based on input parameters.
    """
    
    def __init__(self):
        self.api_key = os.environ.get("OPENAI_API_KEY")
        self.logger = logging.getLogger(__name__)
        
    def generate_cover_letter(self, letter_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a professional cover letter based on input parameters
        
        Args:
            letter_data: Dictionary containing cover letter parameters
                fullName: Applicant's full name (required)
                jobDescription: Full job description text (required)
                skills: Relevant skills for the position (optional)
                education: Education background (optional)
                fullPositions: Array of work experience objects (optional but recommended)
                tone: Tone of the letter (Professional, Enthusiastic, etc.) (optional)
                
        Returns:
            Dictionary containing the generated cover letter
        """
        try:
            # Validate required fields
            required_fields = ['fullName', 'jobDescription']
            missing_fields = [field for field in required_fields if not letter_data.get(field)]
            
            if missing_fields:
                raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
                
            # Create the prompt for GPT
            prompt = self._create_cover_letter_prompt(letter_data)
            
            # Call OpenAI API to generate the cover letter
            client = OpenAI(api_key=self.api_key)

            self.logger.info(f"Generating cover letter for {letter_data.get('fullName')} based on job description")
            
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": """You are a professional career coach who writes polished, structured cover letters. Your cover letters:
- Follow a clear 4-paragraph structure: Hook, Evidence, Bridge, Close
- Use formal professional language appropriate for job applications
- Include specific achievements with quantifiable metrics when available
- Connect candidate experience directly to job requirements
- Are concise and respectful of the hiring manager's time
- Sound confident without being arrogant
- Never use casual slang, buzzwords, or overly creative phrasing
Your goal: Create cover letters that demonstrate professionalism and clear value alignment."""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model="gpt-4.1",
                temperature=0.4,
                response_format={"type": "json_object"},
            )
            
            result = chat_completion.choices[0].message.content
            
            try:
                cover_letter = json.loads(result)
                cover_letter["success"] = True
                return cover_letter
                
            except json.JSONDecodeError:
                # Try to extract JSON if the response isn't properly formatted
                json_match = re.search(r'\{.*\}', result, re.DOTALL)
                if json_match:
                    cover_letter_str = json_match.group(0)
                    try:
                        cover_letter = json.loads(cover_letter_str)
                        cover_letter["success"] = True
                        return cover_letter
                    except json.JSONDecodeError:
                        raise ValueError("Failed to parse response as JSON")
                else:
                    raise ValueError("No valid JSON found in the API response")
                    
        except Exception as e:
            self.logger.error(f"Error generating cover letter: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }   
        
    def _create_cover_letter_prompt(self, letter_data: Dict[str, Any]) -> str:
        """
        Create a prompt for the AI to generate a cover letter
        
        Args:
            letter_data: Dictionary containing cover letter parameters
            
        Returns:
            String containing the prompt
        """
        # Process work experience data
        work_experience = ""
        current_role = ""
        current_company = ""
        previous_role = ""
        previous_company = ""
        
        if letter_data.get('fullPositions'):
            positions = letter_data.get('fullPositions', [])
            work_experience = "CANDIDATE'S WORK EXPERIENCE:\n"
            for i, position in enumerate(positions):
                role = position.get('role', 'N/A')
                company = position.get('company', 'N/A')
                duration = position.get('duration', 'N/A')
                location = position.get('location', 'N/A')
                description = position.get('description', '')
                
                work_experience += f"- {role} at {company} ({duration}, {location})\n"
                if description:
                    work_experience += f"  Description: {description}\n"
                
                # Track current and previous roles for template
                if i == 0:
                    current_role = role
                    current_company = company
                elif i == 1:
                    previous_role = role
                    previous_company = company
        
        # Process skills and education
        skills_section = f"SKILLS: {letter_data.get('skills', '')}" if letter_data.get('skills') else ""
        education_section = f"EDUCATION: {letter_data.get('education', '')}" if letter_data.get('education') else ""
        
        # Get job description
        job_description = letter_data.get('jobDescription', '')
        
        prompt = f"""Generate a professional cover letter following this EXACT 4-paragraph structure.

CANDIDATE INFORMATION:
- Full Name: {letter_data.get('fullName', '')}
- Current Role: {current_role if current_role else 'Not specified'}
- Current Company: {current_company if current_company else 'Not specified'}

{work_experience}

{skills_section}
{education_section}

JOB DESCRIPTION:
{job_description}

---

REQUIRED STRUCTURE (Follow this template exactly):

**PARAGRAPH 1 - THE HOOK (2-3 sentences):**
Start with: "I am writing to express my interest in the [Role Name] position at [Company]."
Then: Reference something specific about the company (recent project, industry trend, company mission).
End with: Connect your top skill to a specific goal mentioned in the job description.

**PARAGRAPH 2 - THE EVIDENCE (3-4 sentences):**
Start with: "In my current role as [Current Job Title], I specialize in [Core Competency]."
Then: Describe a major achievement with specific metrics (e.g., "reduced costs by 20%", "improved performance by 30%").
Include: What action you took to achieve this result.
Add: A second achievement from a previous role that directly aligns with a requirement in the job description.

**PARAGRAPH 3 - THE BRIDGE (2-3 sentences):**
Start with: "I am particularly drawn to this role because [Company] prioritizes [Value/Technology from JD]."
Then: Connect your technical expertise in specific skills to their needs.
End with: State how you are positioned to contribute to a specific team objective.

**PARAGRAPH 4 - THE CLOSE (2 sentences):**
"I would appreciate the opportunity to discuss how my experience aligns with your goals. Thank you for your time and consideration."

---

WRITING GUIDELINES:
- Use formal, professional language throughout
- Include specific metrics and numbers from the candidate's experience
- Reference the EXACT company name and job title from the job description
- Connect achievements directly to job requirements
- Keep the total length to 250-350 words
- Do NOT fabricate any experience or achievements
- Do NOT use casual phrases, slang, or overly creative language
- Do NOT use em-dashes, semicolons, or excessive adjectives

WORDS TO AVOID:
passionate, excited, thrilled, amazing, incredible, game-changer, cutting-edge, groundbreaking, delve, leverage, synergy, dynamic, robust, innovative, revolutionize

Return valid JSON:
{{
    "header": "",
    "salutation": "Dear Hiring Manager,",
    "introductionParagraph": "The Hook paragraph - interest, company reference, skill connection",
    "bodyParagraphs": [
        "The Evidence paragraph - current role, achievements, metrics, previous experience",
        "The Bridge paragraph - why this company, skills match, contribution potential"
    ],
    "closingParagraph": "The Close paragraph - request to discuss, thank you",
    "signature": "Sincerely,\\n\\n{letter_data.get('fullName', '')}",
    "fullLetter": "Complete formatted cover letter with all paragraphs combined"
}}"""
        
        return prompt

    def generate_cover_letter_pdf(self, letter_data: Dict[str, Any]) -> bytes:
        """
        Generate a PDF cover letter from the provided letter data
        
        Args:
            letter_data: Dictionary containing cover letter parameters
            
        Returns:
            bytes: The generated PDF content as bytes
        """
        try:
            # First generate the cover letter content
            cover_letter_result = self.generate_cover_letter(letter_data)
            
            if not cover_letter_result.get('success', False):
                raise ValueError(f"Failed to generate cover letter content: {cover_letter_result.get('error', 'Unknown error')}")
            
            # Extract the cover letter components
            header = cover_letter_result.get('header', '')
            salutation = cover_letter_result.get('salutation', '')
            intro_paragraph = cover_letter_result.get('introductionParagraph', '')
            body_paragraphs = cover_letter_result.get('bodyParagraphs', [])
            closing_paragraph = cover_letter_result.get('closingParagraph', '')
            signature = cover_letter_result.get('signature', '')
            
            # Create a BytesIO buffer to hold the PDF content
            buffer = io.BytesIO()
            
            # Generate the cover letter PDF
            self._generate_cover_letter_to_buffer(
                buffer, header, salutation, intro_paragraph, 
                body_paragraphs, closing_paragraph, signature
            )
            
            # Get the PDF content from the buffer
            buffer.seek(0)
            pdf_content = buffer.getvalue()
            
            return pdf_content
            
        except Exception as e:
            self.logger.error(f"Error generating cover letter PDF: {str(e)}")
            raise


    def _generate_cover_letter_to_buffer(self, buffer, header, salutation, intro_paragraph, 
                                   body_paragraphs, closing_paragraph, signature):
        """
        Generate a cover letter PDF and write it to a buffer
        """
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.lib.enums import TA_LEFT, TA_JUSTIFY
        from app.constants import GARAMOND_REGULAR, GARAMOND_SEMIBOLD
        from reportlab.lib.styles import ParagraphStyle

        # Create the PDF document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=1 * inch,
            leftMargin=1 * inch,
            topMargin=1 * inch,
            bottomMargin=1 * inch
        )
        
        # Define paragraph styles for cover letter
        header_style = ParagraphStyle(
            'HeaderStyle',
            fontName=GARAMOND_REGULAR,
            fontSize=11,
            alignment=TA_LEFT,
            spaceAfter=24  # More space after date
        )
        
        salutation_style = ParagraphStyle(
            'SalutationStyle',
            fontName=GARAMOND_REGULAR,
            fontSize=11,
            alignment=TA_LEFT,
            spaceAfter=12
        )
        
        body_style = ParagraphStyle(
            'BodyStyle',
            fontName=GARAMOND_REGULAR,
            fontSize=11,
            alignment=TA_JUSTIFY,
            spaceAfter=12,
            leading=14
        )
        
        signature_style = ParagraphStyle(
            'SignatureStyle',
            fontName=GARAMOND_REGULAR,
            fontSize=11,
            alignment=TA_LEFT,
            spaceAfter=6
        )
        
        # Build the document content
        story = []
        
        # Add simple date header (no contact info)
        if header:
            story.append(Paragraph(header, header_style))
        
        # Add salutation
        if salutation:
            story.append(Paragraph(salutation, salutation_style))
        
        # Add introduction paragraph
        if intro_paragraph:
            story.append(Paragraph(intro_paragraph, body_style))
        
        # Add body paragraphs
        for paragraph in body_paragraphs:
            if paragraph:
                story.append(Paragraph(paragraph, body_style))
        
        # Add closing paragraph
        if closing_paragraph:
            story.append(Paragraph(closing_paragraph, body_style))
        
        if signature:
            story.append(Spacer(1, 0.3 * inch))
            formatted_signature = signature.replace('\n', '<br/>') 
            signature_style = ParagraphStyle(
                name='Signature',
                leading=14,  
                spaceBefore=6
            )
            story.append(Paragraph(formatted_signature, signature_style))
        # Build the document
        doc.build(story)


        