from fastapi import APIRouter
from backend.database import db

router = APIRouter()


@router.get("/{run_id}")
def get_analysis(run_id: str):
    word_freq = db.get_word_frequency_by_run(run_id)
    return {
        "run_id":                      run_id,
        "total_unique_repeated_words": len(word_freq),
        "word_frequency":              word_freq,
    }