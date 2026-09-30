import re
import math
from typing import List, Dict, Optional

def clean_text(text: str) -> str:
    """Clean extracted resume/job text by normalizing whitespace, bullet points, and special symbols."""
    if not text:
        return ""
    
    # Remove null characters
    text = text.replace("\x00", "")
    
    # Replace weird unicode bullets with standard dashes
    text = re.sub(r"[\u2022\u2023\u25E6\u2043\u2219\uf0b7\u25aa\u25ab]", "\n- ", text)
    
    # Normalize multiple newlines and spaces
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.splitlines()]
    
    # Remove excessive blank lines
    cleaned_lines = []
    prev_blank = False
    for line in lines:
        if not line:
            if not prev_blank:
                cleaned_lines.append("")
                prev_blank = True
        else:
            cleaned_lines.append(line)
            prev_blank = False
            
    return "\n".join(cleaned_lines).strip()

def extract_contact_info(text: str) -> Dict[str, Optional[str]]:
    """Extract candidate email and phone using high-precision regex patterns."""
    email_pattern = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
    phone_pattern = r"(?:(?:\+?1\s*(?:[.-]\s*)?)?(?:\(\s*([2-9]1[02-9]|[2-9][02-8]1|[2-9][02-8][02-9])\s*\)|([2-9]1[02-9]|[2-9][02-8]1|[2-9][02-8][02-9]))\s*(?:[.-]\s*)?)?([2-9]1[02-9]|[2-9][02-9]1|[2-9][02-9]{2})\s*(?:[.-]\s*)?([0-9]{4})(?:\s*(?:#|x\.?|ext\.?|extension)\s*(\d+))?|(?:\+?[0-9]{1,4}[\s.-]?)?\(?[0-9]{2,5}\)?[\s.-]?[0-9]{3,5}[\s.-]?[0-9]{3,5}"

    email_match = re.search(email_pattern, text)
    email = email_match.group(0) if email_match else None

    phone = None
    for match in re.finditer(phone_pattern, text):
        candidate = match.group(0).strip()
        # Ensure it has at least 7 digits to avoid matching short numbers or dates
        digits = re.sub(r"\D", "", candidate)
        if 7 <= len(digits) <= 15:
            phone = candidate
            break

    return {"email": email, "phone": phone}

def chunk_text(text: str, chunk_size_words: int = 250, overlap_words: int = 50) -> List[str]:
    """
    Split text into overlapping word chunks for semantic embedding in the RAG pipeline.
    Preserves context at chunk boundaries.
    """
    cleaned = clean_text(text)
    if not cleaned:
        return []

    words = cleaned.split()
    if len(words) <= chunk_size_words:
        return [cleaned]

    chunks = []
    step = chunk_size_words - overlap_words
    if step <= 0:
        step = chunk_size_words // 2 or 1

    for i in range(0, len(words), step):
        chunk_words = words[i : i + chunk_size_words]
        chunk = " ".join(chunk_words).strip()
        if chunk:
            chunks.append(chunk)
        if i + chunk_size_words >= len(words):
            break

    return chunks

def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Compute cosine similarity between two vector lists."""
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot_product = sum(a * b for a, b in zip(v1, v2))
    norm_a = math.sqrt(sum(a * a for a in v1))
    norm_b = math.sqrt(sum(b * b for b in v2))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return max(0.0, min(1.0, dot_product / (norm_a * norm_b)))
