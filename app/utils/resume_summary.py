"""
Professional summary generation for ATS-optimized resumes.
"""
import re
from typing import Dict, List, Any


class Summary:
    def __init__(self, description='') -> None:
        self.description = description
        
    def set_description(self, description='') -> None:
        self.description = description


def generate_professional_summary(resume_data: Dict[str, Any], job_title: str = None) -> str:
    """
    Generate a professional summary optimized for ATS systems
    
    Args:
        resume_data: Resume data dictionary
        job_title: Target job title if available
        
    Returns:
        Professional summary text
    """
    # Extract key information
    experience_years = extract_years_of_experience(resume_data.get('experience', []))
    top_skills = extract_top_skills(resume_data.get('skills', {}))
    key_achievements = extract_key_achievements(resume_data.get('experience', []))
    
    # Build summary components
    summary_parts = []
    
    # Opening statement with job title and experience
    if job_title and experience_years:
        summary_parts.append(f"Results-driven {job_title} with {experience_years}+ years of experience")
    elif job_title:
        summary_parts.append(f"Experienced {job_title}")
    elif experience_years:
        summary_parts.append(f"Professional with {experience_years}+ years of experience")
    else:
        summary_parts.append("Dedicated professional")
    
    # Add key skills
    if top_skills:
        skills_text = ", ".join(top_skills[:6])  # Top 6 skills for better coverage
        summary_parts.append(f"specializing in {skills_text}")
    
    # Add key achievement or strength
    if key_achievements:
        summary_parts.append(f"Proven track record of {key_achievements[0].lower()}")
    
    # Combine into coherent summary
    summary = ". ".join(summary_parts) + "."
    
    # Ensure proper capitalization and formatting
    summary = format_summary_text(summary)
    
    return summary


def extract_years_of_experience(experience_list: List[Dict]) -> int:
    """Extract total years of experience from experience list"""
    if not experience_list:
        return 0
    
    total_months = 0
    
    for exp in experience_list:
        months = calculate_experience_months(exp)
        total_months += months
    
    # Convert to years (rounded)
    years = round(total_months / 12)
    return max(1, years)  # Minimum 1 year


def calculate_experience_months(experience: Dict) -> int:
    """Calculate months of experience for a single job"""
    start_date = experience.get('start_date', '')
    end_date = experience.get('end_date', '')
    
    if not start_date:
        return 12  # Default to 1 year if no dates
    
    # Handle different date formats
    start_year, start_month = parse_date(start_date)
    
    if end_date and end_date.lower() not in ['present', 'current', 'now']:
        end_year, end_month = parse_date(end_date)
    else:
        # Current job - use current date
        from datetime import datetime
        now = datetime.now()
        end_year, end_month = now.year, now.month
    
    if start_year and end_year:
        months = (end_year - start_year) * 12 + (end_month - start_month)
        return max(1, months)  # Minimum 1 month
    
    return 12  # Default to 1 year


def parse_date(date_str: str) -> tuple:
    """Parse date string and return (year, month)"""
    if not date_str:
        return 0, 0
    
    # Clean the date string
    date_str = date_str.strip()
    
    # Try to extract year
    year_match = re.search(r'(\d{4})', date_str)
    if year_match:
        year = int(year_match.group(1))
    else:
        return 0, 0
    
    # Try to extract month
    month = 1  # Default to January
    month_patterns = {
        r'jan': 1, r'feb': 2, r'mar': 3, r'apr': 4, r'may': 5, r'jun': 6,
        r'jul': 7, r'aug': 8, r'sep': 9, r'oct': 10, r'nov': 11, r'dec': 12,
        r'01': 1, r'02': 2, r'03': 3, r'04': 4, r'05': 5, r'06': 6,
        r'07': 7, r'08': 8, r'09': 9, r'10': 10, r'11': 11, r'12': 12
    }
    
    for pattern, month_num in month_patterns.items():
        if re.search(pattern, date_str.lower()):
            month = month_num
            break
    
    return year, month


def extract_top_skills(skills_data: Any) -> List[str]:
    """Extract top skills from skills data"""
    all_skills = []
    
    if isinstance(skills_data, dict):
        for category, skills_list in skills_data.items():
            if isinstance(skills_list, list):
                all_skills.extend(skills_list)
            elif isinstance(skills_list, str):
                all_skills.extend([s.strip() for s in skills_list.split(',')])
    elif isinstance(skills_data, list):
        for skill_item in skills_data:
            if isinstance(skill_item, dict) and 'elements' in skill_item:
                elements = skill_item['elements']
                if isinstance(elements, list):
                    all_skills.extend(elements)
    
    # Filter and clean skills
    cleaned_skills = []
    for skill in all_skills[:12]:  # Limit to top 12 skills for better selection
        if skill and isinstance(skill, str) and len(skill.strip()) > 1:
            cleaned_skills.append(skill.strip())
    
    return cleaned_skills


