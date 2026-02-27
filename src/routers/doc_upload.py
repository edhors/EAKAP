from fastapi import APIRouter, Depends, HTTPException, UploadFile, File

import os

from uuid import uuid4

import redis

from src.routers import bus_settings, DocEventMsg

router = APIRouter()

# Initialize Redis connection
r = redis.Redis(
    host=bus_settings.REDIS_HOST, 
    port=bus_settings.REDIS_PORT, 
    decode_responses=True
)

@router.post("/publish-doc")
async def publish_document_event(
    dept: str, 
    project: str, 
    clearance: int,
    url: str  # Now receiving the URL string directly
):
    try:
        # 1. Create and Validate the Message Schema
        event_msg = DocEventMsg(
            action="CREATE",
            doc_id=str(uuid4()),
            link=url,
            dept=dept,
            project=project,
            clearance=clearance
        )

        # 2. Publish to the Redis Stream
        # No file saving, no DB calls—just passing information.
        r.xadd(bus_settings.DOC_OPS_STREAM, event_msg.model_dump())
        
        return {
            "status": "Event Published", 
            "doc_id": event_msg.doc_id, 
            "stream": bus_settings.DOC_OPS_STREAM
        }

    except Exception as e:
        # If Redis is down or data is invalid, catch it here
        raise HTTPException(status_code=500, detail=f"Event Bus Error: {str(e)}")