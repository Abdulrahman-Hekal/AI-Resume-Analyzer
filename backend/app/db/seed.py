import asyncio
from typing import Optional
from sqlalchemy.orm import Session
from app.db.database import SessionLocal, engine, Base
from app.db.models import User, Job, KnowledgeDocument, KnowledgeChunk
from app.repositories.users import UserRepository
from app.services.rag_service import RAGService
from app.core.logging import logger

DEMO_JOBS = [
    {
        "title": "Full Stack Python / FastAPI Engineer",
        "company": "Nexus Technologies",
        "description": (
            "We are seeking an innovative Full Stack Python Engineer to build high-performance web applications "
            "and AI-integrated services. You will architect RESTful APIs using FastAPI, design SQLite/PostgreSQL databases, "
            "and craft responsive, accessible user interfaces with HTML5, CSS, and modern JavaScript. "
            "Experience with containerization (Docker) and automated testing (pytest) is highly valued."
        ),
        "required_skills": ["Python", "FastAPI", "REST API", "SQL", "JavaScript", "HTML", "CSS"],
        "preferred_skills": ["Docker", "Pytest", "PostgreSQL", "Git", "CI/CD"],
        "experience_years": 2.0,
        "education_level": "Bachelor's",
        "location": "Remote",
        "employment_type": "Full-time",
        "salary_range": "$85,000 - $115,000",
        "contact_email": "careers@nexustech.io"
    },
    {
        "title": "AI & RAG Systems Engineer",
        "company": "Cognitive Cloud Labs",
        "description": (
            "Join our applied AI team building intelligent retrieval systems and generative agent pipelines. "
            "Key responsibilities include implementing Retrieval-Augmented Generation (RAG) with vector embeddings, "
            "fine-tuning LLM prompts, integrating open-source models, and serving low-latency inference endpoints "
            "using Python and FastAPI."
        ),
        "required_skills": ["Python", "Machine Learning", "NLP", "RAG", "LLM", "FastAPI", "Vector Embeddings"],
        "preferred_skills": ["PyTorch", "HuggingFace", "LangChain", "Docker", "Scikit-Learn"],
        "experience_years": 3.0,
        "education_level": "Bachelor's",
        "location": "San Francisco, CA (Hybrid)",
        "employment_type": "Full-time",
        "salary_range": "$120,000 - $155,000",
        "contact_email": "hiring@cognitivecloudlabs.com"
    },
    {
        "title": "Senior Backend Infrastructure Engineer",
        "company": "Starlight Systems",
        "description": (
            "Looking for a Senior Backend Engineer to design scalable distributed microservices, "
            "optimize high-throughput database queries, and ensure 99.99% uptime. "
            "Deep expertise in Python or Go, relational databases (PostgreSQL/SQLite), Redis caching, "
            "and Kubernetes orchestration is required."
        ),
        "required_skills": ["Python", "Microservices", "PostgreSQL", "Redis", "Docker", "System Design"],
        "preferred_skills": ["Go", "Kubernetes", "AWS", "Kafka", "Linux"],
        "experience_years": 5.0,
        "education_level": "Bachelor's",
        "location": "Remote",
        "employment_type": "Full-time",
        "salary_range": "$140,000 - $180,000",
        "contact_email": "jobs@starlightsystems.dev"
    },
    {
        "title": "Junior Web Developer",
        "company": "Apex Creative Studio",
        "description": (
            "Exciting entry-level opportunity for a motivated Junior Web Developer. "
            "You will collaborate with senior engineers to implement interactive web pages, connect REST APIs, "
            "write clean HTML/CSS/JavaScript, and participate in code reviews. "
            "Academic projects, internships, or demonstrable Git repositories are welcome."
        ),
        "required_skills": ["JavaScript", "HTML", "CSS", "Git", "REST API"],
        "preferred_skills": ["Python", "FastAPI", "Responsive Design", "SQL"],
        "experience_years": 0.5,
        "education_level": "Associate / Bachelor's",
        "location": "New York, NY (Hybrid)",
        "employment_type": "Full-time",
        "salary_range": "$65,000 - $80,000",
        "contact_email": "talent@apexcreative.studio"
    },
    {
        "title": "Cloud & DevOps Solutions Engineer",
        "company": "Vanguard Cloud Services",
        "description": (
            "We are hiring a Cloud & DevOps Engineer to maintain automated deployment pipelines, "
            "manage AWS/GCP infrastructure as code via Terraform, and configure containerized workloads. "
            "Must have solid scripting experience in Python/Bash and a commitment to security best practices."
        ),
        "required_skills": ["AWS", "Docker", "CI/CD", "Linux", "Terraform", "Git"],
        "preferred_skills": ["Kubernetes", "Python", "Bash", "Prometheus", "Ansible"],
        "experience_years": 3.0,
        "education_level": "Bachelor's",
        "location": "Remote",
        "employment_type": "Full-time",
        "salary_range": "$110,000 - $140,000",
        "contact_email": "devops-hiring@vanguardcloud.com"
    }
]

