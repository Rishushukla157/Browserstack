from fastapi import APIRouter, HTTPException
from backend.database import db

router = APIRouter()


@router.get("/")
def get_articles():
    articles = db.get_all_articles()
    return {"total": len(articles), "articles": articles}


@router.get("/{article_id}")
def get_article(article_id: str):
    articles = db.get_all_articles()
    match = next((a for a in articles if a["id"] == article_id), None)
    if not match:
        raise HTTPException(status_code=404, detail="Article not found")
    return match


@router.get("/run/{run_id}")
def get_articles_by_run(run_id: str):
    articles = db.get_articles_by_run(run_id)
    return {"run_id": run_id, "total": len(articles), "articles": articles}