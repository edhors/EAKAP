from pydantic import BaseModel, HttpUrl
from typing import Literal, Optional, Dict, Any

# --- Document Stream Schema ---
class DocEventMsg(BaseModel):
    """Schema for doc_ops_stream messages."""
    action: Literal["CREATE", "UPDATE", "DELETE"]
    doc_id: str
    # For CREATE/UPDATE, a link is required; for DELETE, it can be None
    link: Optional[HttpUrl] = None
    # Metadata for the RS Generator (SpiceDB)
    dept: Optional[str] = None
    project: Optional[str] = None
    clearance: Optional[int] = None

# --- Policy Stream Schema ---
class PolicyEventMsg(BaseModel):
    """Schema for policy_ops_stream messages."""
    action: Literal["SET_RULE", "REMOVE_RULE"]
    policy_id: str
    logic_type: str  # e.g., "DEPT_ACCESS" or "CLEARANCE_HIERARCHY"
    # Flexible payload for different policy types
    payload: Dict[str, Any]

# --- Dead Letter Queue (DLQ) Schema ---
class FailureEventMsg(BaseModel):
    """Schema for failed_events_stream messages."""
    original_data: Dict[str, Any]
    origin_stream: str
    error_reason: str
    worker_id: str