"""FastAPI application for healthcare call processing."""

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from engine.tree_executor import TreeExecutor
from github_client import get_default_github_url, get_latest_commit_sha
from models.schemas import HealthResponse, LogFileResponse, ProcessCallResponse, TreeStructureResponse
from utils.logging_utils import call_logging_context, get_latest_log_file

# Configure base logging (console output)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],  # Console only, file handlers added per request
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Decision Tree Call Processing API",
    description="Process healthcare call audio files using YAML-based decision tree workflow",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Allow requests from your webapp
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# Default GitHub config URL (from github_client)
DEFAULT_GITHUB_CONFIG_URL = get_default_github_url()


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        Health status response
    """
    return HealthResponse(status="healthy", message="API is running")


@app.get("/tree-structure", response_model=TreeStructureResponse)
async def get_tree_structure(
    commit_sha: Optional[str] = Query(None, description="Optional commit SHA for GitHub config (defaults to latest)")
):
    """
    Get the current decision tree structure.
    
    Args:
        commit_sha: Optional commit SHA for GitHub config (defaults to latest/main branch)
        
    Returns:
        Tree structure information
    """
    try:
        tree_executor = TreeExecutor(DEFAULT_GITHUB_CONFIG_URL, commit_sha=commit_sha)
        structure = tree_executor.get_tree_structure()
        return TreeStructureResponse(**structure)
    except Exception as e:
        logger.error(f"Error retrieving tree structure: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/process-call", response_model=ProcessCallResponse)
async def process_call(
    audio_file: UploadFile = File(..., description="MP3 audio file to process"),
    call_id: str = "default",
    commit_sha: Optional[str] = Query(None, description="Optional commit SHA for GitHub config (defaults to latest)")
):
    """
    Process a healthcare call audio file through the decision tree.
    
    Args:
        audio_file: MP3 audio file uploaded via multipart form
        call_id: Optional call identifier for metadata lookup
        commit_sha: Optional commit SHA for GitHub config (defaults to latest/main branch)
        
    Returns:
        Processing results with execution path and outputs
    """
    # Get latest commit SHA if not provided (before setting up logging)
    if commit_sha is None:
        try:
            commit_sha = get_latest_commit_sha()
            logger.info(f"Fetched latest commit SHA: {commit_sha}")
        except Exception as e:
            logger.error(f"Failed to fetch latest commit SHA: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch latest commit SHA from GitHub: {str(e)}"
            )
    
    # Set up per-call logging with call_id and commit_sha
    with call_logging_context(call_id, commit_sha=commit_sha) as log_filepath:
        try:
            # Validate file type
            if not audio_file.filename.endswith((".mp3", ".MP3")):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid file type. Only MP3 files are supported.",
                )
            
            logger.info(f"Processing call: {call_id}, File: {audio_file.filename}, Commit SHA: {commit_sha or 'latest'}")
            logger.info(f"Log file: {log_filepath}")
            
            # Read audio file content
            audio_content = await audio_file.read()
            
            # Prepare initial workflow data
            initial_workflow_data = {
                "audio_file": audio_content,  # Store file content for processing
                "call_id": call_id,
                "filename": audio_file.filename,
            }
            
            # Create tree executor with GitHub config and commit SHA
            tree_executor = TreeExecutor(DEFAULT_GITHUB_CONFIG_URL, commit_sha=commit_sha)
            
            # Execute decision tree
            result = tree_executor.execute(initial_workflow_data)
            
            logger.info(f"Call processing completed: {result['status']}")
            
            # Add log file path to response
            response_data = {
                **result,
                "log_file": str(log_filepath),
            }
            
            return ProcessCallResponse(**response_data)
        
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error processing call: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error processing call: {str(e)}")


@app.get("/logs/{call_id}", response_model=LogFileResponse)
async def get_log_file(
    call_id: str,
    commit_sha: str = Query(..., description="Commit SHA to filter log files")
):
    """
    Get the latest log file for a specific call_id and commit_sha.
    
    Args:
        call_id: Call identifier
        commit_sha: Commit SHA to filter log files
        
    Returns:
        Log file content and metadata
    """
    try:
        log_file_path = get_latest_log_file(call_id, commit_sha)
        
        if log_file_path is None or not log_file_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"No log file found for call_id: {call_id}, commit_sha: {commit_sha}"
            )
        
        # Read log file content
        try:
            with open(log_file_path, "r", encoding="utf-8") as f:
                log_content = f.read()
        except Exception as e:
            logger.error(f"Error reading log file {log_file_path}: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Error reading log file: {str(e)}"
            )
        
        # Get file metadata
        file_stat = log_file_path.stat()
        last_modified = datetime.fromtimestamp(file_stat.st_mtime).isoformat()
        
        return LogFileResponse(
            call_id=call_id,
            commit_sha=commit_sha,
            log_file_path=str(log_file_path),
            log_content=log_content,
            file_size_bytes=file_stat.st_size,
            last_modified=last_modified
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving log file: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving log file: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(app, host="0.0.0.0", port=8000)

