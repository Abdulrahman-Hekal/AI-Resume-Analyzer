import os
from fastapi import UploadFile, HTTPException, status
from app.core.config import settings

def validate_uploaded_file(file: UploadFile, content: bytes) -> str:
    """
    Validates uploaded resume file:
    - Size check (not empty, not oversized)
    - Extension check (.pdf, .docx)
    - Magic bytes signature check to prevent renamed malicious/corrupt files.
    Returns the normalized file extension ('pdf' or 'docx').
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is missing or invalid."
        )

    # Check size
    file_size = len(content)
    if file_size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file is empty (0 bytes). Please upload a valid resume."
        )
    
    if file_size > settings.MAX_UPLOAD_SIZE_BYTES:
        max_mb = settings.MAX_UPLOAD_SIZE_BYTES / (1024 * 1024)
        status_code = getattr(status, "HTTP_413_CONTENT_TOO_LARGE", status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
        raise HTTPException(
            status_code=status_code,
            detail=f"File exceeds maximum allowed size of {max_mb:.1f} MB."
        )

    # Check extension
    filename = file.filename.lower()
    ext = filename.rsplit(".", 1)[-1] if "." in filename else ""
    if ext not in settings.ALLOWED_EXTENSIONS:
        allowed = ", ".join(settings.ALLOWED_EXTENSIONS)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '.{ext}'. Allowed formats are: {allowed}."
        )

    # Magic byte validation
    if ext == "pdf":
        if not content.startswith(b"%PDF-"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid PDF file. The file header does not match the PDF standard."
            )
    elif ext == "docx":
        # Standard ZIP container magic bytes for Office Open XML (.docx)
        if not content.startswith(b"PK\x03\x04"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid DOCX file. The file format is corrupted or not a valid Word document."
            )

    return ext
