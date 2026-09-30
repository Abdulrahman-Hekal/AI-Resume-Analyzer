import os
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError

from app.core.config import settings
from app.core.logging import logger
from app.db.database import engine, Base, SessionLocal
from app.db.models import KnowledgeDocument, Job, User
from app.db.seed import seed_all

# Routers
from app.api.routes.auth import router as auth_router
from app.api.routes.resumes import router as resumes_router
from app.api.routes.analysis import router as analysis_router
from app.api.routes.jobs import router as jobs_router
from app.api.routes.recommendations import router as recommendations_router
from app.api.routes.career import router as career_router

FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: initialize database and auto-seed if empty."""
    logger.info("Initializing SQLite database tables...")
    Base.metadata.create_all(bind=engine)
    
    # Auto-seed if database is brand new
    db = SessionLocal()
    try:
        user_count = db.query(User).count()
        if user_count == 0:
            logger.info("Database is empty. Executing initial seed...")
            await seed_all()
    except Exception as e:
        logger.error(f"Error during auto-seed: {e}")
    finally:
        db.close()
    
    yield
    logger.info("Shutting down AI Resume Analyzer backend.")

app = FastAPI(
    title="AI Resume Analyzer API",
    version="1.0.0",
    description=(
        "Production-grade AI Resume Analyzer API featuring AI Agents (Resume Analyzer, Job Matcher, Career Advisor), "
        "Retrieval-Augmented Generation (RAG), transparent multi-factor scoring, and full job management."
    ),
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Centralized Error Handlers
@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    logger.warning(f"HTTP {exc.status_code} on {request.method} {request.url.path}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "status_code": exc.status_code}
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for err in exc.errors():
        field = " -> ".join(str(loc) for loc in err.get("loc", []))
        msg = err.get("msg", "Invalid value")
        errors.append(f"{field}: {msg}")
    error_summary = "Validation error; " + "; ".join(errors)
    logger.warning(f"Validation error on {request.method} {request.url.path}: {error_summary}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": error_summary, "errors": exc.errors(), "status_code": 422}
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled server error on {request.method} {request.url.path}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred. Please contact the administrator.", "status_code": 500}
    )

# Health & System Status API
@app.get("/api/health", tags=["Health & Status"])
def health_check():
    """Health check endpoint exposing system readiness and active AI provider."""
    db = SessionLocal()
    try:
        jobs_count = db.query(Job).count()
        docs_count = db.query(KnowledgeDocument).count()
        return {
            "status": "healthy",
            "project": settings.PROJECT_NAME,
            "version": "1.0.0",
            "active_ai_provider": settings.AI_PROVIDER,
            "gemini_configured": bool(settings.GEMINI_API_KEY),
            "groq_configured": bool(settings.GROQ_API_KEY),
            "jobs_count": jobs_count,
            "rag_documents_count": docs_count,
            "database": "connected"
        }
    except Exception as e:
        return {"status": "degraded", "database_error": str(e)}
    finally:
        db.close()

# API Router Inclusions
app.include_router(auth_router, prefix="/api")
app.include_router(resumes_router, prefix="/api")
app.include_router(analysis_router, prefix="/api")
app.include_router(jobs_router, prefix="/api")
app.include_router(recommendations_router, prefix="/api")
app.include_router(career_router, prefix="/api")

# Serve Frontend static assets and HTML pages
if FRONTEND_DIR.exists():
    css_dir = FRONTEND_DIR / "css"
    if css_dir.exists():
        app.mount("/css", StaticFiles(directory=str(css_dir)), name="css")

    js_dir = FRONTEND_DIR / "js"
    if js_dir.exists():
        app.mount("/js", StaticFiles(directory=str(js_dir)), name="js")

    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

    # Direct routes for frontend HTML files
    @app.get("/", include_in_schema=False)
    async def serve_index():
        return FileResponse(FRONTEND_DIR / "index.html")

    @app.get("/{page_name}.html", include_in_schema=False)
    async def serve_html_page(page_name: str):
        target = FRONTEND_DIR / f"{page_name}.html"
        if target.exists():
            return FileResponse(target)
        raise HTTPException(status_code=404, detail="Page not found")

    @app.get("/{page_name}", include_in_schema=False)
    async def serve_page_clean_url(page_name: str):
        if page_name in ("api", "docs", "redoc", "openapi.json", "css", "js", "static"):
            raise HTTPException(status_code=404, detail="Not found")
        target_html = FRONTEND_DIR / f"{page_name}.html"
        if target_html.exists():
            return FileResponse(target_html)
        target_direct = FRONTEND_DIR / page_name
        if target_direct.exists() and target_direct.is_file():
            return FileResponse(target_direct)
        raise HTTPException(status_code=404, detail="Page not found")
