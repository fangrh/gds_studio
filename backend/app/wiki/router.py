from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.db import get_db
from app.models import WikiPage
from app.wiki.schemas import (
    WikiPageCreate, WikiPageUpdate, WikiPageResponse, WikiPageListResponse,
)

router = APIRouter(prefix="/api/wiki", tags=["wiki"])


@router.get("", response_model=list[WikiPageListResponse])
def list_wiki_pages(
    category: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(WikiPage)
    if category:
        q = q.filter(WikiPage.category == category)
    return q.order_by(WikiPage.updated_at.desc()).all()


@router.post("", response_model=WikiPageResponse, status_code=201)
def create_wiki_page(data: WikiPageCreate, db: Session = Depends(get_db)):
    existing = db.query(WikiPage).filter(WikiPage.slug == data.slug).first()
    if existing:
        raise HTTPException(409, f"Slug '{data.slug}' already exists")
    page = WikiPage(
        title=data.title,
        slug=data.slug,
        body=data.body,
        category=data.category,
        tags=data.tags,
        version=1,
    )
    db.add(page)
    db.commit()
    db.refresh(page)
    return page


@router.get("/{slug}", response_model=WikiPageResponse)
def get_wiki_page(slug: str, db: Session = Depends(get_db)):
    page = db.query(WikiPage).filter(WikiPage.slug == slug).first()
    if not page:
        raise HTTPException(404, "Wiki page not found")
    return page


@router.patch("/{slug}", response_model=WikiPageResponse)
def update_wiki_page(slug: str, data: WikiPageUpdate, db: Session = Depends(get_db)):
    page = db.query(WikiPage).filter(WikiPage.slug == slug).first()
    if not page:
        raise HTTPException(404, "Wiki page not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(page, key, value)
    page.version += 1

    db.commit()
    db.refresh(page)
    return page
