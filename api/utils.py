# api/utils.py
import re

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

LATEX_TEMPLATE = r"""
        \documentclass[11pt,a4paper]{article}
        \usepackage[left=0.75in,top=0.6in,right=0.75in,bottom=0.6in]{geometry}
        \usepackage{hyperref}
        \usepackage{enumitem}
        \usepackage{fontawesome}
        \usepackage{titlesec}
        \usepackage{xcolor}

        \definecolor{linkcolor}{RGB}{37, 84, 199}

        \titleformat{\section}{\Large\bfseries\color{linkcolor}}{\thesection}{1em}{}[\titlerule]
        \titlespacing*{\section}{0pt}{12pt}{8pt}

        \begin{document}

        \begin{center}
        {\LARGE\textbf{Ekekenta Odonyenfe Clinton}}\\[0.3em]
        {\large Junior Backend Developer}\\[0.3em]
        +234 816 459 3466 $\bullet$ zionekekenta@gmail.com $\bullet$ in/ekekenta-odionyenfe-c-97569b191 $\bullet$ Lagos Island, Nigeria
        \end{center}

        \vspace{0.5em}
        Over 6 years of turning complex backend challenges into scalable solutions! Started coding in 2017, and now as a senior backend developer, I architect systems that handle millions of requests while maintaining peak performance!

        \section*{PROFESSIONAL SUMMARY}
        Senior Backend Developer with over 5 years of experience specializing in building scalable distributed systems and APIs. Expert in Node.js ecosystem, microservices architecture, and real-time applications. Proven track record in implementing secure, high-performance backend solutions handling millions of daily requests. Strong focus on code quality, system architecture, and performance optimization. Experienced in building fintech, event management, and AI-driven applications.

        \section*{SKILLS}
        \textbf{Programming Languages:} JavaScript (ES6+), TypeScript, Python, SQL\\
        \textbf{Backend Development:} Node.js, Express.js, NestJS, GraphQL, WebSocket, Socket.IO, Redis\\
        \textbf{Databases:} PostgreSQL, MongoDB, MySQL, Redis, Elasticsearch\\
        \textbf{Cloud \& DevOps:} AWS (EC2, S3, Lambda), Docker, Kubernetes, Jenkins\\
        \textbf{API Development:} REST, GraphQL, WebSocket, API Gateway, Swagger/OpenAPI\\
        \textbf{Tools \& Platforms:} Git, GitHub, GitLab, Jira, Confluence\\
        \textbf{Testing \& Monitoring:} Jest, Mocha, Chai, Supertest, ELK Stack, Prometheus

        \section*{EXPERIENCE}

        \textbf{ServerStack Solutions} \hfill Remote\\
        \textit{Senior Backend Developer} \hfill October 2023
        \begin{itemize}[leftmargin=*]
        \item Architected microservices infrastructure handling 1M+ daily requests with 99.9\% uptime
        \item Implemented real-time notification system using WebSocket and Redis, supporting 100K+ concurrent users
        \item Designed API gateway with rate limiting and caching, improving response times by 40\%
        \item Created automated deployment pipeline reducing deployment time by 60\%
        \item Built custom NPM packages used across 20+ internal projects
        \item Implemented GraphQL federation across microservices, reducing data fetch times by 45\%
        \item Managed Kubernetes clusters for high-availability production deployments
        \end{itemize}

        \textbf{Easyplan.io} \hfill Remote\\
        \textit{Lead Backend Developer} \hfill September 2022
        \begin{itemize}[leftmargin=*]
        \item Architected and developed scalable backend for event planning platform serving 50K+ users
        \item Implemented real-time availability tracking system for event professionals
        \item Designed and built booking and scheduling system handling 10K+ daily bookings
        \item Created geolocation-based search API with Redis caching, achieving sub-100ms response times
        \item Implemented payment processing system integrating with Stripe and PayPal
        \item Built notification system for real-time booking updates using Socket.IO
        \item Developed API for mobile applications with 99.9\% uptime
        \end{itemize}

        \textbf{Faadoil} \hfill Remote\\
        \textit{Backend Developer} \hfill January 2022
        \begin{itemize}[leftmargin=*]
        \item Developed backend system for fuel distribution management handling 5K+ daily transactions
        \item Implemented real-time inventory tracking system with WebSocket
        \item Created route optimization algorithm reducing delivery times by 30\%
        \item Built automated reporting system for distribution analytics
        \item Implemented secure authentication system with role-based access control
        \item Developed RESTful APIs for mobile and web applications
        \end{itemize}

        \textbf{FastApply} \hfill Remote\\
        \textit{Backend Developer} \hfill July 2020
        \begin{itemize}[leftmargin=*]
        \item Built scalable web scraping system processing 100K+ job listings daily
        \item Implemented AI-powered job matching algorithm using machine learning
        \item Developed automated application system handling 1K+ applications daily
        \item Created resume parsing and analysis system using NLP
        \item Implemented job alert system with custom matching criteria
        \item Built API integration with major job boards and LinkedIn
        \end{itemize}

        \textbf{Karakorma} \hfill Remote\\
        \textit{Backend Developer} \hfill January 2017
        \begin{itemize}[leftmargin=*]
        \item Developed real-time chat system supporting 10K+ concurrent users
        \item Implemented WebRTC-based video calling feature with low latency
        \item Created secure wallet system for cryptocurrency transactions
        \item Built notification system for trade alerts and platform updates
        \item Implemented websocket-based real-time price updates
        \item Developed API for mobile applications with OAuth2 authentication
        \end{itemize}

        \textbf{Tigris Data} \hfill Remote\\
        \textit{Backend Developer} \hfill January 2014
        \begin{itemize}[leftmargin=*]
        \item Built scalable REST APIs handling 500K+ daily transactions
        \item Implemented real-time data processing pipeline using Apache Kafka
        \item Developed authentication system using JWT and OAuth2
        \item Created automated testing suite achieving 90\% code coverage
        \item Optimized database queries reducing response time by 50\%
        \item Implemented caching strategy using Redis and Memcached
        \end{itemize}

        \section*{EDUCATION}
        Bachelor Degree of Computer Science at Boston University

        \end{document}
"""


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