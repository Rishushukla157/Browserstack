from fastapi import APIRouter
from backend.database import db

router = APIRouter()


@router.get("/")
def get_test_runs():
    runs   = db.get_all_test_runs()
    passed = sum(1 for r in runs if r.get("status") == "passed")
    failed = sum(1 for r in runs if r.get("status") == "failed")
    return {"total": len(runs), "passed": passed, "failed": failed, "runs": runs}


@router.get("/{run_id}")
def get_test_run(run_id: str):
    runs = db.get_all_test_runs()
    run  = next((r for r in runs if r["id"] == run_id), None)
    if not run:
        return {"error": "Run not found"}
    return {
        "run":            run,
        "articles":       db.get_articles_by_run(run_id),
        "word_frequency": db.get_word_frequency_by_run(run_id),
    }