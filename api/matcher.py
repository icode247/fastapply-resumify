import PyPDF2
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import spacy
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Set
import re
import logging
from collections import defaultdict
import requests
from io import BytesIO

class EnhancedResumeJobMatcher:
    
    def __init__(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('resume_matcher.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except Exception as e:
            self.logger.error(f"Failed to load NLP models: {str(e)}")
            raise RuntimeError("Failed to initialize required NLP models")

        
        self.vectorizer = TfidfVectorizer(
            stop_words='english',
            max_features=5000,
            ngram_range=(1, 3)
        )
        
        self.weights = {
            'required_skills': 0.25,
            'preferred_skills': 0.15,
            'experience': 0.20,
            'education': 0.15,
            'keyword_similarity': 0.10,
            'context_relevance': 0.05,
            'role_alignment': 0.10,
        }
        
        # Add input validation for weights
        total_weight = sum(self.weights.values())
        if not 0.99 <= total_weight <= 1.01:  # Allow small floating point differences
            raise ValueError(f"Weights must sum to 1.0, got {total_weight}")
        self.cached_embeddings = {}

        self._initialize_skill_patterns()
        
    def _initialize_skill_patterns(self):
        """Initialize comprehensive skill patterns by industry and role."""
        self.skill_patterns = {
            # Software Engineering
            'software_engineering': {
                'pattern': r'python|java(?:script)?|typescript|react|angular|vue|node\.js|express|django|flask|spring|asp\.net|ruby|php|golang|scala|rust',
                'weight': 1.0
            },
            # Backend Development
            'backend': {
                'pattern': r'api|rest|graphql|microservices|django|flask|express|spring|nodejs|postgresql|mysql|mongodb|redis|elasticsearch|kafka|rabbitmq|celery',
                'weight': 1.0
            },
            # Frontend Development
            'frontend': {
                'pattern': r'html5|css3|sass|less|javascript|typescript|react|angular|vue|next\.js|webpack|babel|tailwind|bootstrap|responsive design',
                'weight': 1.0
            },
            # Mobile Development
            'mobile': {
                'pattern': r'ios|android|swift|kotlin|react native|flutter|mobile development|xamarin|ionic|cordova|objective-c|mobile app|ui/ux',
                'weight': 0.9
            },
            # DevOps & Cloud
            'devops': {
                'pattern': r'aws|azure|gcp|docker|kubernetes|jenkins|gitlab|ci/cd|terraform|ansible|prometheus|grafana|cloud formation|helm|istio|openshift',
                'weight': 0.95
            },
            # Data Science & AI
            'data_science': {
                'pattern': r'machine learning|deep learning|tensorflow|pytorch|keras|scikit-learn|pandas|numpy|r|matlab|statistics|data mining|neural networks|nlp',
                'weight': 0.95
            },
            # Blockchain
            'blockchain': {
                'pattern': r'blockchain|ethereum|solidity|web3|smart contracts|cryptocurrency|bitcoin|hyperledger|consensus|defi|nft|dapp|metamask',
                'weight': 0.9
            },
            # Security
            'security': {
                'pattern': r'cybersecurity|penetration testing|ethical hacking|security\+|cissp|ceh|encryption|firewall|siem|vulnerability|incident response|forensics',
                'weight': 0.9
            },
            # UI/UX Design
            'design': {
                'pattern': r'figma|sketch|adobe xd|invision|user research|wireframing|prototyping|user testing|ux design|ui design|accessibility|usability',
                'weight': 0.9
            },
            # Product Management
            'product': {
                'pattern': r'product management|agile|scrum|jira|confluence|roadmap|stakeholder|user stories|backlog|mvp|okr|market research|product strategy',
                'weight': 0.85
            },
            # Data Engineering
            'data_engineering': {
                'pattern': r'etl|data warehouse|big data|hadoop|spark|airflow|databricks|snowflake|redshift|data modeling|data pipeline|data lake',
                'weight': 0.9
            },
            # Technical Writing
            'technical_writing': {
                'pattern': r'technical writing|documentation|api docs|user guides|markdown|restructuredtext|sphinx|swagger|openapi|content strategy|information architecture',
                'weight': 0.8
            },
            # Sales Engineering
            'sales_engineering': {
                'pattern': r'sales engineering|pre-sales|poc|rfi|rfp|customer facing|solution architecture|technical presentations|sales stack|crm|salesforce',
                'weight': 0.8
            },
            # Marketing
            'marketing': {
                'pattern': r'digital marketing|seo|sem|social media|content marketing|analytics|marketing automation|hubspot|marketo|ab testing|conversion|growth',
                'weight': 0.8
            },
            # HR Tech
            'hr': {
                'pattern': r'hris|workday|successfactors|recruiting|talent management|performance management|compensation|benefits|employee relations|diversity',
                'weight': 0.7
            },
            # Finance Tech
            'finance': {
                'pattern': r'financial analysis|trading systems|risk management|bloomberg|refinitiv|financial modeling|payment processing|accounting software|fintech',
                'weight': 0.8
            }
        }

        # Role-specific requirements
        self.role_patterns = {
            'junior': r'junior|entry level|intern|graduate|0-2 years|fresh graduate',
            'mid': r'mid level|intermediate|associate|2-5 years',
            'senior': r'senior|lead|principal|architect|staff|5\+ years|manager',
            'management': r'manager|director|head|vp|chief|c-level|executive'
        }
        
        # Education patterns
        self.education_patterns = {
            'phd': r'ph\.?d|doctor of philosophy',
            'masters': r'master\'?s|ms|m\.s\.|msc|m\.sc\.|mba',
            'bachelors': r'bachelor\'?s|bs|b\.s\.|bsc|b\.sc\.|b\.?a\.',
            'certifications': r'certification|certified|certificate|aws certified|microsoft certified|google certified|cissp|ceh|pmp',
            'associate': r'associate\'?s|asc|a\.sc\.'

        }
        
        # Experience level patterns
        self.experience_patterns = {
            'senior': r'senior|lead|principal|architect|staff|manager',
            'mid': r'mid-level|intermediate|junior|software engineer \d+',
            'junior': r'junior|entry[ -]level|graduate|intern'
        }

    def extract_text_from_pdf(self, pdf_url: str) -> str:
        """Extract text content from PDF URL with improved error handling and timeout."""
        try:
            response = requests.get(pdf_url, timeout=30)
            response.raise_for_status()
            
            pdf_file = BytesIO(response.content)
            
            if not pdf_file.getvalue().startswith(b'%PDF'):
                raise ValueError("Invalid PDF file format")
            
            reader = PyPDF2.PdfReader(pdf_file)
            
            MAX_PAGES = 50
            if len(reader.pages) > MAX_PAGES:
                self.logger.warning(f"PDF exceeds {MAX_PAGES} pages, processing first {MAX_PAGES} pages only")
                pages = reader.pages[:MAX_PAGES]
            else:
                pages = reader.pages
            
            text = ' '.join([page.extract_text() for page in pages])
            
            if not text.strip():
                raise ValueError("No text content extracted from PDF")
                
            return self._preprocess_text(text)
            
        except requests.Timeout:
            self.logger.error(f"Timeout downloading PDF from {pdf_url}")
            raise
        except requests.RequestException as e:
            self.logger.error(f"Failed to download PDF from {pdf_url}: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Error processing PDF from {pdf_url}: {str(e)}")
            raise

    def _preprocess_text(self, text: str) -> str:
        """Clean and preprocess extracted text."""
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def _extract_education_level(self, text: str) -> Dict[str, bool]:
        """Extract education levels from text."""
        education_levels = {}
        for level, pattern in self.education_patterns.items():
            education_levels[level] = bool(re.search(pattern, text.lower()))
        return education_levels

    def _extract_experience_level(self, text: str) -> str:
        """Extract experience level from text."""
        for level, pattern in self.experience_patterns.items():
            if re.search(pattern, text.lower()):
                return level
        return 'unspecified'

    def _calculate_years_of_experience(self, text: str) -> float:
        """Calculate total years of experience from text."""
        # Look for patterns like "X years of experience" or "X+ years"
        experience_matches = re.findall(r'(\d+)(?:\+)?\s*(?:-\s*\d+)?\s*years?(?:\s+of)?\s+experience', text.lower())
        if experience_matches:
            # Take the highest mentioned years
            return max(float(years) for years in experience_matches)
        return 0.0

    def extract_skills(self, text: str) -> Dict[str, Set[str]]:
        """Enhanced skill extraction with categorization."""
        skills = defaultdict(set)
        
        for category, pattern_info in self.skill_patterns.items():
            matches = re.finditer(pattern_info['pattern'], text.lower())
            skills[category].update(match.group() for match in matches)
            
        # Use spaCy for additional skill extraction
        doc = self.nlp(text)
        for ent in doc.ents:
            if ent.label_ in ['ORG', 'PRODUCT']:
                # Categorize based on keywords in entity
                for category, pattern_info in self.skill_patterns.items():
                    if re.search(pattern_info['pattern'], ent.text.lower()):
                        skills[category].add(ent.text.lower())
        
        return skills

    def calculate_semantic_similarity(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity using TF-IDF instead of transformers."""
        try:
            # Use TF-IDF vectorizer for similarity
            texts = [text1, text2]
            tfidf_matrix = self.vectorizer.fit_transform(texts)
            return float(cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0])
        except Exception as e:
            self.logger.error(f"Error calculating semantic similarity: {str(e)}")
            return 0.0

    def calculate_match_score(self, resume_text: str, job_description: str) -> Dict:
        """Calculate match score with input validation and error handling."""
        if not resume_text or not job_description:
            raise ValueError("Resume text and job description cannot be empty")
            
        MAX_TEXT_LENGTH = 100000  # characters
        if len(resume_text) > MAX_TEXT_LENGTH or len(job_description) > MAX_TEXT_LENGTH:
            raise ValueError(f"Text length exceeds maximum of {MAX_TEXT_LENGTH} characters")

        try:
            # Extract all information
            resume_skills = self.extract_skills(resume_text)
            job_skills = self.extract_skills(job_description)
            
            # Calculate skill match scores by category
            skill_scores = {}
            total_skill_score = 0
            matched_skills = defaultdict(set)
            
            for category in self.skill_patterns:
                if job_skills[category]:
                    match_ratio = len(resume_skills[category].intersection(job_skills[category])) / len(job_skills[category])
                    weight = self.skill_patterns[category]['weight']
                    skill_scores[category] = match_ratio * weight
                    total_skill_score += skill_scores[category]
                    matched_skills[category] = resume_skills[category].intersection(job_skills[category])
            
            # Calculate experience match
            required_years = self._calculate_years_of_experience(job_description)
            actual_years = self._calculate_years_of_experience(resume_text)
            experience_score = min(actual_years / required_years if required_years > 0 else 1.0, 1.0)
            
            # Calculate education match
            job_education = self._extract_education_level(job_description)
            resume_education = self._extract_education_level(resume_text)
            education_score = sum(1 for level in job_education if job_education[level] and resume_education[level]) / max(sum(job_education.values()), 1)
            
            # Calculate keyword similarity
            texts = [resume_text, job_description]
            tfidf_matrix = self.vectorizer.fit_transform(texts)
            keyword_score = float(cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0])
            
            # Add semantic similarity scoring
            semantic_score = self.calculate_semantic_similarity(resume_text, job_description)
            
            # Add context windows analysis
            context_scores = self.analyze_context_windows(resume_text, job_description)
            
            # Add role-specific scoring
            role_alignment_score = self.calculate_role_alignment(resume_text, job_description)

            # Calculate weighted total score
            total_score = (
                self.weights['required_skills'] * total_skill_score +
                self.weights['experience'] * experience_score +
                self.weights['education'] * education_score +
                self.weights['keyword_similarity'] * keyword_score +
                self.weights['context_relevance'] * context_scores['relevance'] +
                self.weights['role_alignment'] * role_alignment_score
            )

            # Add score validation
            for score_name, score_value in skill_scores.items():
                if not 0 <= score_value <= 1:
                    self.logger.warning(f"Invalid score value for {score_name}: {score_value}")
                    skill_scores[score_name] = max(0, min(1, score_value))
            
            return {
                'total_score': float(total_score),
                'skill_scores': {k: float(v) for k, v in skill_scores.items()},
                'experience_score': float(experience_score),
                'education_score': float(education_score),
                'keyword_score': float(keyword_score),
                'semantic_similarity': float(semantic_score),
                'context_scores': {k: float(v) for k, v in context_scores.items()},
                'role_alignment': float(role_alignment_score),
                'matched_skills': dict(matched_skills),
                'years_of_experience': float(actual_years),
                'education_level': resume_education,
                'experience_level': self._extract_experience_level(resume_text)
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating match score: {str(e)}")
            raise

    def process_resume(self, resume_url: str, job_description: str) -> Dict:
        """Process a single resume with enhanced error handling."""
        try:
            resume_text = self.extract_text_from_pdf(resume_url)
            if not resume_text:
                return {'resume': resume_url, 'error': 'Failed to extract text'}
            
            scores = self.calculate_match_score(resume_text, job_description)
            return {
                'resume': resume_url,
                'status': 'success',
                **scores
            }
        except Exception as e:
            self.logger.error(f"Error processing resume {resume_url}: {str(e)}")
            return {
                'resume': resume_url,
                'status': 'error',
                'error': str(e)
            }

    def rank_resumes(self, resume_urls: List[str], job_description: str) -> pd.DataFrame:
        """Rank resumes with improved concurrency and error handling."""
        if not resume_urls:
            raise ValueError("No resume URLs provided")
        if not job_description:
            raise ValueError("Job description cannot be empty")
            
        MAX_WORKERS = min(32, len(resume_urls))
        results = []
        
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            future_to_url = {
                executor.submit(self.process_resume, url, job_description): url 
                for url in resume_urls
            }
            
            try:
                for future in as_completed(future_to_url, timeout=300):  # 5 minute timeout
                    url = future_to_url[future]
                    try:
                        result = future.result(timeout=60)  # 1 minute timeout per resume
                        results.append(result)
                    except Exception as e:
                        self.logger.error(f"Error processing {url}: {str(e)}")
                        results.append({
                            'resume': url,
                            'status': 'error',
                            'error': str(e)
                        })
            except TimeoutError:
                self.logger.error("Resume ranking process timed out")
                raise
        
        return pd.DataFrame(results)

    def analyze_context_windows(self, resume_text: str, job_description: str) -> Dict[str, float]:
        """Analyze text in context windows to better understand skill usage context."""
        window_size = 100  # characters
        windows_resume = self._create_context_windows(resume_text, window_size)
        windows_job = self._create_context_windows(job_description, window_size)
        
        context_scores = {
            'relevance': 0.0,
            'skill_context_match': 0.0,
            'experience_context_match': 0.0
        }
        
        # Calculate contextual relevance scores
        for job_window in windows_job:
            max_window_score = max(
                self.calculate_semantic_similarity(job_window, resume_window)
                for resume_window in windows_resume
            )
            context_scores['relevance'] += max_window_score
            
        context_scores['relevance'] /= len(windows_job)
        return context_scores

    def _create_context_windows(self, text: str, window_size: int) -> List[str]:
        """Create overlapping context windows from text."""
        words = text.split()
        windows = []
        for i in range(0, len(words), window_size // 2):
            window = ' '.join(words[i:i + window_size])
            if window:
                windows.append(window)
        return windows

    def calculate_role_alignment(self, resume_text: str, job_description: str) -> float:
        """Calculate how well the resume aligns with the specific role requirements."""
        # Extract role requirements
        job_role = self._extract_role_requirements(job_description)
        resume_role = self._extract_role_requirements(resume_text)
        
        # Calculate alignment score
        return self.calculate_semantic_similarity(job_role, resume_role)

    def _extract_role_requirements(self, text: str) -> str:
        """Extract role-specific requirements and context from text."""
        # Find role level
        role_level = 'unknown'
        for level, pattern in self.role_patterns.items():
            if re.search(pattern, text.lower()):
                role_level = level
                break
        
        # Extract relevant context around role requirements
        context_window = 200  # characters
        role_matches = []
        
        for level, pattern in self.role_patterns.items():
            matches = re.finditer(pattern, text.lower())
            for match in matches:
                start = max(0, match.start() - context_window)
                end = min(len(text), match.end() + context_window)
                role_matches.append(text[start:end])
        
        # If no specific role context found, return a summary
        if not role_matches:
            return f"{role_level} role: {text[:500]}"  # First 500 chars as fallback
        
        # Combine all role-relevant contexts
        return f"{role_level} role: {' ... '.join(role_matches)}"
