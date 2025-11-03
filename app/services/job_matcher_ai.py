"""
AI-powered job matching service using OpenAI.
Analyzes job preferences, job information, and resume to determine fit.
"""
import os
import json
import logging
from typing import Dict, List, Optional
from openai import OpenAI

logger = logging.getLogger(__name__)


class JobMatcherAI:
    """
    Production-ready AI job matcher that analyzes whether a candidate
    should apply for a job based on their preferences, resume, and job details.
    """
    
    def __init__(self):
        """Initialize the OpenAI client."""
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")

        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4o"
        self.useChatGPT = False
        
    def analyze_job_match(
        self,
        resume_text: str,
        job_information: Dict,
        job_preferences: Dict,
        apply_only_qualified: bool = True
    ) -> Dict:
        """
        Analyze if a candidate should apply for a job.

        Args:
            resume_text: The candidate's resume as plain text
            job_information: Dict containing job details (title, description, requirements, etc.)
            job_preferences: Dict containing candidate's preferences (location, salary, remote, language, industry, companyBlacklist, etc.)
            apply_only_qualified: If True, validate both preferences AND resume qualifications. If False, only validate preferences.

        Returns:
            Dict with:
                - shouldApply: bool
                - reason: str (max 20 words explaining mismatches)
                - matchScore: float (0-100)
                - mismatches: List[str] (specific items that don't match)
        """
        try:
            if not resume_text or not resume_text.strip():
                raise ValueError("Resume text cannot be empty")

            if not job_information:
                raise ValueError("Job information is required")

            prompt = self._build_analysis_prompt(
                resume_text=resume_text,
                job_information=job_information,
                job_preferences=job_preferences or {},
                apply_only_qualified=apply_only_qualified
            )

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": self._get_system_prompt()
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.5,
                max_tokens=800,
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)

            return self._validate_and_format_response(result)
            
        except Exception as e:
            logger.error(f"Error in job match analysis: {str(e)}", exc_info=True)
            raise
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the AI."""
        return """You are a STRICT job matching AI that prevents candidates from wasting time on mismatched jobs. Your analysis must be rigorous and conservative, but ACCURATE.

CRITICAL: Before making any decision, you MUST internally calculate years of experience by:
1. Identifying ALL positions that mention the required technology
2. Calculating years for EACH position (end_year - start_year)
3. SUMMING all the years together
4. Only then comparing to the requirement

You must respond with a JSON object containing:
1. "shouldApply": boolean - true ONLY if both preferences AND qualifications match
2. "reason": string - Concise explanation (MAX 20 words) speaking directly to the candidate (use "you"), focusing on the PRIMARY mismatch
3. "matchScore": number - Score 0-100 (be fair, realistic scores based on actual analysis)
4. "mismatches": array of strings - ALL specific mismatches found (speaking to the candidate using "you")

CRITICAL VALIDATION PROCESS (MUST FOLLOW IN ORDER):

STEP 1 - PREFERENCES VALIDATION (IMMEDIATE DISQUALIFICATION IF FAILED - Only check preferences that are specified):
- Deal-breakers: If specified, ANY deal-breaker match = instant rejection
- Company blacklist: If specified, job from blacklisted company = instant rejection. Extract company from description if not explicit.
- Language: If job requires specific languages (check description for "Spanish required", "fluent in French", "bilingual", "must speak X"), you MUST speak those languages. If you specified languages and job requires others = reject.
- Industry: If you specified preferred industries, job MUST be in one of those industries. Infer industry from job title/description if not explicit.
- Job Type: If you specified jobType preferences (Full-time/Part-time), job must match one of them
- Experience Level: If you specified experience preferences (Entry level/Internship/Associate), job must match your level
- Remote Only: If remoteOnly=true, job MUST be remote. Hybrid/onsite = reject
- Work Mode: If you specified workMode preferences (Remote/Hybrid/On-Site), job must match one of them
- Location/City: If you specified city or location, job must be in that location
- Salary: If you specified minimum salary, job salary must meet that minimum. Below min = reject
- Positions: If you specified preferred positions, job title must align with one of them

STEP 2 - RESUME-JOB REQUIREMENTS MATCH (ONLY IF STEP 1 PASSES AND applyOnlyQualified=true):
- NOTE: Skip this step entirely if applyOnlyQualified=false. Only validate preferences in that case.
- Required skills: You MUST have ALL listed required skills
- Experience years: CAREFULLY calculate total years from ALL relevant positions. Add up years from each role that used the required technology. If job requires "5+ years Python" and resume shows "2019-Present" (6 years) + "2016-2019" (3 years) = 9 total years, then requirement IS MET. Do not reject based on miscalculation.
- Education level: If degree specified as required, you must have it
- Technical stack: Core technologies must match (Python job needs Python experience)
- Seniority level: Match entry-level roles with junior/entry-level candidates (0-2 years). Junior roles are entry-level. Mid-level (2-5 years) and senior roles (5+ years) must match appropriately

