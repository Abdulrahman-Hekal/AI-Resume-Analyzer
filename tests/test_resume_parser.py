import io
import docx
from pypdf import PdfWriter
from app.services.resume_parser import ResumeParser
from app.utils.file_validation import validate_uploaded_file
from fastapi import UploadFile, HTTPException

def create_sample_pdf_bytes(text: str) -> bytes:
    """Generate a valid in-memory PDF with text stream for testing."""
    # We can create a simple PDF with pypdf or minimal PDF spec bytes
    # Minimal valid PDF structure with text stream:
    pdf_content = (
        b"%PDF-1.4\n"
        b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n"
        b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n"
        b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >> endobj\n"
        b"4 0 obj << /Length 55 >> stream\n"
        b"BT /F1 12 Tf 72 712 Td (" + text.encode("latin-1", "replace") + b") Tj ET\n"
        b"endstream\nendobj\n"
        b"5 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n"
        b"xref\n0 6\n0000000000 65535 f \n0000000010 00000 n \n0000000060 00000 n \n0000000117 00000 n \n0000000244 00000 n \n0000000352 00000 n \n"
        b"trailer << /Size 6 /Root 1 0 R >>\nstartxref\n428\n%%EOF"
    )
    return pdf_content

def create_sample_docx_bytes(text: str) -> bytes:
    doc = docx.Document()
    doc.add_heading("Jane Doe - Software Engineer", level=1)
    doc.add_paragraph("Email: janedoe@example.com | Phone: (555) 234-5678")
    doc.add_paragraph(text)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()

def test_pdf_extraction():
    sample_text = "Experienced Python and FastAPI Engineer with experience in Docker and PostgreSQL databases."
    pdf_bytes = create_sample_pdf_bytes(sample_text)
    extracted = ResumeParser.extract_text_from_pdf(pdf_bytes)
    assert "Python" in extracted
    assert "FastAPI" in extracted

def test_docx_extraction():
    sample_text = "Proficient in Python, Machine Learning, and building RESTful web services with SQLite."
    docx_bytes = create_sample_docx_bytes(sample_text)
    extracted = ResumeParser.extract_text_from_docx(docx_bytes)
    assert "Jane Doe" in extracted
    assert "Python" in extracted
    assert "janedoe@example.com" in extracted

def test_empty_file_validation():
    upload = UploadFile(filename="empty.pdf", file=io.BytesIO(b""))
    try:
        validate_uploaded_file(upload, b"")
        assert False, "Should have raised 400"
    except HTTPException as e:
        assert e.status_code == 400
        assert "empty" in e.detail.lower()

def test_invalid_extension():
    upload = UploadFile(filename="virus.exe", file=io.BytesIO(b"malicious"))
    try:
        validate_uploaded_file(upload, b"malicious")
        assert False, "Should have raised 400"
    except HTTPException as e:
        assert e.status_code == 400
        assert "unsupported file format" in e.detail.lower()

def test_corrupted_pdf_header():
    upload = UploadFile(filename="fake.pdf", file=io.BytesIO(b"NOT A REAL PDF HEADER"))
    try:
        validate_uploaded_file(upload, b"NOT A REAL PDF HEADER")
        assert False, "Should have raised 400"
    except HTTPException as e:
        assert e.status_code == 400
        assert "invalid pdf" in e.detail.lower()

def test_api_resume_upload_and_list(client, user_auth_headers):
    sample_text = (
        "Alex Developer\n"
        "Email: alex.dev@example.com | Phone: 555-123-4567\n\n"
        "Summary:\nFull Stack developer proficient in Python, FastAPI, React, SQL, and Docker.\n\n"
        "Experience:\nSoftware Engineer at TechCorp for 2 years.\n\n"
        "Education:\nB.S. in Computer Science, University of Technology."
    )
    docx_bytes = create_sample_docx_bytes(sample_text)

    files = {"file": ("my_resume.docx", docx_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
    res = client.post("/api/resumes", files=files, headers=user_auth_headers)
    assert res.status_code == 201
    data = res.json()
    assert data["filename"] == "my_resume.docx"
    assert data["file_type"] == "docx"
    resume_id = data["id"]

    # Verify listing
    res_list = client.get("/api/resumes", headers=user_auth_headers)
    assert res_list.status_code == 200
    assert res_list.json()["total"] >= 1

    # Verify details
    res_detail = client.get(f"/api/resumes/{resume_id}", headers=user_auth_headers)
    assert res_detail.status_code == 200
    assert "FastAPI" in res_detail.json()["raw_text"]

def test_oversized_file_validation():
    """Verify that uploads exceeding 10MB are rejected with HTTP 413."""
    upload = UploadFile(filename="huge.pdf", file=io.BytesIO(b""))
    huge_bytes = b"%PDF-" + b"0" * (11 * 1024 * 1024)
    try:
        validate_uploaded_file(upload, huge_bytes)
        assert False, "Should have raised 413"
    except HTTPException as e:
        assert e.status_code == 413
        assert "exceeds maximum allowed size" in e.detail.lower()

def test_fake_docx_header():
    """Verify that a non-ZIP file with a .docx extension is rejected."""
    upload = UploadFile(filename="fake.docx", file=io.BytesIO(b"Plain text masquerading as docx"))
    try:
        validate_uploaded_file(upload, b"Plain text masquerading as docx")
        assert False, "Should have raised 400"
    except HTTPException as e:
        assert e.status_code == 400
        assert "invalid docx" in e.detail.lower()

def test_scanned_image_only_pdf_disclaimer():
    """Verify that image-only or scanned PDFs raise 400 informing user about OCR/selectable text."""
    # Create valid PDF structure but with almost zero extractable text
    empty_pdf = create_sample_pdf_bytes("Hi")
    try:
        ResumeParser.extract_text_from_pdf(empty_pdf)
        assert False, "Should have raised 400"
    except HTTPException as e:
        assert e.status_code == 400
        assert "scanned image" in e.detail.lower() or "readable text" in e.detail.lower()

def test_corrupted_pdf_structure():
    """Verify that invalid PDF bytes raise 400 gracefully."""
    corrupted_pdf_bytes = b"%PDF-1.4\nCorrupted binary content without xref or EOF"
    try:
        ResumeParser.extract_text_from_pdf(corrupted_pdf_bytes)
        assert False, "Should have raised 400"
    except HTTPException as e:
        assert e.status_code == 400
        assert "pdf" in e.detail.lower()

