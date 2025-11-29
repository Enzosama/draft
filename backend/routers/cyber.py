from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from backend.database import db
from pydantic import BaseModel

router = APIRouter()

class CyberResource(BaseModel):
    id: Optional[int]
    topic_id: Optional[int]
    title: str
    resource_type: str
    source: Optional[str]
    is_offensive: bool
    is_defensive: bool
    difficulty: Optional[str]
    tags: Optional[str]
    summary: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]

class CyberTopic(BaseModel):
    id: Optional[int]
    slug: str
    name: str
    topic_type: str
    domain: Optional[str]
    level: Optional[str]
    description: Optional[str]
    created_at: Optional[str]
    resources: List[CyberResource] = []

@router.get("/topics", response_model=List[CyberTopic])
async def get_topics():
    """Get all cyber security topics with their resources"""
    # Fetch all topics
    topics = await db.fetch_all("SELECT * FROM cyber_topics ORDER BY id")
    
    result = []
    for topic in topics:
        t_dict = dict(topic)
        # Fetch resources for this topic
        resources = await db.fetch_all(
            "SELECT * FROM cyber_resources WHERE topic_id = ?", 
            [t_dict['id']]
        )
        t_dict['resources'] = [dict(r) for r in resources]
        result.append(t_dict)
        
    return result

@router.get("/topics/{slug}", response_model=CyberTopic)
async def get_topic_by_slug(slug: str):
    """Get a specific topic by slug"""
    topic = await db.fetch_one("SELECT * FROM cyber_topics WHERE slug = ?", [slug])
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
        
    t_dict = dict(topic)
    resources = await db.fetch_all(
        "SELECT * FROM cyber_resources WHERE topic_id = ?", 
        [t_dict['id']]
    )
    t_dict['resources'] = [dict(r) for r in resources]
    
    return t_dict
