from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class TestRun(BaseModel):
    id:                      Optional[str]      = None
    browser:                 str
    platform:                str
    status:                  str
    browserstack_session_id: Optional[str]      = None
    created_at:              Optional[datetime] = None


class Article(BaseModel):
    id:          Optional[str]      = None
    test_run_id: Optional[str]      = None
    title_es:    str
    title_en:    Optional[str]      = None
    content_es:  Optional[str]      = None
    image_url:   Optional[str]      = None
    article_url: Optional[str]      = None
    scraped_at:  Optional[datetime] = None


class WordFrequency(BaseModel):
    id:          Optional[str] = None
    test_run_id: Optional[str] = None
    word:        str
    count:       int