STRICTNESS RULES:
- If job requires "5+ years Python" and you have 3 years = REJECT (but if you have 5+ across multiple roles, APPROVE)
- If you require remote and job is onsite = REJECT
- If you prefer $150k+ and job offers $80k-100k = REJECT
- Missing even ONE critical required skill = REJECT
- Any deal-breaker present = REJECT
- When in doubt about experience calculation, add up ALL years carefully before rejecting

SCORING GUIDELINES (be fair but thorough):
- 90-100: Perfect match - all requirements met, all preferences aligned
- 80-89: Excellent match - all requirements met, minor preference mismatches
- 70-79: Good match - requirements met, some preference differences
- 60-69: Acceptable match - most requirements met, several issues
- Below 60: Not a good match - should NOT apply

Set shouldApply=false if matchScore < 70 OR if any critical mismatch exists.

Keep reason under 20 words, focusing on the PRIMARY blocking issue."""

    def _build_analysis_prompt(
        self,
        resume_text: str,
        job_information: Dict,
        job_preferences: Dict,
        apply_only_qualified: bool
    ) -> str:
        """Build the analysis prompt from inputs."""

        job_title = job_information.get('title', 'Not specified')
        job_description = job_information.get('description', 'Not specified')
        job_requirements = job_information.get('requirements', 'Not specified')
        job_location = job_information.get('location', 'Not specified')
        job_salary = job_information.get('salary', 'Not specified')
        job_type = job_information.get('type', 'Not specified')
        experience_required = job_information.get('experience_required', 'Not specified')
        job_company = job_information.get('company', 'Not specified')
        job_languages = job_information.get('languages_required', [])
        job_industry = job_information.get('industry', 'Not specified')

        job_types = job_preferences.get('jobType', [])
        experience_levels = job_preferences.get('experience', [])
        salary_range = job_preferences.get('salary', [])
        min_salary = salary_range[0] if salary_range and len(salary_range) > 0 else None
        max_salary = salary_range[1] if salary_range and len(salary_range) > 1 else None
        city = job_preferences.get('city', None)
        positions = job_preferences.get('positions', [])
        remote_only = job_preferences.get('remoteOnly', False)
        work_modes = job_preferences.get('workMode', [])
        location = job_preferences.get('location', None)
        user_languages = job_preferences.get('language', [])
        preferred_industries = job_preferences.get('industry', [])
        company_blacklist = job_preferences.get('companyBlacklist', [])
        deal_breakers = job_preferences.get('deal_breakers', [])
        
        prompt = f"""STRICT JOB MATCH ANALYSIS - Follow validation steps in order:

JOB INFORMATION:
- Title: {job_title}
- Company: {job_company if job_company != 'Not specified' else 'Not specified (extract from description if mentioned)'}
- Industry: {job_industry if job_industry != 'Not specified' else 'Not specified (infer from job description/title/requirements)'}
- Description: {job_description[:1000]}
- Requirements: {job_requirements[:1000]}
- Location: {job_location}
- Salary: {job_salary}
- Type: {job_type}
- Experience Required: {experience_required}
- Languages Required: {', '.join(job_languages) if job_languages else 'Not specified (check description for language requirements like "Spanish required", "bilingual", etc.)'}

CANDIDATE PREFERENCES (ALL OPTIONAL - Only validate if specified):
- Job Types: {', '.join(job_types) if job_types else 'Any'}
- Experience Levels: {', '.join(experience_levels) if experience_levels else 'Any'}
- Salary Range: {f'${min_salary:,} - ${max_salary:,}' if min_salary and max_salary else f'${min_salary:,}+' if min_salary else 'Not specified'}
- City: {city or 'Any'}
- Location/Country: {location or 'Any'}
- Positions: {', '.join(positions) if positions else 'Any'}
- Remote Only: {'Yes - MUST be remote' if remote_only else 'No'}
- Work Modes: {', '.join(work_modes) if work_modes else 'Any'}
- Languages You Speak: {', '.join(user_languages) if user_languages else 'Not specified'}
- Preferred Industries: {', '.join(preferred_industries) if preferred_industries else 'Any'}
- Company Blacklist: {', '.join(company_blacklist) if company_blacklist else 'None'}
- Deal Breakers: {', '.join(deal_breakers) if deal_breakers else 'None'}

APPLY ONLY QUALIFIED MODE: {"ENABLED - Check resume qualifications" if apply_only_qualified else "DISABLED - Only check preferences, skip resume validation"}

CANDIDATE RESUME {"(CHECK ONLY IF PREFERENCES MATCH AND applyOnlyQualified=true)" if apply_only_qualified else "(DO NOT CHECK - applyOnlyQualified=false)"}:
{resume_text[:3000] if apply_only_qualified else "[Resume check disabled - only validating preferences]"}

IMPORTANT EXPERIENCE CALCULATION EXAMPLE:
If the resume shows:
- "Senior Software Engineer at TechCorp (2019-Present)" using Python/Django
- "Software Engineer at StartupXYZ (2016-2019)" using Python/Flask