def extract_key_achievements(experience_list: List[Dict]) -> List[str]:
    """Extract key achievements from experience descriptions"""
    achievements = []
    
    for exp in experience_list:
        descriptions = exp.get('description', [])
        if isinstance(descriptions, list):
            for desc in descriptions:
                if isinstance(desc, str) and len(desc) > 20:
                    # Look for achievement indicators
                    achievement_indicators = [
                        'increased', 'improved', 'reduced', 'achieved', 'delivered',
                        'implemented', 'developed', 'led', 'managed', 'created',
                        'optimized', 'streamlined', 'enhanced', 'built'
                    ]
                    
                    desc_lower = desc.lower()
                    if any(indicator in desc_lower for indicator in achievement_indicators):
                        # Clean and format the achievement
                        clean_achievement = clean_achievement_text(desc)
                        if clean_achievement:
                            achievements.append(clean_achievement)
    
    return achievements[:3]  # Return top 3 achievements


def clean_achievement_text(text: str) -> str:
    """Clean and format achievement text for summary"""
    # Remove bullet points and clean text
    text = re.sub(r'^[•\-\*]\s*', '', text.strip())

    # Ensure it doesn't end with a period for summary formatting
    text = text.rstrip('.')

    # No truncation - return full text to prevent cutting off important details
    return text


def format_summary_text(summary: str) -> str:
    """Format and clean the summary text"""
    # Ensure proper spacing after periods
    summary = re.sub(r'\.([A-Z])', r'. \1', summary)
    
    # Remove extra spaces
    summary = re.sub(r'\s+', ' ', summary)
    
    # Ensure it ends with a period
    if not summary.endswith('.'):
        summary += '.'
    
    return summary.strip()


def generate_keyword_optimized_summary(resume_data: Dict[str, Any], job_description: str = None, job_title: str = None) -> str:
    """
    Generate a summary optimized for specific job keywords
    
    Args:
        resume_data: Resume data dictionary
        job_description: Target job description for keyword optimization
        job_title: Target job title
        
    Returns:
        Keyword-optimized professional summary
    """
    base_summary = generate_professional_summary(resume_data, job_title)
    
    if not job_description:
        return base_summary
    
    # Extract keywords from job description
    job_keywords = extract_job_keywords(job_description)
    resume_skills = extract_top_skills(resume_data.get('skills', {}))
    
    # Find matching keywords
    matching_keywords = find_matching_keywords(job_keywords, resume_skills)
    
    if matching_keywords:
        # Enhance summary with relevant keywords
        keyword_text = ", ".join(matching_keywords[:3])  # Top 3 matching keywords
        enhanced_summary = base_summary.replace(
            "specializing in", 
            f"with expertise in {keyword_text} and specializing in"
        )
        return enhanced_summary
    
    return base_summary


def extract_job_keywords(job_description: str) -> List[str]:
    """Extract relevant keywords from job description"""
    # Common technical and skill-related keywords
    keywords = []
    
    # Split into words and clean
    words = re.findall(r'\b[A-Za-z][A-Za-z0-9+#\-\.]*\b', job_description)
    
    # Filter for likely skill/technology keywords
    skill_indicators = [
        'python', 'javascript', 'java', 'react', 'node', 'sql', 'aws', 'docker',
        'kubernetes', 'git', 'api', 'rest', 'microservices', 'agile', 'scrum',
        'machine learning', 'data', 'analytics', 'cloud', 'devops', 'ci/cd'
    ]
    
    for word in words:
        word_lower = word.lower()
        if (len(word) > 2 and 
            (word_lower in skill_indicators or 
             word.isupper() or  # Acronyms
             '+' in word or '#' in word)):  # Languages like C++, C#
            keywords.append(word)
    
    return list(set(keywords))  # Remove duplicates


def find_matching_keywords(job_keywords: List[str], resume_skills: List[str]) -> List[str]:
    """Find keywords that match between job and resume"""
    matches = []
    
    job_keywords_lower = [kw.lower() for kw in job_keywords]
    
    for skill in resume_skills:
        skill_lower = skill.lower()
        if skill_lower in job_keywords_lower:
            matches.append(skill)
    
    return matches