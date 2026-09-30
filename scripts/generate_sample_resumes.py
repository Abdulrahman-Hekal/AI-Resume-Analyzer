import os
from pathlib import Path
import docx
from pypdf import PdfWriter

SAMPLES_DIR = Path(__file__).resolve().parent.parent / "samples"
os.makedirs(SAMPLES_DIR, exist_ok=True)

def generate_docx(filename: str, title: str, email: str, phone: str, summary: str, skills: str, experience: list, education: list):
    doc = docx.Document()
    doc.add_heading(title, level=1)
    doc.add_paragraph(f"Email: {email} | Phone: {phone} | Location: Austin, TX | LinkedIn: linkedin.com/in/{email.split('@')[0]}")
    
    doc.add_heading("Professional Summary", level=2)
    doc.add_paragraph(summary)
    
    doc.add_heading("Technical Skills", level=2)
    doc.add_paragraph(skills)
    
    doc.add_heading("Work Experience", level=2)
    for exp in experience:
        p = doc.add_paragraph()
        run = p.add_run(f"{exp['role']} — {exp['company']} ({exp['dates']})\n")
        run.bold = True
        p.add_run(exp['desc'])
        
    doc.add_heading("Education", level=2)
    for edu in education:
        p = doc.add_paragraph()
        run = p.add_run(f"{edu['degree']} — {edu['school']} ({edu['year']})\n")
        run.bold = True
        p.add_run(f"Field of study: {edu['field']}")

    out_path = SAMPLES_DIR / filename
    doc.save(out_path)
    print(f"Created sample DOCX: {out_path}")

def generate_pdf(filename: str, title: str, email: str, phone: str, summary: str, skills: str):
    # Minimal PDF spec text stream
    full_text = f"{title} - {email} - {phone} - Summary: {summary} - Skills: {skills}"
    pdf_bytes = (
        b"%PDF-1.4\n"
        b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n"
        b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n"
        b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >> endobj\n"
        b"4 0 obj << /Length 200 >> stream\n"
        b"BT /F1 12 Tf 72 712 Td (" + full_text.encode("latin-1", "replace")[:190] + b") Tj ET\n"
        b"endstream\nendobj\n"
        b"5 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n"
        b"xref\n0 6\n0000000000 65535 f \n0000000010 00000 n \n0000000060 00000 n \n0000000117 00000 n \n0000000244 00000 n \n0000000490 00000 n \n"
        b"trailer << /Size 6 /Root 1 0 R >>\nstartxref\n560\n%%EOF"
    )
    out_path = SAMPLES_DIR / filename
    with open(out_path, "wb") as f:
        f.write(pdf_bytes)
    print(f"Created sample PDF: {out_path}")

if __name__ == "__main__":
    generate_docx(
        filename="sample_alex_morgan_fullstack.docx",
        title="Alex Morgan - Full Stack & Python Engineer",
        email="alex.morgan@university.edu",
        phone="(512) 555-0199",
        summary="Results-oriented Full Stack Engineer with 2+ years of experience designing robust RESTful APIs in FastAPI and crafting responsive interfaces in JavaScript and HTML5. Passionate about automated testing, containerization, and clean software architecture.",
        skills="Python, FastAPI, SQLite, PostgreSQL, JavaScript, HTML5, CSS3, Docker, Git, REST API, Pytest, Linux",
        experience=[
            {
                "role": "Full Stack Developer",
                "company": "Nexus Solutions",
                "dates": "2023 - Present",
                "desc": "Architected modular FastAPI backend services reducing response latency by 35%. Integrated SQLite and PostgreSQL database persistence with SQLAlchemy ORM. Built responsive client dashboards using modern Vanilla JavaScript and CSS."
            },
            {
                "role": "Junior Backend Intern",
                "company": "Austin Tech Labs",
                "dates": "2022 - 2023",
                "desc": "Implemented RESTful API endpoints and automated unit tests using pytest. Containerized local microservices using Docker Compose."
            }
        ],
        education=[
            {
                "degree": "Bachelor of Science in Computer Science",
                "school": "University of Texas at Austin",
                "year": "2024",
                "field": "Computer Science / Software Engineering"
            }
        ]
    )

    generate_docx(
        filename="sample_sarah_connor_ml_engineer.docx",
        title="Sarah Connor - Machine Learning & AI Engineer",
        email="sarah.connor@ai-labs.org",
        phone="(415) 555-0142",
        summary="AI and Machine Learning Engineer specializing in Natural Language Processing (NLP), Large Language Model (LLM) fine-tuning, and Retrieval-Augmented Generation (RAG) pipelines. Proven ability to deploy low-latency inference services in Python and FastAPI.",
        skills="Python, PyTorch, Machine Learning, Deep Learning, NLP, RAG, Transformers, FastAPI, Docker, Scikit-Learn, Pandas, NumPy, Git",
        experience=[
            {
                "role": "Applied AI Researcher",
                "company": "Cognitive Systems",
                "dates": "2022 - Present",
                "desc": "Built semantic RAG retrieval architectures using dense vector embeddings and cosine similarity. Fine-tuned LLM agents for structured domain extraction with Pydantic."
            }
        ],
        education=[
            {
                "degree": "Master of Science in Artificial Intelligence",
                "school": "Stanford University",
                "year": "2023",
                "field": "Artificial Intelligence & Computational Linguistics"
            }
        ]
    )

    print("All sample resumes generated in samples/ folder.")