KNOWLEDGE_DOCUMENTS = [
    {
        "title": "Resume Writing Best Practices: The Google XYZ Formula",
        "category": "resume_guideline",
        "source": "Industry Hiring Rubric",
        "content": (
            "High-impact resumes clearly differentiate between responsibilities and achievements. "
            "The most effective bullet formula is the Google XYZ structure: 'Accomplished [X] as measured by [Y], by doing [Z]'. "
            "For example: 'Reduced API response latency by 45% (measured via Prometheus) by implementing Redis caching and asynchronous query batching in FastAPI'. "
            "Avoid generic statements such as 'Responsible for backend bugs'. "
            "Always include measurable metrics: percentage improvements, volume of requests handled, dollar cost reductions, or user base growth. "
            "Keep technical resumes to 1-2 pages, use standard font sizes (10-12pt), and avoid multiple columns that confuse Applicant Tracking Systems (ATS)."
        )
    },
    {
        "title": "ATS Optimization and Formatting Standards",
        "category": "resume_guideline",
        "source": "ATS Technical Standards",
        "content": (
            "Applicant Tracking Systems (ATS) parse resumes using text extraction and keyword matching algorithms. "
            "To maximize ATS compatibility: 1. Use clean, single-column layouts without nested text boxes, graphics, or tables. "
            "2. Label sections with standard recognized headings: 'Work Experience', 'Education', 'Technical Skills', 'Projects', and 'Certifications'. "
            "3. State your technical skills explicitly in a dedicated section using both acronyms and full names (e.g. 'AWS (Amazon Web Services)', 'NLP (Natural Language Processing)'). "
            "4. Export files as clean selectable digital PDFs or DOCX files. Never upload scanned image PDFs where text is not selectable."
        )
    },
    {
        "title": "Modern Backend Engineer Career Roadmap: Junior to Senior",
        "category": "career_roadmap",
        "source": "Engineering Leadership Framework",
        "content": (
            "The journey from Junior to Senior Backend Engineer consists of three critical transitions:\n"
            "Phase 1: Implementation Proficiency (Junior). Mastering core programming (Python/Go), writing idiomatic code, handling errors gracefully, and writing unit tests.\n"
            "Phase 2: Architectural Ownership (Mid-Level). Designing relational database schemas, handling transactions, understanding index optimization, building clean RESTful APIs with FastAPI, and containerizing services with Docker.\n"
            "Phase 3: System Design & Strategic Impact (Senior). Designing distributed microservices, implementing event-driven architectures (Kafka/RabbitMQ), managing cloud infrastructure (AWS/GCP), conducting architecture reviews, and mentoring team members."
        )
    },
    {
        "title": "Fullstack AI Engineer Specialization Roadmap",
        "category": "career_roadmap",
        "source": "AI Engineering Consortium",
        "content": (
            "AI Engineering is bridging machine learning research and production software engineering. "
            "Core requirements for AI Engineers include: 1. Strong software engineering foundations: modular architecture, async programming in Python, FastAPI REST services. "
            "2. Retrieval-Augmented Generation (RAG): understanding vector databases, chunking strategies, semantic similarity metrics (cosine similarity), and reranking. "
            "3. LLM Integration & Prompt Engineering: structured schema outputs (Pydantic), system instruction design, and handling rate limits gracefully. "
            "4. Production deployment: Docker packaging, monitoring LLM token costs, and automated regression testing."
        )
    },
    {
        "title": "Essential Technical Skills: FastAPI and Asynchronous Python",
        "category": "skill_description",
        "source": "Python Web Standards",
        "content": (
            "FastAPI is a modern, high-performance web framework for building APIs with Python 3.8+ based on standard Python type hints. "
            "Key architectural advantages: High performance on par with NodeJS and Go (thanks to Starlette and Pydantic), "
            "automatic interactive API documentation via Swagger UI / OpenAPI, native async/await concurrency, "
            "and robust dependency injection. Key concepts to master include path operations, Pydantic request/response schemas, "
            "background tasks, database session lifecycle management with SQLAlchemy, and OAuth2 security with JWT tokens."
        )
    },
    {
        "title": "Docker Containerization & Kubernetes Fundamentals",
        "category": "skill_description",
        "source": "Cloud Native Computing Foundation",
        "content": (
            "Containerization packages an application and all its dependencies into an immutable container image. "
            "Docker concepts every developer must master: Multi-stage Dockerfiles for minimal production images, "
            "environment variable configuration, volume mounts for persistent data, and Docker Compose for multi-container local orchestration (app + database + redis). "
            "Kubernetes extends this to production cluster orchestration with Pods, Deployments, Services, ConfigMaps, and Ingress controllers."
        )
    },
    {
        "title": "Top Free Learning Resources for Software & AI Engineers",
        "category": "learning_resource",
        "source": "Open Education Directory",
        "content": (
            "Curated highest-quality free resources for self-directed engineering excellence:\n"
            "1. roadmap.sh: Industry standard interactive developer roadmaps covering Backend, DevOps, and AI.\n"
            "2. FastAPI Official Tutorials (fastapi.tiangolo.com): Comprehensive, hands-on architectural documentation.\n"
            "3. Full Stack Deep Learning (fullstackdeeplearning.com): Complete course on shipping machine learning systems to production.\n"
            "4. CS50 by Harvard University: Premier foundations of computer science, algorithms, and data structures.\n"
            "5. System Design Primer by Donne Martin: GitHub repository covering scalability, distributed caching, database sharding, and CAP theorem."
        )
    },
    {
        "title": "Top Industry Certifications with High ROI",
        "category": "learning_resource",
        "source": "Cloud & Hiring Benchmark Report",
        "content": (
            "Industry certifications that carry genuine credibility with technical hiring managers:\n"
            "1. AWS Certified Solutions Architect - Associate: Validates comprehensive cloud architecture and resilience patterns.\n"
            "2. Certified Kubernetes Administrator (CKA): Demonstrates hands-on cluster configuration and container troubleshooting.\n"
            "3. HashiCorp Certified: Terraform Associate: Proves Infrastructure-as-Code (IaC) competency.\n"
            "4. Meta Backend Developer Professional Certificate: Covers Python, database management, APIs, and version control."
        )
    }
]

