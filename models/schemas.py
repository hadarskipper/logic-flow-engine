"""Pydantic models for API request/response schemas."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class ProcessCallResponse(BaseModel):
    """Response model for process-call endpoint."""
    
    status: str
    execution_path: List[str]
    final_output: Dict[str, Any]
    processing_time_seconds: float
    log_file: Optional[str] = None


class HealthResponse(BaseModel):
    """Response model for health check endpoint."""
    
    status: str
    message: str


class TreeStructureResponse(BaseModel):
    """Response model for tree-structure endpoint."""
    
    tree_name: str
    start_node: str
    nodes: Dict[str, Any]


class LogFileResponse(BaseModel):
    """Response model for get-log endpoint."""
    
    call_id: str
    commit_sha: str
    log_file_path: str
    log_content: str
    file_size_bytes: int
    last_modified: str


class ResultResponse(BaseModel):
    """Response model for get-result endpoint."""
    
    call_id: str
    commit_sha: str
    result_file_path: str
    result: Dict[str, Any]
    file_size_bytes: int
    last_modified: str
