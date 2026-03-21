"""FastAPI application — Exposes the article pipeline as a REST API."""
import os
import uuid
import time
import threading
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from typing import Optional
from core.logger import setup_logger, get_logger

setup_logger()
logger = get_logger("api")

app = FastAPI(
    title="Fabrica de Artigos SEO — API",
    version="1.0.0",
    description="REST API for automated SEO article generation",
)

# In-memory job store (replace with Redis for production)
_jobs = {}

# API keys per tenant (loaded from env: API_KEY_MJESUS=xxx)
def _get_tenant_from_key(api_key: str) -> Optional[str]:
    """Validate API key and return tenant ID."""
    from core.tenant_config import TenantConfig
    for tenant_id in TenantConfig.list_all():
        env_key = os.getenv(f"API_KEY_{tenant_id.upper()}", "")
        if env_key and env_key == api_key:
            return tenant_id
    return None


# --- Models ---

class GenerateRequest(BaseModel):
    keyword: str
    dry_run: bool = True


class JobResponse(BaseModel):
    job_id: str
    status: str
    keyword: str
    tenant: str


class ArticleResponse(BaseModel):
    job_id: str
    status: str
    title: str = ""
    content: str = ""
    seo_score: int = 0
    seo_grade: str = ""
    slug: str = ""
    error: str = ""


# --- Endpoints ---

@app.get("/health")
async def health():
    return {"status": "ok", "timestamp": time.strftime('%Y-%m-%d %H:%M:%S')}


@app.post("/generate", response_model=JobResponse)
async def generate_article(request: GenerateRequest, x_api_key: str = Header(...)):
    """Queue an article generation job."""
    tenant_id = _get_tenant_from_key(x_api_key)
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Invalid API key")

    job_id = str(uuid.uuid4())[:8]
    _jobs[job_id] = {
        "job_id": job_id,
        "status": "queued",
        "tenant": tenant_id,
        "keyword": request.keyword,
        "dry_run": request.dry_run,
        "created_at": time.time(),
        "result": None,
    }

    # Run in background thread
    thread = threading.Thread(
        target=_run_pipeline,
        args=(job_id, tenant_id, request.keyword, request.dry_run),
        daemon=True,
    )
    thread.start()

    return JobResponse(
        job_id=job_id,
        status="queued",
        keyword=request.keyword,
        tenant=tenant_id,
    )


@app.get("/status/{job_id}", response_model=ArticleResponse)
async def get_job_status(job_id: str, x_api_key: str = Header(...)):
    """Check job status and get results."""
    tenant_id = _get_tenant_from_key(x_api_key)
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Invalid API key")

    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job["tenant"] != tenant_id:
        raise HTTPException(status_code=403, detail="Access denied")

    result = job.get("result") or {}
    return ArticleResponse(
        job_id=job_id,
        status=job["status"],
        title=result.get("title", ""),
        content=result.get("content", "")[:500],  # Truncate for status check
        seo_score=result.get("seo_score", 0),
        seo_grade=result.get("seo_grade", ""),
        slug=result.get("slug", ""),
        error=result.get("error", ""),
    )


@app.get("/articles")
async def list_articles(x_api_key: str = Header(...), limit: int = 20):
    """List recent jobs for the authenticated tenant."""
    tenant_id = _get_tenant_from_key(x_api_key)
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Invalid API key")

    tenant_jobs = [
        {
            "job_id": j["job_id"],
            "status": j["status"],
            "keyword": j["keyword"],
            "created_at": time.strftime('%Y-%m-%d %H:%M', time.localtime(j["created_at"])),
            "seo_score": (j.get("result") or {}).get("seo_score", 0),
        }
        for j in _jobs.values()
        if j["tenant"] == tenant_id
    ]

    tenant_jobs.sort(key=lambda x: x["job_id"], reverse=True)
    return tenant_jobs[:limit]


# --- Background worker ---

def _run_pipeline(job_id, tenant_id, keyword, dry_run):
    """Run the article pipeline in a background thread."""
    job = _jobs[job_id]
    job["status"] = "processing"

    try:
        from core.tenant_config import TenantConfig
        from core.llm_client import LLMClient
        from core.knowledge_base import KnowledgeBase
        from core.pipeline import ArticlePipeline
        from core.prompt_engine import PromptEngine
        from core.kb_cache import KnowledgeBaseCache
        from core.rate_limiter import RateLimiter
        from core.circuit_breaker import CircuitBreaker

        tc = TenantConfig.load(tenant_id)
        llm = LLMClient(
            rate_limiter=RateLimiter(rpm=15),
            circuit_breaker=CircuitBreaker(name="gemini", failure_threshold=5, cooldown=60),
        )
        kb = KnowledgeBase(tc.kb_path)
        prompt_engine = PromptEngine(tc)
        kb_cache = KnowledgeBaseCache(ttl=3600)

        pipeline = ArticlePipeline(
            llm, kb,
            prompt_engine=prompt_engine,
            kb_cache=kb_cache,
            tenant_config=tc,
        )

        site = tc.to_site_config()
        result = pipeline.run(keyword, [], site_config=site)

        if result.success:
            job["status"] = "completed"
            job["result"] = {
                "title": result.title,
                "content": result.content,
                "seo_score": result.seo_score,
                "seo_grade": result.seo_grade,
                "slug": result.slug,
                "meta_description": result.meta_description,
            }
        else:
            job["status"] = "failed"
            job["result"] = {"error": result.error}

    except Exception as e:
        job["status"] = "failed"
        job["result"] = {"error": str(e)}
        logger.error("Pipeline failed for job %s: %s", job_id, e)