Then Python experience = (2025-2019) + (2019-2016) = 6 + 3 = 9 years total
NOT just 6 years from the current role!

VALIDATION STEPS:

BEFORE ANYTHING ELSE - If checking experience requirements:
a) List out EVERY job position that mentions the required technology
b) For EACH position, calculate: (end_year - start_year) or (2025 - start_year) if current
c) Add ALL those years together
d) Compare the SUM to the requirement

Example for this resume:
- Position 1: "Senior Software Engineer at TechCorp (2019-Present)" → 2025-2019 = 6 years Python
- Position 2: "Software Engineer at StartupXYZ (2016-2019)" → 2019-2016 = 3 years Python
- TOTAL Python experience = 6 + 3 = 9 years
- Required: 5+ years
- RESULT: 9 ≥ 5, requirement MET ✓

1. First, validate ALL your specified preferences against job information (skip any preference not provided)
   - EXTRACT missing info: If company/industry/languages not explicitly in job info, extract from description
   - Check company blacklist first (if specified, instant reject if match)
   - Check deal-breakers (if specified, instant reject if match)
   - Validate language requirements (job requires languages you don't speak = reject)
   - Validate industry match (if you specified industries, job must be in one of them)
   - Validate job type (if specified Full-time/Part-time, must match)
   - Validate experience level (if specified Entry/Internship/Associate, must match)
   - Validate remoteOnly (if true, job MUST be remote)
   - Validate workMode (if specified Remote/Hybrid/On-Site, must match)
   - Validate location/city (if specified, must match)
   - Validate salary (if specified min, job must meet it)
   - Validate positions (if specified, job title must align)

2. {"Only if Step 1 passes completely, validate your resume against job requirements" if apply_only_qualified else "SKIP THIS STEP - applyOnlyQualified is false, only preferences matter"}
   {"- Check if you have required skills (list each required skill and verify presence in resume)" if apply_only_qualified else ""}
   {"- Calculate experience using the method shown above - do NOT skip this step" if apply_only_qualified else ""}
   {"- Confirm your technical stack aligns with required technologies" if apply_only_qualified else ""}
   {"- Validate seniority level match (remember: junior = entry-level)" if apply_only_qualified else ""}

{"If ANY preference mismatches or ANY critical requirement is unmet, set shouldApply=false." if apply_only_qualified else "If ANY preference mismatches, set shouldApply=false. Do NOT check resume qualifications."}
List ALL mismatches found using "you" language. Be strict and conservative."""
        
        return prompt
    
    def _validate_and_format_response(self, result: Dict) -> Dict:
        """Validate and format the AI response with strict enforcement."""
        if 'shouldApply' not in result:
            raise ValueError("AI response missing 'shouldApply' field")

        if 'reason' not in result:
            raise ValueError("AI response missing 'reason' field")

        reason_words = result['reason'].split()
        if len(reason_words) > 20:
            result['reason'] = ' '.join(reason_words[:20])
            logger.warning("AI response reason exceeded 20 words, truncated")

        match_score = result.get('matchScore', 0)
        if not isinstance(match_score, (int, float)) or match_score < 0 or match_score > 100:
            result['matchScore'] = 50
            logger.warning(f"Invalid matchScore: {match_score}, defaulting to 50")

        if 'mismatches' not in result or not isinstance(result['mismatches'], list):
            result['mismatches'] = []

        should_apply = bool(result['shouldApply'])
        match_score = float(result['matchScore'])
        mismatches = result['mismatches']

        if match_score < 70:
            should_apply = False
            logger.info(f"Overriding shouldApply to false due to low score: {match_score}")

        if mismatches and len(mismatches) > 0:
            if match_score < 80:
                should_apply = False
                logger.info(f"Overriding shouldApply to false due to mismatches and score < 80")
        
        return {
            'shouldApply': should_apply,
            'reason': str(result['reason']).strip(),
            'matchScore': match_score,
            'mismatches': [str(m).strip() for m in result['mismatches']]
        }
    
    def batch_analyze_jobs(
        self,
        resume_text: str,
        jobs: List[Dict],
        job_preferences: Dict
    ) -> List[Dict]:
        """
        Analyze multiple jobs at once.
        
        Args:
            resume_text: The candidate's resume
            jobs: List of job information dicts
            job_preferences: Candidate's preferences
            
        Returns:
            List of analysis results for each job
        """
        results = []
        
        for job in jobs:
            try:
                result = self.analyze_job_match(
                    resume_text=resume_text,
                    job_information=job,
                    job_preferences=job_preferences
                )
                result['job_id'] = job.get('id', None)
                result['job_title'] = job.get('title', 'Unknown')
                results.append(result)
            except Exception as e:
                logger.error(f"Error analyzing job {job.get('id', 'unknown')}: {str(e)}")
                results.append({
                    'job_id': job.get('id', None),
                    'job_title': job.get('title', 'Unknown'),
                    'shouldApply': False,
                    'reason': 'Analysis failed',
                    'matchScore': 0,
                    'mismatches': ['Error during analysis'],
                    'error': str(e)
                })
        
        return results