async def seed_all(db: Optional[Session] = None):
    """Populates the database with initial users, jobs, and knowledge base documents."""
    should_close = False
    if db is None:
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        should_close = True

    rag = RAGService()

    try:
        logger.info("Checking and seeding demo users...")
        admin = UserRepository.get_by_email(db, "admin@gmail.com")
        if not admin:
            admin = UserRepository.create(
                db=db,
                email="admin@gmail.com",
                password="123456",
                full_name="Abdulrahman Hekal",
                role="admin"
            )
            logger.info(f"Created admin user: {admin.email}")

        candidate = UserRepository.get_by_email(db, "user@gmail.com")
        if not candidate:
            candidate = UserRepository.create(
                db=db,
                email="user@gmail.com",
                password="123456",
                full_name="Ahmed Salem",
                role="user"
            )
            logger.info(f"Created demo candidate user: {candidate.email}")

        logger.info("Checking and seeding demo jobs...")
        existing_jobs = db.query(Job).count()
        if existing_jobs == 0:
            for j_data in DEMO_JOBS:
                job = Job(
                    title=j_data["title"],
                    company=j_data["company"],
                    description=j_data["description"],
                    required_skills=j_data["required_skills"],
                    preferred_skills=j_data["preferred_skills"],
                    experience_years=j_data["experience_years"],
                    education_level=j_data["education_level"],
                    location=j_data["location"],
                    employment_type=j_data["employment_type"],
                    salary_range=j_data["salary_range"],
                    contact_email=j_data.get("contact_email"),
                    created_by_user_id=admin.id
                )
                db.add(job)
            db.commit()
            logger.info(f"Successfully seeded {len(DEMO_JOBS)} realistic job postings.")
        else:
            logger.info(f"Jobs already exist ({existing_jobs} records). Skipping job seed.")

        logger.info("Checking and seeding RAG knowledge base documents...")
        existing_docs = db.query(KnowledgeDocument).count()
        if existing_docs == 0:
            for doc in KNOWLEDGE_DOCUMENTS:
                await rag.ingest_document(
                    db=db,
                    title=doc["title"],
                    category=doc["category"],
                    content=doc["content"],
                    source=doc["source"]
                )
            logger.info(f"Successfully ingested {len(KNOWLEDGE_DOCUMENTS)} RAG knowledge documents with vector embeddings.")
        else:
            logger.info(f"Knowledge base already seeded ({existing_docs} docs). Skipping.")

        logger.info("Database seeding completed successfully!")
    finally:
        if should_close:
            db.close()

if __name__ == "__main__":
    asyncio.run(seed_all())
